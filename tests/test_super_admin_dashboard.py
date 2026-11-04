"""
test_super_admin_dashboard.py — Unit & Integration tests for Super Admin Operations Dashboard.
Covers:
1. Request overview and analytics computation
2. 2-minute snapshot caching & table fallback
3. Worker heartbeat tracking & 3-minute offline detection
4. RBAC access control: Super Admin strictly required
"""
import pytest
import time
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from app.services.dashboard_service import (
    compute_fresh_dashboard_stats,
    get_dashboard_snapshot,
    _format_duration,
    _MEMORY_CACHE,
)
from app.services.worker_tracker import WorkerTracker


def test_format_duration():
    assert _format_duration(None) == "None"
    assert _format_duration(45) == "45s"
    assert _format_duration(95) == "1m 35s"
    assert _format_duration(3665) == "1h 1m"


def test_offline_worker_detection_over_3_minutes():
    """Requirement 3: A worker is marked offline if its last heartbeat is older than 3 minutes (180s)."""
    now = datetime.now(timezone.utc)
    mock_workers = [
        {
            "worker_id": "active-worker-1",
            "worker_type": "service_bus_worker",
            "status": "active",
            "current_task": "Processing 5 items",
            "jobs_completed": 100,
            "started_at": now - timedelta(hours=1),
            "last_heartbeat": now - timedelta(seconds=30),
            "seconds_since_heartbeat": 30.0,
        },
        {
            "worker_id": "idle-worker-2",
            "worker_type": "db_fallback_worker",
            "status": "idle",
            "current_task": "Waiting for messages",
            "jobs_completed": 50,
            "started_at": now - timedelta(hours=2),
            "last_heartbeat": now - timedelta(seconds=120),
            "seconds_since_heartbeat": 120.0,
        },
        {
            "worker_id": "stale-worker-3",
            "worker_type": "service_bus_worker",
            "status": "active",  # Recorded as active before crashing
            "current_task": "Dead task",
            "jobs_completed": 10,
            "started_at": now - timedelta(hours=3),
            "last_heartbeat": now - timedelta(seconds=240), # > 180s ago!
            "seconds_since_heartbeat": 240.0,
        },
    ]

    mock_cur = MagicMock()
    mock_cur.fetchall.side_effect = [
        # 1. status counts
        [{"status": "RECEIVED", "count": 10}, {"status": "COMPLETED", "count": 90}],
        # 2. hourly timeline
        [{"bucket": now, "count": 5}],
        # 3. daily timeline
        [{"bucket": now, "count": 100}],
        # 4. worker rows
        mock_workers,
    ]
    mock_cur.fetchone.side_effect = [
        # avg seconds
        {"avg_seconds": 1.25},
        # oldest pending
        {"submission_id": "sub-1234", "created_at": now - timedelta(minutes=10), "waiting_seconds": 600.0},
    ]

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    with patch("app.services.dashboard_service.get_db_connection", return_value=mock_conn):
        stats = compute_fresh_dashboard_stats()

    # Check worker classification
    wp = stats["worker_progress"]
    assert wp["total_workers"] == 3
    assert wp["active_workers"] == 1
    assert wp["idle_workers"] == 1
    assert wp["offline_workers"] == 1  # Stale worker marked offline!

    # Check oldest pending
    assert stats["analytics"]["oldest_pending_request"]["waiting_time_formatted"] == "10m 0s"
    assert stats["request_overview"]["pending"] == 10
    assert stats["request_overview"]["completed"] == 90
    assert stats["analytics"]["success_rate"] == 100.0


def test_snapshot_memory_cache_prevents_db_queries():
    """Requirement 5: Stats must not be queried on every page load. Cached for 2 minutes."""
    _MEMORY_CACHE["data"] = {
        "timestamp": "2026-11-04T19:00:00Z",
        "cached_data": True
    }
    _MEMORY_CACHE["cached_at"] = time.monotonic()  # Just cached

    with patch("app.services.dashboard_service.get_db_connection") as mock_db:
        result = get_dashboard_snapshot(force_refresh=False)
        assert result["cached_data"] is True
        mock_db.assert_not_called()  # Zero database queries!


def test_worker_tracker_heartbeat_throttling():
    """Requirement 5: Workers update their own row every 30-60 seconds, not on every step."""
    tracker = WorkerTracker(worker_id="test-w1", heartbeat_interval=45.0)

    with patch("app.services.worker_tracker.get_db_connection") as mock_db:
        # First heartbeat forced
        tracker.heartbeat_if_due(force=True)
        assert mock_db.call_count == 1

        # Second heartbeat immediately after (should be throttled / skipped)
        tracker.heartbeat_if_due(force=False)
        assert mock_db.call_count == 1  # Still 1, didn't write to DB!


def test_super_admin_route_access_control():
    """Requirement 6: Strictly accessible only to users with the Super Admin role."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # 1. Unauthenticated -> 401
    res1 = client.get("/api/admin/dashboard")
    assert res1.status_code == 401

    # 2. Normal Admin role="admin" -> 403 Forbidden
    with patch("app.core.authorization.get_user_from_request", return_value={"email": "admin@example.com", "role": "admin"}):
        res2 = client.get("/api/admin/dashboard", headers={"Authorization": "Bearer mock-token"})
        assert res2.status_code == 403
        assert "Super administrator privileges required" in res2.json()["detail"]

    # 3. Super Admin role="super" -> 200 OK
    mock_snapshot = {
        "timestamp": "2026-11-04T19:00:00Z",
        "request_overview": {"total_requests": 100, "pending": 5},
        "analytics": {"success_rate": 99.0},
        "worker_progress": {"total_workers": 2}
    }
    with patch("app.core.authorization.get_user_from_request", return_value={"email": "super@example.com", "role": "super"}), \
         patch("app.services.dashboard_service.get_dashboard_snapshot", return_value=mock_snapshot):
        res3 = client.get("/api/admin/dashboard", headers={"Authorization": "Bearer mock-token"})
        assert res3.status_code == 200
        assert res3.json()["request_overview"]["pending"] == 5
