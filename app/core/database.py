"""
database.py — Database connection management with connection pooling
"""
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import logging
import os
from app.core.config import PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD

logger = logging.getLogger(__name__)

# Connection pool initialization
_connection_pool = None

def is_production_database(host: str, dbname: str = "") -> bool:
    """Return True if host/dbname represents the live production Azure database."""
    if not host:
        return False
    h = host.lower()
    return "postgres.database.azure.com" in h or "generative-ai" in h


def check_test_isolation_guard(host: str = None, dbname: str = None):
    """Safety guard preventing automated tests from connecting to the live production database."""
    app_env = os.environ.get("APP_ENV", "").lower()
    is_test = os.environ.get("TESTING") == "true" or app_env in ("test", "testing")
    target_host = host or PGHOST or os.environ.get("PGHOST", "")
    target_db = dbname or PGDATABASE or os.environ.get("PGDATABASE", "")
    if is_test and is_production_database(target_host, target_db):
        raise RuntimeError(
            f"SAFETY GUARD TRIGGERED: Automated test execution against production Azure database "
            f"({target_host}/{target_db}) is strictly prohibited! "
            f"Tests must use an isolated test database or mock connection."
        )


def init_connection_pool(minconn=2, maxconn=10):
    """
    Initialize the database connection pool.
    Should be called once at application startup.
    
    Args:
        minconn: Minimum number of connections in the pool (default: 2)
        maxconn: Maximum number of connections in the pool (default: 10)
    """
    global _connection_pool
    check_test_isolation_guard()
    
    if _connection_pool is not None:
        logger.warning("Connection pool already initialized")
        return
    
    try:
        _connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            host=PGHOST,
            port=PGPORT,
            dbname=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD,
            sslmode="require",
            # Connection lifetime settings
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
            # Connection timeout settings
            connect_timeout=10,
        )
        logger.info(f"Database connection pool initialized (min={minconn}, max={maxconn})")
    except Exception as e:
        logger.error(f"Failed to initialize connection pool: {e}")
        raise


def close_connection_pool():
    """
    Close all connections in the pool.
    Should be called at application shutdown.
    """
    global _connection_pool
    
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None
        logger.info("Database connection pool closed")


def get_conn():
    """
    Get a connection from the pool wrapped in PooledConnection.
    Always safe to close via conn.close() or context manager.
    """
    global _connection_pool
    check_test_isolation_guard()
    
    # Fallback to direct connection if pool not initialized
    if _connection_pool is None:
        logger.warning("Connection pool not initialized, using direct connection")
        raw_conn = psycopg2.connect(
            host=PGHOST,
            port=PGPORT,
            dbname=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD,
            sslmode="require",
        )
        return PooledConnection(raw_conn, None)
    
    try:
        conn = _connection_pool.getconn()
        conn.rollback()
        return PooledConnection(conn, _connection_pool)
    except pool.PoolError as e:
        logger.error(f"Failed to get connection from pool: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting connection: {e}")
        raise


@contextmanager
def get_db_connection():
    """
    Guaranteed connection cleanup context manager.
    Yields a connection that is ALWAYS returned to pool or closed upon exit.
    """
    conn = get_conn()
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception as e:
            logger.warning(f"Error returning connection to pool: {e}")


@contextmanager
def get_db_transaction():
    """
    Context manager that yields a connection inside a transaction block.
    Commits on successful completion, rolls back on exception, and guarantees connection return.
    """
    conn = get_conn()
    try:
        with conn:
            yield conn
    finally:
        try:
            conn.close()
        except Exception as e:
            logger.warning(f"Error returning transaction connection to pool: {e}")


def return_conn(conn):
    """
    Explicitly return a connection to the pool.
    """
    if conn is not None:
        try:
            conn.close()
        except Exception as e:
            logger.error(f"Failed to return connection to pool: {e}")


class PooledConnection:
    """
    Wrapper for database connections that automatically returns them to the pool upon close().
    Supports both context manager patterns:
      with get_db_connection() as conn: ...
      with get_conn() as conn: ...
    """
    
    def __init__(self, pool_conn, pool_ref=None):
        self._conn = pool_conn
        self._pool = pool_ref
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed or bool(getattr(self._conn, "closed", False))
    
    def __getattr__(self, name):
        """Proxy all attributes to the underlying connection"""
        return getattr(self._conn, name)
    
    def __enter__(self):
        """Context manager entry - start transaction and return self"""
        self._conn.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - commit/rollback transaction and return to pool"""
        res = self._conn.__exit__(exc_type, exc_val, exc_tb)
        self.close()
        return res
    
    def close(self):
        """Return connection to pool idempotently instead of terminating underlying socket"""
        if not self._closed:
            self._closed = True
            if self._pool is not None:
                try:
                    self._pool.putconn(self._conn)
                except Exception as e:
                    logger.error(f"Failed to return connection to pool: {e}")
                    try:
                        self._conn.close()
                    except Exception:
                        pass
            else:
                try:
                    self._conn.close()
                except Exception:
                    pass
