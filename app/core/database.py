"""
database.py — Database connection management with connection pooling
"""
import psycopg2
import psycopg2.extensions
from psycopg2 import pool
from contextlib import contextmanager
import logging
import os
import time
import threading
from app.core.config import PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD

logger = logging.getLogger(__name__)

# Connection pool initialization
_connection_pool = None
_pool_condition = threading.Condition()

class WorkerPoolMetrics:
    """
    Thread-safe, process-local diagnostics for the database connection pool.
    Accurately tracks checkout lifecycle, hold duration, and detects connection leaks.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.checkout_attempts: int = 0
        self.checkout_successes: int = 0
        self.checkout_pool_errors: int = 0
        self.checkout_other_errors: int = 0
        self.returns_count: int = 0
        self.active_connections: int = 0
        self.peak_connections: int = 0
        self.total_hold_time_ms: float = 0.0
        self.max_hold_time_ms: float = 0.0
        self.long_hold_count: int = 0  # Hold duration > 1000ms
        self.wait_attempts: int = 0
        self.wait_successes: int = 0
        self.wait_timeouts: int = 0
        self.total_wait_time_ms: float = 0.0

    def record_attempt(self):
        with self._lock:
            self.checkout_attempts += 1

    def record_wait_attempt(self):
        with self._lock:
            self.wait_attempts += 1

    def record_wait_success(self, wait_ms: float):
        with self._lock:
            self.wait_successes += 1
            self.total_wait_time_ms += wait_ms

    def record_wait_timeout(self, wait_ms: float):
        with self._lock:
            self.wait_timeouts += 1
            self.total_wait_time_ms += wait_ms

    def record_success(self) -> float:
        """Called ONLY after connection is successfully acquired from pool."""
        now = time.monotonic()
        with self._lock:
            self.checkout_successes += 1
            self.active_connections += 1
            if self.active_connections > self.peak_connections:
                self.peak_connections = self.active_connections
        return now

    def record_pool_error(self, err: Exception):
        with self._lock:
            self.checkout_pool_errors += 1
            active = self.active_connections
            peak = self.peak_connections
            attempts = self.checkout_attempts
        logger.error(
            "POOL_EXHAUSTION: Worker PID %s | Active=%d | Peak=%d | Attempts=%d | Err=%s",
            os.getpid(), active, peak, attempts, err
        )

    def record_other_error(self, err: Exception):
        with self._lock:
            self.checkout_other_errors += 1
        logger.error("CONNECTION_ERROR: Worker PID %s | Err=%s", os.getpid(), err)

    def record_return(self, checkout_time: float):
        """Called when connection is safely returned via putconn()."""
        hold_duration_ms = (time.monotonic() - checkout_time) * 1000.0 if checkout_time else 0.0
        with self._lock:
            self.returns_count += 1
            self.active_connections = max(0, self.active_connections - 1)
            self.total_hold_time_ms += hold_duration_ms
            if hold_duration_ms > self.max_hold_time_ms:
                self.max_hold_time_ms = hold_duration_ms
            if hold_duration_ms > 1000.0:
                self.long_hold_count += 1

        if hold_duration_ms > 2000.0:
            logger.warning(
                "LONG_CONNECTION_HOLD: Worker PID %s held connection for %.2f ms",
                os.getpid(), hold_duration_ms
            )

    def get_snapshot(self) -> dict:
        with self._lock:
            avg_hold = (self.total_hold_time_ms / self.returns_count) if self.returns_count > 0 else 0.0
            return {
                "pid": os.getpid(),
                "minconn": getattr(_connection_pool, "minconn", 2) if _connection_pool else 2,
                "maxconn": getattr(_connection_pool, "maxconn", 10) if _connection_pool else 10,
                "checkout_attempts": self.checkout_attempts,
                "checkout_successes": self.checkout_successes,
                "checkout_pool_errors": self.checkout_pool_errors,
                "checkout_other_errors": self.checkout_other_errors,
                "returns_count": self.returns_count,
                "active_connections": self.active_connections,
                "peak_connections": self.peak_connections,
                "max_hold_time_ms": round(self.max_hold_time_ms, 2),
                "avg_hold_time_ms": round(avg_hold, 2),
                "long_hold_count": self.long_hold_count,
                "wait_attempts": self.wait_attempts,
                "wait_successes": self.wait_successes,
                "wait_timeouts": self.wait_timeouts,
                "total_wait_time_ms": round(self.total_wait_time_ms, 2),
                "in_flight_delta": (self.checkout_successes - self.returns_count) - self.active_connections,
            }

_worker_metrics = WorkerPoolMetrics()

def get_pool_diagnostics() -> dict:
    return _worker_metrics.get_snapshot()

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


def init_connection_pool(minconn=10, maxconn=10):
    """
    Initialize the database connection pool.
    Pre-warms all connections to eliminate dynamic 1.5s SSL handshakes during user requests.
    
    Args:
        minconn: Minimum number of connections in the pool (default: 10)
        maxconn: Maximum number of connections in the pool (default: 10)
    """
    global _connection_pool
    check_test_isolation_guard()
    
    if _connection_pool is not None:
        logger.warning("Connection pool already initialized")
        return
    
    try:
        pg_options = os.environ.get("PGOPTIONS", "-c statement_timeout=15000")
        _connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            host=PGHOST,
            port=PGPORT,
            dbname=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD,
            sslmode="require",
            options=pg_options,
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


def get_conn(timeout: float = 10.0):
    """
    Get a connection from the pool wrapped in PooledConnection with bounded wait queue.
    If pool is full, waits up to `timeout` seconds before raising an error.
    Always safe to close via conn.close() or context manager.
    """
    global _connection_pool
    check_test_isolation_guard()
    
    _worker_metrics.record_attempt()
    
    # Fallback to direct connection if pool not initialized
    if _connection_pool is None:
        logger.warning("Connection pool not initialized, using direct connection")
        try:
            raw_conn = psycopg2.connect(
                host=PGHOST,
                port=PGPORT,
                dbname=PGDATABASE,
                user=PGUSER,
                password=PGPASSWORD,
                sslmode="require",
                options=os.environ.get("PGOPTIONS", "-c statement_timeout=15000"),
            )
            checkout_time = _worker_metrics.record_success()
            return PooledConnection(raw_conn, None, checkout_time)
        except Exception as e:
            _worker_metrics.record_other_error(e)
            raise
    
    deadline = time.monotonic() + timeout
    conn = None
    start_wait = time.monotonic()
    waited = False

    while conn is None:
        try:
            conn = _connection_pool.getconn()
        except pool.PoolError as e:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                total_wait = (time.monotonic() - start_wait) * 1000.0
                _worker_metrics.record_pool_error(e)
                _worker_metrics.record_wait_timeout(total_wait)
                logger.error(
                    "Database connection pool exhausted after %.2f ms wait (maxconn=%s): %s",
                    total_wait, getattr(_connection_pool, "maxconn", "unknown"), e
                )
                raise RuntimeError(f"Database connection pool exhausted: {e}") from e

            waited = True
            _worker_metrics.record_wait_attempt()
            with _pool_condition:
                _pool_condition.wait(timeout=min(remaining, 0.2))
        except Exception as e:
            _worker_metrics.record_other_error(e)
            logger.error(f"Unexpected error getting connection: {e}")
            raise

    if waited:
        _worker_metrics.record_wait_success((time.monotonic() - start_wait) * 1000.0)

    # Defensively inspect status (handles wrapped connections and test mocks without AttributeError)
    conn_status = getattr(conn, "status", None)
    if conn_status is not None and conn_status != psycopg2.extensions.STATUS_READY:
        try:
            conn.rollback()
        except Exception as e:
            logger.warning(f"Error rolling back connection on checkout: {e}")

    checkout_time = _worker_metrics.record_success()
    return PooledConnection(conn, _connection_pool, checkout_time)


@contextmanager
def get_db_connection(timeout: float = 10.0):
    """
    Guaranteed connection cleanup context manager.
    Yields a connection that is ALWAYS returned to pool or closed upon exit.
    """
    conn = get_conn(timeout=timeout)
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception as e:
            logger.warning(f"Error returning connection to pool: {e}")


@contextmanager
def get_db_transaction(timeout: float = 10.0):
    """
    Context manager that yields a connection inside a transaction block.
    Commits on successful completion, rolls back on exception, and guarantees connection return.
    """
    conn = get_conn(timeout=timeout)
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
    
    def __init__(self, pool_conn, pool_ref=None, checkout_time: float = 0.0):
        self._conn = pool_conn
        self._pool = pool_ref
        self._checkout_time = checkout_time
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
        """Context manager exit - commit/rollback transaction without prematurely returning connection to pool"""
        return self._conn.__exit__(exc_type, exc_val, exc_tb)
    
    def close(self):
        """Return connection to pool idempotently instead of terminating underlying socket"""
        if not self._closed:
            self._closed = True
            if self._pool is not None:
                is_closed = getattr(self._conn, "closed", False)
                conn_status = getattr(self._conn, "status", None)
                try:
                    if not is_closed and conn_status is not None and conn_status != psycopg2.extensions.STATUS_READY:
                        try:
                            self._conn.rollback()
                        except Exception:
                            is_closed = True

                    if is_closed:
                        # Dead or severed socket: tell pool to discard it rather than re-pooling
                        self._pool.putconn(self._conn, close=True)
                    else:
                        self._pool.putconn(self._conn)
                except Exception as e:
                    logger.error(f"Failed to return connection to pool: {e}")
                    try:
                        self._pool.putconn(self._conn, close=True)
                    except Exception:
                        try:
                            self._conn.close()
                        except Exception:
                            pass
                finally:
                    _worker_metrics.record_return(self._checkout_time)
                    with _pool_condition:
                        _pool_condition.notify_all()
            else:
                try:
                    self._conn.close()
                except Exception:
                    pass
                finally:
                    _worker_metrics.record_return(self._checkout_time)
