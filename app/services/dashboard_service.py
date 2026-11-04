"""
dashboard_service.py — Super Admin Operations & Worker Performance Dashboard.
Aggregates ingestion queue stats, processing latency, and worker fleet status.
Caches snapshot for 2 minutes in memory and in the dashboard_snapshot table.
"""
import time
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional
import psycopg2.extras
from app.core.database import get_db_connection

logger = logging.getLogger("dashboard_service")

# In-memory snapshot cache for single-process fast path
_MEMORY_CACHE = {
    "data": None,
    "cached_at": 0.0,
    "ttl": 120.0  # 2 minutes in seconds
}

def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def _format_duration(seconds: Optional[float]) -> str:
    """Format seconds into readable human-friendly duration string."""
    if seconds is None:
        return "None"
    s = int(round(seconds))
    if s < 60:
        return f"{s}s"
    m = s // 60
    rem_s = s % 60
    if m < 60:
        return f"{m}m {rem_s}s"
    h = m // 60
    rem_m = m % 60
    return f"{h}h {rem_m}m"


def compute_fresh_dashboard_stats() -> Dict[str, Any]:
    """
    Executes aggregate queries against raw_submissions and workers to generate
    a comprehensive system operational snapshot.
    Uses grouped queries and indexed scans for sub-millisecond execution.
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. Request Overview: Single grouped query (GROUP BY status)
            cur.execute("""
                SELECT status, COUNT(*) as count
                FROM raw_submissions
                GROUP BY status;
            """)
            status_rows = cur.fetchall()

            status_map = {
                "pending": 0,       # RECEIVED, PENDING
                "in_progress": 0,   # PROCESSING, RETRYING
                "completed": 0,     # COMPLETED
                "failed": 0         # FAILED, DEAD_LETTERED
            }
            raw_breakdown = {}
            total_requests = 0

            for r in status_rows:
                st = (r["status"] or "").upper()
                c = int(r["count"])
                total_requests += c
                raw_breakdown[st] = c

                if st in ("RECEIVED", "PENDING"):
                    status_map["pending"] += c
                elif st in ("PROCESSING", "RETRYING"):
                    status_map["in_progress"] += c
                elif st in ("COMPLETED",):
                    status_map["completed"] += c
                elif st in ("FAILED", "DEAD_LETTERED"):
                    status_map["failed"] += c
                else:
                    status_map["pending"] += c

            # 2. Request Analytics: Success vs. Failure Rate
            finalized_total = status_map["completed"] + status_map["failed"]
            if finalized_total > 0:
                success_rate = round((status_map["completed"] / finalized_total) * 100.0, 1)
                failure_rate = round((status_map["failed"] / finalized_total) * 100.0, 1)
            else:
                success_rate = 100.0 if status_map["completed"] > 0 else 0.0
                failure_rate = 0.0

            # 3. Request Analytics: Average processing time (actual worker execution duration)
            cur.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) as avg_seconds
                FROM raw_submissions
                WHERE status = 'COMPLETED'
                  AND processing_started_at IS NOT NULL
                  AND processing_completed_at IS NOT NULL
                  AND processing_completed_at >= processing_started_at
                  AND (processing_completed_at - processing_started_at) < INTERVAL '5 minutes'
                  AND processing_completed_at >= NOW() - INTERVAL '24 hours';
            """)
            avg_row = cur.fetchone()
            avg_proc_seconds = float(avg_row["avg_seconds"]) if avg_row and avg_row["avg_seconds"] is not None else 0.0

            # 4. Request Analytics: Oldest pending request (waiting time)
            cur.execute("""
                SELECT submission_id, created_at,
                       EXTRACT(EPOCH FROM (NOW() - created_at)) AS waiting_seconds
                FROM raw_submissions
                WHERE status IN ('RECEIVED', 'PENDING')
                ORDER BY created_at ASC
                LIMIT 1;
            """)
            oldest_row = cur.fetchone()
            oldest_pending = None
            if oldest_row:
                wait_sec = float(oldest_row["waiting_seconds"]) if oldest_row["waiting_seconds"] else 0.0
                oldest_pending = {
                    "submission_id": str(oldest_row["submission_id"]),
                    "created_at": oldest_row["created_at"].isoformat() if oldest_row["created_at"] else None,
                    "waiting_seconds": round(wait_sec, 1),
                    "waiting_time_formatted": _format_duration(wait_sec)
                }

            # 5. Request Analytics: Requests over time (Hourly, last 24 hours)
            cur.execute("""
                SELECT date_trunc('hour', created_at) AS bucket, COUNT(*) as count
                FROM raw_submissions
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY bucket
                ORDER BY bucket ASC;
            """)
            hourly_rows = cur.fetchall()
            hourly_timeline = [
                {
                    "bucket": r["bucket"].strftime("%Y-%m-%d %H:00") if r["bucket"] else "",
                    "label": r["bucket"].strftime("%H:00") if r["bucket"] else "",
                    "count": int(r["count"])
                }
                for r in hourly_rows
            ]

            # 6. Request Analytics: Requests over time (Daily, last 7 days)
            cur.execute("""
                SELECT date_trunc('day', created_at) AS bucket, COUNT(*) as count
                FROM raw_submissions
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY bucket
                ORDER BY bucket ASC;
            """)
            daily_rows = cur.fetchall()
            daily_timeline = [
                {
                    "bucket": r["bucket"].strftime("%Y-%m-%d") if r["bucket"] else "",
                    "label": r["bucket"].strftime("%b %d") if r["bucket"] else "",
                    "count": int(r["count"])
                }
                for r in daily_rows
            ]

            # 7. Worker Progress: Fleet monitoring & offline detection (> 3 minutes)
            cur.execute("""
                SELECT worker_id, worker_type, status, current_task,
                       jobs_completed, started_at, last_heartbeat,
                       EXTRACT(EPOCH FROM (NOW() - last_heartbeat)) AS seconds_since_heartbeat
                FROM workers
                ORDER BY last_heartbeat DESC;
            """)
            worker_rows = cur.fetchall()

            worker_list = []
            active_count = 0
            idle_count = 0
            offline_count = 0

            for w in worker_rows:
                sec_since = float(w["seconds_since_heartbeat"]) if w["seconds_since_heartbeat"] is not None else 999999.0
                raw_st = (w["status"] or "idle").lower()

                # Requirement 3: A worker is marked offline if its last heartbeat is older than 3 minutes (180s)
                if sec_since > 180.0:
                    effective_status = "offline"
                    offline_count += 1
                elif raw_st == "active":
                    effective_status = "active"
                    active_count += 1
                else:
                    effective_status = "idle"
                    idle_count += 1

                worker_list.append({
                    "worker_id": w["worker_id"],
                    "worker_type": w["worker_type"],
                    "status": effective_status,
                    "current_task": w["current_task"] or "None",
                    "jobs_completed": int(w["jobs_completed"] or 0),
                    "started_at": w["started_at"].isoformat() if w["started_at"] else None,
                    "last_heartbeat": w["last_heartbeat"].isoformat() if w["last_heartbeat"] else None,
                    "seconds_since_heartbeat": round(sec_since, 1),
                    "last_heartbeat_formatted": f"{int(sec_since)}s ago" if sec_since < 60 else f"{int(sec_since // 60)}m ago"
                })

            total_workers = len(worker_list)

    now_utc = datetime.now(timezone.utc)

    snapshot_data = {
        "timestamp": now_utc.isoformat(),
        "cache_ttl_seconds": 120,
        "request_overview": {
            "total_requests": total_requests,
            "pending": status_map["pending"],
            "in_progress": status_map["in_progress"],
            "completed": status_map["completed"],
            "failed": status_map["failed"],
            "raw_breakdown": raw_breakdown
        },
        "analytics": {
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "average_processing_time_seconds": round(avg_proc_seconds, 3),
            "average_processing_time_formatted": f"{round(avg_proc_seconds * 1000)}ms" if avg_proc_seconds < 1.0 else f"{round(avg_proc_seconds, 2)}s",
            "oldest_pending_request": oldest_pending,
            "hourly_timeline_24h": hourly_timeline,
            "daily_timeline_7d": daily_timeline
        },
        "worker_progress": {
            "total_workers": total_workers,
            "active_workers": active_count,
            "idle_workers": idle_count,
            "offline_workers": offline_count,
            "workers": worker_list
        }
    }

    return snapshot_data


def get_dashboard_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Returns the Super Admin operations dashboard snapshot.
    Guarantees that database stats are NOT queried on every page load:
    1. Returns in-memory cache if < 2 minutes old.
    2. Returns database `dashboard_snapshot` row if < 2 minutes old.
    3. If expired, computes snapshot once, updates table and in-memory cache, and returns.
    """
    now_monotonic = time.monotonic()

    # 1. Fast in-memory check
    if not force_refresh and _MEMORY_CACHE["data"] is not None:
        if now_monotonic - _MEMORY_CACHE["cached_at"] < _MEMORY_CACHE["ttl"]:
            return _MEMORY_CACHE["data"]

    # 2. Check persistent one-row snapshot table in database
    if not force_refresh:
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT data, updated_at,
                               EXTRACT(EPOCH FROM (NOW() - updated_at)) AS age_seconds
                        FROM dashboard_snapshot
                        WHERE id = 1;
                    """)
                    row = cur.fetchone()
                    if row and row.get("data") and row.get("age_seconds") is not None:
                        age = float(row["age_seconds"])
                        if age < 120.0:  # Valid within 2 minutes
                            data = row["data"]
                            if isinstance(data, str):
                                data = json.loads(data)
                            data["cached_at_db"] = row["updated_at"].isoformat() if row["updated_at"] else None
                            data["age_seconds"] = round(age, 1)

                            # Populate local memory cache
                            _MEMORY_CACHE["data"] = data
                            _MEMORY_CACHE["cached_at"] = now_monotonic
                            return data
        except Exception as e:
            logger.warning("Could not read dashboard_snapshot from database: %s", e)

    # 3. Compute fresh aggregate statistics
    fresh_data = compute_fresh_dashboard_stats()

    # 4. Save to persistent snapshot table (UPSERT one row)
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO dashboard_snapshot (id, data, updated_at)
                        VALUES (1, %s::jsonb, NOW())
                        ON CONFLICT (id) DO UPDATE SET
                            data = EXCLUDED.data,
                            updated_at = EXCLUDED.updated_at;
                    """, (json.dumps(fresh_data, default=_json_serial),))
    except Exception as e:
        logger.error("Failed to persist dashboard_snapshot: %s", e)

    # 5. Store in memory cache
    _MEMORY_CACHE["data"] = fresh_data
    _MEMORY_CACHE["cached_at"] = now_monotonic

    return fresh_data

