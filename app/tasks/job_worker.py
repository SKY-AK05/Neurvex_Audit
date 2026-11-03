"""
job_worker.py — Resilient background worker for post-submit processing.
Handles durable background queue (post_submit_jobs):
1. Email body rendering and dispatch (via ACS)
2. HubSpot CRM sync with exponential backoff & dead-letter tracking (resolves DEF-006)
3. Recovery of crashed/stranded workers (reclaims stuck PROCESSING jobs)
4. Draining legacy email_dlq table
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import psycopg2.extras

from app.core.database import get_db_connection
from app.services.scoring_service import build_email, _e
from app.services.settings_service import send_acs_email
from app.services.crm_service import sync_to_hubspot

logger = logging.getLogger(__name__)

_worker_running = False
_worker_task: Optional[asyncio.Task] = None

SECTION_META = [
    ("lc", "Leadership & Culture"),
    ("ro", "Recruitment & Onboarding"),
    ("we", "Work Environment"),
    ("be", "Built Environment"),
    ("tm", "Talent Management"),
    ("ca", "Communication & Accessibility"),
    ("pc", "Products & Customer Service"),
    ("sp", "Supply Chain & Procurement"),
]


def reconstruct_section_scores(sub_row: dict) -> list:
    """Reconstruct section scores list for build_email from persisted row."""
    section_scores = []
    dim_scores = sub_row.get("dimension_scores")
    if isinstance(dim_scores, str):
        try:
            dim_scores = json.loads(dim_scores)
        except Exception:
            dim_scores = {}
    elif not isinstance(dim_scores, dict):
        dim_scores = {}

    for key, label in SECTION_META:
        score_val = sub_row.get(f"{key}_score")
        level_val = sub_row.get(f"{key}_level") or "Foundational"
        
        # Check NA
        if score_val is None or score_val == "NA":
            score_formatted = "NA"
            level_formatted = "Not applicable"
        else:
            try:
                score_formatted = float(score_val)
                level_formatted = str(level_val)
            except (ValueError, TypeError):
                score_formatted = "NA"
                level_formatted = "Not applicable"

        # Low visibility check if present in dimension_scores metadata
        is_low_vis = dim_scores.get(f"{key}_low_visibility", False)
        section_scores.append((key, label, score_formatted, level_formatted, is_low_vis))

    return section_scores


def claim_next_job(worker_id: str = "worker-1") -> Optional[dict]:
    """Claim one pending or retryable job using SELECT ... FOR UPDATE SKIP LOCKED."""
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, submission_id, job_type, payload, attempts, max_attempts
                        FROM post_submit_jobs
                        WHERE status IN ('PENDING', 'RETRY')
                          AND next_attempt_at <= NOW()
                        ORDER BY created_at ASC
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                    """)
                    job = cur.fetchone()
                    if job:
                        cur.execute("""
                            UPDATE post_submit_jobs
                            SET status = 'PROCESSING',
                                locked_at = NOW(),
                                locked_by = %s,
                                attempts = attempts + 1,
                                updated_at = NOW()
                            WHERE id = %s
                        """, (worker_id, job["id"]))
                        return dict(job)
    except Exception as e:
        logger.error("Failed to claim post-submit job: %s", e)
    return None


def reclaim_stranded_jobs() -> int:
    """Reclaim jobs stuck in PROCESSING longer than 5 minutes due to worker crashes."""
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE post_submit_jobs
                        SET status = 'RETRY',
                            next_attempt_at = NOW(),
                            locked_at = NULL,
                            locked_by = NULL,
                            updated_at = NOW()
                        WHERE status = 'PROCESSING'
                          AND locked_at < NOW() - INTERVAL '5 minutes'
                    """)
                    reclaimed = cur.rowcount
                    if reclaimed > 0:
                        logger.warning("Reclaimed %d stranded post_submit_jobs", reclaimed)
                    return reclaimed
    except Exception as e:
        logger.error("Failed to reclaim stranded jobs: %s", e)
        return 0


def process_email_job(submission_id: str, payload: dict) -> None:
    """Generate email body from persisted scores and update submission."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM submissions WHERE id = %s", (str(submission_id),))
            sub_row = cur.fetchone()

    if not sub_row:
        logger.warning("Submission %s not found for email job", submission_id)
        return

    section_scores = reconstruct_section_scores(sub_row)
    overall_avg = float(sub_row.get("overall_avg") or 0.0)
    overall_level = str(sub_row.get("overall_level") or "Level 1 — Foundational")

    html_email = build_email(
        name=sub_row.get("name") or "",
        designation=sub_row.get("designation") or "",
        company_name=sub_row.get("company_name") or "",
        contact_number=sub_row.get("contact_number") or "",
        section_scores=section_scores,
        overall_avg=overall_avg,
        overall_level=overall_level,
    )

    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE submissions SET email_body = %s WHERE id = %s",
                    (html_email, str(submission_id))
                )
    logger.info("Generated and stored email body for submission %s", submission_id)


def process_crm_job(submission_id: str, payload: dict) -> None:
    """Sync submission to HubSpot CRM with error bubbling for retry tracking."""
    data = payload.get("data") or {}
    score_data = payload.get("score_data") or {}
    sync_to_hubspot(data, score_data, str(submission_id))


def complete_job(job_id: str) -> None:
    """Mark job as DONE in post_submit_jobs."""
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE post_submit_jobs
                        SET status = 'DONE',
                            updated_at = NOW(),
                            locked_at = NULL,
                            locked_by = NULL
                        WHERE id = %s
                    """, (str(job_id),))
    except Exception as e:
        logger.error("Failed to mark job %s as DONE: %s", job_id, e)


def fail_or_retry_job(job_id: str, current_attempts: int, max_attempts: int, error_msg: str) -> None:
    """Schedule retry with exponential backoff or mark FAILED."""
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    if current_attempts >= max_attempts:
                        cur.execute("""
                            UPDATE post_submit_jobs
                            SET status = 'FAILED',
                                last_error = %s,
                                updated_at = NOW(),
                                locked_at = NULL,
                                locked_by = NULL
                            WHERE id = %s
                        """, (error_msg[:1000], str(job_id)))
                        logger.error("Job %s permanently FAILED after %d attempts: %s", job_id, current_attempts, error_msg)
                    else:
                        delay_secs = min(300, 5 * (2 ** max(0, current_attempts - 1)))
                        next_retry = datetime.now(timezone.utc) + timedelta(seconds=delay_secs)
                        cur.execute("""
                            UPDATE post_submit_jobs
                            SET status = 'RETRY',
                                next_attempt_at = %s,
                                last_error = %s,
                                updated_at = NOW(),
                                locked_at = NULL,
                                locked_by = NULL
                            WHERE id = %s
                        """, (next_retry, error_msg[:1000], str(job_id)))
                        logger.warning("Job %s scheduled for retry in %ds (attempt %d/%d)", job_id, delay_secs, current_attempts, max_attempts)
    except Exception as e:
        logger.error("Failed to update retry status for job %s: %s", job_id, e)


def drain_legacy_email_dlq() -> None:
    """Drain any pending items in legacy email_dlq table safely with SKIP LOCKED."""
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, submission_id, payload, attempts
                        FROM email_dlq
                        WHERE status = 'pending' AND next_retry_at <= NOW()
                        ORDER BY created_at ASC
                        LIMIT 5
                        FOR UPDATE SKIP LOCKED
                    """)
                    rows = cur.fetchall()
                    for row in rows:
                        payload = row.get("payload")
                        if isinstance(payload, str):
                            try:
                                payload = json.loads(payload)
                            except Exception:
                                payload = {}
                        try:
                            send_acs_email(**payload)
                            cur.execute("UPDATE email_dlq SET status = 'sent' WHERE id = %s", (row["id"],))
                            cur.execute("UPDATE submissions SET status = 'sent', sent_at = NOW() WHERE id = %s", (row["submission_id"],))
                        except Exception as e:
                            attempts = row.get("attempts", 0) + 1
                            if attempts >= 5:
                                cur.execute("UPDATE email_dlq SET status = 'failed', attempts = %s, last_error = %s WHERE id = %s", (attempts, str(e), row["id"]))
                            else:
                                next_retry = datetime.now(timezone.utc) + timedelta(minutes=10)
                                cur.execute("UPDATE email_dlq SET attempts = %s, last_error = %s, next_retry_at = %s WHERE id = %s", (attempts, str(e), next_retry, row["id"]))
    except Exception as e:
        logger.error("Legacy DLQ drain error: %s", e)


async def run_job_worker(worker_id: str = "worker-1", poll_interval: float = 2.0):
    """Main worker loop."""
    global _worker_running
    _worker_running = True
    logger.info("Started background job worker [%s]", worker_id)

    last_reclaim = 0.0

    while _worker_running:
        try:
            loop_now = asyncio.get_event_loop().time()
            # Every 60 seconds, reclaim any stranded jobs
            if loop_now - last_reclaim > 60:
                await asyncio.to_thread(reclaim_stranded_jobs)
                await asyncio.to_thread(drain_legacy_email_dlq)
                last_reclaim = loop_now

            # Claim next job
            job = await asyncio.to_thread(claim_next_job, worker_id)
            if not job:
                await asyncio.sleep(poll_interval)
                continue

            job_id = job["id"]
            sub_id = job["submission_id"]
            j_type = job["job_type"]
            payload = job.get("payload") or {}
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}

            logger.info("Executing job %s (type=%s, sub=%s)", job_id, j_type, sub_id)
            try:
                if j_type == "email":
                    await asyncio.to_thread(process_email_job, sub_id, payload)
                elif j_type == "crm":
                    await asyncio.to_thread(process_crm_job, sub_id, payload)
                else:
                    logger.warning("Unknown job type: %s", j_type)

                await asyncio.to_thread(complete_job, job_id)
            except Exception as job_err:
                logger.error("Job execution error (id=%s, type=%s): %s", job_id, j_type, job_err)
                await asyncio.to_thread(
                    fail_or_retry_job,
                    job_id,
                    job["attempts"],
                    job.get("max_attempts", 5),
                    str(job_err)
                )

        except asyncio.CancelledError:
            logger.info("Background job worker cancelled")
            break
        except Exception as e:
            logger.error("Unexpected error in job worker loop: %s", e)
            await asyncio.sleep(poll_interval)

    _worker_running = False
    logger.info("Background job worker stopped")


async def start_job_worker(worker_id: str = "worker-1"):
    """Start background job worker as an asyncio task."""
    global _worker_task
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(run_job_worker(worker_id))
        logger.info("Created background job worker task")


def stop_job_worker():
    """Signal background job worker to stop."""
    global _worker_running, _worker_task
    _worker_running = False
    if _worker_task and not _worker_task.done():
        _worker_task.cancel()

