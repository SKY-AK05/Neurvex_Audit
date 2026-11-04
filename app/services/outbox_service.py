"""
outbox_service.py — Transactional Outbox Dispatcher for Azure Service Bus.
Polls PostgreSQL service_bus_outbox table using SELECT ... FOR UPDATE SKIP LOCKED
and reliably dispatches events to Azure Service Bus with exponential backoff and lease management.
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
from app.core.service_bus import publish_event, close_service_bus

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

        try:
            logger.info("Dispatching outbox event %s (%s) for aggregate %s", evt_id, event_type, aggregate_id)
            publish_event(
                event_type=event_type,
                aggregate_id=aggregate_id,
                payload=payload,
                message_id=f"outbox-{evt_id}"
            )

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


def run_outbox_dispatcher(poll_interval: float = DEFAULT_POLL_INTERVAL):
    """Continuous outbox dispatcher loop."""
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    worker_id = f"outbox-disp-{socket.gethostname()}-{os.getpid()}"
    logger.info("Outbox dispatcher daemon started [worker_id=%s, poll_interval=%.2fs]", worker_id, poll_interval)

    while not _stop_requested:
        try:
            processed = dispatch_pending_outbox_events(batch_size=BATCH_SIZE, worker_id=worker_id)
            if processed > 0:
                time.sleep(0.05)  # Yield briefly under heavy load
            else:
                time.sleep(poll_interval)
        except Exception as e:
            logger.error("Unexpected error in outbox dispatcher loop: %s", e, exc_info=True)
            time.sleep(poll_interval)

    logger.info("Outbox dispatcher daemon stopping, closing Service Bus connections...")
    close_service_bus()
    logger.info("Outbox dispatcher shutdown complete.")


if __name__ == "__main__":
    run_outbox_dispatcher()

