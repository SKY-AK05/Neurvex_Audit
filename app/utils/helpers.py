"""
helpers.py — General utility functions
"""
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def now_ist() -> datetime:
    return datetime.now(IST)


def to_iso_utc(dt: datetime | None) -> str | None:
    """Serialize datetimes for JSON (always UTC with Z suffix)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_isoformat(dt) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return to_iso_utc(dt)
    return str(dt)
