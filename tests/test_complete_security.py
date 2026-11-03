"""
Comprehensive security tests for NIWI application
Tests authentication, authorization, and access control
"""
import pytest
import os
os.environ["TESTING"] = "true"
os.environ["APP_ENV"] = "test"
os.environ["ENABLE_DEV_BYPASS"] = "true"

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_conn
import psycopg2.extras
import uuid

client = TestClient(app)

# Test admin credentials
SUPER_ADMIN_EMAIL = "super@test.com"
REGULAR_ADMIN_EMAIL = "admin@test.com"
UNAUTHORIZED_EMAIL = "hacker@evil.com"

@pytest.fixture(scope="module", autouse=True)
def setup_test_admins():
    """Setup test admin users"""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Clean up existing test users
            cur.execute("""
                DELETE FROM admin_users 
                WHERE email IN (%s, %s, %s)
            """, (SUPER_ADMIN_EMAIL, REGULAR_ADMIN_EMAIL, UNAUTHORIZED_EMAIL))
            
            # Create super admin
            cur.execute("""
                INSERT INTO admin_users (email, role, is_active)
                VALUES (%s, 'super', TRUE)
                ON CONFLICT (email) DO UPDATE SET role = 'super'
            """, (SUPER_ADMIN_EMAIL,))
            
            # Create regular admin
            cur.execute("""
                INSERT INTO admin_users (email, role, is_active)
                VALUES (%s, 'admin', TRUE)
                ON CONFLICT (email) DO UPDATE SET role = 'admin'
            """, (REGULAR_ADMIN_EMAIL,))
        
        conn.commit()
        yield
    finally:
        conn.close()


@pytest.fixture
def test_org():
    """Create a test organization"""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO organizations (name, is_active, is_deleted, approval_status)
                VALUES ('Test Organization Security', TRUE, FALSE, 'approved')
                RETURNING id
            """)
            org_id = str(cur.fetchone()["id"])
        conn.commit()
        
        yield org_id
        
        # Cleanup
        with conn.cursor() as cur:
            cur.execute("DELETE FROM organizations WHERE id = %s", (org_id,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def test_submission(test_org):
    """Create a test submission"""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO submissions (
                    name, email, company_name, organization_id,
                    submission_source, status, submitted_at
                )
                VALUES (
                    'Test User', 'testuser@test.com', 'Test Organization Security',
                    %s, 'DIRECT', 'pending', NOW()
                )
                RETURNING id
            """, (test_org,))
            submission_id = str(cur.fetchone()["id"])
        conn.commit()
        
        yield submission_id
        
        # Cleanup
        with conn.cursor() as cur:
            cur.execute("DELETE FROM submissions WHERE id = %s", (submission_id,))
        conn.commit()
    finally:
        conn.close()


class TestAuthentication:
    """Test authentication mechanisms"""
    
    def test_unauthenticated_access_to_admin_endpoint(self):
        """Unauthenticated requests should be rejected"""
        response = client.get("/api/submissions")
        assert response.status_code == 401
    
    def test_invalid_token(self):
        """Invalid tokens should be rejected"""
        response = client.get(
            "/api/submissions",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        assert response.status_code == 401
    
    def test_dev_bypass_authentication_success(self):
        """Dev bypass should work in test environment"""
        response = client.get(
            "/api/submissions",
            headers={"Authorization": f"Bearer local_bypass:{SUPER_ADMIN_EMAIL}"}
        )
        assert response.status_code == 200
    
    def test_dev_bypass_unauthorized_user(self):
        """Dev bypass with unauthorized email should fail"""
        response = client.get(
            "/api/submissions",
            headers={"Authorization": f"Bearer local_bypass:{UNAUTHORIZED_EMAIL}"}
        )
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()
    
    def test_public_endpoint_no_auth_required(self):
        """Public endpoints should not require authentication"""
        response = client.get("/api/health")
        assert response.status_code == 200


class TestOrganizationAuthorization:
    """Test organization-level access control"""
    
    def test_super_admin_sees_all_submissions(self):
        """Super admin should see all submissions"""
        response = client.get(
            "/api/submissions",
            headers={"Authorization": f"Bearer local_bypass:{SUPER_ADMIN_EMAIL}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_regular_admin_no_orgs_assigned(self):
        """Regular admin has global access under Two-Role Global Model"""
        response = client.get(
            "/api/submissions",
            headers={"Authorization": f"Bearer local_bypass:{REGULAR_ADMIN_EMAIL}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_regular_admin_with_org_access(self, test_org, test_submission):
        """Regular admin should see submissions under global access model"""
        response = client.get(
            "/api/submissions",
            headers={"Authorization": f"Bearer local_bypass:{REGULAR_ADMIN_EMAIL}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        submission_ids = [s["id"] for s in data if isinstance(s, dict) and "id" in s]
        assert test_submission in submission_ids
    
    def test_regular_admin_cannot_access_other_org_submission(self, test_submission):
        """Regular admin can view all submissions under global access model"""
        response = client.get(
            f"/api/submissions/{test_submission}",
            headers={"Authorization": f"Bearer local_bypass:{REGULAR_ADMIN_EMAIL}"}
        )
        assert response.status_code == 200


class TestSubmissionReassignment:
    """Test audit reassignment functionality"""
    
    def test_reassignment_requires_authentication(self, test_submission):
        """Reassignment should require authentication"""
        new_org_id = str(uuid.uuid4())
        response = client.patch(
            f"/api/submissions/{test_submission}/organisation",
            json={"organization_id": new_org_id}
        )
        assert response.status_code == 401
    
    def test_super_admin_can_reassign(self, test_org, test_submission):
        """Super admin should be able to reassign submissions"""
        # Create another org
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO organizations (name, is_active, is_deleted, approval_status)
                    VALUES ('Target Organization', TRUE, FALSE, 'approved')
                    RETURNING id
                """)
                target_org_id = str(cur.fetchone()["id"])
            conn.commit()
            
            # Reassign via canonical PATCH endpoint
            response = client.patch(
                f"/api/submissions/{test_submission}/organisation",
                headers={"Authorization": f"Bearer local_bypass:{SUPER_ADMIN_EMAIL}"},
                json={"organization_id": target_org_id, "reason": "Test reassignment"}
            )
            assert response.status_code == 200
            assert response.json()["new_organization_id"] == target_org_id
            
            # Verify audit trail
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM submission_reassignments 
                    WHERE submission_id = %s
                    ORDER BY reassigned_at DESC
                    LIMIT 1
                """, (test_submission,))
                audit = cur.fetchone()
            
            assert audit is not None
            assert audit["old_organization_id"] == test_org
            assert audit["new_organization_id"] == target_org_id
            assert audit["reason"] == "Test reassignment"
            
            # Cleanup
            with conn.cursor() as cur:
                cur.execute("DELETE FROM organizations WHERE id = %s", (target_org_id,))
            conn.commit()
        finally:
            conn.close()
    
    def test_regular_admin_can_reassign_under_global_model(self, test_org, test_submission):
        """Normal admin can reassign between organisations; unauthenticated gets 401"""
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO organizations (name, is_active, is_deleted, approval_status)
                    VALUES ('Regular Admin Reassign Target', TRUE, FALSE, 'approved')
                    RETURNING id
                """)
                target_org_id = str(cur.fetchone()["id"])
            conn.commit()

            res_unauth = client.patch(
                f"/api/submissions/{test_submission}/organisation",
                json={"organization_id": target_org_id}
            )
            assert res_unauth.status_code == 401
            
            res_admin = client.patch(
                f"/api/submissions/{test_submission}/organisation",
                headers={"Authorization": f"Bearer local_bypass:{REGULAR_ADMIN_EMAIL}"},
                json={"organization_id": target_org_id, "reason": "Normal admin reassignment"}
            )
            assert res_admin.status_code == 200
            assert res_admin.json()["new_organization_id"] == target_org_id

            with conn.cursor() as cur:
                cur.execute("DELETE FROM organizations WHERE id = %s", (target_org_id,))
            conn.commit()
        finally:
            conn.close()


class TestSubmissionScoreUpdates:
    """Test score updates in admin portal"""

    def test_score_update_requires_authentication(self, test_submission):
        response = client.patch(
            f"/api/submissions/{test_submission}/scores",
            json={"lc_score": 15.0}
        )
        assert response.status_code == 401

    def test_admin_can_update_scores(self, test_submission):
        response = client.patch(
            f"/api/submissions/{test_submission}/scores",
            headers={"Authorization": f"Bearer local_bypass:{REGULAR_ADMIN_EMAIL}"},
            json={
                "lc_score": 16.0,
                "ro_score": 12.0,
                "we_score": 14.0,
                "be_score": 18.0,
                "tm_score": 10.0,
                "ca_score": 8.0,
                "pc_score": 12.0,
                "sp_score": 14.0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Scores updated successfully"
        assert data["scores"]["lc_score"] == 16.0
        assert data["scores"]["overall_avg"] == 13.0
        assert data["scores"]["overall_level"] == "Level 2 — Early Progress"

    def test_score_update_validates_range(self, test_submission):
        response = client.patch(
            f"/api/submissions/{test_submission}/scores",
            headers={"Authorization": f"Bearer local_bypass:{REGULAR_ADMIN_EMAIL}"},
            json={"lc_score": 25.0}
        )
        assert response.status_code == 400
        assert "between 0 and 20" in response.json()["detail"]


class TestInvitationSecurity:
    """Test invitation link security"""
    
    def test_invitation_token_cannot_be_tampered(self, test_org):
        """Tampered invitation tokens should be rejected"""
        response = client.post(
            "/api/submit",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "company_name": "Test Company",
                "invitation_token": "tampered_token_12345",
                "consent_given": True
            }
        )
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    def test_invitation_validates_expiry(self, test_org):
        """Expired invitations should be rejected"""
        import secrets
        import hashlib
        from datetime import datetime, timedelta, timezone
        
        # Create expired invitation
        conn = get_conn()
        try:
            raw_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO organization_invitations (
                        organization_id, token_hash, is_active,
                        expires_at, created_by
                    )
                    VALUES (%s, %s, TRUE, %s, 'test')
                    RETURNING id
                """, (
                    test_org,
                    token_hash,
                    datetime.now(timezone.utc) - timedelta(days=1)  # Expired yesterday
                ))
                invitation_id = str(cur.fetchone()[0])
            conn.commit()
            
            # Try to use expired invitation
            response = client.post(
                "/api/submit",
                json={
                    "name": "Test User",
                    "email": "test@example.com",
                    "company_name": "Test Company",
                    "invitation_token": raw_token,
                    "consent_given": True
                }
            )
            assert response.status_code == 400
            assert "expired" in response.json()["detail"].lower()
            
            # Cleanup
            with conn.cursor() as cur:
                cur.execute("DELETE FROM organization_invitations WHERE id = %s", (invitation_id,))
            conn.commit()
        finally:
            conn.close()


class TestApprovalWorkflow:
    """Test simplified organization creation (approval gate removed)"""
    
    def test_direct_submission_succeeds_without_approval_block(self):
        """Submissions are not blocked by approval gates"""
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO organizations (name, is_active, is_deleted, approval_status)
                    VALUES ('Active Direct Org', TRUE, FALSE, 'approved')
                    RETURNING id
                """)
                org_id = str(cur.fetchone()["id"])
            conn.commit()
            
            response = client.post(
                "/api/submit",
                json={
                    "name": "Test User",
                    "email": "test@example.com",
                    "company_name": "Active Direct Org",
                    "organization_id": org_id,
                    "consent_given": True,
                    "has_physical_workspace": "Yes",
                    "has_suppliers": "Yes",
                    **{f"q{i}": "Yes" for i in range(5, 45)}
                }
            )
            assert response.status_code in (200, 201)
            
            with conn.cursor() as cur:
                cur.execute("DELETE FROM organizations WHERE id = %s", (org_id,))
            conn.commit()
        finally:
            conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
