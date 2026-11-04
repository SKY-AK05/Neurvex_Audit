"""
service_bus_worker.py — Azure Service Bus Consumer Worker for NIWI.
Single processing mechanism for new submissions with durable per-operation idempotency,
crash recovery, and accurate external delivery status semantics.
"""
import os
import sys
import json
import signal
import socket
import logging
from typing import Optional, Dict, Any

from azure.servicebus import ServiceBusReceivedMessage

from app.core.database import get_db_connection
from app.core.service_bus import get_service_bus_client, SERVICE_BUS_QUEUE_NAME
from app.tasks.job_worker import process_email_job
from app.services.settings_service import (
    is_acs_configured,
    get_settings,
    notify_admin_new_submission,
)
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
RECEIVE_BATCH_SIZE = int(os.environ.get("SERVICE_BUS_BATCH_SIZE", "5"))

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
                    SELECT status, result_metadata, locked_at, locked_by
                    FROM submission_operation_states
                    WHERE submission_id = %s AND operation_type = %s
                    """,
                    (str(submission_id), operation_type)
                )
                existing = cur.fetchone()

        if existing:
            status, meta, locked_at, locked_by = existing
            if status in TERMINAL_STATES:
                logger.info(
                    "Operation %s for submission %s already completed with status %s, skipping duplicate execution.",
                    operation_type, submission_id, status
                )
                return {"status": status, "result_metadata": meta or {}, "reused": True}
            elif status == "PROCESSING":
                logger.warning(
                    "Operation %s for submission %s is actively locked by %s (at %s). Avoiding duplicate execution.",
                    operation_type, submission_id, locked_by, locked_at
                )
                return {"status": "LOCKED", "reused": True, "locked_by": locked_by}

    # Step 3: Execute operation function
    try:
        res = execute_fn(*args, **kwargs) or {}
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
                            completed_at = CASE WHEN %s IN ('COMPLETED', 'GENERATED', 'SENT', 'SYNCED', 'SKIPPED') THEN NOW() ELSE NULL END,
                            locked_at = NULL,
                            locked_by = NULL,
                            result_metadata = %s::jsonb,
                            last_error = %s,
                            updated_at = NOW()
                        WHERE submission_id = %s AND operation_type = %s
                        """,
                        (final_status, final_status, json.dumps(meta), err_msg, str(submission_id), operation_type)
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
    """
    Check external email delivery configuration.
    User assessment reports are reviewed and dispatched manually by admins via /api/submissions/{id}/send.
    In post-submission:
    - If ACS is not configured: SKIPPED.
    - If ACS is configured: SKIPPED (awaiting manual admin dispatch).
    """
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
    """Send admin alert email if notifications are enabled and ACS is configured."""
    if not is_acs_configured():
        return {
            "status": "SKIPPED",
            "metadata": {"reason": "ACS_CONNECTION_STRING not configured"}
        }

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            settings = get_settings(cur)
            notifications_enabled = settings.get("notifications_enabled", False)

    if not notifications_enabled:
        return {
            "status": "SKIPPED",
            "metadata": {"reason": "Notifications disabled in app_settings"}
        }

    name = admin_payload.get("name", "")
    company_name = admin_payload.get("company_name", "")

    status, err = notify_admin_new_submission(
        cur=None,
        submission_id=submission_id,
        name=name,
        company_name=company_name,
        sync=True
    )
    return {
        "status": status,
        "metadata": {"reason": err} if err else {"sent": True}
    }


def handle_submission_created(submission_id: str, payload: Dict[str, Any], worker_id: str = "sb-worker-1") -> None:
    """
    Process asynchronous tasks for a created submission with per-operation idempotency:
    1. Report generation (HTML compilation and persistence)
    2. Email delivery status evaluation
    3. HubSpot CRM synchronization (idempotent deal creation/update)
    4. Admin alert notification
    5. Final atomic submission status update
    """
    # 1. Inspect existing submission
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT async_status, email_status, crm_status, report_status, hubspot_deal_id
                FROM submissions
                WHERE id = %s
                """,
                (str(submission_id),)
            )
            sub = cur.fetchone()

    if not sub:
        logger.warning("Submission %s not found in database; cannot process post-submit tasks.", submission_id)
        return

    async_status = sub[0] if len(sub) > 0 else "PENDING"
    email_status = sub[1] if len(sub) > 1 else "PENDING"
    crm_status = sub[2] if len(sub) > 2 else "PENDING"
    report_status = sub[3] if len(sub) > 3 else "PENDING"
    existing_deal_id = sub[4] if len(sub) > 4 else None
    if async_status == "COMPLETED":
        logger.info("Submission %s already COMPLETED, skipping duplicate processing.", submission_id)
        return

    email_payload = payload.get("email_job_payload") or {}
    crm_payload = payload.get("crm_job_payload") or {}
    admin_payload = {
        "name": payload.get("name", ""),
        "company_name": payload.get("company_name", ""),
    }

    # 2. Execute Report Generation
    rep_res = claim_and_execute_operation(
        submission_id,
        OP_REPORT_GENERATION,
        worker_id,
        _run_report_generation,
        submission_id,
        email_payload
    )

    # 3. Execute Email Delivery
    email_res = claim_and_execute_operation(
        submission_id,
        OP_EMAIL_DELIVERY,
        worker_id,
        _run_email_delivery,
        submission_id,
        email_payload
    )

    # 4. Execute CRM Sync
    crm_res = claim_and_execute_operation(
        submission_id,
        OP_CRM_SYNC,
        worker_id,
        _run_crm_sync,
        submission_id,
        crm_payload,
        known_deal_id=existing_deal_id
    )

    # 5. Execute Admin Notification
    admin_res = claim_and_execute_operation(
        submission_id,
        OP_ADMIN_NOTIFICATION,
        worker_id,
        _run_admin_notification,
        submission_id,
        admin_payload
    )

    # 6. Reconcile final statuses
    final_report_status = rep_res.get("status", "FAILED")
    final_email_status = email_res.get("status", "SKIPPED")
    final_crm_status = crm_res.get("status", "SKIPPED")
    final_admin_status = admin_res.get("status", "SKIPPED")

    deal_id = (crm_res.get("result_metadata") or {}).get("deal_id")
    contact_id = (crm_res.get("result_metadata") or {}).get("contact_id")

    # Overall async_status determination:
    # COMPLETED: internal processing succeeded and all external operations completed or skipped
    # PARTIAL: internal processing succeeded but an external integration failed
    # FAILED: core report generation failed
    if final_report_status not in ("GENERATED", "COMPLETED"):
        overall_status = "FAILED"
    elif any(s == "FAILED" for s in (final_email_status, final_crm_status, final_admin_status)):
        overall_status = "PARTIAL"
    else:
        overall_status = "COMPLETED"

    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE submissions
                    SET async_status = %s,
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
                        overall_status,
                        final_report_status,
                        final_email_status,
                        final_crm_status,
                        final_admin_status,
                        deal_id,
                        contact_id,
                        str(submission_id)
                    )
                )

    logger.info(
        "Submission %s post-processing finished [async_status=%s, report=%s, email=%s, crm=%s, admin=%s]",
        submission_id, overall_status, final_report_status, final_email_status, final_crm_status, final_admin_status
    )


def process_message(receiver, msg: ServiceBusReceivedMessage, worker_id: str = "sb-worker-1") -> None:
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

        aggregate_id = data.get("submission_id") or msg.correlation_id

        logger.info("Processing message %s [event=%s, aggregate=%s, delivery_count=%s]",
                    message_id, event_type, aggregate_id, delivery_count)

        if event_type == "SUBMISSION_CREATED":
            handle_submission_created(str(aggregate_id), data, worker_id=worker_id)
        else:
            logger.warning("Unrecognized event_type '%s' on message %s, completing anyway.", event_type, message_id)

        # Successfully processed -> Complete message to remove from queue
        receiver.complete_message(msg)
        logger.info("Successfully settled (completed) message %s", message_id)

    except json.JSONDecodeError as jde:
        logger.critical("Unparseable payload on message %s, routing to DLQ: %s", message_id, jde)
        receiver.dead_letter_message(
            msg,
            reason="JSONDecodeError",
            error_description=str(jde)[:500]
        )
    except Exception as e:
        logger.error("Error processing message %s (attempt %s): %s", message_id, delivery_count, e, exc_info=True)
        if delivery_count >= MAX_DELIVERY_BEFORE_DLQ:
            logger.critical("Delivery count %s exceeded threshold %s, moving message %s to DLQ",
                            delivery_count, MAX_DELIVERY_BEFORE_DLQ, message_id)
            receiver.dead_letter_message(
                msg,
                reason="MaxDeliveryCountExceeded",
                error_description=str(e)[:500]
            )
        else:
            # Abandon message so Service Bus can redeliver it after lock expires
            receiver.abandon_message(msg)
            logger.warning("Message %s abandoned for redelivery", message_id)


def run_service_bus_worker():
    """Main consumer loop connecting to Azure Service Bus submission queue."""
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    worker_id = f"sb-worker-{socket.gethostname()}-{os.getpid()}"
    logger.info("Azure Service Bus Consumer Worker started [worker_id=%s, queue=%s]",
                worker_id, SERVICE_BUS_QUEUE_NAME)

    client = get_service_bus_client()

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
                        continue

                    for msg in messages:
                        if _stop_requested:
                            try:
                                receiver.abandon_message(msg)
                            except Exception:
                                pass
                            break
                        process_message(receiver, msg, worker_id=worker_id)

        except Exception as e:
            if not _stop_requested:
                logger.error("Receiver error in Service Bus worker: %s. Reconnecting in 3 seconds...", e, exc_info=True)
                import time
                time.sleep(3)

    logger.info("Service Bus Consumer Worker stopped cleanly.")


if __name__ == "__main__":
    run_service_bus_worker()
