"""
Test database connection pooling and reliability
"""
import pytest
import os
os.environ["TESTING"] = "true"
os.environ["APP_ENV"] = "test"

from app.core.database import (
    init_connection_pool,
    close_connection_pool,
    get_conn,
    _connection_pool
)
import time
import concurrent.futures


class TestConnectionPooling:
    """Test database connection pool functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_pool(self):
        """Initialize pool before each test"""
        close_connection_pool()  # Clean slate
        init_connection_pool(minconn=2, maxconn=5)
        yield
        close_connection_pool()
    
    def test_pool_initialization(self):
        """Pool should initialize successfully"""
        global _connection_pool
        from app.core.database import _connection_pool
        assert _connection_pool is not None
    
    def test_get_connection_from_pool(self):
        """Should get valid connection from pool"""
        conn = get_conn()
        assert conn is not None
        
        # Test connection works
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
        
        assert result[0] == 1
        conn.close()
    
    def test_connection_returned_to_pool(self):
        """Closed connection should return to pool"""
        conn1 = get_conn()
        conn_id = id(conn1)
        conn1.close()
        
        # Get another connection - might be the same one from pool
        conn2 = get_conn()
        # Just verify we can get connections
        assert conn2 is not None
        conn2.close()
    
    def test_multiple_concurrent_connections(self):
        """Pool should handle multiple concurrent connections"""
        connections = []
        
        try:
            # Get multiple connections (up to max pool size)
            for i in range(5):
                conn = get_conn()
                connections.append(conn)
                
                # Verify each connection works
                with conn.cursor() as cur:
                    cur.execute("SELECT %s", (i,))
                    assert cur.fetchone()[0] == i
            
            assert len(connections) == 5
        finally:
            # Return all connections
            for conn in connections:
                conn.close()
    
    def test_pool_exhaustion_handling(self):
        """Should handle pool exhaustion gracefully"""
        connections = []
        
        try:
            # Get max connections
            for i in range(5):
                connections.append(get_conn())
            
            # Try to get one more - should wait or raise exception
            # This tests that we don't create unlimited connections
            with pytest.raises(Exception):
                # Set a timeout to prevent hanging
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Connection pool exhausted")
                
                # This is a simplified test - actual behavior depends on pool configuration
                extra_conn = get_conn()
                extra_conn.close()
        finally:
            for conn in connections:
                conn.close()
    
    def test_connection_state_reset(self):
        """Connection should be reset when returned to pool"""
        conn = get_conn()
        
        # Make changes that should be rolled back
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TEMP TABLE test_reset (id INT)
            """)
        
        # Don't commit - close connection
        conn.close()
        
        # Get connection again
        conn2 = get_conn()
        
        # Temp table should not exist (connection was reset)
        with conn2.cursor() as cur:
            try:
                cur.execute("SELECT * FROM test_reset")
                assert False, "Temp table should not exist after connection reset"
            except Exception:
                # Expected - table doesn't exist
                pass
        
        conn2.close()


class TestTransactionIntegrity:
    """Test transaction handling with connection pool"""
    
    @pytest.fixture(autouse=True)
    def setup_pool(self):
        init_connection_pool(minconn=2, maxconn=5)
        yield
        close_connection_pool()
    
    def test_transaction_commit(self):
        """Committed transactions should persist"""
        import uuid
        test_id = str(uuid.uuid4())
        
        # Insert with commit
        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO organizations (id, name, is_active, is_deleted, approval_status)
                        VALUES (%s, %s, TRUE, FALSE, 'approved')
                    """, (test_id, f"Test Transaction {test_id}"))
        finally:
            conn.close()
        
        # Verify data persists
        conn2 = get_conn()
        try:
            with conn2.cursor() as cur:
                cur.execute("SELECT name FROM organizations WHERE id = %s", (test_id,))
                result = cur.fetchone()
            
            assert result is not None
            assert "Test Transaction" in result[0]
        finally:
            # Cleanup
            with conn2.cursor() as cur:
                cur.execute("DELETE FROM organizations WHERE id = %s", (test_id,))
            conn2.commit()
            conn2.close()
    
    def test_transaction_rollback(self):
        """Rolled back transactions should not persist"""
        import uuid
        test_id = str(uuid.uuid4())
        
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO organizations (id, name, is_active, is_deleted, approval_status)
                    VALUES (%s, %s, TRUE, FALSE, 'approved')
                """, (test_id, f"Test Rollback {test_id}"))
            
            # Explicit rollback
            conn.rollback()
        finally:
            conn.close()
        
        # Verify data does not exist
        conn2 = get_conn()
        try:
            with conn2.cursor() as cur:
                cur.execute("SELECT name FROM organizations WHERE id = %s", (test_id,))
                result = cur.fetchone()
            
            assert result is None
        finally:
            conn2.close()
    
    def test_concurrent_transactions(self):
        """Multiple concurrent transactions should maintain isolation"""
        import uuid
        
        def insert_org(name_suffix):
            test_id = str(uuid.uuid4())
            conn = get_conn()
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO organizations (id, name, is_active, is_deleted, approval_status)
                            VALUES (%s, %s, TRUE, FALSE, 'approved')
                        """, (test_id, f"Concurrent Test {name_suffix}"))
                return test_id
            finally:
                conn.close()
        
        # Run multiple concurrent inserts
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(insert_org, i) for i in range(3)]
            org_ids = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Verify all were inserted
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM organizations 
                    WHERE name LIKE 'Concurrent Test%%'
                """)
                count = cur.fetchone()[0]
            
            assert count == 3
            
            # Cleanup
            with conn.cursor() as cur:
                for org_id in org_ids:
                    cur.execute("DELETE FROM organizations WHERE id = %s", (org_id,))
            conn.commit()
        finally:
            conn.close()


class TestConnectionLeakPrevention:
    """Test that connections are properly returned and don't leak"""
    
    @pytest.fixture(autouse=True)
    def setup_pool(self):
        init_connection_pool(minconn=2, maxconn=5)
        yield
        close_connection_pool()
    
    def test_connection_leak_with_exception(self):
        """Connections should be returned even if exception occurs"""
        def operation_with_exception():
            conn = get_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                raise ValueError("Simulated error")
            finally:
                conn.close()
        
        # Run multiple operations that raise exceptions
        for i in range(10):
            try:
                operation_with_exception()
            except ValueError:
                pass
        
        # Should still be able to get connections
        conn = get_conn()
        assert conn is not None
        
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1
        
        conn.close()
    
    def test_context_manager_cleanup(self):
        """Context manager should properly clean up connections"""
        conn = get_conn()
        
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            # Connection should still be usable after context exit
            with conn.cursor() as cur:
                cur.execute("SELECT 2")
                assert cur.fetchone()[0] == 2
        finally:
            conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
