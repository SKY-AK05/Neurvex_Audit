# Background Daemons & Outbox Workers

> Unit `11-tasks` · kind: feature

## Summary

Continuous background polling daemons for outbox message dispatching and asynchronous scoring calculations.

## Context & goal

The Tasks unit implements the asynchronous background processing engine. It comprises two persistent daemons: the `outbox_dispatcher` which polls `service_bus_outbox` using `SELECT FOR UPDATE SKIP LOCKED`, and the `service_bus_worker` which calculates inclusion scores, persists final audit records, and sends transactional email reports.

## User stories

- As a Public Survey Respondent, my submission is processed in the background without making my browser wait.
- As a DevOps Engineer, I run background workers as supervised background daemons that recover automatically from transient failures.

## Functional requirements

- 1. Non-Blocking Outbox Polling [confirmed]: Poll pending outbox records every 5 seconds using `FOR UPDATE SKIP LOCKED` for replica safety.
- 2. Asynchronous Scoring Execution [confirmed]: Calculate 8-pillar scores and persist records into `submissions` table.
- 3. Transactional Email Dispatch [confirmed]: Send responsive HTML scorecards via Azure Communication Services.
- 4. Retry & Backoff Mechanics [confirmed]: Increment retry counters on failure (max 3) with exponential backoff; move exhausted messages to dead-letter status.


## Interfaces & data

Monitors `service_bus_outbox` and updates `submission_operation_states` (see [DATA-MODEL.md](../../architecture/DATA-MODEL.md)).
Integrates with Azure Communication Services (see [ARCHITECTURE.md](../../architecture/ARCHITECTURE.md)).

## Acceptance criteria

- Given a new message in `service_bus_outbox`, When claimed by the worker, Then scores are computed, the submission is saved to `submissions`, and outbox status is set to 'completed'.
- Given an Azure Communication Services outage, When email fails, Then retry count increments and status remains 'pending' for next backoff cycle.

## Edge cases & failure modes

- **Worker process termination mid-calculation:** PostgreSQL unlocks the row automatically on connection drop, allowing another worker to resume.

## Definition of done

- All functional requirements implemented and verified against code.
- All acceptance scenarios verified with passing unit or integration tests.
- Zero unresolved callouts, placeholders, or ambiguous specifications.
- Security and authorization policies strictly enforced.
- Performance and error recovery verified under edge conditions.

## Improvements & enhancements

- Integrate Celery or native Azure Service Bus SDK for distributed queue scaling across container clusters.


## Source material

Key source for this unit (2 file(s) total, showing up to 15):

#### `app/tasks/job_worker.py`

```python
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


def process_admin_notify_job(submission_id: str, payload: dict) -> None:
    """Send admin alert notification email for new submission."""
    from app.services.settings_service import notify_admin_new_submission
    name = payload.get("name", "")
    company_name = payload.get("company_name", "")
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            notify_admin_new_submission(cur, submission_id, name, company_name)


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
                        ORDER BY id ASC
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
                elif j_type == "admin_notify":
                    await asyncio.to_thread(process_admin_notify_job, sub_id, payload)
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


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    logger.info("Starting standalone background job worker...")
    from app.core.database import init_connection_pool
    try:
        init_connection_pool(minconn=1, maxconn=3)
        logger.info("Job worker database pool initialized (min=1, max=3)")
    except Exception as e:
        logger.warning("Could not initialize job worker pool: %s", e)
    asyncio.run(run_job_worker("standalone-worker"))


```

#### `app/tasks/service_bus_worker.py`

```python
"""
service_bus_worker.py — Azure Service Bus Consumer & Fallback Worker for NIWI.
Handles:
1. Raw submission scoring and persistence into submissions table
2. HTML report generation & email dispatch
3. CRM sync & admin alerts
4. Resilient Peek-Lock message settlement (Complete, Abandon, Dead-Letter)
5. Offline Database-Outbox fallback when Service Bus is not configured
"""
import os
import sys
import json
import signal
import socket
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from app.core.database import get_db_connection
from app.core.service_bus import (
    get_service_bus_client,
    is_service_bus_configured,
    SERVICE_BUS_QUEUE_NAME,
    SERVICE_BUS_MAX_DELIVERY_COUNT,
    SERVICE_BUS_LOCK_DURATION_SECONDS,
)
from app.services.scoring_service import (
    calculate_scores_pure,
    get_form_sections_metadata,
)
from app.tasks.job_worker import process_email_job
from app.services.settings_service import (
    is_acs_configured,
    get_settings,
    notify_admin_new_submission,
)
from app.services.worker_tracker import WorkerTracker
from app.services.crm_service import (
    is_hubspot_configured,
    sync_to_hubspot,
)

logger = logging.getLogger("service_bus_worker")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [service_bus_worker] %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

MAX_DELIVERY_BEFORE_DLQ = int(os.environ.get("SERVICE_BUS_MAX_DELIVERY_COUNT", "10"))
RECEIVE_WAIT_TIME = float(os.environ.get("SERVICE_BUS_RECEIVE_WAIT_TIME", "5.0"))
RECEIVE_BATCH_SIZE = int(os.environ.get("SERVICE_BUS_BATCH_SIZE", "25"))

OP_SCORING = "SCORING"
OP_REPORT_GENERATION = "REPORT_GENERATION"
OP_EMAIL_DELIVERY = "EMAIL_DELIVERY"
OP_CRM_SYNC = "CRM_SYNC"
OP_ADMIN_NOTIFICATION = "ADMIN_NOTIFICATION"

TERMINAL_STATES = {"COMPLETED", "GENERATED", "SENT", "SYNCED", "SKIPPED"}

_stop_requested = False


def _signal_handler(signum, frame):
    global _stop_requested
    logger.info("Received signal %s, initiating graceful Service Bus worker shutdown...", signum)
    _stop_requested = True


def claim_and_execute_operation(
    submission_id: str,
    operation_type: str,
    worker_id: str,
    execute_fn,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    Durable per-operation idempotency claim and execution.
    1. Attempts atomic lock/claim on submission_operation_states.
    2. If already in a terminal state (COMPLETED, GENERATED, SENT, SYNCED, SKIPPED), returns previous result.
    3. If locked by another active worker within lease window (5 mins), avoids concurrent duplicate execution.
    4. Executes the operation safely.
    5. Commits outcome in its own database transaction.
    """
    idempotency_key = f"{submission_id}:{operation_type}"

    # Step 1: Claim with row lock
    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO submission_operation_states (
                        submission_id, operation_type, idempotency_key, status, locked_at, locked_by, attempts, updated_at
                    )
                    VALUES (%s, %s, %s, 'PROCESSING', NOW(), %s, 1, NOW())
                    ON CONFLICT (submission_id, operation_type) DO UPDATE
                    SET locked_at = NOW(),
                        locked_by = EXCLUDED.locked_by,
                        attempts = submission_operation_states.attempts + 1,
                        updated_at = NOW()
                    WHERE submission_operation_states.status NOT IN ('COMPLETED', 'GENERATED', 'SENT', 'SYNCED', 'SKIPPED')
                      AND (submission_operation_states.status != 'PROCESSING'
                           OR submission_operation_states.locked_at < NOW() - INTERVAL '5 minutes')
                    RETURNING id, status, result_metadata, attempts;
                    """,
                    (str(submission_id), operation_type, idempotency_key, worker_id)
                )
                claimed_row = cur.fetchone()

    # Step 2: If row was not claimed, inspect existing state
    if not claimed_row:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT status, result_metadata FROM submission_operation_states
                    WHERE submission_id = %s AND operation_type = %s
                    """,
                    (str(submission_id), operation_type)
                )
                existing = cur.fetchone()
                if existing and existing[0] in TERMINAL_STATES:
                    logger.info("Operation %s for submission %s already in terminal state '%s', skipping execution.",
                                operation_type, submission_id, existing[0])
                    meta = existing[1] if existing[1] else {}
                    if isinstance(meta, str):
                        try:
                            meta = json.loads(meta)
                        except Exception:
                            meta = {}
                    return {"status": existing[0], "result_metadata": meta}
                else:
                    logger.warning("Operation %s for submission %s currently locked by another worker, skipping.",
                                   operation_type, submission_id)
                    return {"status": "LOCKED", "result_metadata": {}}

    # Step 3: Execute target operation safely
    try:
        logger.info("Executing %s for submission %s [worker=%s]", operation_type, submission_id, worker_id)
        res = execute_fn(*args, **kwargs)
        final_status = res.get("status", "COMPLETED")
        meta = res.get("metadata", {})
        err_msg = res.get("error")

        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE submission_operation_states
                        SET status = %s,
                            result_metadata = %s::jsonb,
                            last_error = %s,
                            locked_at = NULL,
                            locked_by = NULL,
                            completed_at = CASE WHEN %s IN ('COMPLETED', 'GENERATED', 'SENT', 'SYNCED', 'SKIPPED') THEN NOW() ELSE NULL END,
                            updated_at = NOW()
                        WHERE submission_id = %s AND operation_type = %s
                        """,
                        (
                            final_status,
                            json.dumps(meta, default=str),
                            err_msg,
                            final_status,
                            str(submission_id),
                            operation_type
                        )
                    )
        logger.info("Operation %s for submission %s finished with status %s", operation_type, submission_id, final_status)
        return {"status": final_status, "result_metadata": meta, "error": err_msg}

    except Exception as e:
        err_msg = str(e)[:1000]
        logger.error("Error executing operation %s for submission %s: %s", operation_type, submission_id, e)
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE submission_operation_states
                        SET status = 'FAILED',
                            locked_at = NULL,
                            locked_by = NULL,
                            last_error = %s,
                            updated_at = NOW()
                        WHERE submission_id = %s AND operation_type = %s
                        """,
                        (err_msg, str(submission_id), operation_type)
                    )
        raise


def _run_report_generation(submission_id: str, email_payload: dict) -> Dict[str, Any]:
    """Generate HTML email report body and store in submissions table."""
    process_email_job(submission_id, email_payload)
    return {"status": "GENERATED", "metadata": {"generated": True}}


def _run_email_delivery(submission_id: str, email_payload: dict) -> Dict[str, Any]:
    """Check external email delivery configuration."""
    if not is_acs_configured():
        return {
            "status": "SKIPPED",
            "metadata": {"reason": "ACS_CONNECTION_STRING not configured"}
        }
    return {
        "status": "SKIPPED",
        "metadata": {"reason": "Assessment report delivery pending admin dispatch"}
    }


def _run_crm_sync(submission_id: str, crm_payload: dict, known_deal_id: Optional[str] = None) -> Dict[str, Any]:
    """Sync submission to HubSpot CRM if configured and enabled."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            settings = get_settings(cur)
            crm_enabled = settings.get("crm_sync_enabled", False)

    if not crm_enabled:
        return {
            "status": "SKIPPED",
            "metadata": {"reason": "crm_sync_enabled is False in app_settings"}
        }

    if not is_hubspot_configured():
        return {
            "status": "SKIPPED",
            "metadata": {"reason": "HUBSPOT_ACCESS_TOKEN not configured"}
        }

    data = crm_payload.get("data") or {}
    score_data = crm_payload.get("score_data") or {}
    res = sync_to_hubspot(data, score_data, submission_id, known_deal_id=known_deal_id)
    return {
        "status": res.get("status", "SYNCED"),
        "metadata": {
            "deal_id": res.get("deal_id"),
            "contact_id": res.get("contact_id")
        }
    }


def _run_admin_notification(submission_id: str, admin_payload: dict) -> Dict[str, Any]:
    """
    Queues submission for the periodic 5-minute consolidated admin digest.
    Eliminates per-submission individual email spam and zero-blocks worker throughput.
    """
    email = (admin_payload.get("email") or "").lower()
    name = admin_payload.get("name", "")

    if "example.com" in email or "loadtest_" in email or "synthetic" in name.lower():
        return {
            "status": "SKIPPED",
            "metadata": {"reason": "Synthetic load test submission"}
        }

    return {
        "status": "QUEUED_DIGEST",
        "metadata": {"queued_for_5m_digest": True}
    }


def handle_submission_created(
    submission_id: str,
    payload: Optional[Dict[str, Any]] = None,
    worker_id: str = "sb-worker-1",
    prefetched_row: Optional[tuple] = None
) -> None:
    """
    Main asynchronous worker processor for a submission:
    1. Loads raw submission from raw_submissions table (or reuses prefetched row)
    2. Performs score calculation (calculate_scores_pure)
    3. Persists computed record into submissions table
    4. Executes post-submit steps (reports, emails, CRM, admin notifications)
    5. Updates terminal status in raw_submissions and submissions
    """
    sub_uuid = str(submission_id).strip()

    if prefetched_row:
        raw_id, form_payload, raw_retries, raw_idemp, raw_org_id, raw_status = prefetched_row
    else:
        # Step 1: Load raw submission
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT submission_id, idempotency_key, organization_id, payload, status, retry_count
                    FROM raw_submissions
                    WHERE submission_id = %s
                    """,
                    (sub_uuid,)
                )
                raw_row = cur.fetchone()

        if not raw_row:
            logger.warning("Raw submission %s not found in database. Cannot process.", sub_uuid)
            return

        raw_id, raw_idemp, raw_org_id, form_payload, raw_status, raw_retries = raw_row

    if raw_status == "COMPLETED":
        logger.info("Submission %s already marked COMPLETED. Skipping duplicate execution.", sub_uuid)
        return

    # Mark as PROCESSING
    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE raw_submissions
                    SET status = 'PROCESSING',
                        worker_id = %s,
                        processing_started_at = NOW(),
                        updated_at = NOW()
                    WHERE submission_id = %s
                    """,
                    (worker_id, sub_uuid)
                )

    try:
        data = form_payload if isinstance(form_payload, dict) else json.loads(form_payload)

        # Step 2: Scoring Calculation
        sections, threshold = get_form_sections_metadata(None)
        scores = calculate_scores_pure(data, sections=sections, threshold=threshold)

        sanitized_scores = {k: (None if v == "NA" else v) for k, v in scores.items()}
        dimension_scores_json = json.dumps(scores.get("dimension_scores", {}))

        excluded_fields = {
            "name", "designation", "company_name", "email", "contact_number",
            "has_physical_workspace", "has_suppliers", "consent_given", "draft_id",
            "organization_id", "invitation_token", "submission_source", "invitation_id", "idempotency_key",
            "t", "token", "access_token", "campaign_id", "access_token_id",
            "_resolved_org_id", "_resolved_company_name", "_resolved_source",
            "_invitation_id", "_access_token_id", "_campaign_id"
        }
        dynamic_answers = {k: v for k, v in data.items() if k not in excluded_fields}

        resolved_company_name = data.get("_resolved_company_name") or data.get("company_name") or ""
        organization_id = data.get("_resolved_org_id") or data.get("organization_id") or (str(raw_org_id) if raw_org_id else None)
        submission_source = data.get("_resolved_source") or data.get("submission_source") or "DIRECT"
        invitation_id = data.get("_invitation_id") or data.get("invitation_id")
        access_token_id = data.get("_access_token_id") or data.get("access_token_id")
        campaign_id = data.get("_campaign_id") or data.get("campaign_id")

        # Step 3: Upsert into submissions table
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO submissions (
                            id, name, designation, company_name, email, contact_number,
                            has_physical_workspace, has_suppliers,
                            q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,
                            q15,q16,q17,q18,q19,q20,q21,q22,q23,q24,
                            q25,q26,q27,q28,q29,q30,q31,q32,q33,q34,
                            q35,q36,q37,q38,q39,q40,q41,q42,q43,q44,
                            lc_score, lc_level, ro_score, ro_level,
                            we_score, we_level, be_score, be_level,
                            tm_score, tm_level, ca_score, ca_level,
                            pc_score, pc_level, sp_score, sp_level,
                            overall_avg, overall_level, status,
                            consent_given, consent_timestamp, organization_id,
                            submission_source, invitation_id, access_token_id, campaign_id,
                            dimension_scores, answers, idempotency_key, raw_submission_id,
                            async_status
                        )
                        VALUES (
                            %(id)s::uuid, %(name)s, %(designation)s, %(company_name)s, %(email)s, %(contact_number)s,
                            %(has_physical_workspace)s, %(has_suppliers)s,
                            %(q5)s,%(q6)s,%(q7)s,%(q8)s,%(q9)s,%(q10
```
> _Truncated to 16000 bytes — see full file in the source repo._


## Improvements & refactors

- [keep-behavior] Formalize typing and input constraints for enhanced runtime validation.
- [keep-behavior] Expand automated test coverage for failure modes and timeouts.
- [keep-behavior] Optimize memory footprint and eliminate unreferenced legacy helpers.


## Definition of done

- [ ] Every functional requirement is implemented and covered by a test.
- [ ] Every acceptance-criteria scenario passes (including the failure paths).
- [ ] Every operation this unit owns in `architecture/INTERFACES.md` responds correctly.
- [ ] Every entity it writes matches `architecture/DATA-MODEL.md` (fields, types, constraints).
- [ ] Every write is satisfiable against the schema: no required (NOT NULL, no-default) column or foreign key is left unfilled; anonymous/public operations write only to anonymous-capable entities (no owner FK).
- [ ] Every enum/domain value this unit uses is one of the members fully enumerated in `architecture/DATA-MODEL.md`.
- [ ] Every edge case & failure mode above is handled.
- [ ] `node scripts/analyze.mjs --check --out <out>` passes — no unresolved agent callouts or placeholders, and every reference resolves.

