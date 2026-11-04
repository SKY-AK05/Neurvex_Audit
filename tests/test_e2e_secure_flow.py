"""
test_e2e_secure_flow.py — Comprehensive End-to-End Verification of Secure Assessment Flow (Phase 6).
Tests the complete lifecycle:
1. Admin creates opaque assessment link (/audit?t=SECURE_TOKEN)
2. Employee resolves assessment context
3. Employee validates corporate email eligibility
4. Employee submits assessment with secure token
5. Authoritative tenant binding and anti-tampering verification
6. Immediate rejection upon token revocation
"""

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.token_service import generate_secure_token, hash_token

client = TestClient(app)
ADMIN_HEADERS = {"Authorization": "Bearer local_bypass:admin@test.com"}


class TestEndToEndSecureAssessmentFlow:
    """Verifies complete flow from token creation to submission persistence."""

    def test_complete_secure_assessment_lifecycle(self):
        org_id = str(uuid.uuid4())
        campaign_id = str(uuid.uuid4())
        org_name = "Global Aerospace Ltd"
        raw_token = generate_secure_token()
        t_hash = hash_token(raw_token)
        token_id = str(uuid.uuid4())

        # 1. Admin generates assessment link
        mock_org = {
            "id": org_id,
            "name": org_name,
            "is_active": True,
            "is_deleted": False,
            "approval_status": "approved",
        }
        mock_token_row = {
            "id": token_id,
            "organisation_id": org_id,
            "campaign_id": campaign_id,
            "name": "Aerospace Q4 Campaign",
            "created_by": "admin@test.com",
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
        }

        with patch("app.services.token_service.get_db_connection") as mock_db:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchone.side_effect = [mock_org, mock_token_row]

            create_res = client.post(
                f"/api/manage/orgs/{org_id}/assessment-links",
                headers=ADMIN_HEADERS,
                json={"name": "Aerospace Q4 Campaign", "campaign_id": campaign_id}
            )
            assert create_res.status_code == 200
            token_data = create_res.json()
            assert "raw_token" in token_data
            issued_token = token_data["raw_token"]
            assert token_data["assessment_url"] == f"/audit?t={issued_token}"
            # URL does NOT leak organisation name or ID
            assert org_name not in token_data["assessment_url"]
            assert org_id not in token_data["assessment_url"]

        # 2. Employee opens link: Frontend resolves assessment context
        resolve_record = {
            "token_id": token_id,
            "organisation_id": org_id,
            "campaign_id": campaign_id,
            "link_name": "Aerospace Q4 Campaign",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "revoked_at": None,
            "organization_name": org_name,
            "org_active": True,
            "org_deleted": False,
            "org_approval": "approved",
        }

        with patch("app.services.token_service.get_db_connection") as mock_db:
            mock_c = MagicMock()
            mock_cur = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_c
            mock_c.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchone.return_value = resolve_record

            resolve_res = client.post(
                "/api/public/assessment/resolve-link",
                json={"token": issued_token}
            )
            assert resolve_res.status_code == 200
            context = resolve_res.json()
            assert context["valid"] is True
            assert context["organization_name"] == org_name
            assert context["campaign_id"] == campaign_id

        # 3. Employee corporate email validation: Personal provider rejected, corporate accepted
        personal_check = client.post("/api/public/email/validate", json={"email": "pilot@gmail.com"})
        assert personal_check.status_code == 200
        assert personal_check.json()["eligible"] is False
        assert "personal or free email provider" in personal_check.json()["error"]

        corp_check = client.post("/api/public/email/validate", json={"email": "pilot@aerospace.co.uk"})
        assert corp_check.status_code == 200
        assert corp_check.json()["eligible"] is True
        assert corp_check.json()["domain"] == "aerospace.co.uk"

        # 4. Employee submits assessment with secure token
        submission_payload = {
            "name": "Jane Pilot",
            "email": "pilot@aerospace.co.uk",
            "t": issued_token,
            "consent_given": True,
            "idempotency_key": str(uuid.uuid4()),
            **{f"q{i}": "Yes" for i in range(5, 45)}
        }

        submission_id = str(uuid.uuid4())
        with patch("app.api.routes.get_db_connection") as mock_routes_db, \
             patch("app.services.token_service.get_db_connection") as mock_token_db:

            # Token resolution inside submit()
            mock_tc = MagicMock()
            mock_tcur = MagicMock()
            mock_token_db.return_value.__enter__.return_value = mock_tc
            mock_tc.cursor.return_value.__enter__.return_value = mock_tcur
            mock_tcur.fetchone.return_value = resolve_record

            # Submission CTE execution inside submit()
            mock_rc = MagicMock()
            mock_rcur = MagicMock()
            mock_routes_db.return_value.__enter__.return_value = mock_rc
            mock_rc.cursor.return_value.__enter__.return_value = mock_rcur
            # res = (new_id, existing_idempotent_id, duplicate_id, valid_org_id)
            mock_rcur.fetchone.return_value = (submission_id, None, None, org_id)

            sub_res = client.post("/api/submit", json=submission_payload)
            assert sub_res.status_code == 201
            assert sub_res.json()["success"] is True
            assert sub_res.json()["submission_id"] == submission_id

    def test_tenant_anti_tampering_at_submission(self):
        """Even if client attempts to pass a different organisation_id, token binds to authoritative tenant."""
        legit_org_id = str(uuid.uuid4())
        attacker_org_id = str(uuid.uuid4())
        raw_token = generate_secure_token()

        resolve_record = {
            "token_id": str(uuid.uuid4()),
            "organisation_id": legit_org_id,
            "campaign_id": None,
            "link_name": "Legit Link",
            "expires_at": None,
            "revoked_at": None,
            "organization_name": "Legit Tenant Corp",
            "org_active": True,
            "org_deleted": False,
            "org_approval": "approved",
        }

        with patch("app.api.routes.get_db_connection") as mock_routes_db, \
             patch("app.services.token_service.get_db_connection") as mock_token_db:

            mock_tc = MagicMock()
            mock_tcur = MagicMock()
            mock_token_db.return_value.__enter__.return_value = mock_tc
            mock_tc.cursor.return_value.__enter__.return_value = mock_tcur
            mock_tcur.fetchone.return_value = resolve_record

            mock_rc = MagicMock()
            mock_rcur = MagicMock()
            mock_routes_db.return_value.__enter__.return_value = mock_rc
            mock_rc.cursor.return_value.__enter__.return_value = mock_rcur
            mock_rcur.fetchone.return_value = (str(uuid.uuid4()), None, None, legit_org_id)

            # Attacker supplies token for Legit Org, but tries to inject organization_id of Attacker Org
            tamper_payload = {
                "name": "Attacker",
                "email": "attacker@legitcorp.com",
                "t": raw_token,
                "organization_id": attacker_org_id,
                "company_name": "Malicious Corp",
                "consent_given": True,
                **{f"q{i}": "Yes" for i in range(5, 45)}
            }

            sub_res = client.post("/api/submit", json=tamper_payload)
            assert sub_res.status_code == 201

            # Verify the SQL was executed with legit_org_id from token, NOT attacker_org_id
            executed_params = mock_rcur.execute.call_args[0][1]
            assert executed_params["organization_id"] == legit_org_id
            assert executed_params["company_name"] == "Legit Tenant Corp"

    def test_revoked_token_rejected_at_submission(self):
        raw_token = generate_secure_token()
        revoked_record = {
            "token_id": str(uuid.uuid4()),
            "organisation_id": str(uuid.uuid4()),
            "campaign_id": None,
            "link_name": "Revoked Link",
            "expires_at": None,
            "revoked_at": datetime.now(timezone.utc) - timedelta(minutes=5),
            "organization_name": "Revoked Corp",
            "org_active": True,
            "org_deleted": False,
            "org_approval": "approved",
        }

        with patch("app.services.token_service.get_db_connection") as mock_token_db:
            mock_tc = MagicMock()
            mock_tcur = MagicMock()
            mock_token_db.return_value.__enter__.return_value = mock_tc
            mock_tc.cursor.return_value.__enter__.return_value = mock_tcur
            mock_tcur.fetchone.return_value = revoked_record

            sub_res = client.post("/api/submit", json={
                "name": "User",
                "email": "user@corporate.com",
                "t": raw_token,
                "consent_given": True,
                **{f"q{i}": "Yes" for i in range(5, 45)}
            })
            assert sub_res.status_code == 400
            assert "revoked" in sub_res.json()["detail"].lower()
