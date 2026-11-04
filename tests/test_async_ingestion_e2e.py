"""
test_async_ingestion_e2e.py — End-to-end integration test for the durable ingestion pipeline.
"""
import os
os.environ["APP_ENV"] = "development"
os.environ["APP-ENV"] = "development"
import sys
import uuid
import json
import pytest
from fastapi.testclient import TestClient

# Ensure root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import get_db_connection
from app.tasks.service_bus_worker import handle_submission_created


def test_durable_ingestion_and_async_worker():
    client = TestClient(app)

    # 1. Create a unique test submission payload
    test_key = f"test_idemp_{uuid.uuid4()}"
    test_email = f"e2e_test_{uuid.uuid4().hex[:8]}@example.com"
    org_name = "Test Organization Inc"

    # Make sure org exists or can be resolved
    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM organizations WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s)) AND is_deleted = FALSE",
                    (org_name,)
                )
                org_row = cur.fetchone()
                if org_row:
                    org_id = str(org_row[0])
                else:
                    cur.execute(
                        "INSERT INTO organizations (name, is_active, is_deleted, approval_status) VALUES (%s, TRUE, FALSE, 'approved') RETURNING id",
                        (org_name,)
                    )
                    org_id = str(cur.fetchone()[0])

    payload = {
        "name": "Jane Tester",
        "company_name": org_name,
        "organization_id": org_id,
        "email": test_email,
        "contact_number": "+1 555 123 4567",
        "designation": "Staff Engineer",
        "has_physical_workspace": "Yes",
        "has_suppliers": "Yes",
        "consent_given": True,
        "idempotency_key": test_key,
        "function": "Engineering",
        "role": "Staff Engineer",
        "country": "India",
        "state_ut": "Karnataka",
        "gender": "Woman",
        "is_pwd": "No",
        "is_neurodivergent": "Yes",
        "is_marginalized": "No",
        **{f"q{i}": "Yes" for i in range(5, 45)}
    }

    # 2. Test POST /api/submit -> Expect HTTP 202 Accepted
    resp = client.post("/api/submit", json=payload)
    assert resp.status_code == 202, f"Expected HTTP 202, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("success") is True
    assert body.get("status") == "RECEIVED"
    sub_id = body.get("submission_id")
    assert sub_id is not None

    # 3. Test Idempotency: Immediate duplicate POST with identical key -> Expect same submission_id
    resp_dup = client.post("/api/submit", json=payload)
    assert resp_dup.status_code in (200, 202)
    body_dup = resp_dup.json()
    assert body_dup.get("submission_id") == sub_id

    # 4. Verify raw_submissions table state
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status, idempotency_key FROM raw_submissions WHERE submission_id = %s",
                (sub_id,)
            )
            raw_row = cur.fetchone()
            assert raw_row is not None, "raw_submissions row must exist"
            assert raw_row[0] in ("RECEIVED", "PENDING", "PROCESSING")
            assert raw_row[1] == test_key

            cur.execute(
                "SELECT status, aggregate_id FROM service_bus_outbox WHERE aggregate_id = %s",
                (sub_id,)
            )
            outbox_row = cur.fetchone()
            assert outbox_row is not None, "service_bus_outbox row must exist"
            assert str(outbox_row[1]) == sub_id

    # 5. Check status endpoint before worker processing
    resp_status = client.get(f"/api/submissions/{sub_id}/status")
    assert resp_status.status_code == 200
    st_data = resp_status.json()
    assert st_data.get("submission_id") == sub_id
    assert st_data.get("status") in ("RECEIVED", "PENDING", "PROCESSING")

    # 6. Run Worker processing for this submission (idempotent pipeline)
    handle_submission_created(sub_id, worker_id="test-worker")

    # 7. Verify post-worker state in raw_submissions and submissions
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status, scoring_status FROM raw_submissions WHERE submission_id = %s",
                (sub_id,)
            )
            raw_after = cur.fetchone()
            assert raw_after[0] == "COMPLETED", f"Expected COMPLETED, got {raw_after[0]}"
            assert raw_after[1] == "COMPLETED"

            cur.execute(
                """
                SELECT id, overall_avg, overall_level, status, async_status
                FROM submissions WHERE id = %s
                """,
                (sub_id,)
            )
            sub_after = cur.fetchone()
            assert sub_after is not None, "submissions row must be populated by worker"
            assert float(sub_after[1]) > 0, "overall_avg score must be computed"
            assert sub_after[3] == "completed"
            assert sub_after[4] == "COMPLETED"

    # 8. Check status endpoint after worker processing
    resp_status_after = client.get(f"/api/submissions/{sub_id}/status")
    assert resp_status_after.status_code == 200
    st_after = resp_status_after.json()
    assert st_after.get("status") == "COMPLETED"
    assert st_after.get("scoring_status") == "COMPLETED"

    # 9. Verify worker idempotency: calling handle_submission_created again skips gracefully
    handle_submission_created(sub_id, worker_id="test-worker-2")

    print(f"\n[PASS] End-to-end durable ingestion verified for submission {sub_id}")


if __name__ == "__main__":
    test_durable_ingestion_and_async_worker()
