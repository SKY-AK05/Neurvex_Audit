"""
org_cache_service.py — High-Performance In-Memory Organisation Registry Cache
Provides sub-millisecond organisation lookups, thread-safe atomic snapshots,
a scheduled 30-minute refresh loop, multi-worker invalidation synchronization,
and negative lookup caching to protect PostgreSQL connection pools under load.
"""

import asyncio
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from cachetools import TTLCache
import psycopg2.extras

from app.core.database import get_db_connection

logger = logging.getLogger(__name__)

# Concurrency lock for atomic cache replacement and metric tracking
_lock = threading.RLock()

# In-memory lookup dictionaries:
# _orgs_by_normalized_name: normalized_name -> dict(id, name, is_active, is_deleted, approval_status, updated_at)
# _orgs_by_id: str(id) -> dict(...)
_orgs_by_normalized_name: dict[str, dict[str, Any]] = {}
_orgs_by_id: dict[str, dict[str, Any]] = {}

# Negative lookup cache with 30s TTL to prevent DB connection exhaustion from bursts of invalid lookups
_negative_cache: TTLCache = TTLCache(maxsize=2000, ttl=30.0)

# Metadata and performance diagnostics
_last_refresh_timestamp: float = 0.0
_last_refresh_datetime: Optional[datetime] = None
_last_refresh_duration_ms: float = 0.0
_cache_hits: int = 0
_cache_misses: int = 0
_negative_hits: int = 0

# Multi-worker synchronization file
INVALIDATION_FILE = Path(os.environ.get("NIWI_ORG_CACHE_INVALIDATION_FILE", "/tmp/niwi_org_cache_version"))
_last_seen_invalidation_mtime_ns: int = 0

# Background scheduled task reference
_background_task: Optional[asyncio.Task] = None
_background_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()


def normalize_org_name(name: str) -> str:
    """Case-insensitive and whitespace-normalized name representation."""
    if not name:
        return ""
    return " ".join(name.strip().lower().split())


def _touch_invalidation_file() -> None:
    """Updates the mtime of the invalidation file so other workers detect the change."""
    global _last_seen_invalidation_mtime_ns
    try:
        INVALIDATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        now_ns = time.time_ns()
        with open(INVALIDATION_FILE, "w") as f:
            f.write(str(now_ns))
        stat_res = INVALIDATION_FILE.stat()
        _last_seen_invalidation_mtime_ns = stat_res.st_mtime_ns
    except Exception as e:
        logger.warning("Failed to touch cache invalidation file %s: %s", INVALIDATION_FILE, e)


def _check_interprocess_invalidation() -> None:
    """
    Checks if another worker has signaled an invalidation via the invalidation file.
    Fast stat check on local tmpfs/disk takes <1 microsecond.
    """
    global _last_seen_invalidation_mtime_ns
    try:
        if INVALIDATION_FILE.exists():
            stat_res = INVALIDATION_FILE.stat()
            if stat_res.st_mtime_ns > _last_seen_invalidation_mtime_ns:
                logger.info(
                    "Detected cross-worker organisation cache invalidation (mtime %s > %s). Reloading...",
                    stat_res.st_mtime_ns,
                    _last_seen_invalidation_mtime_ns,
                )
                refresh_org_cache()
    except Exception as e:
        logger.warning("Error checking inter-process cache invalidation file: %s", e)


def refresh_org_cache(conn=None) -> bool:
    """
    Atomically refreshes the in-memory organisation registry from PostgreSQL.
    Builds the new lookup snapshots in local scope first. If the database query
    fails, the last known good snapshot is preserved without interruption.
    """
    global _orgs_by_normalized_name, _orgs_by_id
    global _last_refresh_timestamp, _last_refresh_datetime, _last_refresh_duration_ms
    global _last_seen_invalidation_mtime_ns

    t0 = time.perf_counter()
    new_by_name: dict[str, dict[str, Any]] = {}
    new_by_id: dict[str, dict[str, Any]] = {}

    try:
        def _fetch(active_conn):
            with active_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, is_active, is_deleted, approval_status, updated_at
                    FROM organizations
                """)
                return cur.fetchall()

        if conn is not None:
            rows = _fetch(conn)
        else:
            with get_db_connection() as active_conn:
                rows = _fetch(active_conn)

        for r in rows:
            entry = {
                "id": str(r["id"]),
                "name": r["name"],
                "is_active": bool(r["is_active"]),
                "is_deleted": bool(r["is_deleted"]),
                "approval_status": str(r["approval_status"]).lower() if r["approval_status"] else "approved",
                "updated_at": r.get("updated_at"),
            }
            norm_name = normalize_org_name(entry["name"])
            if norm_name:
                new_by_name[norm_name] = entry
            new_by_id[entry["id"]] = entry

        duration_ms = (time.perf_counter() - t0) * 1000.0

        with _lock:
            _orgs_by_normalized_name = new_by_name
            _orgs_by_id = new_by_id
            _negative_cache.clear()
            _last_refresh_timestamp = time.monotonic()
            _last_refresh_datetime = datetime.now(timezone.utc)
            _last_refresh_duration_ms = round(duration_ms, 2)
            if INVALIDATION_FILE.exists():
                try:
                    _last_seen_invalidation_mtime_ns = INVALIDATION_FILE.stat().st_mtime_ns
                except Exception:
                    pass

        logger.info(
            "Organisation cache refreshed: %d organisations indexed in %.2f ms (PID: %s)",
            len(new_by_id),
            duration_ms,
            os.getpid(),
        )
        return True

    except Exception as e:
        duration_ms = (time.perf_counter() - t0) * 1000.0
        logger.error(
            "Failed to refresh organisation cache after %.2f ms (retaining previous snapshot of %d orgs): %s",
            duration_ms,
            len(_orgs_by_id),
            e,
        )
        return False


def invalidate_org_cache() -> None:
    """
    Invalidates the organisation cache across all workers.
    Touches the invalidation file and immediately refreshes the current worker.
    """
    _touch_invalidation_file()
    refresh_org_cache()


def get_organisation_by_name(name: str) -> tuple[Optional[dict[str, Any]], str]:
    """
    Resolves an organisation by name using memory cache first, falling back to DB.
    Returns: (org_dict, source_str) where source_str is:
      - 'CACHE_HIT': Served directly from process memory (<10ms)
      - 'NEGATIVE_HIT': Recognized non-existent name from negative cache
      - 'DB_HIT': Cache miss, retrieved from PostgreSQL and cached
      - 'DB_MISS': Not found in PostgreSQL, recorded in negative cache
      - 'EMPTY': Input was empty
    """
    global _cache_hits, _cache_misses, _negative_hits

    normalized = normalize_org_name(name)
    if not normalized:
        return None, "EMPTY"

    _check_interprocess_invalidation()

    with _lock:
        if normalized in _orgs_by_normalized_name:
            _cache_hits += 1
            return _orgs_by_normalized_name[normalized], "CACHE_HIT"

        if normalized in _negative_cache:
            _negative_hits += 1
            return None, "NEGATIVE_HIT"

    # Cache miss: Fall back to authoritative PostgreSQL query
    _cache_misses += 1
    t0 = time.perf_counter()
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, is_active, is_deleted, approval_status, updated_at
                    FROM organizations
                    WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))
                """, (name.strip(),))
                row = cur.fetchone()

        if row:
            entry = {
                "id": str(row["id"]),
                "name": row["name"],
                "is_active": bool(row["is_active"]),
                "is_deleted": bool(row["is_deleted"]),
                "approval_status": str(row["approval_status"]).lower() if row["approval_status"] else "approved",
                "updated_at": row.get("updated_at"),
            }
            with _lock:
                _orgs_by_normalized_name[normalized] = entry
                _orgs_by_id[entry["id"]] = entry
                _negative_cache.pop(normalized, None)
            logger.info("DB fallback resolved org '%s' in %.2f ms", entry["name"], (time.perf_counter() - t0) * 1000.0)
            return entry, "DB_HIT"
        else:
            with _lock:
                _negative_cache[normalized] = True
            return None, "DB_MISS"

    except Exception as e:
        logger.error("Database fallback query failed for org '%s': %s", name, e)
        raise


def get_organisation_by_id(org_id: str | UUID) -> tuple[Optional[dict[str, Any]], str]:
    """Resolves an organisation by UUID string using memory cache first, falling back to DB."""
    global _cache_hits, _cache_misses

    if not org_id:
        return None, "EMPTY"

    org_id_str = str(org_id).strip().lower()
    _check_interprocess_invalidation()

    with _lock:
        if org_id_str in _orgs_by_id:
            _cache_hits += 1
            return _orgs_by_id[org_id_str], "CACHE_HIT"

    # Cache miss
    _cache_misses += 1
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, is_active, is_deleted, approval_status, updated_at
                    FROM organizations
                    WHERE id = %s
                """, (org_id_str,))
                row = cur.fetchone()

        if row:
            entry = {
                "id": str(row["id"]),
                "name": row["name"],
                "is_active": bool(row["is_active"]),
                "is_deleted": bool(row["is_deleted"]),
                "approval_status": str(row["approval_status"]).lower() if row["approval_status"] else "approved",
                "updated_at": row.get("updated_at"),
            }
            norm_name = normalize_org_name(entry["name"])
            with _lock:
                _orgs_by_id[entry["id"]] = entry
                if norm_name:
                    _orgs_by_normalized_name[norm_name] = entry
            return entry, "DB_HIT"
        return None, "DB_MISS"
    except Exception as e:
        logger.error("Database fallback query failed for org ID '%s': %s", org_id_str, e)
        raise


def is_org_eligible(org: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validates whether an organisation is currently eligible for assessments.
    Returns: (is_eligible, error_message)
    """
    if not org:
        return False, "We couldn't find this organisation. Please check the spelling or contact your administrator."
    if org.get("is_deleted"):
        return False, "This organisation has been deactivated or removed."
    if not org.get("is_active"):
        return False, "This organisation is currently inactive."
    if org.get("approval_status") != "approved":
        return False, "This organisation is pending administrative approval."
    return True, None


def get_cache_stats() -> dict[str, Any]:
    """Diagnostic metrics for health and monitoring endpoints."""
    with _lock:
        total_requests = _cache_hits + _cache_misses + _negative_hits
        hit_ratio = round((_cache_hits / total_requests * 100.0), 2) if total_requests > 0 else 0.0
        return {
            "pid": os.getpid(),
            "total_cached_orgs": len(_orgs_by_id),
            "cache_hits": _cache_hits,
            "cache_misses": _cache_misses,
            "negative_hits": _negative_hits,
            "hit_ratio_percent": hit_ratio,
            "negative_cache_size": len(_negative_cache),
            "last_refresh_utc": _last_refresh_datetime.isoformat() if _last_refresh_datetime else None,
            "last_refresh_duration_ms": _last_refresh_duration_ms,
        }


def _run_scheduled_refresh_thread(interval_seconds: int):
    """Background worker thread executing periodic refreshes every interval_seconds (default 30m)."""
    logger.info("Organisation cache background refresh thread started (interval=%ds)", interval_seconds)
    while not _stop_event.is_set():
        if _stop_event.wait(timeout=interval_seconds):
            break
        try:
            refresh_org_cache()
        except Exception as e:
            logger.error("Periodic organisation cache refresh encountered an error: %s", e)
    logger.info("Organisation cache background refresh thread stopped")


def start_org_cache_refresher(interval_seconds: int = 1800) -> None:
    """Starts the background scheduled refresh (default 1800s = 30 minutes)."""
    global _background_thread, _stop_event
    with _lock:
        if _background_thread is not None and _background_thread.is_alive():
            return
        _stop_event.clear()
        _background_thread = threading.Thread(
            target=_run_scheduled_refresh_thread,
            args=(interval_seconds,),
            name="OrgCacheRefresher",
            daemon=True,
        )
        _background_thread.start()


def stop_org_cache_refresher() -> None:
    """Stops the background scheduled refresh."""
    global _background_thread, _stop_event
    with _lock:
        _stop_event.set()
        if _background_thread and _background_thread.is_alive():
            _background_thread.join(timeout=2.0)
            _background_thread = None

