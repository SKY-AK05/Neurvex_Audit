"""
test_permissions_and_reliability.py — Comprehensive tests for:
1. Two-Role Permission Model (Normal Admin vs Super Admin)
2. Global Organisation Management (No per-org lockout)
3. Simplified Organisation Creation (Elimination of approval workflow)
4. Reassignment updating both organization_id and company_name
5. Secure Delete All Submissions (Super Admin only, explicit confirmation)
6. Unified Dashboard exposing submission_source, organization_id, invitation_id
7. Database connection pooling reliability and leak prevention
"""

import os
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Ensure test bypass environment is enabled
os.environ["APP_ENV"] = "test"
os.environ["ENABLE_DEV_BYPASS"] = "true"

from app.main import app
from app.core.database import PooledConnection, get_db_connection, get_db_transaction
from app.services.user_service import add_user, remove_user, VALID_ROLES
from app.services.filter_service import build_filter_query, ALLOWED_FILTER_FIELDS


@pytest.fixture(autouse=True)
def setup_test_env():
    os.environ["APP_ENV"] = "test"
    os.environ["ENABLE_DEV_BYPASS"] = "true"
    orig_enabled = getattr(app.state.limiter, "enabled", True)
    app.state.limiter.enabled = False
    yield
    app.state.limiter.enabled = orig_enabled


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Unauthenticated Access Protection (HTTP 401)
# ---------------------------------------------------------------------------

class TestUnauthenticatedAccess:
    def test_unauthenticated_requests_receive_401(self, client):
        endpoints = [
            ("GET", "/api/submissions"),
            ("GET", "/api/settings"),
            ("POST", "/api/settings/delete-all-records"),
            ("GET", "/api/manage/orgs"),
            ("GET", "/api/manage/users"),
            ("GET", "/api/manage/audit-logs"),
            ("PATCH", "/api/submissions/00000000-0000-0000-0000-000000000000/scores"),
        ]
        for method, url in endpoints:
            if method == "GET":
                res = client.get(url)
            elif method == "PATCH":
                res = client.patch(url, json={"lc_score": 10})
            else:
                res = client.post(url, json={})
            assert res.status_code == 401, f"{method} {url} should require authentication, got {res.status_code}"


# ---------------------------------------------------------------------------
# 2. Normal Admin vs Super Admin Permissions (HTTP 403 enforcement)
# ---------------------------------------------------------------------------

class TestRolePermissions:
    def test_normal_admin_blocked_from_delete_all_records(self, client):
        """Normal Admin must receive HTTP 403 on delete-all-records."""
        res = client.post(
            "/api/settings/delete-all-records",
            headers={"Authorization": "Bearer local_bypass:admin@test.com"},
            json={"confirmation": "DELETE ALL SUBMISSIONS"}
        )
        assert res.status_code == 403
        assert "Super administrator privileges required" in res.json().get("detail", "")

    def test_normal_admin_blocked_from_user_management(self, client):
        """Normal Admin must receive HTTP 403 on all /api/manage/users endpoints."""
        headers = {"Authorization": "Bearer local_bypass:admin@test.com"}
        
        # List users
        res = client.get("/api/manage/users", headers=headers)
        assert res.status_code == 403
        assert "Super administrator privileges required" in res.json().get("detail", "")

        # Add user
        res = client.post("/api/manage/users", headers=headers, json={"email": "new@example.com", "role": "admin"})
        assert res.status_code == 403
        assert "Super administrator privileges required" in res.json().get("detail", "")

        # Remove user
        res = client.delete("/api/manage/users/test@example.com", headers=headers)
        assert res.status_code == 403
        assert "Super administrator privileges required" in res.json().get("detail", "")

    def test_super_admin_requires_explicit_confirmation_to_delete_all(self, client):
        """Super admin must supply explicit confirmation string."""
        headers = {"Authorization": "Bearer local_bypass:super@test.com"}
        
        res = client.post(
            "/api/settings/delete-all-records",
            headers=headers,
            json={"confirmation": "wrong_confirmation"}
        )
        assert res.status_code == 400
        assert "DELETE ALL SUBMISSIONS" in res.json().get("detail", "")

    def test_user_service_protects_last_super_admin(self):
        """Cannot delete or demote the last remaining active super admin."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        mock_cur.fetchone.side_effect = [
            {"id": "usr-1", "email": "only_super@test.com", "role": "super"},
            {"count": 1}
        ]

        with pytest.raises(HTTPException) as exc_info:
            remove_user(mock_conn, "only_super@test.com")
        assert exc_info.value.status_code == 400
        assert "Cannot delete the last remaining Super Admin" in exc_info.value.detail

    def test_user_service_validates_role(self):
        """Invalid roles are rejected with 400."""
        mock_conn = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            add_user(mock_conn, "test@example.com", "unknown_role")
        assert exc_info.value.status_code == 400
        assert "Invalid role" in exc_info.value.detail


# ---------------------------------------------------------------------------
# 3. Global Access (No Per-Organisation Lockout)
# ---------------------------------------------------------------------------

class TestGlobalOrganisationAccess:
    def test_normal_admin_can_access_all_orgs(self, client):
        """Normal Admin can list all organisations without being locked out."""
        headers = {"Authorization": "Bearer local_bypass:admin@test.com"}
        with patch("app.api.orgs.get_db_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur

            mock_cur.fetchall.side_effect = [
                [{"id": "11111111-1111-1111-1111-111111111111", "name": "Global Org A", "is_active": True, "is_deleted": False, "created_at": None, "updated_at": None}],
                [],  # all_links
                [],  # unlinked_groups
            ]

            res = client.get("/api/manage/orgs", headers=headers)
            assert res.status_code == 200
            data = res.json()
            assert any(o.get("name") == "Global Org A" for o in data)

    def test_normal_admin_can_soft_delete_and_restore_org(self, client):
        """Normal Admin can soft-delete and restore an organisation."""
        headers = {"Authorization": "Bearer local_bypass:admin@test.com"}
        org_id = "11111111-1111-1111-1111-111111111111"

        with patch("app.api.orgs.get_db_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.rowcount = 1

            # Soft delete
            res_del = client.delete(f"/api/manage/orgs/{org_id}", headers=headers)
            assert res_del.status_code == 200
            assert res_del.json()["success"] is True

            # Unauthenticated soft delete must fail
            res_unauth = client.delete(f"/api/manage/orgs/{org_id}")
            assert res_unauth.status_code == 401

            # Restore
            res_res = client.post(f"/api/manage/orgs/{org_id}/restore", headers=headers)
            assert res_res.status_code == 200
            assert res_res.json()["success"] is True

            # Unauthenticated restore must fail
            res_res_unauth = client.post(f"/api/manage/orgs/{org_id}/restore")
            assert res_res_unauth.status_code == 401

    def test_normal_admin_can_update_org_and_manage_invitations(self, client):
        """Normal Admin can edit organisation details and create/revoke invitations."""
        headers = {"Authorization": "Bearer local_bypass:admin@test.com"}
        org_id = "11111111-1111-1111-1111-111111111111"
        inv_id = "22222222-2222-2222-2222-222222222222"

        with patch("app.api.orgs.get_db_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.rowcount = 1
            mock_cur.fetchone.side_effect = [
                None,  # duplicate check -> no duplicate
                {"id": org_id, "name": "Updated Org Name", "is_active": True, "is_deleted": False, "updated_at": None},
                {"id": inv_id, "token_hash": "mockhash", "organization_id": org_id, "is_active": True, "current_submissions": 0, "max_submissions": 100},
                {"id": inv_id, "token_hash": "mockhash", "organization_id": org_id, "is_active": True, "current_submissions": 0, "max_submissions": 100},
            ]

            # Edit organisation
            res_edit = client.put(f"/api/manage/orgs/{org_id}", headers=headers, json={"name": "Updated Org Name"})
            assert res_edit.status_code == 200

            # Create invitation
            res_inv = client.post(
                f"/api/manage/orgs/{org_id}/invitations",
                headers=headers,
                json={"invitation_name": "Q1 Audit", "max_submissions": 50, "valid_days": 30}
            )
            assert res_inv.status_code in (200, 201)

            # Revoke invitation
            res_rev = client.post(f"/api/manage/orgs/invitations/{inv_id}/revoke", headers=headers)
            assert res_rev.status_code == 200

    def test_normal_admin_can_view_all_submissions(self, client):
        """Normal Admin can view all submissions without org restrictions."""
        headers = {"Authorization": "Bearer local_bypass:admin@test.com"}
        with patch("app.api.routes.get_db_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur

            mock_cur.fetchall.return_value = [
                {
                    "id": "22222222-2222-2222-2222-222222222222",
                    "name": "Jane Doe",
                    "company_name": "Any Org",
                    "email": "jane@example.com",
                    "submitted_at": None,
                    "overall_avg": 14.5,
                    "overall_level": "Developing",
                    "status": "pending",
                    "answers": {},
                    "organization_id": "11111111-1111-1111-1111-111111111111",
                    "submission_source": "DIRECT",
                    "invitation_id": None,
                }
            ]

            res = client.get("/api/submissions", headers=headers)
            assert res.status_code == 200
            data = res.json()
            assert len(data) >= 1
            assert data[0]["submission_source"] == "DIRECT"


# ---------------------------------------------------------------------------
# 4. Reassignment Updates Both organization_id and company_name
# ---------------------------------------------------------------------------

class TestAuditReassignment:
    def test_reassignment_updates_both_org_id_and_company_name(self, client):
        """Reassignment must update both organization_id and company_name simultaneously."""
        headers = {"Authorization": "Bearer local_bypass:admin@test.com"}
        sub_id = "33333333-3333-3333-3333-333333333333"
        target_org_id = "44444444-4444-4444-4444-444444444444"

        with patch("app.api.routes.get_db_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur

            mock_cur.fetchone.side_effect = [
                {"id": sub_id, "organization_id": "11111111-1111-1111-1111-111111111111", "company_name": "Old Corp"},
                {"id": target_org_id, "name": "New Canonical Corp"},
            ]

            res = client.patch(
                f"/api/submissions/{sub_id}/organisation",
                headers=headers,
                json={"organization_id": target_org_id, "reason": "Department restructuring"}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["new_organization_id"] == target_org_id
            assert data["company_name"] == "New Canonical Corp"

            executed_sqls = [call[0][0] for call in mock_cur.execute.call_args_list]
            update_sql = next(s for s in executed_sqls if "UPDATE submissions SET" in s)
            assert "organization_id = %s" in update_sql
            assert "company_name = %s" in update_sql


# ---------------------------------------------------------------------------
# 5. Simplified Organisation Creation (No Approval Workflow)
# ---------------------------------------------------------------------------

class TestSimplifiedOrgCreation:
    def test_new_org_created_as_approved_and_active(self, client):
        """When a new organisation name is submitted, it is created as approved/active."""
        payload = {
            "name": "Employee John",
            "company_name": "Fresh Startup Inc",
            "email": "john@freshstartup.com",
            "consent_given": True,
            **{f"q{i}": "Yes" for i in range(5, 45)}
        }

        mock_scores = {
            "overall_avg": 15.0,
            "overall_level": "Developing",
            "email_body": "<p>Results</p>",
            "dimension_scores": {}
        }

        with patch("app.api.routes.calculate_scores", return_value=mock_scores), \
             patch("app.api.routes.notify_admin_new_submission", return_value=True), \
             patch("app.api.routes.get_db_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur

            mock_cur.fetchone.side_effect = [
                None,  # No recent submission from email
                None,  # Org not found
                {"id": "55555555-5555-5555-5555-555555555555", "name": "Fresh Startup Inc"},  # Insert new org
                ("sub-uuid-1234",),  # Submission ID
                (False,),  # CRM sync disabled
            ]

            res = client.post("/api/submit", json=payload)
            assert res.status_code == 201
            assert res.json()["success"] is True

            executed_sqls = [call[0][0] for call in mock_cur.execute.call_args_list]
            org_insert_sql = next(s for s in executed_sqls if "INSERT INTO organizations" in s)
            assert "'approved'" in org_insert_sql
            assert "TRUE" in org_insert_sql


# ---------------------------------------------------------------------------
# 6. Unified Dashboard & Filter Service
# ---------------------------------------------------------------------------

class TestUnifiedDashboardFilter:
    def test_filter_service_allowed_fields(self):
        """submission_source and organization_id must be allowed filter fields."""
        assert "submission_source" in ALLOWED_FILTER_FIELDS
        assert "organization_id" in ALLOWED_FILTER_FIELDS

    def test_filter_service_builds_source_query(self):
        """Query builder correctly constructs submission_source condition."""
        data_sql, count_sql, params, summary = build_filter_query(
            filter_groups=[
                {
                    "logical_operator": "AND",
                    "conditions": [
                        {"field": "submission_source", "operator": "is", "value": "INVITATION"}
                    ]
                }
            ],
            sort_by=[{"field": "submitted_at", "direction": "desc"}],
            page=1,
            per_page=20
        )
        assert "submission_source = %s" in data_sql
        assert "INVITATION" in params


# ---------------------------------------------------------------------------
# 7. Database Connection Pool Reliability
# ---------------------------------------------------------------------------

class TestDatabasePoolReliability:
    def test_pooled_connection_idempotent_close(self):
        """Calling .close() multiple times on PooledConnection is safe and does not crash."""
        mock_raw = MagicMock()
        mock_raw.closed = False
        mock_pool = MagicMock()
        pconn = PooledConnection(mock_raw, mock_pool)

        assert not pconn.closed
        pconn.close()
        assert pconn.closed
        mock_pool.putconn.assert_called_once_with(mock_raw)

        # Second close should be a no-op and not call putconn again
        pconn.close()
        mock_pool.putconn.assert_called_once_with(mock_raw)

    def test_context_manager_cleanup_on_exception(self):
        """get_db_connection() guarantees conn.close() is called on exception."""
        mock_raw = MagicMock()
        mock_raw.closed = False
        mock_pool = MagicMock()

        with patch("app.core.database.get_conn") as mock_get_conn:
            mock_pconn = PooledConnection(mock_raw, mock_pool)
            mock_get_conn.return_value = mock_pconn

            try:
                with get_db_connection() as conn:
                    raise RuntimeError("Simulated failure during DB query")
            except RuntimeError:
                pass

            assert mock_pconn.closed
            mock_pool.putconn.assert_called_once_with(mock_raw)
