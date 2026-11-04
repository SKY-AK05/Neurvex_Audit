from app.services.worker_tracker import WorkerTracker
"""
outbox_service.py — Transactional Outbox Dispatcher for Azure Service Bus.
Polls PostgreSQL service_bus_outbox table using SELECT ... FOR UPDATE SKIP LOCKED
and reliably dispatches events to Azure Service Bus with exponential backoff and lease management.
When Service Bus is not configured, yields gracefully to DB-outbox fallback worker.
"""
import os
import sys
import time
import signal
import socket
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.core.database import get_db_connection
from app.core.service_bus import publish_event, close_service_bus, is_service_bus_configured

logger = logging.getLogger("outbox_dispatcher")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [outbox_dispatcher] %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

MAX_RETRIES = 5
LOCK_TIMEOUT_SECONDS = 60
DEFAULT_POLL_INTERVAL = float(os.environ.get("OUTBOX_POLL_INTERVAL", "1.0"))
BATCH_SIZE = int(os.environ.get("OUTBOX_BATCH_SIZE", "10"))

_stop_requested = False


def _signal_handler(signum, frame):
    global _stop_requested
    logger.info("Received signal %s, initiating graceful outbox dispatcher shutdown...", signum)
    _stop_requested = True


def dispatch_pending_outbox_events(batch_size: int = BATCH_SIZE, worker_id: Optional[str] = None) -> int:
    """
    Claim and dispatch pending outbox events using FOR UPDATE SKIP LOCKED.
    
    Returns:
        Number of events processed in this iteration.
    """
    if not is_service_bus_configured():
        return 0

    if worker_id is None:
        worker_id = f"outbox-{socket.gethostname()}-{os.getpid()}"

    claimed_events: List[Dict[str, Any]] = []

    # 1. Claim batch with row locks and lease timeout
    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, event_type, aggregate_id, payload, attempt_count
                    FROM service_bus_outbox
                    WHERE status IN ('PENDING', 'FAILED')
                      AND next_retry_at <= NOW()
                      AND (locked_until IS NULL OR locked_until < NOW())
                    ORDER BY created_at ASC
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED;
                    """,
                    (batch_size,)
                )
                rows = cur.fetchall()
                if not rows:
                    return 0

                event_ids = [r[0] for r in rows]
                cur.execute(
                    """
                    UPDATE service_bus_outbox
                    SET status = 'PROCESSING',
                        locked_until = NOW() + INTERVAL '1 second' * %s,
                        locked_by = %s
                    WHERE id = ANY(%s::uuid[])
                    """,
                    (LOCK_TIMEOUT_SECONDS, worker_id, event_ids)
                )

                for r in rows:
                    claimed_events.append({
                        "id": str(r[0]),
                        "event_type": r[1],
                        "aggregate_id": str(r[2]),
                        "payload": r[3],
                        "attempt_count": r[4],
                    })

    # 2. Dispatch each claimed event to Azure Service Bus
    for event in claimed_events:
        evt_id = event["id"]
        event_type = event["event_type"]
        aggregate_id = event["aggregate_id"]
        payload = event["payload"]
        attempt_count = event["attempt_count"]

        # User requirement: Publish submission IDs, not large payloads. MessageId = submission_id
        dispatch_payload = {
            "submission_id": str(aggregate_id),
            "event_type": event_type,
            "outbox_id": str(evt_id)
        }

        try:
            logger.info("Dispatching outbox event %s (%s) for submission %s", evt_id, event_type, aggregate_id)
            res = publish_event(
                event_type=event_type,
                aggregate_id=aggregate_id,
                payload=dispatch_payload,
                message_id=str(aggregate_id)
            )

            if res is None:
                # Service bus became unavailable or is offline
                logger.warning("Service Bus publish returned None for event %s. Reverting to PENDING.", evt_id)
                with get_db_connection() as conn:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                """
                                UPDATE service_bus_outbox
                                SET status = 'PENDING',
                                    locked_until = NULL,
                                    locked_by = NULL
                                WHERE id = %s::uuid
                                """,
                                (evt_id,)
                            )
                continue

            # Mark as PUBLISHED
            with get_db_connection() as conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE service_bus_outbox
                            SET status = 'PUBLISHED',
                                published_at = NOW(),
                                locked_until = NULL,
                                locked_by = NULL,
                                last_error = NULL
                            WHERE id = %s::uuid
                            """,
                            (evt_id,)
                        )
            logger.info("Successfully published outbox event %s to Service Bus", evt_id)

        except Exception as e:
            new_attempts = attempt_count + 1
            err_msg = str(e)[:1000]
            logger.error("Failed to publish outbox event %s (attempt %s/%s): %s", evt_id, new_attempts, MAX_RETRIES, err_msg)

            with get_db_connection() as conn:
                with conn:
                    with conn.cursor() as cur:
                        if new_attempts >= MAX_RETRIES:
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
                                (new_attempts, err_msg, evt_id)
                            )
                            logger.critical("Outbox event %s moved to DEAD_LETTER after %s failed attempts", evt_id, new_attempts)
                        else:
                            backoff_seconds = 2 ** new_attempts
                            cur.execute(
                                """
                                UPDATE service_bus_outbox
                                SET status = 'FAILED',
                                    attempt_count = %s,
                                    next_retry_at = NOW() + INTERVAL '1 second' * %s,
                                    locked_until = NULL,
                                    locked_by = NULL,
                                    last_error = %s
                                WHERE id = %s::uuid
                                """,
                                (new_attempts, backoff_seconds, err_msg, evt_id)
                            )

    return len(claimed_events)




def cleanup_published_outbox_events(retention_days: int = 7, batch_size: int = 5000) -> int:
    """
    Safely prunes PUBLISHED outbox rows older than retention_days in small batches
    to avoid long-lived exclusive table locks.
    """
    total_deleted = 0
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        WITH to_delete AS (
                            SELECT id FROM service_bus_outbox
                            WHERE status = 'PUBLISHED'
                              AND published_at < NOW() - (%s || ' days')::interval
                            LIMIT %s
                        )
                        DELETE FROM service_bus_outbox
                        WHERE id IN (SELECT id FROM to_delete);
                        """,
                        (retention_days, batch_size)
                    )
                    total_deleted = cur.rowcount
        if total_deleted > 0:
            logger.info("Cleaned up %d expired published outbox events (retention: %d days)", total_deleted, retention_days)
    except Exception as e:
        logger.error("Outbox cleanup failed: %s", e)
    return total_deleted

def run_db_maintenance_vacuum():
    """Periodic non-blocking VACUUM ANALYZE to keep Postgres statistics fresh and prune dead tuples."""
    try:
        from app.core.database import get_conn
        conn = get_conn()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("VACUUM (ANALYZE) raw_submissions;")
            cur.execute("VACUUM (ANALYZE) service_bus_outbox;")
        conn.close()
        logger.info("Database automated VACUUM ANALYZE completed successfully.")
    except Exception as e:
        logger.error("Periodic VACUUM ANALYZE error: %s", e)


def check_system_health_and_alert():
    """Alert super admin if queue is backed up (>200 items for >15m) or workers are offline."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) as pending_count,
                           EXTRACT(EPOCH FROM (NOW() - MIN(created_at))) as oldest_wait_sec
                    FROM raw_submissions
                    WHERE status IN ('RECEIVED', 'PENDING');
                    """
                )
                q_row = cur.fetchone()
                pending_count = q_row[0] or 0
                oldest_wait = q_row[1] or 0.0

                if pending_count >= 200 and oldest_wait >= 900:  # > 200 items waiting > 15 mins
                    from app.services.settings_service import get_settings, send_acs_email, get_sender_for_send, is_acs_configured
                    settings = get_settings(cur)
                    admin_email = settings.get("notification_email")
                    if admin_email and is_acs_configured():
                        sender_addr, sender_name = get_sender_for_send(cur)
                        send_acs_email(
                            to_address=admin_email,
                            subject=f"⚠️ [NIWI System Alert] Ingestion Queue Backlog High ({pending_count} pending)",
                            html=f"<p>System Alert: Ingestion queue has <strong>{pending_count}</strong> pending submissions. Oldest request waiting: {int(oldest_wait // 60)} minutes.</p>",
                            plain=f"System Alert: Ingestion queue has {pending_count} pending submissions. Oldest waiting: {int(oldest_wait // 60)} mins.",
                            sender_address=sender_addr,
                            sender_name=sender_name
                        )
                        logger.warning("Dispatched high queue backlog alert to %s", admin_email)
    except Exception as e:
        logger.error("Health check alert error: %s", e)


def run_outbox_dispatcher(poll_interval: float = DEFAULT_POLL_INTERVAL):
    """Continuous outbox dispatcher loop."""
    try:
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)
    except (ValueError, AttributeError):
        pass

    worker_id = f"outbox-disp-{socket.gethostname()}-{os.getpid()}"
    tracker = WorkerTracker(worker_id=worker_id, worker_type="outbox_dispatcher", heartbeat_interval=45.0)
    tracker.set_idle("Polling outbox events")
    logger.info("Outbox dispatcher daemon started [worker_id=%s, poll_interval=%.2fs]", worker_id, poll_interval)

    from app.core.database import init_connection_pool
    try:
        init_connection_pool(minconn=2, maxconn=4)
    except Exception as e:
        logger.warning("Could not initialize outbox connection pool: %s", e)

    warned_offline = False
    last_cleanup_time = time.monotonic()
    last_digest_time = time.monotonic()
    last_vacuum_time = time.monotonic()
    last_health_check_time = time.monotonic()

    while not _stop_requested:
        # 1. Periodic batch cleanup of published outbox events (every 1 hour)
        if time.monotonic() - last_cleanup_time > 3600:
            cleanup_published_outbox_events()
            last_cleanup_time = time.monotonic()

        # 2. Periodic 5-minute batched digest notification to admin
        if time.monotonic() - last_digest_time >= 300:
            try:
                from app.services.settings_service import send_admin_submission_digest
                send_admin_submission_digest()
            except Exception as d_err:
                logger.error("Failed to execute 5-minute admin digest: %s", d_err)
            last_digest_time = time.monotonic()

        # 3. Periodic 15-minute system health monitoring & alerting
        if time.monotonic() - last_health_check_time >= 900:
            check_system_health_and_alert()
            last_health_check_time = time.monotonic()

        # 4. Periodic 24-hour non-blocking database vacuum & analysis
        if time.monotonic() - last_vacuum_time >= 86400:
            run_db_maintenance_vacuum()
            last_vacuum_time = time.monotonic()

        try:
            if not is_service_bus_configured():
                if not warned_offline:
                    logger.info("Service Bus is not configured. Outbox events will be processed by DB fallback worker.")
                    warned_offline = True
                time.sleep(poll_interval * 2)
                continue
            else:
                warned_offline = False

            processed = dispatch_pending_outbox_events(batch_size=BATCH_SIZE, worker_id=worker_id)
            if processed > 0:
                tracker.record_job_completed(processed)
                tracker.set_task(f"Dispatched {processed} outbox events", status="active")
                time.sleep(0.05)  # Yield briefly under heavy load
            else:
                tracker.set_idle("Waiting for outbox events")
                tracker.heartbeat_if_due()
                time.sleep(poll_interval)
        except Exception as e:
            logger.error("Unexpected error in outbox dispatcher loop: %s", e, exc_info=True)
            time.sleep(poll_interval)

    logger.info("Outbox dispatcher daemon stopping, closing Service Bus connections...")
    close_service_bus()
    logger.info("Outbox dispatcher shutdown complete.")


if __name__ == "__main__":
    run_outbox_dispatcher()
