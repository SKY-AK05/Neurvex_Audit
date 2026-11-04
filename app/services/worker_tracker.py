"""
worker_tracker.py — Background worker fleet and heartbeat tracking.
Workers update their status in the `workers` table at 30-60 second intervals.
"""
import os
import time
import socket
import logging
from typing import Optional
import psycopg2.extras
from app.core.database import get_db_connection

logger = logging.getLogger("worker_tracker")

class WorkerTracker:
    def __init__(self, worker_id: str, worker_type: str = "service_bus_worker", heartbeat_interval: float = 45.0):
        self.worker_id = worker_id
        self.worker_type = worker_type
        self.heartbeat_interval = heartbeat_interval
        self._last_heartbeat_time = 0.0
        self.jobs_completed = 0
        self.current_task = "Initialized"
        self.status = "idle" # 'active', 'idle', 'offline'

    def record_job_completed(self, count: int = 1) -> None:
        self.jobs_completed += count

    def set_task(self, task: str, status: str = "active") -> None:
        self.current_task = task[:250]
        self.status = status
        self.heartbeat_if_due()

    def set_idle(self, idle_msg: str = "Waiting for queue messages") -> None:
        self.current_task = idle_msg
        self.status = "idle"
        self.heartbeat_if_due()

    def heartbeat_if_due(self, force: bool = False) -> None:
        """Update worker heartbeat in database if 30-60 seconds have elapsed."""
        now = time.monotonic()
        if not force and (now - self._last_heartbeat_time < self.heartbeat_interval):
            return

        try:
            with get_db_connection() as conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO workers (
                                worker_id, worker_type, status, current_task,
                                jobs_completed, started_at, last_heartbeat
                            )
                            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                            ON CONFLICT (worker_id) DO UPDATE SET
                                status = EXCLUDED.status,
                                current_task = EXCLUDED.current_task,
                                jobs_completed = EXCLUDED.jobs_completed,
                                last_heartbeat = NOW();
                            """,
                            (
                                self.worker_id,
                                self.worker_type,
                                self.status,
                                self.current_task,
                                self.jobs_completed
                            )
                        )
            self._last_heartbeat_time = now
        except Exception as e:
            logger.debug("Failed to flush worker heartbeat: %s", e)

    def mark_offline(self) -> None:
        """Mark worker as offline upon graceful shutdown."""
        try:
            with get_db_connection() as conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE workers
                            SET status = 'offline',
                                current_task = 'Stopped / Shutdown',
                                last_heartbeat = NOW()
                            WHERE worker_id = %s;
                            """,
                            (self.worker_id,)
                        )
        except Exception as e:
            logger.debug("Failed to set worker offline: %s", e)
