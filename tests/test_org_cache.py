"""
test_org_cache.py — Unit and integration tests for the in-memory organisation cache
and optimised organisation verification endpoint (Phases 1 & 2).
"""

import os
import time
import uuid
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.org_cache_service import (
    normalize_org_name,
    refresh_org_cache,
    invalidate_org_cache,
    get_organisation_by_name,
    get_organisation_by_id,
    is_org_eligible,
    get_cache_stats,
    INVALIDATION_FILE,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_cache_state():
    """Ensure clean cache state before each test."""
    if INVALIDATION_FILE.exists():
        try:
            INVALIDATION_FILE.unlink()
        except Exception:
            pass


class TestOrgCacheNormalisation:
    """Test organisation name normalisation logic."""

    def test_normalize_org_name_standard(self):
        assert normalize_org_name("Acme Corp") == "acme corp"
        assert normalize_org_name("  ACME   CORP  ") == "acme corp"
        assert normalize_org_name("Orchvate") == "orchvate"
        assert normalize_org_name("") == ""
        assert normalize_org_name(None) == ""


class TestOrgCacheFunctionality:
    """Test in-memory caching, atomic swaps, and database fallbacks."""

    def test_cache_refresh_and_hit(self):
        sample_orgs = [
            {
                "id": str(uuid.uuid4()),
                "name": "Sky11 Technologies",
                "is_active": True,
                "is_deleted": False,
                "approval_status": "approved",
                "updated_at": None,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Inactive Corp",
                "is_active": False,
                "is_deleted": False,
                "approval_status": "approved",
                "updated_at": None,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Pending Corp",
                "is_active": True,
                "is_deleted": False,
                "approval_status": "pending",
                "updated_at": None,
            },
        ]

        with patch("app.services.org_cache_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchall.return_value = sample_orgs

            success = refresh_org_cache()
            assert success is True

        # Warm cache lookup should be a CACHE_HIT without invoking DB
        t0 = time.perf_counter()
        org, source = get_organisation_by_name("Sky11 Technologies")
        duration_ms = (time.perf_counter() - t0) * 1000.0

        assert source == "CACHE_HIT"
        assert org is not None
        assert org["name"] == "Sky11 Technologies"
        assert duration_ms < 5.0, f"Cache lookup took {duration_ms}ms, expected <5ms"

        # Case-insensitive whitespace test
        org2, source2 = get_organisation_by_name("  sky11   technologies  ")
        assert source2 == "CACHE_HIT"
        assert org2["id"] == org["id"]

    def test_cache_miss_db_fallback_and_negative_cache(self):
        fake_id = str(uuid.uuid4())
        db_org = {
            "id": fake_id,
            "name": "Fallback Solutions",
            "is_active": True,
            "is_deleted": False,
            "approval_status": "approved",
            "updated_at": None,
        }

        with patch("app.services.org_cache_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            # First call finds the org in DB
            mock_cur.fetchone.return_value = db_org

            org, source = get_organisation_by_name("Fallback Solutions")
            assert source == "DB_HIT"
            assert org["id"] == fake_id

        # Second call must be a CACHE_HIT
        org_cached, source_cached = get_organisation_by_name("Fallback Solutions")
        assert source_cached == "CACHE_HIT"
        assert org_cached["id"] == fake_id

        # Non-existent org DB fallback
        with patch("app.services.org_cache_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchone.return_value = None

            org_none, source_miss = get_organisation_by_name("Completely NonExistent Inc")
            assert source_miss == "DB_MISS"
            assert org_none is None

        # Subsequent call for the same non-existent org should hit negative cache (zero DB calls)
        with patch("app.services.org_cache_service.get_db_connection") as mock_conn:
            org_neg, source_neg = get_organisation_by_name("Completely NonExistent Inc")
            assert source_neg == "NEGATIVE_HIT"
            assert org_neg is None
            mock_conn.assert_not_called()

    def test_cache_refresh_failure_preserves_snapshot(self):
        sample_orgs = [{
            "id": str(uuid.uuid4()),
            "name": "Resilient Corp",
            "is_active": True,
            "is_deleted": False,
            "approval_status": "approved",
            "updated_at": None,
        }]

        with patch("app.services.org_cache_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchall.return_value = sample_orgs
            refresh_org_cache()

        # Simulate DB connection error on next refresh
        with patch("app.services.org_cache_service.get_db_connection") as mock_conn:
            mock_conn.side_effect = RuntimeError("PostgreSQL connection timeout")
            success = refresh_org_cache()
            assert success is False

        # Old snapshot must be safely preserved
        org, source = get_organisation_by_name("Resilient Corp")
        assert source == "CACHE_HIT"
        assert org["name"] == "Resilient Corp"

    def test_eligibility_logic(self):
        valid_org = {"is_active": True, "is_deleted": False, "approval_status": "approved"}
        assert is_org_eligible(valid_org)[0] is True

        inactive_org = {"is_active": False, "is_deleted": False, "approval_status": "approved"}
        eligible, err = is_org_eligible(inactive_org)
        assert eligible is False
        assert "inactive" in err.lower()

        deleted_org = {"is_active": True, "is_deleted": True, "approval_status": "approved"}
        eligible, err = is_org_eligible(deleted_org)
        assert eligible is False
        assert "deactivated or removed" in err.lower()

        pending_org = {"is_active": True, "is_deleted": False, "approval_status": "pending"}
        eligible, err = is_org_eligible(pending_org)
        assert eligible is False
        assert "approval" in err.lower()

    def test_interprocess_invalidation_trigger(self):
        sample_orgs_v1 = [{
            "id": str(uuid.uuid4()),
            "name": "Sync Corp",
            "is_active": True,
            "is_deleted": False,
            "approval_status": "approved",
            "updated_at": None,
        }]
        sample_orgs_v2 = [{
            "id": sample_orgs_v1[0]["id"],
            "name": "Sync Corp Renamed",
            "is_active": True,
            "is_deleted": False,
            "approval_status": "approved",
            "updated_at": None,
        }]

        with patch("app.services.org_cache_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchall.return_value = sample_orgs_v1
            refresh_org_cache()

        # Invalidate via file touch
        with patch("app.services.org_cache_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchall.return_value = sample_orgs_v2
            invalidate_org_cache()

        org, _ = get_organisation_by_name("Sync Corp Renamed")
        assert org is not None
        assert org["name"] == "Sync Corp Renamed"


class TestPublicOrganisationEndpoint:
    """Integration tests for POST /api/public/organisations/validate."""

    def test_validate_org_cached_success(self):
        test_id = str(uuid.uuid4())
        sample = [{
            "id": test_id,
            "name": "FastTrack Logistics",
            "is_active": True,
            "is_deleted": False,
            "approval_status": "approved",
            "updated_at": None,
        }]

        with patch("app.services.org_cache_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchall.return_value = sample
            refresh_org_cache()

        t0 = time.perf_counter()
        res = client.post("/api/public/organisations/validate", json={"name": "fasttrack logistics"})
        latency_ms = (time.perf_counter() - t0) * 1000.0

        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert data["organization_id"] == test_id
        assert data["organization_name"] == "FastTrack Logistics"
        assert latency_ms < 50.0, f"Endpoint took {latency_ms}ms, expected sub-50ms"

    def test_validate_org_inactive_fails(self):
        test_id = str(uuid.uuid4())
        sample = [{
            "id": test_id,
            "name": "Inactive Logistics",
            "is_active": False,
            "is_deleted": False,
            "approval_status": "approved",
            "updated_at": None,
        }]

        with patch("app.services.org_cache_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchall.return_value = sample
            refresh_org_cache()

        res = client.post("/api/public/organisations/validate", json={"name": "Inactive Logistics"})
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is False
        assert "inactive" in data["error"].lower()

    def test_validate_org_empty_input(self):
        res = client.post("/api/public/organisations/validate", json={"name": "   "})
        assert res.status_code == 200
        assert res.json()["valid"] is False
        assert "empty" in res.json()["error"].lower()

    def test_diagnostic_cache_metrics_endpoint(self):
        res = client.get("/api/health/cache-metrics")
        assert res.status_code == 200
        data = res.json()
        assert "total_cached_orgs" in data
        assert "cache_hits" in data
        assert "hit_ratio_percent" in data

