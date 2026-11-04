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
                            %(q5)s,%(q6)s,%(q7)s,%(q8)s,%(q9)s,%(q10)s,%(q11)s,%(q12)s,%(q13)s,%(q14)s,
                            %(q15)s,%(q16)s,%(q17)s,%(q18)s,%(q19)s,%(q20)s,%(q21)s,%(q22)s,%(q23)s,%(q24)s,
                            %(q25)s,%(q26)s,%(q27)s,%(q28)s,%(q29)s,%(q30)s,%(q31)s,%(q32)s,%(q33)s,%(q34)s,
                            %(q35)s,%(q36)s,%(q37)s,%(q38)s,%(q39)s,%(q40)s,%(q41)s,%(q42)s,%(q43)s,%(q44)s,
                            %(lc_score)s, %(lc_level)s, %(ro_score)s, %(ro_level)s,
                            %(we_score)s, %(we_level)s, %(be_score)s, %(be_level)s,
                            %(tm_score)s, %(tm_level)s, %(ca_score)s, %(ca_level)s,
                            %(pc_score)s, %(pc_level)s, %(sp_score)s, %(sp_level)s,
                            %(overall_avg)s, %(overall_level)s, 'completed',
                            %(consent_given)s, %(consent_timestamp)s, %(organization_id)s::uuid,
                            %(submission_source)s, %(invitation_id)s, %(access_token_id)s, %(campaign_id)s,
                            %(dimension_scores)s::jsonb, %(answers)s::jsonb, %(idempotency_key)s, %(id)s::uuid,
                            'PROCESSING'
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            overall_avg = EXCLUDED.overall_avg,
                            overall_level = EXCLUDED.overall_level,
                            dimension_scores = EXCLUDED.dimension_scores,
                            answers = EXCLUDED.answers,
                            status = 'completed',
                            async_status = 'PROCESSING'
                        """,
                        {
                            **sanitized_scores,
                            "id": sub_uuid,
                            "name": data.get("name") or "",
                            "designation": data.get("designation") or data.get("role") or "",
                            "company_name": resolved_company_name,
                            "email": data.get("email"),
                            "contact_number": data.get("contact_number", None),
                            "has_physical_workspace": data.get("has_physical_workspace") or None,
                            "has_suppliers": data.get("has_suppliers") or None,
                            "consent_given": data.get("consent_given", False),
                            "consent_timestamp": data.get("consent_timestamp", datetime.now(timezone.utc)),
                            "organization_id": organization_id,
                            "submission_source": submission_source,
                            "invitation_id": invitation_id,
                            "access_token_id": access_token_id,
                            "campaign_id": campaign_id,
                            "idempotency_key": raw_idemp,
                            **{f"q{i}": data.get(f"q{i}") for i in range(5, 45)},
                            "dimension_scores": dimension_scores_json,
                            "answers": json.dumps(dynamic_answers)
                        }
                    )

                    if organization_id:
                        cur.execute(
                            """
                            INSERT INTO org_submission_links (org_id, submission_id, weight, linked_by)
                            VALUES (%s::uuid, %s::uuid, 1.0, NULL)
                            ON CONFLICT (org_id, submission_id) DO NOTHING
                            """,
                            (organization_id, sub_uuid)
                        )

        # Step 4: Execute Post-Submit Operations
        email_payload = {
            "email": data.get("email"),
            "name": data.get("name", ""),
            "company_name": resolved_company_name,
            "designation": data.get("designation") or data.get("role") or "",
            "contact_number": data.get("contact_number")
        }
        crm_payload = {
            "data": data,
            "score_data": scores
        }
        admin_payload = {
            "name": data.get("name", ""),
            "company_name": resolved_company_name,
            "email": data.get("email", "")
        }

        rep_res = claim_and_execute_operation(sub_uuid, OP_REPORT_GENERATION, worker_id, _run_report_generation, sub_uuid, email_payload)
        email_res = claim_and_execute_operation(sub_uuid, OP_EMAIL_DELIVERY, worker_id, _run_email_delivery, sub_uuid, email_payload)
        crm_res = claim_and_execute_operation(sub_uuid, OP_CRM_SYNC, worker_id, _run_crm_sync, sub_uuid, crm_payload)
        admin_res = claim_and_execute_operation(sub_uuid, OP_ADMIN_NOTIFICATION, worker_id, _run_admin_notification, sub_uuid, admin_payload)

        final_report_status = rep_res.get("status", "COMPLETED")
        final_email_status = email_res.get("status", "SKIPPED")
        final_crm_status = crm_res.get("status", "SKIPPED")
        final_admin_status = admin_res.get("status", "SKIPPED")

        deal_id = (crm_res.get("result_metadata") or {}).get("deal_id")
        contact_id = (crm_res.get("result_metadata") or {}).get("contact_id")

        # Step 5: Mark Terminal COMPLETED
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE raw_submissions
                        SET status = 'COMPLETED',
                            scoring_status = 'COMPLETED',
                            report_status = %s,
                            email_status = %s,
                            crm_status = %s,
                            worker_id = %s,
                            processing_completed_at = NOW(),
                            updated_at = NOW(),
                            last_error = NULL
                        WHERE submission_id = %s
                        """,
                        (final_report_status, final_email_status, final_crm_status, worker_id, sub_uuid)
                    )
                    cur.execute(
                        """
                        UPDATE submissions
                        SET async_status = 'COMPLETED',
                            report_status = %s,
                            email_status = %s,
                            crm_status = %s,
                            admin_notify_status = %s,
                            hubspot_deal_id = COALESCE(%s, hubspot_deal_id),
                            hubspot_contact_id = COALESCE(%s, hubspot_contact_id),
                            async_completed_at = NOW()
                        WHERE id = %s
                        """,
                        (
                            final_report_status,
                            final_email_status,
                            final_crm_status,
                            final_admin_status,
                            deal_id,
                            contact_id,
                            sub_uuid
                        )
                    )

        from app.api.routes import dashboard_cache
        dashboard_cache.clear()

        logger.info("Submission %s successfully scored, persisted, and marked COMPLETED", sub_uuid)

    except Exception as e:
        err_msg = str(e)[:1000]
        logger.error("Processing failed for submission %s: %s", sub_uuid, err_msg, exc_info=True)

        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE raw_submissions
                        SET retry_count = retry_count + 1,
                            worker_id = %s,
                            last_error = %s,
                            status = CASE WHEN retry_count + 1 >= %s THEN 'DEAD_LETTERED' ELSE 'RETRYING' END,
                            updated_at = NOW()
                        WHERE submission_id = %s
                        RETURNING retry_count, status;
                        """,
                        (worker_id, err_msg, MAX_DELIVERY_BEFORE_DLQ, sub_uuid)
                    )
                    row = cur.fetchone()
                    if row:
                        cur.execute(
                            """
                            UPDATE submissions
                            SET async_status = %s
                            WHERE id = %s
                            """,
                            (row[1], sub_uuid)
                        )
        raise


def process_message(receiver, msg, worker_id: str = "sb-worker-1") -> None:
    """Process an individual Service Bus message and settle it appropriately."""
    message_id = msg.message_id
    delivery_count = msg.delivery_count or 1

    try:
        raw_body = b"".join(msg.body) if hasattr(msg.body, "__iter__") else bytes(msg.body)
        body_str = raw_body.decode("utf-8")
        data = json.loads(body_str)

        props = msg.application_properties or {}
        raw_event_type = props.get("event_type") or props.get(b"event_type") or data.get("event_type") or "SUBMISSION_CREATED"
        if isinstance(raw_event_type, bytes):
            event_type = raw_event_type.decode("utf-8")
        else:
            event_type = str(raw_event_type)

        aggregate_id = data.get("submission_id") or msg.correlation_id or message_id

        logger.info("Processing message %s [event=%s, aggregate=%s, delivery_count=%s]",
                    message_id, event_type, aggregate_id, delivery_count)

        handle_submission_created(str(aggregate_id), data, worker_id=worker_id)

        # Settle: Complete message to remove from queue
        receiver.complete_message(msg)
        logger.info("Successfully completed message %s", message_id)

    except json.JSONDecodeError as jde:
        logger.critical("Unparseable payload on message %s, routing to DLQ: %s", message_id, jde)
        receiver.dead_letter_message(
            msg,
            reason="JSONDecodeError",
            error_description=str(jde)[:500]
        )
    except Exception as e:
        logger.error("Error processing message %s (attempt %s): %s", message_id, delivery_count, e)
        if delivery_count >= MAX_DELIVERY_BEFORE_DLQ:
            logger.critical("Delivery count %s exceeded threshold %s, moving message %s to DLQ",
                            delivery_count, MAX_DELIVERY_BEFORE_DLQ, message_id)
            receiver.dead_letter_message(
                msg,
                reason="MaxDeliveryCountExceeded",
                error_description=str(e)[:500]
            )
        else:
            receiver.abandon_message(msg)
            logger.warning("Message %s abandoned for redelivery", message_id)


def run_db_fallback_worker(poll_interval: float = 0.5):
    """
    Offline DB-outbox fallback consumer loop.
    Polls service_bus_outbox directly and executes submission processing without Azure Service Bus.
    """
    worker_id = f"db-fallback-{socket.gethostname()}-{os.getpid()}"
    tracker = WorkerTracker(worker_id=worker_id, worker_type="db_fallback_worker", heartbeat_interval=45.0)
    tracker.set_idle("Polling outbox queue")
    logger.info("DB Fallback Worker active [worker_id=%s, poll_interval=%.2fs]", worker_id, poll_interval)

    while not _stop_requested:
        try:
            claimed_rows = []
            with get_db_connection() as conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT id, aggregate_id, payload, attempt_count
                            FROM service_bus_outbox
                            WHERE status IN ('PENDING', 'FAILED')
                              AND next_retry_at <= NOW()
                              AND (locked_until IS NULL OR locked_until < NOW())
                            ORDER BY created_at ASC
                            LIMIT %s
                            FOR UPDATE SKIP LOCKED;
                            """,
                            (RECEIVE_BATCH_SIZE,)
                        )
                        rows = cur.fetchall()
                        if rows:
                            row_ids = [r[0] for r in rows]
                            cur.execute(
                                """
                                UPDATE service_bus_outbox
                                SET status = 'PROCESSING',
                                    locked_until = NOW() + INTERVAL '60 seconds',
                                    locked_by = %s
                                WHERE id = ANY(%s::uuid[])
                                """,
                                (worker_id, row_ids)
                            )
                            claimed_rows = rows

            if not claimed_rows:
                # Check raw_submissions directly for any unprocessed received rows
                with get_db_connection() as conn:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                """
                                SELECT submission_id, payload, retry_count, idempotency_key, organization_id, status
                                FROM raw_submissions
                                WHERE status = 'RECEIVED'
                                   OR (status = 'PROCESSING' AND processing_started_at < NOW() - INTERVAL '3 minutes')
                                ORDER BY created_at ASC
                                LIMIT %s
                                FOR UPDATE SKIP LOCKED;
                                """,
                                (RECEIVE_BATCH_SIZE,)
                            )
                            raw_pending = cur.fetchall()
                if raw_pending:
                    for raw in raw_pending:
                        try:
                            handle_submission_created(str(raw[0]), raw[1], worker_id=worker_id, prefetched_row=raw)
                        except Exception as e:
                            logger.error("Error processing pending raw submission %s: %s", raw[0], e)
                else:
                    tracker.heartbeat_if_due()
                    import time
                    time.sleep(poll_interval)
                continue

            for row in claimed_rows:
                evt_id, aggregate_id, evt_payload, attempt_count = row
                try:
                    handle_submission_created(str(aggregate_id), evt_payload, worker_id=worker_id)
                    with get_db_connection() as conn:
                        with conn:
                            with conn.cursor() as cur:
                                cur.execute(
                                    """
                                    UPDATE service_bus_outbox
                                    SET status = 'PUBLISHED',
                                        published_at = NOW(),
                                        locked_until = NULL,
                                        locked_by = NULL
                                    WHERE id = %s::uuid
                                    """,
                                    (evt_id,)
                                )
                except Exception as ex:
                    new_attempts = attempt_count + 1
                    err_str = str(ex)[:1000]
                    with get_db_connection() as conn:
                        with conn:
                            with conn.cursor() as cur:
                                if new_attempts >= MAX_DELIVERY_BEFORE_DLQ:
                                    cur.execute(
                                        """
                                        UPDATE service_bus_outbox
                                        SET status = 'DEAD_LETTER',
                                            attempt_count = %s,
                                            locked_until = NULL,
                                            locked_by = NULL,
                                            last_error = %s
                                        WHERE id = %s::uuid
                                        """,
                                        (new_attempts, err_str, evt_id)
                                    )
                                else:
                                    cur.execute(
                                        """
                                        UPDATE service_bus_outbox
                                        SET status = 'FAILED',
                                            attempt_count = %s,
                                            next_retry_at = NOW() + INTERVAL '2 seconds',
                                            locked_until = NULL,
                                            locked_by = NULL,
                                            last_error = %s
                                        WHERE id = %s::uuid
                                        """,
                                        (new_attempts, err_str, evt_id)
                                    )

        except Exception as e:
            logger.error("Error in DB fallback worker loop: %s", e, exc_info=True)
            import time
            time.sleep(poll_interval)


def run_service_bus_worker():
    """Main consumer loop connecting to Azure Service Bus submission queue (or DB fallback)."""
    try:
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)
    except (ValueError, AttributeError):
        pass

    worker_id = f"sb-worker-{socket.gethostname()}-{os.getpid()}"
    tracker = WorkerTracker(worker_id=worker_id, worker_type="service_bus_worker", heartbeat_interval=45.0)
    tracker.set_idle("Waiting for Service Bus messages")

    if not is_service_bus_configured():
        logger.info("Azure Service Bus is not configured. Starting in DB-outbox fallback mode.")
        run_db_fallback_worker()
        return

    client = get_service_bus_client()
    if not client:
        logger.info("Unable to initialize Service Bus client. Falling back to DB-outbox worker.")
        run_db_fallback_worker()
        return

    logger.info("Azure Service Bus Consumer Worker started [worker_id=%s, queue=%s]",
                worker_id, SERVICE_BUS_QUEUE_NAME)

    while not _stop_requested:
        try:
            with client.get_queue_receiver(
                queue_name=SERVICE_BUS_QUEUE_NAME,
                max_wait_time=RECEIVE_WAIT_TIME
            ) as receiver:
                logger.info("Service Bus receiver active, waiting for incoming messages...")
                while not _stop_requested:
                    messages = receiver.receive_messages(
                        max_message_count=RECEIVE_BATCH_SIZE,
                        max_wait_time=RECEIVE_WAIT_TIME
                    )
                    if not messages:
                        tracker.heartbeat_if_due()
                        continue

                    for msg in messages:
                        if _stop_requested:
                            try:
                                receiver.abandon_message(msg)
                            except Exception:
                                pass
                            break
                        process_message(receiver, msg, worker_id=worker_id)
                        tracker.record_job_completed(1)
                    tracker.set_idle()

        except Exception as e:
            if not _stop_requested:
                logger.error("Receiver error in Service Bus worker: %s. Reconnecting in 3 seconds...", e, exc_info=True)
                import time
                time.sleep(3)

    logger.info("Service Bus Consumer Worker stopped cleanly.")


if __name__ == "__main__":
    run_service_bus_worker()
