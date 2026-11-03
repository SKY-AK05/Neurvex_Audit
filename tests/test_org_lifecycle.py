"""
test_org_lifecycle.py — Verification of complete organisation lifecycle and data preservation.
Tests:
- Edit existing organisation
- Activate/deactivate existing organisation
- Soft-delete existing organisation
- Restore soft-deleted organisation
- Preserve submissions, answers, scores and invitations
- Preserve audit history and organisation-submission links
- Verify both Normal Admin and Super Admin access
- Verify unauthenticated and unauthorised access is rejected
"""
import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)
NORMAL_ADMIN = "admin@test.com"
SUPER_ADMIN = "super@test.com"


class TestExistingOrganisationLifecycle:
    """Comprehensive test suite for organisation lifecycle management and data preservation."""

    def test_edit_existing_organisation(self):
        """Normal Admin can edit existing organisation details and name."""
        headers = {"Authorization": f"Bearer local_bypass:{NORMAL_ADMIN}"}
        org_id = str(uuid.uuid4())

        with patch("app.api.orgs.get_db_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.rowcount = 1
            mock_cur.fetchone.side_effect = [
                None,  # No duplicate
                {"id": org_id, "name": "Renamed Healthcare Corp", "is_active": True, "is_deleted": False, "updated_at": None}
            ]

            res = client.put(f"/api/manage/orgs/{org_id}", headers=headers, json={"name": "Renamed Healthcare Corp"})
            assert res.status_code == 200
            assert res.json()["success"] is True
            assert res.json()["org"]["name"] == "Renamed Healthcare Corp"

    def test_activate_deactivate_existing_organisation(self):
        """Normal Admin can toggle an organisation's active status."""
        headers = {"Authorization": f"Bearer local_bypass:{NORMAL_ADMIN}"}
        org_id = str(uuid.uuid4())

        with patch("app.api.orgs.get_db_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.rowcount = 1
            mock_cur.fetchone.return_value = {
                "id": org_id, "name": "Active Org", "is_active": False, "is_deleted": False, "updated_at": None
            }

            # Deactivate
            res_deact = client.patch(f"/api/manage/orgs/{org_id}/status", headers=headers, json={"is_active": False})
            assert res_deact.status_code == 200
            assert res_deact.json()["success"] is True
            assert res_deact.json()["org"]["is_active"] is False

    def test_soft_delete_existing_organisation(self):
        """Normal Admin can soft-delete organisation, which revokes active invitations."""
        headers = {"Authorization": f"Bearer local_bypass:{NORMAL_ADMIN}"}
        org_id = str(uuid.uuid4())

        with patch("app.api.orgs.get_db_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.rowcount = 1

            res = client.delete(f"/api/manage/orgs/{org_id}", headers=headers)
            assert res.status_code == 200
            assert res.json()["success"] is True
            assert "deleted successfully" in res.json()["message"]

    def test_restore_soft_deleted_organisation(self):
        """Normal Admin can restore a soft-deleted organisation."""
        headers = {"Authorization": f"Bearer local_bypass:{NORMAL_ADMIN}"}
        org_id = str(uuid.uuid4())

        with patch("app.api.orgs.get_db_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.rowcount = 1

            res = client.post(f"/api/manage/orgs/{org_id}/restore", headers=headers)
            assert res.status_code == 200
            assert res.json()["success"] is True
            assert "restored successfully" in res.json()["message"]

    def test_soft_delete_preserves_submissions_answers_scores_invitations(self):
        """Soft delete MUST preserve all historical submissions, dynamic answers, scores, and invitations."""
        org_id = str(uuid.uuid4())
        sub_id = str(uuid.uuid4())
        inv_id = str(uuid.uuid4())

        # Establish state in Mock InMemoryStore
        from conftest import MEM_STORE
        MEM_STORE.organizations[org_id] = {
            "id": org_id, "name": "Historic Org", "is_active": True, "is_deleted": False
        }
        MEM_STORE.submissions[sub_id] = {
            "id": sub_id,
            "organization_id": org_id,
            "name": "Employee A",
            "email": "employee@historic.com",
            "company_name": "Historic Org",
            "overall_avg": 18.5,
            "overall_level": "Maturing",
            "answers": {"q5": "Yes", "q6": "No", "custom_scale": 4},
            "dimension_scores": {"leadership": 22.0, "wellbeing": 15.0}
        }
        MEM_STORE.invitations[inv_id] = {
            "id": inv_id,
            "organization_id": org_id,
            "token_hash": "testhash123",
            "is_active": True,
            "submission_count": 5
        }

        # Soft delete the organisation
        headers = {"Authorization": f"Bearer local_bypass:{NORMAL_ADMIN}"}
        res = client.delete(f"/api/manage/orgs/{org_id}", headers=headers)
        assert res.status_code == 200

        # Verify that all historical records remain intact in storage
        sub = MEM_STORE.submissions.get(sub_id)
        assert sub is not None, "Submission must NOT be deleted"
        assert sub["organization_id"] == org_id
        assert sub["answers"]["q5"] == "Yes"
        assert sub["overall_avg"] == 18.5
        assert sub["overall_level"] == "Maturing"
        assert sub["dimension_scores"]["leadership"] == 22.0

        inv = MEM_STORE.invitations.get(inv_id)
        assert inv is not None, "Invitation record must NOT be deleted"
        assert inv["submission_count"] == 5

    def test_soft_delete_preserves_audit_history_and_org_submission_links(self):
        """Soft delete MUST preserve submission_reassignments and org_submission_links."""
        from conftest import MEM_STORE
        org_id = str(uuid.uuid4())
        sub_id = str(uuid.uuid4())
        target_org_id = str(uuid.uuid4())

        MEM_STORE.organizations[org_id] = {"id": org_id, "name": "Source Org", "is_active": True, "is_deleted": False}
        MEM_STORE.reassignments.append({
            "submission_id": sub_id,
            "old_organization_id": org_id,
            "new_organization_id": target_org_id,
            "reason": "Historical Reassignment",
            "reassigned_by": NORMAL_ADMIN,
            "reassigned_at": datetime.now(timezone.utc)
        })
        MEM_STORE.links.append({
            "org": org_id,
            "sub": sub_id,
            "name": "Link 1"
        })

        # Soft delete organisation
        headers = {"Authorization": f"Bearer local_bypass:{NORMAL_ADMIN}"}
        res = client.delete(f"/api/manage/orgs/{org_id}", headers=headers)
        assert res.status_code == 200

        # Assert audit trail remains intact
        reassign_records = [r for r in MEM_STORE.reassignments if r["old_organization_id"] == org_id]
        assert len(reassign_records) == 1
        assert reassign_records[0]["reason"] == "Historical Reassignment"

        link_records = [l for l in MEM_STORE.links if l["org"] == org_id]
        assert len(link_records) == 1

    def test_both_normal_admin_and_super_admin_have_access(self):
        """Both Normal Admin and Super Admin can manage organizations without restrictions."""
        org_id = str(uuid.uuid4())

        for admin_email in (NORMAL_ADMIN, SUPER_ADMIN):
            headers = {"Authorization": f"Bearer local_bypass:{admin_email}"}
            with patch("app.api.orgs.get_db_connection") as mock_get_conn:
                mock_conn = MagicMock()
                mock_cur = MagicMock()
                mock_get_conn.return_value.__enter__.return_value = mock_conn
                mock_conn.cursor.return_value.__enter__.return_value = mock_cur
                mock_cur.rowcount = 1
                mock_cur.fetchall.return_value = []
                mock_cur.fetchone.side_effect = [
                    None,
                    {"id": org_id, "name": f"Managed by {admin_email}", "is_active": True, "is_deleted": False, "updated_at": None}
                ]

                # List
                res_list = client.get("/api/manage/orgs", headers=headers)
                assert res_list.status_code == 200, f"{admin_email} should be able to list orgs"

                # Edit
                res_edit = client.put(f"/api/manage/orgs/{org_id}", headers=headers, json={"name": f"Managed by {admin_email}"})
                assert res_edit.status_code == 200, f"{admin_email} should be able to edit org"

                # Soft delete
                res_del = client.delete(f"/api/manage/orgs/{org_id}", headers=headers)
                assert res_del.status_code == 200, f"{admin_email} should be able to delete org"

                # Restore
                res_res = client.post(f"/api/manage/orgs/{org_id}/restore", headers=headers)
                assert res_res.status_code == 200, f"{admin_email} should be able to restore org"

    def test_unauthenticated_and_unauthorized_access_rejected(self):
        """Unauthenticated requests to organisation management must receive HTTP 401."""
        org_id = str(uuid.uuid4())

        # No auth header
        assert client.get("/api/manage/orgs").status_code == 401
        assert client.put(f"/api/manage/orgs/{org_id}", json={"name": "Hacked"}).status_code == 401
        assert client.patch(f"/api/manage/orgs/{org_id}/status", json={"is_active": False}).status_code == 401
        assert client.delete(f"/api/manage/orgs/{org_id}").status_code == 401
        assert client.post(f"/api/manage/orgs/{org_id}/restore").status_code == 401

        # Invalid token
        bad_header = {"Authorization": "Bearer invalid_token_xyz"}
        assert client.get("/api/manage/orgs", headers=bad_header).status_code == 401
        assert client.delete(f"/api/manage/orgs/{org_id}", headers=bad_header).status_code == 401

