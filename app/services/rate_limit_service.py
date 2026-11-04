"""
rate_limit_service.py — Central Dynamic Rate Limiting & Security Configuration Service
Manages persistent, admin-configurable rate limits in PostgreSQL with in-memory caching,
instant cross-worker synchronization via version notification, trusted IP extraction,
and dynamic traffic classification (Public, Secure Link, Session Protection, Invalid Token).
"""

import inspect
import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

import psycopg2.extras
from limits import parse
from slowapi.errors import RateLimitExceeded
from slowapi.wrappers import Limit
from starlette.requests import Request

from app.core.database import get_db_connection
from app.core.limiter import limiter
from app.services.token_service import resolve_assessment_token

logger = logging.getLogger(__name__)

# Default rate limits (initial baseline and reset target)
DEFAULT_RATE_LIMITS: dict[str, int] = {
    "submit_rate_limit_hour": 500,
    "submit_rate_limit_day": 2000,
    "secure_submit_rate_limit_hour": 500,
    "secure_submit_rate_limit_day": 2000,
    "assessment_session_limit_hour": 3,
    "invalid_token_limit_minute": 10,
}

# Validation constraints
RATE_LIMIT_CONSTRAINTS: dict[str, dict[str, Any]] = {
    "submit_rate_limit_hour": {"min": 1, "max": 100_000, "label": "Public submissions per IP per hour"},
    "submit_rate_limit_day": {"min": 1, "max": 1_000_000, "label": "Public submissions per IP per day"},
    "secure_submit_rate_limit_hour": {"min": 1, "max": 100_000, "label": "Secure-link submissions per IP per hour"},
    "secure_submit_rate_limit_day": {"min": 1, "max": 1_000_000, "label": "Secure-link submissions per IP per day"},
    "assessment_session_limit_hour": {"min": 1, "max": 100, "label": "Assessment session attempts per hour"},
    "invalid_token_limit_minute": {"min": 1, "max": 1_000, "label": "Invalid-token attempts per IP per minute"},
}

# In-memory synchronization lock & snapshot
_lock = threading.RLock()
_cached_settings: dict[str, int] = {}
_cached_descriptions: dict[str, str] = {}
_last_updated_at: Optional[str] = None
_last_updated_by: str = "system"
_last_sync_timestamp: float = 0.0

# Cross-worker invalidation file
INVALIDATION_FILE = Path(os.environ.get("NIWI_RATE_LIMIT_INVALIDATION_FILE", "/tmp/niwi_rate_limit_version"))
_last_mtime_ns: int = 0

# Runtime metrics
_429_count: int = 0
_last_429_at: Optional[str] = None


def get_client_ip(request: Request) -> str:
    """
    Extracts the authentic client IP address behind trusted Nginx proxy.
    Prefers X-Real-IP set directly by local Nginx proxy.
    """
    if not request:
        return "127.0.0.1"

    # Priority 1: X-Real-IP directly configured in Nginx
    real_ip = request.headers.get("x-real-ip")
    if real_ip and real_ip.strip():
        return real_ip.strip()

    # Priority 2: Leftmost IP from X-Forwarded-For
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            return parts[0]

    # Fallback: direct connection host
    if hasattr(request, "client") and request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


def _get_env_fallback(key: str, default_val: int) -> int:
    """Retrieves environment variable fallback if set, otherwise default_val."""
    env_var_name = key.upper()
    val_str = os.environ.get(env_var_name)
    if val_str:
        try:
            return int(val_str.strip())
        except ValueError:
            pass
    return default_val


def _load_settings_from_db() -> tuple[dict[str, int], dict[str, str], Optional[str], str]:
    """Loads active rate-limit configuration directly from PostgreSQL."""
    settings = {}
    descriptions = {}
    latest_updated_at = None
    latest_updated_by = "system"

    # Pre-populate defaults with environment variable hierarchy
    for k, v in DEFAULT_RATE_LIMITS.items():
        settings[k] = _get_env_fallback(k, v)
        descriptions[k] = RATE_LIMIT_CONSTRAINTS[k]["label"]

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT setting_key, setting_value, description, updated_at, updated_by
                    FROM system_security_settings
                """)
                rows = cur.fetchall()
                for r in rows:
                    key = r["setting_key"]
                    val_str = r["setting_value"]
                    if key in DEFAULT_RATE_LIMITS:
                        try:
                            settings[key] = int(val_str)
                            descriptions[key] = r["description"] or descriptions.get(key, "")
                            if r["updated_at"]:
                                dt_iso = r["updated_at"].isoformat()
                                if not latest_updated_at or dt_iso > latest_updated_at:
                                    latest_updated_at = dt_iso
                                    latest_updated_by = r["updated_by"] or "admin"
                        except (ValueError, TypeError):
                            logger.warning("Invalid value for %s in DB: %s, using fallback", key, val_str)
    except Exception as e:
        logger.error("Failed to load system_security_settings from database: %s", e)

    return settings, descriptions, latest_updated_at, latest_updated_by


def _check_and_sync():
    """Checks if invalidation file has been touched or cache is empty and reloads if needed."""
    global _cached_settings, _cached_descriptions, _last_updated_at, _last_updated_by
    global _last_mtime_ns, _last_sync_timestamp

    needs_reload = False
    current_time = time.time()

    if not _cached_settings:
        needs_reload = True
    elif INVALIDATION_FILE.exists():
        try:
            mtime = INVALIDATION_FILE.stat().st_mtime_ns
            if mtime != _last_mtime_ns:
                needs_reload = True
        except OSError:
            pass

    if needs_reload:
        with _lock:
            settings, descriptions, updated_at, updated_by = _load_settings_from_db()
            _cached_settings = settings
            _cached_descriptions = descriptions
            _last_updated_at = updated_at
            _last_updated_by = updated_by
            _last_sync_timestamp = current_time
            if INVALIDATION_FILE.exists():
                try:
                    _last_mtime_ns = INVALIDATION_FILE.stat().st_mtime_ns
                except OSError:
                    pass
            logger.info("Rate limit settings refreshed from PostgreSQL: %s", _cached_settings)


def notify_workers():
    """Touches the invalidation file so all Uvicorn worker processes refresh their cache."""
    try:
        INVALIDATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        now_ts = str(time.time_ns())
        INVALIDATION_FILE.write_text(now_ts)
    except Exception as e:
        logger.warning("Failed to touch rate limit invalidation file: %s", e)


def get_current_limits() -> dict[str, int]:
    """Returns active rate-limit dictionary for high-speed runtime lookups."""
    _check_and_sync()
    with _lock:
        return dict(_cached_settings)


def get_rate_limit_config_response() -> dict[str, Any]:
    """Returns complete settings payload for Admin UI & API."""
    _check_and_sync()
    with _lock:
        settings = dict(_cached_settings)
        descriptions = dict(_cached_descriptions)
        updated_at = _last_updated_at
        updated_by = _last_updated_by
        sync_ts = _last_sync_timestamp
        count_429 = _429_count
        last_429 = _last_429_at

    return {
        "settings": settings,
        "defaults": DEFAULT_RATE_LIMITS,
        "descriptions": descriptions,
        "constraints": RATE_LIMIT_CONSTRAINTS,
        "last_updated_at": updated_at,
        "last_updated_by": updated_by,
        "last_synced_at": datetime.fromtimestamp(sync_ts, tz=timezone.utc).isoformat() if sync_ts else None,
        "sync_status": "SYNCHRONIZED",
        "metrics": {
            "rate_limit_exceeded_total": count_429,
            "last_rate_limit_exceeded_at": last_429,
            "active_mode": "POSTGRESQL_DYNAMIC",
        }
    }


def validate_rate_limit_values(values: dict[str, Any]) -> dict[str, int]:
    """Validates submitted rate-limit values against schema and logic rules."""
    cleaned = {}
    for key, rule in RATE_LIMIT_CONSTRAINTS.items():
        if key not in values:
            raise ValueError(f"Missing required rate limit setting: '{key}'")
        raw_val = values[key]

        # Reject floats, booleans, strings that aren't clean ints
        if isinstance(raw_val, (bool, float)) or raw_val is None:
            raise ValueError(f"Setting '{key}' must be an integer.")
        try:
            val = int(raw_val)
        except (ValueError, TypeError):
            raise ValueError(f"Setting '{key}' must be a valid integer, got '{raw_val}'.")

        if val < rule["min"]:
            raise ValueError(f"Setting '{key}' cannot be less than {rule['min']}.")
        if val > rule["max"]:
            raise ValueError(f"Setting '{key}' cannot exceed {rule['max']:,}.")

        cleaned[key] = val

    # Logical validation: daily must be >= hourly
    if cleaned["submit_rate_limit_day"] < cleaned["submit_rate_limit_hour"]:
        raise ValueError("Public daily limit cannot be less than hourly limit.")
    if cleaned["secure_submit_rate_limit_day"] < cleaned["secure_submit_rate_limit_hour"]:
        raise ValueError("Secure-link daily limit cannot be less than hourly limit.")

    return cleaned


def update_rate_limit_settings(new_values: dict[str, Any], admin_email: str, client_ip: str) -> dict[str, Any]:
    """
    Validates, persists, logs, and synchronizes updated rate limit settings.
    """
    cleaned = validate_rate_limit_values(new_values)
    current = get_current_limits()

    now = datetime.now(timezone.utc)
    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                for k, v in cleaned.items():
                    cur.execute("""
                        INSERT INTO system_security_settings (setting_key, setting_value, updated_at, updated_by)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (setting_key) DO UPDATE
                        SET setting_value = EXCLUDED.setting_value,
                            updated_at = EXCLUDED.updated_at,
                            updated_by = EXCLUDED.updated_by
                    """, (k, str(v), now, admin_email))

                # Record audit log
                cur.execute("""
                    INSERT INTO audit_logs (admin_id, action_type, old_value, new_value, ip_address)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    admin_email,
                    "update_rate_limits",
                    json.dumps(current),
                    json.dumps(cleaned),
                    client_ip,
                ))

    # Update local in-memory cache immediately in current process
    with _lock:
        _cached_settings = dict(cleaned)
        _last_updated_at = now.isoformat()
        _last_updated_by = admin_email
        _last_sync_timestamp = time.time()

    # Touch invalidation file so peer workers reload
    notify_workers()
    if INVALIDATION_FILE.exists():
        try:
            _last_mtime_ns = INVALIDATION_FILE.stat().st_mtime_ns
        except OSError:
            pass

    logger.info("Admin %s updated rate limits from %s: %s", admin_email, client_ip, cleaned)
    return get_rate_limit_config_response()


def reset_rate_limit_settings(admin_email: str, client_ip: str) -> dict[str, Any]:
    """Restores system default rate-limit settings."""
    return update_rate_limit_settings(DEFAULT_RATE_LIMITS, admin_email, client_ip)


# ---------------------------------------------------------------------------
# Dynamic SlowAPI Limit Callables
# ---------------------------------------------------------------------------

def get_public_submit_hourly_limit() -> str:
    limits = get_current_limits()
    return f"{limits['submit_rate_limit_hour']}/hour"


def get_public_submit_daily_limit() -> str:
    limits = get_current_limits()
    return f"{limits['submit_rate_limit_day']}/day"


def get_secure_submit_hourly_limit() -> str:
    limits = get_current_limits()
    return f"{limits['secure_submit_rate_limit_hour']}/hour"


def get_secure_submit_daily_limit() -> str:
    limits = get_current_limits()
    return f"{limits['secure_submit_rate_limit_day']}/day"


def get_session_hourly_limit() -> str:
    limits = get_current_limits()
    return f"{limits['assessment_session_limit_hour']}/hour"


def get_invalid_token_minute_limit() -> str:
    limits = get_current_limits()
    return f"{limits['invalid_token_limit_minute']}/minute"


def get_effective_submit_hourly_limit() -> str:
    """Returns upper-bound hourly limit across public and secure channels for outer SlowAPI guard."""
    limits = get_current_limits()
    max_hr = max(limits["submit_rate_limit_hour"], limits["secure_submit_rate_limit_hour"])
    return f"{max_hr}/hour"


def get_effective_submit_daily_limit() -> str:
    """Returns upper-bound daily limit across public and secure channels for outer SlowAPI guard."""
    limits = get_current_limits()
    max_day = max(limits["submit_rate_limit_day"], limits["secure_submit_rate_limit_day"])
    return f"{max_day}/day"


# ---------------------------------------------------------------------------
# Dynamic Traffic Classification & Enforcement
# ---------------------------------------------------------------------------

def record_rate_limit_exceeded(key: str, limit_str: str, client_ip: str, classification: str):
    """Tracks metrics and sets state on rate limit violation."""
    global _429_count, _last_429_at
    with _lock:
        _429_count += 1
        _last_429_at = datetime.now(timezone.utc).isoformat()
    logger.warning(
        "Rate limit exceeded: classification=%s, ip=%s, key=%s, limit=%s (total_429=%d)",
        classification, client_ip, key, limit_str, _429_count
    )


def _raise_rate_limit_exceeded(request: Request, limit_str: str, key: str, client_ip: str, classification: str):
    """Constructs and raises RateLimitExceeded compatible with SlowAPI exception handler."""
    record_rate_limit_exceeded(key, limit_str, client_ip, classification)
    limit_item = parse(limit_str)
    # SlowAPI's exception handler reads request.state.view_rate_limit
    request.state.view_rate_limit = str(limit_item)
    limit_obj = Limit(
        limit_item,
        lambda r: key,
        None,
        False,
        None,
        limit_str,
        None,
        1,
        True,
    )
    raise RateLimitExceeded(limit_obj)


def enforce_submission_rate_limits(request: Request, data: dict[str, Any]):
    """
    Evaluates submission payload and client context to dynamically enforce:
      - Policy A: Public submissions per-IP hourly & daily limits.
      - Policy B: Valid secure-link submissions per-IP hourly & daily limits.
      - Policy C: Assessment session attempt bounds (server-issued draft IDs).
      - Policy D: Invalid / revoked assessment token abuse protection.
    """
    client_ip = get_client_ip(request)
    limits = get_current_limits()

    # Step 1: Assessment Session Attempt Limit (Policy C)
    draft_id_raw = (data.get("draft_id") or "").strip()
    if draft_id_raw:
        is_valid_uuid = False
        try:
            val_uuid = UUID(draft_id_raw)
            # Confirm draft exists in database to prevent trusting arbitrary client IDs
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM assessment_drafts WHERE id = %s", (str(val_uuid),))
                    if cur.fetchone():
                        is_valid_uuid = True
        except (ValueError, Exception):
            is_valid_uuid = False

        if is_valid_uuid:
            session_limit_str = f"{limits['assessment_session_limit_hour']}/hour"
            session_key = f"sess_hr:{draft_id_raw}"
            if not limiter.limiter.hit(parse(session_limit_str), session_key):
                _raise_rate_limit_exceeded(request, session_limit_str, session_key, client_ip, "SESSION")

    # Step 2: Traffic Classification (Policies A, B, D)
    raw_token = (data.get("t") or data.get("token") or data.get("access_token") or data.get("invitation_token") or "").strip()

    if raw_token:
        # Validate token authoritatively
        token_res = resolve_assessment_token(raw_token)
        if token_res.get("valid") is True:
            # Policy B: Valid Secure Link Submission
            sec_hr_limit = f"{limits['secure_submit_rate_limit_hour']}/hour"
            sec_day_limit = f"{limits['secure_submit_rate_limit_day']}/day"
            key_hr = f"sec_hr:{client_ip}"
            key_day = f"sec_day:{client_ip}"

            if not limiter.limiter.hit(parse(sec_hr_limit), key_hr):
                _raise_rate_limit_exceeded(request, sec_hr_limit, key_hr, client_ip, "SECURE_LINK_HOURLY")
            if not limiter.limiter.hit(parse(sec_day_limit), key_day):
                _raise_rate_limit_exceeded(request, sec_day_limit, key_day, client_ip, "SECURE_LINK_DAILY")
        else:
            # Policy D: Invalid or Revoked Assessment Token
            inv_min_limit = f"{limits['invalid_token_limit_minute']}/minute"
            inv_key = f"inv_min:{client_ip}"
            if not limiter.limiter.hit(parse(inv_min_limit), inv_key):
                _raise_rate_limit_exceeded(request, inv_min_limit, inv_key, client_ip, "INVALID_TOKEN")
    else:
        # Policy A: Normal Public Submission
        pub_hr_limit = f"{limits['submit_rate_limit_hour']}/hour"
        pub_day_limit = f"{limits['submit_rate_limit_day']}/day"
        key_hr = f"pub_hr:{client_ip}"
        key_day = f"pub_day:{client_ip}"

        if not limiter.limiter.hit(parse(pub_hr_limit), key_hr):
            _raise_rate_limit_exceeded(request, pub_hr_limit, key_hr, client_ip, "PUBLIC_HOURLY")
        if not limiter.limiter.hit(parse(pub_day_limit), key_day):
            _raise_rate_limit_exceeded(request, pub_day_limit, key_day, client_ip, "PUBLIC_DAILY")
