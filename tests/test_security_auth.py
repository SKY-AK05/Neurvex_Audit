"""
test_security_auth.py — Automated tests for security, authentication, and authorization.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI


def test_production_jwt_secret_validation():
    """Verify application fails to start if JWT_SECRET is weak or default in production."""
    import sys
    import importlib

    with patch.dict(os.environ, {"APP_ENV": "production", "JWT_SECRET": "default_jwt_secret_key_change_me"}, clear=False):
        sys.modules.pop("app.core.config", None)
        with pytest.raises(RuntimeError, match="Missing or insecure JWT_SECRET"):
            import app.core.config

    with patch.dict(os.environ, {"APP_ENV": "production", "JWT_SECRET": "too-short"}, clear=False):
        sys.modules.pop("app.core.config", None)
        with pytest.raises(RuntimeError, match="too short for production"):
            import app.core.config

    # Restore dev config
    with patch.dict(os.environ, {"APP_ENV": "development", "JWT_SECRET": "a-sufficiently-long-secret-key-for-tests-32chars"}, clear=False):
        sys.modules.pop("app.core.config", None)
        import app.core.config



@pytest.fixture
def client():
    # Set development environment for testing
    with patch.dict(os.environ, {
        "APP_ENV": "development",
        "ENABLE_DEV_BYPASS": "true",
        "JWT_SECRET": "a-sufficiently-long-secret-key-for-tests-32chars",
    }):
        from app.main import app
        with TestClient(app) as c:
            yield c


def test_unauthenticated_admin_endpoints(client):
    """Admin endpoints must reject requests with missing or invalid Authorization header."""
    protected_urls = [
        ("GET", "/api/submissions"),
        ("POST", "/api/submissions/filter"),
        ("GET", "/api/submissions/saved-filters"),
        ("POST", "/api/submissions/saved-filters"),
        ("GET", "/api/manage/users"),
        ("GET", "/api/settings"),
    ]

    for method, url in protected_urls:
        if method == "GET":
            res = client.get(url)
        else:
            res = client.post(url, json={})
        assert res.status_code == 401, f"{method} {url} should require authorization, got {res.status_code}"
        assert "Missing or invalid Authorization header" in res.json().get("detail", "")


def test_form_builder_mutations_protected(client):
    """Form builder modifications must require authentication, while GET /api/form/sections is public."""
    # Public questionnaire endpoint
    with patch("app.api.form_builder.get_conn") as mock_conn:
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cur
        get_res = client.get("/api/form/sections")
        assert get_res.status_code == 200

    # Mutating endpoints must be rejected with 401
    post_res = client.post("/api/form/sections", json={"section_code": "test", "title": "Test"})
    assert post_res.status_code == 401

    put_res = client.put("/api/form/sections/1", json={"section_code": "test", "title": "Test"})
    assert put_res.status_code == 401

    del_res = client.delete("/api/form/sections/1")
    assert del_res.status_code == 401


def test_public_endpoints_accessible(client):
    """Legitimate public endpoints must remain accessible without auth."""
    res_health = client.get("/api/health")
    assert res_health.status_code in (200, 503)  # Depending on DB connection

    res_auth_cfg = client.get("/api/auth/config")
    assert res_auth_cfg.status_code == 200


def test_dev_bypass_disabled_in_production(client):
    """Dev bypass must be rejected in production even if token starts with local_bypass:."""
    with patch.dict(os.environ, {"APP_ENV": "production", "ENABLE_DEV_BYPASS": "false"}):
        res = client.get(
            "/api/submissions",
            headers={"Authorization": "Bearer local_bypass:test@orchvate.com"}
        )
        assert res.status_code == 401


def test_submission_id_format_validation(client):
    """GET /api/submissions/{id} must reject malformed IDs with 400 Bad Request."""
    with patch.dict(os.environ, {"APP_ENV": "development", "ENABLE_DEV_BYPASS": "true"}):
        # Mock admin auth via bypass
        with patch("app.core.database.get_conn") as mock_db:
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = ("admin",)
            mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cur

            # Request with non-UUID non-integer garbage ID
            res = client.get(
                "/api/submissions/malicious-sql-injection-or-garbage!",
                headers={"Authorization": "Bearer local_bypass:admin@orchvate.com"}
            )
            assert res.status_code == 400
            assert "Invalid submission ID format" in res.json().get("detail", "")
