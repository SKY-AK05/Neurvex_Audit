"""
test_concurrent_submissions.py — Concurrent Submissions Verification

Tests:
1. 100 concurrent employees submitting for the same organisation with zero lost submissions, zero duplicates.
2. Concurrent duplicate retry with identical idempotency key returning identical submission_id.
3. Fast execution without event loop or connection starvation.
"""

import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest
from fastapi.testclient import TestClient

from app.main import app
from conftest import MEM_STORE


@pytest.fixture
def client():
    MEM_STORE.reset()
    return TestClient(app)


def test_100_concurrent_submissions_same_organisation(client):
    """
    Simulate 100 concurrent employees submitting audits for the SAME company.
    Verifies:
    - 100% success rate (100 / 100 HTTP 201 Created).
    - 0 lost submissions.
    - Zero duplicates.
    - Response time well within performance budget.
    """
    company_name = "Global Concurrency Enterprises"
    total_users = 100
    concurrency = 20  # Virtual users pool

    def submit_employee(idx: int):
        employee_email = f"emp_{idx}_{uuid.uuid4().hex[:6]}@concurrency.com"
        idemp_key = f"idemp-same-org-{idx}-{uuid.uuid4().hex}"
        payload = {
            "name": f"Employee {idx}",
            "company_name": company_name,
            "email": employee_email,
            "consent_given": True,
            "idempotency_key": idemp_key,
            **{f"q{i}": "Yes" if i % 2 == 0 else "Partially" for i in range(5, 45)}
        }
        start = time.perf_counter()
        resp = client.post("/api/submit", json=payload)
        elapsed = time.perf_counter() - start
        return idx, resp.status_code, resp.json(), elapsed

    start_all = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(submit_employee, i) for i in range(total_users)]
        for f in as_completed(futures):
            results.append(f.result())

    total_time = time.perf_counter() - start_all

    # Assertions
    status_codes = [r[1] for r in results]
    success_count = status_codes.count(201)
    submission_ids = [r[2].get("submission_id") for r in results if r[1] == 201]
    latencies = [r[3] for r in results]
    latencies.sort()
    p95_latency = latencies[int(len(latencies) * 0.95)]

    print(f"\n--- 100 CONCURRENT SUBMISSIONS BENCHMARK ---")
    print(f"Total Submissions: {total_users}")
    print(f"Successful (201 Created): {success_count} (100%)")
    print(f"Unique Submission IDs: {len(set(submission_ids))} (0 duplicates)")
    print(f"Total Wall Clock Time: {total_time:.2f}s")
    print(f"P95 Latency: {p95_latency * 1000:.1f}ms")
    print(f"Throughput: {total_users / total_time:.1f} req/s")

    assert success_count == total_users, f"Expected {total_users} successful submissions, got {success_count}"
    assert len(set(submission_ids)) == total_users, "Expected 0 duplicate submission IDs across employees"
    assert p95_latency < 2.5, f"P95 latency {p95_latency:.2f}s breached 2.5s SLA target"


def test_concurrent_idempotent_retries(client):
    """
    Simulate multiple concurrent network retries with the EXACT SAME idempotency_key.
    Verifies that all retries return the exact same submission_id without creating multiple submissions.
    """
    idemp_key = f"retry-key-{uuid.uuid4()}"
    employee_email = f"retry_{uuid.uuid4().hex[:6]}@company.com"
    payload = {
        "name": "Retry User",
        "company_name": "Retry Systems Corp",
        "email": employee_email,
        "consent_given": True,
        "idempotency_key": idemp_key,
        **{f"q{i}": "Yes" for i in range(5, 45)}
    }

    # Burst 10 concurrent requests with the identical payload & idempotency_key
    def do_submit():
        return client.post("/api/submit", json=payload)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(do_submit) for _ in range(10)]
        responses = [f.result() for f in futures]

    for resp in responses:
        assert resp.status_code == 201
        assert resp.json()["success"] is True

    # All 10 requests must return the identical submission_id
    sub_ids = [resp.json()["submission_id"] for resp in responses]
    assert len(set(sub_ids)) == 1, "Concurrent retries must return the exact same submission_id"

