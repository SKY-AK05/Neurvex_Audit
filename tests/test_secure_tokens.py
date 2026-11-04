"""
test_secure_tokens.py — Unit and integration tests for secure organisation assessment links (Phase 4).
"""

import hashlib
import time
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.token_service import (
    generate_secure_token,
    hash_token,
    create_assessment_token,
    resolve_assessment_token,
    revoke_assessment_token,
)

client = TestClient(app)
ADMIN_HEADERS = {"Authorization": "Bearer local_bypass:admin@test.com"}


class TestTokenServicePrimitives:
    """Test token generation and hashing security primitives."""

    def test_token_entropy_and_format(self):
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        assert token1 != token2
        assert len(token1) >= 42  # 32 bytes base64-urlsafe gives 43 chars
        assert "/" not in token1
        assert "+" not in token1

    def test_hash_token_sha256(self):
        raw = "test-token-12345"
        expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        assert hash_token(raw) == expected
        assert len(hash_token(raw)) == 64
        assert hash_token("") == ""


class TestTokenResolution:
    """Test assessment token validation, revocation, and backward compatibility."""

    def test_resolve_valid_assessment_token(self):
        token_id = str(uuid.uuid4())
        org_id = str(uuid.uuid4())
        campaign_id = str(uuid.uuid4())
        raw_token = generate_secure_token()
        t_hash = hash_token(raw_token)

        db_record = {
            "token_id": token_id,
            "organisation_id": org_id,
            "campaign_id": campaign_id,
            "link_name": "Q4 Neurodiversity Assessment",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "revoked_at": None,
            "organization_name": "Nexora Global",
            "org_active": True,
            "org_deleted": False,
            "org_approval": "approved",
        }

        with patch("app.services.token_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchone.return_value = db_record

            res = resolve_assessment_token(raw_token)

        assert res["valid"] is True
        assert res["organization_name"] == "Nexora Global"
        assert res["campaign_id"] == campaign_id
        assert res["link_name"] == "Q4 Neurodiversity Assessment"
        assert res["token_id"] == token_id
        assert "error" not in res

    def test_resolve_revoked_token(self):
        raw_token = generate_secure_token()
        db_record = {
            "token_id": str(uuid.uuid4()),
            "organisation_id": str(uuid.uuid4()),
            "campaign_id": None,
            "link_name": "Revoked Link",
            "expires_at": None,
            "revoked_at": datetime.now(timezone.utc) - timedelta(hours=1),
            "organization_name": "Test Org",
            "org_active": True,
            "org_deleted": False,
            "org_approval": "approved",
        }

        with patch("app.services.token_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchone.return_value = db_record

            res = resolve_assessment_token(raw_token)

        assert res["valid"] is False
        assert "revoked" in res["error"].lower()

    def test_resolve_expired_token(self):
        raw_token = generate_secure_token()
        db_record = {
            "token_id": str(uuid.uuid4()),
            "organisation_id": str(uuid.uuid4()),
            "campaign_id": None,
            "link_name": "Expired Link",
            "expires_at": datetime.now(timezone.utc) - timedelta(days=1),
            "revoked_at": None,
            "organization_name": "Test Org",
            "org_active": True,
            "org_deleted": False,
            "org_approval": "approved",
        }

        with patch("app.services.token_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchone.return_value = db_record

            res = resolve_assessment_token(raw_token)

        assert res["valid"] is False
        assert "expired" in res["error"].lower()

    def test_resolve_inactive_organisation(self):
        raw_token = generate_secure_token()
        db_record = {
            "token_id": str(uuid.uuid4()),
            "organisation_id": str(uuid.uuid4()),
            "campaign_id": None,
            "link_name": "Inactive Org Link",
            "expires_at": None,
            "revoked_at": None,
            "organization_name": "Inactive Org",
            "org_active": False,
            "org_deleted": False,
            "org_approval": "approved",
        }

        with patch("app.services.token_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchone.return_value = db_record

            res = resolve_assessment_token(raw_token)

        assert res["valid"] is False
        assert "inactive" in res["error"].lower()

    def test_backward_compatibility_fallback_to_legacy_invitation(self):
        raw_token = generate_secure_token()
        legacy_inv = {
            "token_id": str(uuid.uuid4()),
            "organisation_id": str(uuid.uuid4()),
            "campaign_id": None,
            "link_name": "Legacy Invitation",
            "expires_at": None,
            "revoked_at": None,
            "inv_active": True,
            "max_submissions": 50,
            "submission_count": 5,
            "organization_name": "Legacy Partner",
            "org_active": True,
            "org_deleted": False,
            "org_approval": "approved",
        }

        with patch("app.services.token_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            # First fetchone on assessment_access_tokens returns None
            # Second fetchone on organization_invitations returns legacy_inv
            mock_cur.fetchone.side_effect = [None, legacy_inv]

            res = resolve_assessment_token(raw_token)

        assert res["valid"] is True
        assert res["organization_name"] == "Legacy Partner"
        assert res["is_legacy_invitation"] is True


class TestPublicResolveLinkEndpoint:
    """Integration tests for POST /api/public/assessment/resolve-link."""

    def test_endpoint_resolve_success(self):
        raw_token = generate_secure_token()
        db_record = {
            "token_id": str(uuid.uuid4()),
            "organisation_id": str(uuid.uuid4()),
            "campaign_id": None,
            "link_name": "Engineering Assessment",
            "expires_at": None,
            "revoked_at": None,
            "organization_name": "Orchvate Internal",
            "org_active": True,
            "org_deleted": False,
            "org_approval": "approved",
        }

        with patch("app.services.token_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchone.return_value = db_record

            t0 = time.perf_counter()
            res = client.post("/api/public/assessment/resolve-link", json={"token": raw_token})
            latency_ms = (time.perf_counter() - t0) * 1000.0

        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert data["organization_name"] == "Orchvate Internal"
        assert latency_ms < 50.0

    def test_endpoint_empty_token(self):
        res = client.post("/api/public/assessment/resolve-link", json={"token": ""})
        assert res.status_code == 422


class TestAdminAssessmentLinkManagement:
    """Tests for admin creation, listing, and revocation of assessment links."""

    def test_create_assessment_link(self):
        org_id = str(uuid.uuid4())
        mock_org = {"id": org_id, "name": "Titan Corp", "is_active": True, "is_deleted": False, "approval_status": "approved"}
        mock_inserted = {
            "id": str(uuid.uuid4()),
            "organisation_id": org_id,
            "campaign_id": None,
            "name": "Titan Link",
            "created_by": "admin@test.com",
            "created_at": datetime.now(timezone.utc),
            "expires_at": None,
        }

        with patch("app.services.token_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchone.side_effect = [mock_org, mock_inserted]

            res = client.post(
                f"/api/manage/orgs/{org_id}/assessment-links",
                headers=ADMIN_HEADERS,
                json={"name": "Titan Link"}
            )

        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Titan Link"
        assert "raw_token" in data
        assert data["assessment_url"].startswith("/audit?t=")

    def test_revoke_assessment_link(self):
        org_id = str(uuid.uuid4())
        token_id = str(uuid.uuid4())

        with patch("app.services.token_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.rowcount = 1

            res = client.delete(
                f"/api/manage/orgs/{org_id}/assessment-links/{token_id}",
                headers=ADMIN_HEADERS,
            )

        assert res.status_code == 200
        assert res.json()["success"] is True

    def test_get_or_create_default_assessment_link_endpoint(self):
        org_id = str(uuid.uuid4())
        mock_token_row = {
            "id": str(uuid.uuid4()),
            "organisation_id": org_id,
            "campaign_id": None,
            "name": "Corporate Assessment Link",
            "token": "test-default-token-xyz123",
            "is_default": True,
            "created_by": "admin@test.com",
            "created_at": datetime.now(timezone.utc),
            "expires_at": None,
        }

        with patch("app.services.token_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchone.return_value = mock_token_row

            res = client.post(
                f"/api/manage/orgs/{org_id}/assessment-links/default",
                headers=ADMIN_HEADERS,
            )

        assert res.status_code == 200
        data = res.json()
        assert data["raw_token"] == "test-default-token-xyz123"
        assert data["assessment_url"] == "/audit?t=test-default-token-xyz123"


class TestTokenEncryptionAndLegacySupport:
    """Tests for token encryption/decryption and legacy org resolution."""

    def test_encrypt_and_decrypt_org_token(self):
        from app.services.token_service import encrypt_org_token, decrypt_org_token

        org_id = str(uuid.uuid4())
        org_name = "SKY11"
        enc_token = encrypt_org_token(org_id, org_name)

        assert enc_token.startswith("enc_")
        assert org_name not in enc_token  # Ensure org name is encrypted, not plaintext

        decrypted = decrypt_org_token(enc_token)
        assert decrypted is not None
        assert decrypted["org_id"] == org_id
        assert decrypted["org_name"] == org_name

    def test_resolve_encrypted_token_via_token_service(self):
        from app.services.token_service import encrypt_org_token

        org_id = str(uuid.uuid4())
        org_name = "SKY11"
        enc_token = encrypt_org_token(org_id, org_name)

        # Mock org cache lookup
        mock_org = {
            "id": org_id,
            "name": org_name,
            "is_active": True,
            "is_deleted": False,
            "approval_status": "approved",
        }

        with patch("app.services.token_service.get_db_connection") as mock_conn:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchone.return_value = None  # Not found in DB hash lookup

            with patch("app.services.org_cache_service.get_organisation_by_id", return_value=(mock_org, "cache")):
                res = resolve_assessment_token(enc_token)

        assert res["valid"] is True
        assert res["organization_name"] == org_name
        assert res["organization_id"] == org_id

    def test_resolve_legacy_org_endpoint_success(self):
        org_id = str(uuid.uuid4())
        mock_org = {
            "id": org_id,
            "name": "SKY11",
            "is_active": True,
            "is_deleted": False,
            "approval_status": "approved",
        }
        mock_token_info = {
            "id": str(uuid.uuid4()),
            "organisation_id": org_id,
            "campaign_id": None,
            "name": "Corporate Assessment Link",
            "raw_token": "sky11-secure-opaque-token",
            "assessment_url": "/audit?t=sky11-secure-opaque-token",
            "is_default": True,
        }

        with patch("app.api.public.get_organisation_by_name", return_value=(mock_org, "cache")):
            with patch("app.api.public.get_or_create_default_token", return_value=mock_token_info):
                res = client.post(
                    "/api/public/assessment/resolve-legacy-org",
                    json={"org": "SKY11"}
                )

        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert data["token"] == "sky11-secure-opaque-token"
        assert data["assessment_url"] == "/audit?t=sky11-secure-opaque-token"
        assert data["organization_name"] == "SKY11"

