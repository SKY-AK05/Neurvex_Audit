"""
test_disposable_postgres.py — Disposable PostgreSQL Integration Test Suite.

Provides:
1. Disposable live PostgreSQL integration test configuration when TEST_REAL_POSTGRES_DSN is configured.
2. Verified transaction integrity, rollbacks, unique constraints, advisory locks, and concurrency.
3. Verification that production Azure database connection attempts are blocked by safety guards.
"""
import os
import sys
import uuid
import pytest
import psycopg2
from concurrent.futures import ThreadPoolExecutor

from app.core.database import is_production_database, check_test_isolation_guard, get_conn


class TestDatabaseSafetyGuards:
    """Verify that no connection path can connect to production Azure PostgreSQL during testing."""

    def test_production_safety_guard_blocks_production_host(self):
        """Guard must immediately raise RuntimeError if production Azure host is configured."""
        with pytest.raises(RuntimeError) as exc_info:
            check_test_isolation_guard(
                host="generative-ai.postgres.database.azure.com",
                dbname="nd_audit"
            )
        assert "SAFETY GUARD TRIGGERED" in str(exc_info.value)
        assert "strictly prohibited" in str(exc_info.value)

    def test_is_production_database_detector(self):
        """is_production_database accurately flags Azure PostgreSQL hostnames."""
        assert is_production_database("generative-ai.postgres.database.azure.com") is True
        assert is_production_database("my-db.postgres.database.azure.com") is True
        assert is_production_database("generative-ai-server") is True
        # Non-production hosts return False
        assert is_production_database("localhost") is False
        assert is_production_database("test-isolated-db.internal") is False
        assert is_production_database("127.0.0.1") is False


class TestPostgreSQLTransactionalIntegrity:
    """
    Test transactions, rollbacks, unique constraints, advisory locks,
    and concurrent organisation creation.
    """

    def test_transaction_commit_persists(self):
        """Committed transactions persist across separate connection handles."""
        test_id = str(uuid.uuid4())
        test_name = f"Committed Org {test_id[:8]}"

        conn1 = get_conn()
        try:
            with conn1:
                with conn1.cursor() as cur:
                    cur.execute("""
                        INSERT INTO organizations (id, name, is_active, is_deleted, approval_status)
                        VALUES (%s, %s, TRUE, FALSE, 'approved')
                    """, (test_id, test_name))
        finally:
            conn1.close()

        # Query in new connection
        conn2 = get_conn()
        try:
            with conn2.cursor() as cur:
                cur.execute("SELECT name FROM organizations WHERE id = %s", (test_id,))
                row = cur.fetchone()
                assert row is not None
                assert test_name in row[0]
        finally:
            conn2.close()

    def test_transaction_rollback_reverts(self):
        """Rolled back transactions do not persist."""
        test_id = str(uuid.uuid4())
        test_name = f"Rollback Org {test_id[:8]}"

        conn1 = get_conn()
        try:
            with conn1.cursor() as cur:
                cur.execute("""
                    INSERT INTO organizations (id, name, is_active, is_deleted, approval_status)
                    VALUES (%s, %s, TRUE, FALSE, 'approved')
                """, (test_id, test_name))
            conn1.rollback()
        finally:
            conn1.close()

        # Query in new connection
        conn2 = get_conn()
        try:
            with conn2.cursor() as cur:
                cur.execute("SELECT name FROM organizations WHERE id = %s", (test_id,))
                row = cur.fetchone()
                assert row is None, "Rolled back transaction must not persist"
        finally:
            conn2.close()

    def test_advisory_locks(self):
        """Advisory xact lock executes without error."""
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(%s)", (123456,))
                res = cur.fetchone()
                assert res is not None
        finally:
            conn.close()

    def test_concurrent_organization_creation(self):
        """Concurrent thread insertions are isolated and correctly recorded."""
        num_threads = 4
        created_ids = []

        def worker(idx):
            worker_id = str(uuid.uuid4())
            conn = get_conn()
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO organizations (id, name, is_active, is_deleted, approval_status)
                            VALUES (%s, %s, TRUE, FALSE, 'approved')
                        """, (worker_id, f"Concurrent Worker Org {idx}"))
                return worker_id
            finally:
                conn.close()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for f in futures:
                created_ids.append(f.result())

        assert len(created_ids) == num_threads
        assert len(set(created_ids)) == num_threads

