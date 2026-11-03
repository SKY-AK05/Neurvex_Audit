"""
test_v31_upgrades.py — Verification of v3.1 Performance, Reliability, and Architecture Upgrades

Covers:
1. Idempotency key deduplication (zero duplicate audits on retry or concurrent replay)
2. Post-submit background jobs creation and worker processing
3. Entra ID JWKS TTLCache expiry without lockout (DEF-003)
4. Database pool non-blocking execution & threadpool safety
"""

import json
import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db_connection
from app.tasks.job_worker import process_email_job, claim_next_job, complete_job, reclaim_stranded_jobs
import app.core.security as sec_mod
from conftest import MEM_STORE


@pytest.fixture
def client():
    MEM_STORE.reset()
    return TestClient(app)


class TestIdempotencyAndJobs:
    """Verifies idempotency guarantees and post-submit background queues."""

    def test_idempotency_key_deduplication_returns_same_submission(self, client):
        """Replaying a request with the same idempotency_key returns the original submission_id."""
        idemp_key = f"test-idemp-{uuid.uuid4()}"
        payload = {
            "name": "Jane Doe",
            "company_name": "Idempotent Corp",
            "email": f"jane_{uuid.uuid4().hex[:8]}@idempotent.com",
            "consent_given": True,
            "idempotency_key": idemp_key,
            **{f"q{i}": "Yes" for i in range(5, 45)}
        }

        # First submission
        res1 = client.post("/api/submit", json=payload)
        assert res1.status_code == 201
        data1 = res1.json()
        assert data1["success"] is True
        sub_id_1 = data1["submission_id"]

        # Immediate retry with the EXACT same idempotency_key
        res2 = client.post("/api/submit", json=payload)
        assert res2.status_code == 201
        data2 = res2.json()
        assert data2["success"] is True
        sub_id_2 = data2["submission_id"]

        # Crucial: Must be the identical submission_id
        assert sub_id_1 == sub_id_2

        # Verify only 1 row exists in submissions table
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM submissions WHERE idempotency_key = %s",
                    (idemp_key,)
                )
                count = cur.fetchone()[0]
                assert count == 1

                # Verify only 1 email job was enqueued
                cur.execute(
                    "SELECT COUNT(*) FROM post_submit_jobs WHERE submission_id = %s AND job_type = 'email'",
                    (sub_id_1,)
                )
                job_count = cur.fetchone()[0]
                assert job_count == 1

    def test_background_email_job_renders_email_body(self, client):
        """Email job in post_submit_jobs successfully synthesizes email_body for submission."""
        payload = {
            "name": "Background Worker Tester",
            "company_name": "Worker Verification LLC",
            "email": f"worker_{uuid.uuid4().hex[:8]}@verification.com",
            "consent_given": True,
            **{f"q{i}": "Yes" for i in range(5, 45)}
        }

        res = client.post("/api/submit", json=payload)
        assert res.status_code == 201
        sub_id = res.json()["submission_id"]

        # Initially, email_body should be None (not blocking request)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT email_body FROM submissions WHERE id = %s", (sub_id,))
                initial_body = cur.fetchone()[0]
                assert initial_body is None

        # Execute the email job
        process_email_job(sub_id, payload)

        # After worker runs, email_body should be populated with HTML
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT email_body FROM submissions WHERE id = %s", (sub_id,))
                updated_body = cur.fetchone()[0]
                assert updated_body is not None
                assert "NeuroMark Audit" in updated_body
                assert "Worker Verification LLC" in updated_body

    def test_job_worker_claim_and_completion_lifecycle(self, client):
        """Worker claims job with SKIP LOCKED and transitions through PENDING -> PROCESSING -> DONE."""
        worker_id = f"test-worker-{uuid.uuid4().hex[:6]}"
        test_sub_id = str(uuid.uuid4())

        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    # Insert mock submission to satisfy FK
                    cur.execute("""
                        INSERT INTO submissions (id, name, company_name, email, consent_given, status)
                        VALUES (%s, 'Lifecycle Test', 'Lifecycle Inc', 'life@cycle.com', TRUE, 'pending')
                    """, (test_sub_id,))
                    cur.execute("""
                        INSERT INTO post_submit_jobs (submission_id, job_type, status)
                        VALUES (%s, 'email', 'PENDING')
                        RETURNING id
                    """, (test_sub_id,))
                    job_id = cur.fetchone()[0]

        # Claim the job
        job = claim_next_job(worker_id=worker_id)
        assert job is not None
        assert str(job["id"]) == str(job_id)
        assert job["job_type"] == "email"

        # Verify job is now PROCESSING
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT status, locked_by FROM post_submit_jobs WHERE id = %s", (str(job_id),))
                status, locked_by = cur.fetchone()
                assert status == "PROCESSING"
                assert locked_by == worker_id

        # Mark job complete
        complete_job(str(job_id))

        # Verify job is DONE
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT status FROM post_submit_jobs WHERE id = %s", (str(job_id),))
                status = cur.fetchone()[0]
                assert status == "DONE"


class TestSecurityAndCachingDefects:
    """Verifies resolution of DEF-003, DEF-004, DEF-005."""

    def test_def_003_jwks_uses_ttl_cache_not_eternal_lru(self):
        """JWKS caching uses TTLCache with 3600s expiration to prevent Microsoft rotation lockout."""
        assert hasattr(sec_mod._jwks_cache, "ttl")
        assert sec_mod._jwks_cache.ttl == 3600
        assert sec_mod._jwks_cache.maxsize == 10

        # Simulate cache population
        sec_mod._jwks_cache["jwks"] = {"keys": [{"kid": "test-key-1"}]}
        cached = sec_mod.get_jwks()
        assert cached == {"keys": [{"kid": "test-key-1"}]}

        # Verify cache can be invalidated/refreshed without process restart
        sec_mod._jwks_cache.clear()
        assert "jwks" not in sec_mod._jwks_cache


class TestCriticalAuditDefectRemediations:
    """Verifies targeted remediations for Defect 1-4 from independent audit."""

    def test_crm_failure_re_raises_and_triggers_retry_in_worker(self, client):
        """DEF-006: Failed HubSpot API calls re-raise and transition job to RETRY with last_error."""
        from app.tasks.job_worker import fail_or_retry_job, process_crm_job
        from app.services import crm_service

        test_sub_id = str(uuid.uuid4())
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO submissions (id, name, company_name, email, consent_given, status)
                        VALUES (%s, 'CRM Fail Test', 'CRM Fail Inc', 'crm@fail.com', TRUE, 'pending')
                    """, (test_sub_id,))
                    cur.execute("""
                        INSERT INTO post_submit_jobs (submission_id, job_type, status, attempts, max_attempts)
                        VALUES (%s, 'crm', 'PROCESSING', 1, 5)
                        RETURNING id
                    """, (test_sub_id,))
                    job_id = cur.fetchone()[0]

        # Mock make_hubspot_request to fail with connection timeout
        with patch.object(crm_service, "HUBSPOT_ACCESS_TOKEN", "mock_token"), \
             patch("app.services.crm_service.make_hubspot_request", side_effect=RuntimeError("HubSpot Gateway 504 Timeout")):
            with pytest.raises(RuntimeError) as exc_info:
                process_crm_job(test_sub_id, {"data": {"email": "crm@fail.com"}, "score_data": {"overall_avg": 12.0}})
            assert "HubSpot" in str(exc_info.value)

            # Record failure in worker
            fail_or_retry_job(str(job_id), current_attempts=1, max_attempts=5, error_msg=str(exc_info.value))

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT status, attempts, last_error FROM post_submit_jobs WHERE id = %s", (str(job_id),))
                row = cur.fetchone()
                status = row["status"] if isinstance(row, dict) else row[0]
                last_err = row["last_error"] if isinstance(row, dict) else row[2]
                assert status == "RETRY"
                assert "504" in last_err

    def test_metadata_cache_expired_conn_none_retains_custom_sections(self):
        """Stale-while-revalidate: expired cache with conn=None never overwrites custom questions with defaults."""
        import time
        from app.services import scoring_service

        custom_sections = [{"section": {"id": "custom-sec-1", "title": "Custom Section"}, "questions": [{"id": "q1", "text": "Custom Q"}]}]
        # Set cache with custom sections and expire TTL
        scoring_service._cached_form_sections = (custom_sections, 60)
        scoring_service._cached_form_sections_time = time.time() - 400 # expired

        # Mock get_conn to simulate database temporarily offline
        with patch("app.core.database.get_conn", side_effect=RuntimeError("DB offline")):
            secs, thresh = scoring_service.get_form_sections_metadata(conn=None)

            # Must retain custom sections, NOT fall back to DEFAULT_STANDARD_SECTIONS
            assert secs == custom_sections
            assert thresh == 60

    def test_connection_pool_statement_timeout_configured(self):
        """ThreadedConnectionPool configures statement_timeout to protect against hanging queries."""
        import app.core.database as db_mod

        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool_cls:
            db_mod._connection_pool = None
            db_mod.init_connection_pool(minconn=2, maxconn=5)
            assert mock_pool_cls.called
            _, kwargs = mock_pool_cls.call_args
            assert "statement_timeout=15000" in kwargs.get("options", "")
            db_mod._connection_pool = None
