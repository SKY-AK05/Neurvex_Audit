"""
helpers.py — General utility functions
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def safe_isoformat(dt) -> str | None:
    return dt.isoformat() if dt else None
