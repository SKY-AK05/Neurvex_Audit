"""
tests/test_rate_limits.py — Comprehensive tests for dynamic, admin-configurable rate limits.
Covers validation, database persistence, in-memory caching, cross-worker invalidation,
traffic classification (Policies A, B, C, D), and admin API authorization.
"""

import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from limits import parse

from app.main import app
from app.core.limiter import limiter
from app.services.rate_limit_service import (
    DEFAULT_RATE_LIMITS,
    RATE_LIMIT_CONSTRAINTS,
    validate_rate_limit_values,
    get_current_limits,
    get_rate_limit_config_response,
    update_rate_limit_settings,
    reset_rate_limit_settings,
    enforce_submission_rate_limits,
    notify_workers,
    get_client_ip,
    get_effective_submit_hourly_limit,
    get_effective_submit_daily_limit,
)

client = TestClient(app)
ADMIN_HEADERS = {"Authorization": "Bearer local_bypass:admin@test.com"}
NON_ADMIN_HEADERS = {"Authorization": "Bearer local_bypass:user@external.com"}


class TestValidation:
    """Tests validation of rate limit parameters."""

    def test_valid_default_configuration(self):
        cleaned = validate_rate_limit_values(DEFAULT_RATE_LIMITS)
        assert cleaned == DEFAULT_RATE_LIMITS

    def test_missing_key_raises_value_error(self):
        incomplete = dict(DEFAULT_RATE_LIMITS)
        del incomplete["submit_rate_limit_hour"]
        with pytest.raises(ValueError, match="Missing required rate limit setting"):
            validate_rate_limit_values(incomplete)

    def test_invalid_type_raises_value_error(self):
        bad_types = [
            ("submit_rate_limit_hour", "not_a_number"),
            ("submit_rate_limit_hour", 50.5),
            ("submit_rate_limit_hour", True),
            ("submit_rate_limit_hour", None),
        ]
        for key, val in bad_types:
            copy_cfg = dict(DEFAULT_RATE_LIMITS)
            copy_cfg[key] = val
            with pytest.raises(ValueError):
                validate_rate_limit_values(copy_cfg)

    def test_out_of_range_raises_value_error(self):
        # Value < min
        cfg_too_low = dict(DEFAULT_RATE_LIMITS)
        cfg_too_low["submit_rate_limit_hour"] = 0
        with pytest.raises(ValueError, match="cannot be less than 1"):
            validate_rate_limit_values(cfg_too_low)

        # Value > max
        cfg_too_high = dict(DEFAULT_RATE_LIMITS)
        cfg_too_high["submit_rate_limit_hour"] = 200_000
        with pytest.raises(ValueError, match="cannot exceed"):
            validate_rate_limit_values(cfg_too_high)

    def test_daily_less_than_hourly_rejected(self):
        cfg = dict(DEFAULT_RATE_LIMITS)
        cfg["submit_rate_limit_hour"] = 500
        cfg["submit_rate_limit_day"] = 400
        with pytest.raises(ValueError, match="Public daily limit cannot be less than hourly limit"):
            validate_rate_limit_values(cfg)

        cfg2 = dict(DEFAULT_RATE_LIMITS)
        cfg2["secure_submit_rate_limit_hour"] = 600
        cfg2["secure_submit_rate_limit_day"] = 500
        with pytest.raises(ValueError, match="Secure-link daily limit cannot be less than hourly limit"):
            validate_rate_limit_values(cfg2)


class TestClientIpExtraction:
    """Tests authentic client IP extraction behind proxies."""

    def test_x_real_ip_precedence(self):
        req = MagicMock()
        req.headers = {
            "x-real-ip": "203.0.113.10",
            "x-forwarded-for": "198.51.100.1, 10.0.0.1",
        }
        assert get_client_ip(req) == "203.0.113.10"

    def test_x_forwarded_for_fallback(self):
        req = MagicMock()
        req.headers = {
            "x-forwarded-for": "198.51.100.5, 10.0.0.2",
        }
        assert get_client_ip(req) == "198.51.100.5"

    def test_direct_host_fallback(self):
        req = MagicMock()
        req.headers = {}
        req.client.host = "192.168.1.50"
        assert get_client_ip(req) == "192.168.1.50"


class TestWorkerInvalidation:
    """Tests cross-worker notification file mechanism."""

    def test_invalidation_file_touch(self, tmp_path):
        test_file = tmp_path / "test_rate_limit_version"
        with patch("app.services.rate_limit_service.INVALIDATION_FILE", test_file):
            assert not test_file.exists()
            notify_workers()
            assert test_file.exists()
            content1 = test_file.read_text()
            time.sleep(0.01)
            notify_workers()
            content2 = test_file.read_text()
            assert int(content2) >= int(content1)


class TestAdminApis:
    """Tests the admin rate limit configuration endpoints."""

    def test_get_rate_limits_unauthenticated(self):
        resp = client.get("/api/manage/settings/rate-limits")
        assert resp.status_code in (401, 403)

    @patch("app.api.routes.require_admin")
    def test_get_rate_limits_admin(self, mock_auth):
        mock_auth.return_value = {"email": "admin@orchvate.com", "role": "admin"}
        resp = client.get("/api/manage/settings/rate-limits", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "settings" in data
        assert "defaults" in data
        assert "constraints" in data
        assert data["settings"]["submit_rate_limit_hour"] >= 1

    @patch("app.api.routes.require_admin")
    def test_update_rate_limits_validation_error(self, mock_auth):
        mock_auth.return_value = {"email": "admin@orchvate.com", "role": "admin"}
        bad_payload = dict(DEFAULT_RATE_LIMITS)
        bad_payload["submit_rate_limit_day"] = 5  # less than hourly (500)
        resp = client.put(
            "/api/manage/settings/rate-limits",
            json=bad_payload,
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 400
        assert "Public daily limit cannot be less than hourly limit" in resp.json()["detail"]

    @patch("app.api.routes.require_admin")
    def test_update_and_reset_rate_limits(self, mock_auth):
        mock_auth.return_value = {"email": "admin@orchvate.com", "role": "admin"}
        new_cfg = dict(DEFAULT_RATE_LIMITS)
        new_cfg["submit_rate_limit_hour"] = 650
        new_cfg["submit_rate_limit_day"] = 2500

        # Update
        put_resp = client.put(
            "/api/manage/settings/rate-limits",
            json=new_cfg,
            headers=ADMIN_HEADERS,
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["settings"]["submit_rate_limit_hour"] == 650

        # Reset back to defaults
        rst_resp = client.post(
            "/api/manage/settings/rate-limits/reset",
            headers=ADMIN_HEADERS,
        )
        assert rst_resp.status_code == 200
        assert rst_resp.json()["settings"]["submit_rate_limit_hour"] == 500


class TestDynamicSlowAPIProviders:
    """Tests dynamic SlowAPI limit string providers."""

    def test_effective_limit_callables(self):
        hr = get_effective_submit_hourly_limit()
        day = get_effective_submit_daily_limit()
        assert "/hour" in hr
        assert "/day" in day


class TestTrafficClassificationEnforcement:
    """Tests fine-grained traffic classification under SlowAPI."""

    def test_policy_c_session_attempt_limit(self):
        # Draft session ID hitting limit
        draft_id = str(uuid.uuid4())
        mock_req = MagicMock()
        mock_req.headers = {"x-real-ip": "1.2.3.4"}
        mock_req.state = MagicMock()

        # Mock DB finding draft ID
        with patch("app.services.rate_limit_service.get_db_connection") as mock_conn:
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = (1,)
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cur

            # Clear limiter counter
            limiter.reset()

            # First 3 should succeed
            for i in range(3):
                enforce_submission_rate_limits(mock_req, {"draft_id": draft_id})

            # 4th should exceed session attempt limit
            with pytest.raises(Exception) as exc_info:
                enforce_submission_rate_limits(mock_req, {"draft_id": draft_id})
            assert "RateLimitExceeded" in type(exc_info.value).__name__

    def test_policy_d_invalid_token_abuse_protection(self):
        mock_req = MagicMock()
        mock_req.headers = {"x-real-ip": "99.88.77.66"}
        mock_req.state = MagicMock()

        with patch("app.services.rate_limit_service.resolve_assessment_token") as mock_resolve:
            mock_resolve.return_value = {"valid": False, "error": "Invalid token"}

            limiter.reset()

            # 10 invalid token attempts should succeed within minute limit
            for _ in range(10):
                enforce_submission_rate_limits(mock_req, {"t": "bogus-token-attempt"})

            # 11th should raise RateLimitExceeded
            with pytest.raises(Exception) as exc_info:
                enforce_submission_rate_limits(mock_req, {"t": "bogus-token-attempt"})
            assert "RateLimitExceeded" in type(exc_info.value).__name__

    def test_policy_b_secure_link_allows_traffic(self):
        mock_req = MagicMock()
        mock_req.headers = {"x-real-ip": "100.200.50.25"}
        mock_req.state = MagicMock()

        with patch("app.services.rate_limit_service.resolve_assessment_token") as mock_resolve:
            mock_resolve.return_value = {
                "valid": True,
                "organization_id": str(uuid.uuid4()),
                "organization_name": "Test Enterprise",
            }

            limiter.reset()
            # Valid token succeeds
            enforce_submission_rate_limits(mock_req, {"t": "valid-secure-token"})
