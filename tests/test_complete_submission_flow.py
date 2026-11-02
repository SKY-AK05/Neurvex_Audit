"""
Complete submission flow integration tests
Tests both manual and invitation-based assessment entry
"""
import pytest
import os
os.environ["TESTING"] = "true"
os.environ["APP_ENV"] = "test"

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_conn, init_connection_pool, close_connection_pool
import psycopg2.extras
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
import uuid

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    init_connection_pool(minconn=2, maxconn=5)
    yield
    close_connection_pool()


@pytest.fixture
def test_org():
    """Create approved test organization"""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO organizations (name, is_active, is_deleted, approval_status)
                VALUES ('Integration Test Org', TRUE, FALSE, 'approved')
                RETURNING id
            """)
            org_id = str(cur.fetchone()["id"])
        conn.commit()
        
        yield org_id
        
        # Cleanup
        with conn.cursor() as cur:
            cur.execute("DELETE FROM submissions WHERE organization_id = %s", (org_id,))
            cur.execute("DELETE FROM organization_invitations WHERE organization_id = %s", (org_id,))
            cur.execute("DELETE FROM organizations WHERE id = %s", (org_id,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def valid_invitation(test_org):
    """Create valid invitation link"""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO organization_invitations (
                    organization_id, token_hash, is_active,
                    expires_at, max_submissions, submission_count,
                    invitation_name, created_by
                )
                VALUES (%s, %s, TRUE, %s, 10, 0, 'Test Invitation', 'test')
                RETURNING id
            """, (
                test_org,
                token_hash,
                datetime.now(timezone.utc) + timedelta(days=30)
            ))
            invitation_id = str(cur.fetchone()["id"])
        conn.commit()
        
        yield {"token": raw_token, "id": invitation_id}
        
        # Cleanup handled by test_org fixture
    finally:
        conn.close()


class TestManualOrganizationEntry:
    """Test Method A: Manual organization text input"""
    
    def test_submission_with_existing_approved_org(self, test_org):
        """Submission with existing approved organization should succeed"""
        response = client.post("/api/submit", json={
            "name": "John Doe",
            "email": f"john.{uuid.uuid4()}@test.com",
            "company_name": "Integration Test Org",
            "organization_id": test_org,
            "designation": "Manager",
            "consent_given": True,
            "has_physical_workspace": "Yes",
            "has_suppliers": "Yes",
            # Minimal required questions
            "q5": "Often", "q6": "Sometimes", "q7": "Rarely", "q8": "Always",
            "q9": "Often", "q10": "Sometimes", "q11": "Rarely", "q12": "Always",
            "q13": "Often", "q14": "Sometimes", "q15": "Rarely", "q16": "Always",
            "q17": "Often", "q18": "Sometimes", "q19": "Rarely", "q20": "Always",
            "q21": "Often", "q22": "Sometimes", "q23": "Rarely", "q24": "Always",
            "q25": "Often", "q26": "Sometimes", "q27": "Rarely", "q28": "Always",
            "q29": "Often", "q30": "Sometimes", "q31": "Rarely", "q32": "Always",
            "q33": "Often", "q34": "Sometimes", "q35": "Rarely", "q36": "Always",
            "q37": "Often", "q38": "Sometimes", "q39": "Rarely", "q40": "Always",
            "q41": "Often", "q42": "Sometimes", "q43": "Rarely", "q44": "Always",
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "submission_id" in data
        
        # Verify submission in database
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT organization_id, submission_source, name, email
                    FROM submissions
                    WHERE id = %s
                """, (data["submission_id"],))
                submission = cur.fetchone()
            
            assert submission is not None
            assert submission["organization_id"] == test_org
            assert submission["submission_source"] == "DIRECT"
            assert submission["name"] == "John Doe"
        finally:
            conn.close()
    
    def test_submission_creates_new_pending_org(self):
        """Submission with new company name should create pending org"""
        new_company = f"New Company {uuid.uuid4()}"
        
        response = client.post("/api/submit", json={
            "name": "Jane Smith",
            "email": f"jane.{uuid.uuid4()}@test.com",
            "company_name": new_company,
            "designation": "Director",
            "consent_given": True,
            "has_physical_workspace": "Yes",
            "has_suppliers": "No",
            "q5": "Often", "q6": "Sometimes", "q7": "Rarely", "q8": "Always",
            "q9": "Often", "q10": "Sometimes", "q11": "Rarely", "q12": "Always",
            "q13": "Often", "q14": "Sometimes", "q15": "Rarely", "q16": "Always",
            "q17": "Often", "q18": "Sometimes", "q19": "Rarely", "q20": "Always",
            "q21": "Often", "q22": "Sometimes", "q23": "Rarely", "q24": "Always",
            "q25": "Often", "q26": "Sometimes", "q27": "Rarely", "q28": "Always",
            "q29": "Often", "q30": "Sometimes", "q31": "Rarely", "q32": "Always",
            "q33": "Often", "q34": "Sometimes", "q35": "Rarely", "q36": "Always",
            "q37": "Often", "q38": "Sometimes", "q39": "Rarely", "q40": "Always",
            "q41": "Often", "q42": "Sometimes", "q43": "Rarely", "q44": "Always",
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        
        # Verify organization was created with pending status
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, approval_status, is_active
                    FROM organizations
                    WHERE name = %s
                """, (new_company,))
                org = cur.fetchone()
            
            assert org is not None
            assert org["approval_status"] == "approved"
            assert org["is_active"] is True
            
            # Cleanup
            with conn.cursor() as cur:
                cur.execute("DELETE FROM submissions WHERE organization_id = %s", (org["id"],))
                cur.execute("DELETE FROM organizations WHERE id = %s", (org["id"],))
            conn.commit()
        finally:
            conn.close()
    
    def test_duplicate_email_prevention(self, test_org):
        """Duplicate submissions within 5 minutes should be rejected"""
        email = f"duplicate.{uuid.uuid4()}@test.com"
        
        # First submission
        response1 = client.post("/api/submit", json={
            "name": "Test User",
            "email": email,
            "company_name": "Integration Test Org",
            "organization_id": test_org,
            "consent_given": True,
            "has_physical_workspace": "Yes",
            "has_suppliers": "Yes",
            "q5": "Often", "q6": "Sometimes", "q7": "Rarely", "q8": "Always",
            "q9": "Often", "q10": "Sometimes", "q11": "Rarely", "q12": "Always",
            "q13": "Often", "q14": "Sometimes", "q15": "Rarely", "q16": "Always",
            "q17": "Often", "q18": "Sometimes", "q19": "Rarely", "q20": "Always",
            "q21": "Often", "q22": "Sometimes", "q23": "Rarely", "q24": "Always",
            "q25": "Often", "q26": "Sometimes", "q27": "Rarely", "q28": "Always",
            "q29": "Often", "q30": "Sometimes", "q31": "Rarely", "q32": "Always",
            "q33": "Often", "q34": "Sometimes", "q35": "Rarely", "q36": "Always",
            "q37": "Often", "q38": "Sometimes", "q39": "Rarely", "q40": "Always",
            "q41": "Often", "q42": "Sometimes", "q43": "Rarely", "q44": "Always",
        })
        assert response1.status_code == 201
        
        # Second submission with same email (should fail)
        response2 = client.post("/api/submit", json={
            "name": "Test User",
            "email": email,
            "company_name": "Integration Test Org",
            "organization_id": test_org,
            "consent_given": True,
            "has_physical_workspace": "Yes",
            "has_suppliers": "Yes",
            "q5": "Often", "q6": "Sometimes", "q7": "Rarely", "q8": "Always",
            "q9": "Often", "q10": "Sometimes", "q11": "Rarely", "q12": "Always",
            "q13": "Often", "q14": "Sometimes", "q15": "Rarely", "q16": "Always",
            "q17": "Often", "q18": "Sometimes", "q19": "Rarely", "q20": "Always",
            "q21": "Often", "q22": "Sometimes", "q23": "Rarely", "q24": "Always",
            "q25": "Often", "q26": "Sometimes", "q27": "Rarely", "q28": "Always",
            "q29": "Often", "q30": "Sometimes", "q31": "Rarely", "q32": "Always",
            "q33": "Often", "q34": "Sometimes", "q35": "Rarely", "q36": "Always",
            "q37": "Often", "q38": "Sometimes", "q39": "Rarely", "q40": "Always",
            "q41": "Often", "q42": "Sometimes", "q43": "Rarely", "q44": "Always",
        })
        
        assert response2.status_code == 429
        assert "recently" in response2.json()["detail"].lower()


class TestInvitationBasedEntry:
    """Test Method B: Invitation link entry"""
    
    def test_submission_with_valid_invitation(self, test_org, valid_invitation):
        """Submission with valid invitation token should succeed"""
        response = client.post("/api/submit", json={
            "name": "Bob Johnson",
            "email": f"bob.{uuid.uuid4()}@test.com",
            "invitation_token": valid_invitation["token"],
            "company_name": "Will be overridden",  # Should be ignored
            "designation": "Employee",
            "consent_given": True,
            "has_physical_workspace": "Yes",
            "has_suppliers": "Yes",
            "q5": "Often", "q6": "Sometimes", "q7": "Rarely", "q8": "Always",
            "q9": "Often", "q10": "Sometimes", "q11": "Rarely", "q12": "Always",
            "q13": "Often", "q14": "Sometimes", "q15": "Rarely", "q16": "Always",
            "q17": "Often", "q18": "Sometimes", "q19": "Rarely", "q20": "Always",
            "q21": "Often", "q22": "Sometimes", "q23": "Rarely", "q24": "Always",
            "q25": "Often", "q26": "Sometimes", "q27": "Rarely", "q28": "Always",
            "q29": "Often", "q30": "Sometimes", "q31": "Rarely", "q32": "Always",
            "q33": "Often", "q34": "Sometimes", "q35": "Rarely", "q36": "Always",
            "q37": "Often", "q38": "Sometimes", "q39": "Rarely", "q40": "Always",
            "q41": "Often", "q42": "Sometimes", "q43": "Rarely", "q44": "Always",
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        
        # Verify submission
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT organization_id, submission_source, invitation_id, company_name
                    FROM submissions
                    WHERE id = %s
                """, (data["submission_id"],))
                submission = cur.fetchone()
            
            assert submission is not None
            assert submission["organization_id"] == test_org
            assert submission["submission_source"] == "INVITATION"
            assert submission["invitation_id"] == valid_invitation["id"]
            assert submission["company_name"] == "Integration Test Org"  # From org, not user input
            
            # Verify invitation counter incremented
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT submission_count
                    FROM organization_invitations
                    WHERE id = %s
                """, (valid_invitation["id"],))
                invitation = cur.fetchone()
            
            assert invitation["submission_count"] == 1
        finally:
            conn.close()
    
    def test_submission_with_invalid_token(self):
        """Submission with invalid invitation token should fail"""
        response = client.post("/api/submit", json={
            "name": "Invalid User",
            "email": f"invalid.{uuid.uuid4()}@test.com",
            "invitation_token": "invalid_token_12345",
            "consent_given": True,
            "has_physical_workspace": "Yes",
            "has_suppliers": "Yes",
            "q5": "Often", "q6": "Sometimes", "q7": "Rarely", "q8": "Always",
            "q9": "Often", "q10": "Sometimes", "q11": "Rarely", "q12": "Always",
            "q13": "Often", "q14": "Sometimes", "q15": "Rarely", "q16": "Always",
            "q17": "Often", "q18": "Sometimes", "q19": "Rarely", "q20": "Always",
            "q21": "Often", "q22": "Sometimes", "q23": "Rarely", "q24": "Always",
            "q25": "Often", "q26": "Sometimes", "q27": "Rarely", "q28": "Always",
            "q29": "Often", "q30": "Sometimes", "q31": "Rarely", "q32": "Always",
            "q33": "Often", "q34": "Sometimes", "q35": "Rarely", "q36": "Always",
            "q37": "Often", "q38": "Sometimes", "q39": "Rarely", "q40": "Always",
            "q41": "Often", "q42": "Sometimes", "q43": "Rarely", "q44": "Always",
        })
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    def test_submission_limit_enforcement(self, test_org):
        """Invitation submission limit should be enforced"""
        # Create invitation with limit of 1
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO organization_invitations (
                        organization_id, token_hash, is_active,
                        expires_at, max_submissions, submission_count,
                        invitation_name, created_by
                    )
                    VALUES (%s, %s, TRUE, %s, 1, 0, 'Limited Invitation', 'test')
                    RETURNING id
                """, (
                    test_org,
                    token_hash,
                    datetime.now(timezone.utc) + timedelta(days=30)
                ))
                invitation_id = str(cur.fetchone()["id"])
            conn.commit()
            
            # First submission should succeed
            response1 = client.post("/api/submit", json={
                "name": "User 1",
                "email": f"user1.{uuid.uuid4()}@test.com",
                "invitation_token": raw_token,
                "consent_given": True,
                "has_physical_workspace": "Yes",
                "has_suppliers": "Yes",
                "q5": "Often", "q6": "Sometimes", "q7": "Rarely", "q8": "Always",
                "q9": "Often", "q10": "Sometimes", "q11": "Rarely", "q12": "Always",
                "q13": "Often", "q14": "Sometimes", "q15": "Rarely", "q16": "Always",
                "q17": "Often", "q18": "Sometimes", "q19": "Rarely", "q20": "Always",
                "q21": "Often", "q22": "Sometimes", "q23": "Rarely", "q24": "Always",
                "q25": "Often", "q26": "Sometimes", "q27": "Rarely", "q28": "Always",
                "q29": "Often", "q30": "Sometimes", "q31": "Rarely", "q32": "Always",
                "q33": "Often", "q34": "Sometimes", "q35": "Rarely", "q36": "Always",
                "q37": "Often", "q38": "Sometimes", "q39": "Rarely", "q40": "Always",
                "q41": "Often", "q42": "Sometimes", "q43": "Rarely", "q44": "Always",
            })
            assert response1.status_code == 201
            
            # Second submission should fail (limit reached)
            response2 = client.post("/api/submit", json={
                "name": "User 2",
                "email": f"user2.{uuid.uuid4()}@test.com",
                "invitation_token": raw_token,
                "consent_given": True,
                "has_physical_workspace": "Yes",
                "has_suppliers": "Yes",
                "q5": "Often", "q6": "Sometimes", "q7": "Rarely", "q8": "Always",
                "q9": "Often", "q10": "Sometimes", "q11": "Rarely", "q12": "Always",
                "q13": "Often", "q14": "Sometimes", "q15": "Rarely", "q16": "Always",
                "q17": "Often", "q18": "Sometimes", "q19": "Rarely", "q20": "Always",
                "q21": "Often", "q22": "Sometimes", "q23": "Rarely", "q24": "Always",
                "q25": "Often", "q26": "Sometimes", "q27": "Rarely", "q28": "Always",
                "q29": "Often", "q30": "Sometimes", "q31": "Rarely", "q32": "Always",
                "q33": "Often", "q34": "Sometimes", "q35": "Rarely", "q36": "Always",
                "q37": "Often", "q38": "Sometimes", "q39": "Rarely", "q40": "Always",
                "q41": "Often", "q42": "Sometimes", "q43": "Rarely", "q44": "Always",
            })
            
            assert response2.status_code == 400
            assert "limit" in response2.json()["detail"].lower()
            
            # Cleanup
            with conn.cursor() as cur:
                cur.execute("DELETE FROM organization_invitations WHERE id = %s", (invitation_id,))
            conn.commit()
        finally:
            conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
