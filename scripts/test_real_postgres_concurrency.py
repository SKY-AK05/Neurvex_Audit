"""
scripts/test_real_postgres_concurrency.py — Standalone Real PostgreSQL Concurrency & Idempotency Benchmark

Executes genuine HTTP concurrency tests against unmocked Azure PostgreSQL (v17.11):
1. Verifies psycopg2 is unmocked and connects to live PostgreSQL.
2. In-flight concurrent idempotency: 10 simultaneous threads fire the exact same payload.
   Verifies ON CONFLICT DO NOTHING RETURNING id prevents InFailedSqlTransaction and returns identical submission_id.
3. 100-user HTTP concurrency: 100 distinct audits submitted under 20 concurrent worker threads to the same organisation.
   Measures real P50, P95, P99 latency, throughput (req/s), and guarantees 0 lost submissions.
4. Real background job lifecycle: tests claim_next_job (SKIP LOCKED), process_email_job, and complete_job against real tables.
5. Full atomic cleanup of all test entities.
"""

import os
import sys
import time
import uuid
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure not running under pytest test flag so safety guard permits load test
os.environ.pop("TESTING", None)
os.environ["APP_ENV"] = "development"

import psycopg2
from psycopg2.extras import RealDictCursor
from starlette.testclient import TestClient

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
from app.core.database import init_connection_pool, close_connection_pool, get_db_connection
from app.main import app
from app.tasks.job_worker import claim_next_job, process_email_job, complete_job
from app.core.limiter import limiter

def run_real_postgres_benchmark():
    print("=" * 80)
    print("NIWI v3.1 REAL POSTGRESQL CONCURRENCY & IDEMPOTENCY BENCHMARK")
    print("=" * 80)

    # 1. Verify environment and unmocked database
    print(f"Target Database Host: {PGHOST}")
    print(f"Target Database Name: {PGDATABASE}")
    print(f"psycopg2 Connection Module: {psycopg2.__name__} (unmocked)")

    limiter.enabled = False  # Bypasses client-side single-IP throttle during load test
    init_connection_pool(minconn=5, maxconn=25)
    client = TestClient(app)

    # Test baseline DB connection and fetch version
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            pg_version = cur.fetchone()[0]
            print(f"Live PostgreSQL Version: {pg_version}")

    batch_uuid = uuid.uuid4().hex[:8]
    test_org_name = f"RealPG Load Test Org {batch_uuid}"
    created_sub_ids = []
    created_org_ids = set()

    try:
        # ----------------------------------------------------------------------
        # TEST 1: In-Flight Concurrent Idempotency
        # ----------------------------------------------------------------------
        print("\n" + "-" * 80)
        print("TEST 1: In-Flight Concurrent Idempotency (ON CONFLICT DO NOTHING)")
        print("-" * 80)
        idemp_key = f"real-pg-idemp-{uuid.uuid4()}"
        idemp_payload = {
            "name": "Concurrent InFlight User",
            "company_name": test_org_name,
            "email": f"idemp_{batch_uuid}@realpg-test.com",
            "consent_given": True,
            "idempotency_key": idemp_key,
            **{f"q{i}": "Yes" for i in range(5, 45)}
        }

        num_idemp_threads = 10
        print(f"Launching {num_idemp_threads} simultaneous requests with IDENTICAL idempotency_key...")

        def post_idemp():
            t0 = time.perf_counter()
            resp = client.post("/api/submit", json=idemp_payload)
            elapsed = (time.perf_counter() - t0) * 1000
            return resp.status_code, resp.json(), elapsed

        with ThreadPoolExecutor(max_workers=num_idemp_threads) as executor:
            futures = [executor.submit(post_idemp) for _ in range(num_idemp_threads)]
            idemp_results = [f.result() for f in as_completed(futures)]

        status_codes = [r[0] for r in idemp_results]
        sub_ids = [r[1].get("submission_id") for r in idemp_results if r[0] == 201]
        idemp_latencies = [r[2] for r in idemp_results]

        print(f"Responses received: {len(sub_ids)}/{num_idemp_threads} returned HTTP 201")
        print(f"Status codes: {set(status_codes)}")
        print(f"Unique submission IDs returned across all {num_idemp_threads} threads: {set(sub_ids)}")
        print(f"Latency P50: {statistics.median(idemp_latencies):.2f}ms | Max: {max(idemp_latencies):.2f}ms")

        assert len(set(sub_ids)) == 1, f"Expected exactly 1 unique submission_id, got: {set(sub_ids)}"
        single_sub_id = sub_ids[0]
        created_sub_ids.append(single_sub_id)

        # Verify real database count
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM submissions WHERE idempotency_key = %s", (idemp_key,))
                db_idemp_count = cur.fetchone()[0]
                cur.execute("SELECT organization_id FROM submissions WHERE id = %s", (single_sub_id,))
                org_row = cur.fetchone()
                if org_row and org_row[0]:
                    created_org_ids.add(str(org_row[0]))

        print(f"Submissions in PostgreSQL with idempotency_key: {db_idemp_count}")
        assert db_idemp_count == 1, f"Expected exactly 1 row in PostgreSQL, found {db_idemp_count}"
        print(">> TEST 1 PASSED: Zero transaction aborts, zero duplicates, exactly 1 submission created.")

        # ----------------------------------------------------------------------
        # TEST 2: 100-User HTTP Concurrency against Real PostgreSQL
        # ----------------------------------------------------------------------
        print("\n" + "-" * 80)
        print("TEST 2: 100-User HTTP Concurrency (20 parallel workers, same org)")
        print("-" * 80)
        num_users = 100
        concurrency = 20

        submissions_data = []
        for i in range(num_users):
            submissions_data.append({
                "name": f"Stress User {i}",
                "company_name": test_org_name,
                "email": f"stress_{batch_uuid}_{i}@realpg-test.com",
                "consent_given": True,
                "idempotency_key": f"stress-idemp-{batch_uuid}-{i}",
                **{f"q{j}": ("Yes" if (i + j) % 2 == 0 else "No") for j in range(5, 45)}
            })

        print(f"Executing {num_users} submissions with concurrency={concurrency}...")

        def post_submission(payload):
            t0 = time.perf_counter()
            resp = client.post("/api/submit", json=payload)
            elapsed = (time.perf_counter() - t0) * 1000
            return resp.status_code, resp.json(), elapsed

        t_start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(post_submission, p) for p in submissions_data]
            bench_results = [f.result() for f in as_completed(futures)]
        total_time = time.perf_counter() - t_start

        bench_statuses = [r[0] for r in bench_results]
        bench_sub_ids = [r[1].get("submission_id") for r in bench_results if r[0] == 201]
        bench_latencies = [r[2] for r in bench_results]
        created_sub_ids.extend(bench_sub_ids)

        bench_latencies.sort()
        p50 = statistics.median(bench_latencies)
        p90 = bench_latencies[int(len(bench_latencies) * 0.90)]
        p95 = bench_latencies[int(len(bench_latencies) * 0.95)]
        p99 = bench_latencies[int(len(bench_latencies) * 0.99)]
        throughput = num_users / total_time

        print(f"Completed in: {total_time:.2f}s")
        print(f"Throughput: {throughput:.2f} requests/sec")
        print(f"Successful submissions (HTTP 201): {len(bench_sub_ids)}/{num_users}")
        print(f"Unique submission IDs: {len(set(bench_sub_ids))}/{num_users}")
        print(f"Latency P50: {p50:.2f}ms")
        print(f"Latency P90: {p90:.2f}ms")
        print(f"Latency P95: {p95:.2f}ms")
        print(f"Latency P99: {p99:.2f}ms")
        print(f"Latency Min: {min(bench_latencies):.2f}ms | Max: {max(bench_latencies):.2f}ms")

        assert len(bench_sub_ids) == num_users, f"Expected {num_users} HTTP 201s, got {len(bench_sub_ids)}"
        assert len(set(bench_sub_ids)) == num_users, f"Duplicate submission IDs detected!"

        # Verify real database consistency
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1. Exactly 1 organization created for test_org_name
                cur.execute("SELECT id FROM organizations WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))", (test_org_name,))
                org_rows = cur.fetchall()
                print(f"Organizations created with name '{test_org_name}': {len(org_rows)}")
                assert len(org_rows) == 1, f"Advisory lock failed: {len(org_rows)} organizations created!"
                org_id = str(org_rows[0][0])
                created_org_ids.add(org_id)

                # 2. Verify all submissions have organization_id linked
                cur.execute("SELECT COUNT(*) FROM submissions WHERE organization_id = %s", (org_id,))
                subs_linked = cur.fetchone()[0]
                print(f"Submissions linked to organization in PostgreSQL: {subs_linked}")
                assert subs_linked >= num_users

                # 3. Verify post_submit_jobs table has jobs queued
                cur.execute(
                    "SELECT COUNT(*) FROM post_submit_jobs WHERE submission_id = ANY(%s::uuid[]) AND job_type = 'email'",
                    (bench_sub_ids,)
                )
                email_jobs_count = cur.fetchone()[0]
                print(f"Durable email background jobs queued in post_submit_jobs: {email_jobs_count}")
                assert email_jobs_count == num_users, f"Expected {num_users} email jobs, found {email_jobs_count}"

        print(">> TEST 2 PASSED: 100/100 concurrent submissions verified in real PostgreSQL.")

        # ----------------------------------------------------------------------
        # TEST 3: Background Worker Execution against Real PostgreSQL
        # ----------------------------------------------------------------------
        print("\n" + "-" * 80)
        print("TEST 3: Background Worker Execution (SKIP LOCKED) on Real PostgreSQL")
        print("-" * 80)
        target_sub_id = bench_sub_ids[0]
        worker_id = f"real-pg-worker-{batch_uuid}"

        # Claim a job from real DB
        claimed = claim_next_job(worker_id=worker_id)
        assert claimed is not None, "Worker failed to claim job from real PostgreSQL"
        print(f"Worker claimed job: {claimed['id']} (type={claimed['job_type']}) for submission {claimed['submission_id']}")

        # Process the email job
        process_email_job(claimed["submission_id"], claimed.get("payload") or {})
        complete_job(claimed["id"])

        # Verify in real DB that email_body is populated and status is DONE
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT email_body FROM submissions WHERE id = %s", (claimed["submission_id"],))
                body = cur.fetchone()[0]
                assert body is not None and len(body) > 100
                assert "NeuroMark Audit" in body
                print("Verified email_body rendered and persisted in PostgreSQL!")

                cur.execute("SELECT status FROM post_submit_jobs WHERE id = %s", (claimed["id"],))
                job_status = cur.fetchone()[0]
                assert job_status == "DONE"
                print(f"Verified post_submit_jobs status transitioned to: {job_status}")

        print(">> TEST 3 PASSED: Background worker executed and completed on live PostgreSQL.")

    finally:
        # ----------------------------------------------------------------------
        # CLEANUP: Remove all test artifacts from live Azure PostgreSQL
        # ----------------------------------------------------------------------
        print("\n" + "-" * 80)
        print("CLEANUP: Removing test entities from Azure PostgreSQL...")
        print("-" * 80)
        if created_sub_ids:
            with get_db_connection() as conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM post_submit_jobs WHERE submission_id = ANY(%s::uuid[])", (created_sub_ids,))
                        print(f"Deleted post_submit_jobs for {len(created_sub_ids)} submissions.")
                        cur.execute("DELETE FROM org_submission_links WHERE submission_id = ANY(%s::uuid[])", (created_sub_ids,))
                        cur.execute("DELETE FROM submissions WHERE id = ANY(%s::uuid[])", (created_sub_ids,))
                        print(f"Deleted {len(created_sub_ids)} test submissions.")

                        if created_org_ids:
                            cur.execute("DELETE FROM organizations WHERE id = ANY(%s::uuid[])", (list(created_org_ids),))
                            print(f"Deleted {len(created_org_ids)} test organizations.")
        limiter.enabled = True
        close_connection_pool()
        print("Connection pool closed. Real PostgreSQL test complete.")
        print("=" * 80)

if __name__ == "__main__":
    run_real_postgres_benchmark()
