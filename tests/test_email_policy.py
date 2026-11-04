"""
test_email_policy.py — Unit and integration tests for corporate email eligibility verification (Phase 3).
"""

import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.email_policy_service import (
    check_corporate_email_eligibility,
    validate_email_syntax,
    extract_and_normalize_domain,
)

client = TestClient(app)


class TestEmailPolicyService:
    """Tests for email syntax and provider blocklist verification."""

    @pytest.mark.parametrize("email,expected_domain", [
        ("person@company.com", "company.com"),
        ("person@orchvate.in", "orchvate.in"),
        ("person@startup.ai", "startup.ai"),
        ("person@enterprise.co.in", "enterprise.co.in"),
        ("john.doe+audit@sub.fintech-group.org", "sub.fintech-group.org"),
        ("FIRST.LAST@CORP-DOMAIN.NET", "corp-domain.net"),
    ])
    def test_corporate_email_accepted(self, email, expected_domain):
        res = check_corporate_email_eligibility(email)
        assert res["eligible"] is True
        assert res["email_verified"] is False
        assert res["domain"] == expected_domain
        assert "error" not in res

    @pytest.mark.parametrize("email,expected_domain", [
        ("person@gmail.com", "gmail.com"),
        ("person@googlemail.com", "googlemail.com"),
        ("person@yahoo.com", "yahoo.com"),
        ("person@yahoo.co.in", "yahoo.co.in"),
        ("person@outlook.com", "outlook.com"),
        ("person@hotmail.com", "hotmail.com"),
        ("person@live.com", "live.com"),
        ("person@icloud.com", "icloud.com"),
        ("person@me.com", "me.com"),
        ("person@aol.com", "aol.com"),
        ("person@proton.me", "proton.me"),
        ("person@protonmail.com", "protonmail.com"),
        ("person@zoho.com", "zoho.com"),
        ("person@mailinator.com", "mailinator.com"),
        ("person@tempmail.com", "tempmail.com"),
        ("person@10minutemail.com", "10minutemail.com"),
        ("person@rediffmail.com", "rediffmail.com"),
    ])
    def test_personal_and_disposable_email_rejected(self, email, expected_domain):
        res = check_corporate_email_eligibility(email)
        assert res["eligible"] is False
        assert res["email_verified"] is False
        assert res["domain"] == expected_domain
        assert "error" in res
        assert "personal or free email provider" in res["error"]

    @pytest.mark.parametrize("invalid_email", [
        "",
        "   ",
        None,
        "not-an-email",
        "missing-domain@",
        "@missing-user.com",
        "spaces in@domain.com",
        "user@nodot",
    ])
    def test_malformed_email_rejected(self, invalid_email):
        res = check_corporate_email_eligibility(invalid_email)
        assert res["eligible"] is False
        assert "error" in res

    def test_email_policy_submillisecond_performance(self):
        """Verify blocklist verification runs in <0.1ms."""
        emails = [
            "person@company.com",
            "person@gmail.com",
            "person@orchvate.in",
            "person@yahoo.com",
            "person@startup.ai",
        ]
        t0 = time.perf_counter()
        for _ in range(1000):
            for e in emails:
                check_corporate_email_eligibility(e)
        duration_ms = (time.perf_counter() - t0) * 1000.0
        avg_per_check_ms = duration_ms / (1000 * len(emails))
        assert avg_per_check_ms < 0.05, f"Average check was {avg_per_check_ms:.4f}ms, expected <0.05ms"


class TestEmailValidationEndpoint:
    """Integration tests for POST /api/public/email/validate."""

    def test_endpoint_corporate_email_eligible(self):
        t0 = time.perf_counter()
        res = client.post("/api/public/email/validate", json={"email": "employee@orchvate.in"})
        latency_ms = (time.perf_counter() - t0) * 1000.0

        assert res.status_code == 200
        data = res.json()
        assert data["eligible"] is True
        assert data["email_verified"] is False
        assert data["domain"] == "orchvate.in"
        assert latency_ms < 20.0

    def test_endpoint_personal_email_ineligible(self):
        res = client.post("/api/public/email/validate", json={"email": "applicant@gmail.com"})
        assert res.status_code == 200
        data = res.json()
        assert data["eligible"] is False
        assert data["email_verified"] is False
        assert data["domain"] == "gmail.com"
        assert "error" in data

    def test_endpoint_empty_email_rejected(self):
        res = client.post("/api/public/email/validate", json={"email": ""})
        assert res.status_code == 422  # Pydantic validation failure on min_length=3

