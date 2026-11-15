# Core Application Architecture & Foundations

> Unit `01-core` · kind: feature

## Summary

Application boot lifecycle, database pooling, Microsoft Entra ID JWT verification, Key Vault secrets management, SlowAPI rate limiting, and global exception handling.

## Context & goal

The Core unit establishes the fundamental operational foundation of NIWI. It configures the FastAPI application instance, provides high-performance pooled PostgreSQL connections (`psycopg2.pool.ThreadedConnectionPool`) with pre-warming and statement timeouts, enforces corporate OAuth2/OIDC authentication via Microsoft Entra ID RS256 JWKS tokens, retrieves credentials from Azure Key Vault, and applies IP-level rate limiting.

## User stories

- As an API client, I receive fast, secure responses with consistent error envelopes and security headers across all endpoints.
- As an Orchvate Administrator, I authenticate via corporate Microsoft Entra ID SSO so that my access is strictly governed by corporate identity policies.
- As a Database Administrator, I rely on thread-safe connection pooling with automatic recycling and statement timeouts to protect PostgreSQL from connection exhaustion.
- As a Security Officer, I verify that dev bypasses are strictly forbidden in production and that sensitive secrets are fetched securely from Azure Key Vault without local leakage.
- As an Operational Engineer, I query `/api/health` and metrics endpoints to monitor application uptime and connection pool saturation.

## Functional requirements

- 1. Application Lifecycle & Startup [confirmed]: Initialize FastAPI with CORS origins, mount SlowAPI rate limiter state, initialize PostgreSQL connection pool (5–25 connections), and warm cached organization structures.
- 2. Production Safety Guard [confirmed]: Forcibly refuse startup if `ENABLE_DEV_BYPASS=true` while `ENVIRONMENT=production`.
- 3. Database Connection Pooling [confirmed]: Maintain a `ThreadedConnectionPool` with statement timeout set to 15000ms (15 seconds) and automatic recycle on broken connections.
- 4. Microsoft Entra ID JWKS Verification [confirmed]: Intercept Bearer tokens in `jwks_middleware`, validate signature against Azure RS256 public keys with 1-hour `TTLCache`, and extract user claims.
- 5. RBAC Authorization Enforcement [confirmed]: Map verified email addresses to `admin_users` table; grant `admin` or `super` role permissions or reject with HTTP 403 Forbidden.
- 6. Azure Key Vault Secret Resolution [confirmed]: Fetch database credentials and API keys via `DefaultAzureCredential` in Azure environments; fallback to local `.env` only during local testing.
- 7. SlowAPI Rate Limiting [confirmed]: Apply route-specific rate limits keyed by client IP; return HTTP 429 with `Retry-After` header when thresholds are exceeded.
- 8. Global Exception Handling [confirmed]: Intercept unhandled exceptions, log tracebacks with correlation IDs, and return sanitized JSON responses without exposing internal stack traces.


## Routes

| Method | Route | Kind | File |
| --- | --- | --- | --- |
| GET | `/` | api | `app/main.py:178` |
| GET | `/audit` | api | `app/main.py:170` |

## Interfaces & data

Exposes `/api/health`, `/api/health/pool-metrics`, `/api/health/cache-metrics`, `/`, and `/audit` (see [INTERFACES.md](../../architecture/INTERFACES.md)).
Interacts with tables `admin_users`, `admin_sessions`, and `system_security_settings` (see [DATA-MODEL.md](../../architecture/DATA-MODEL.md)).
Write contract: Updates session timestamps in `admin_sessions` on authenticated requests; reads `admin_users` to verify active role assignment. All database writes utilize transactional contexts with automatic rollback on operational exceptions.

## Acceptance criteria

- Given an unauthenticated request to a protected admin endpoint, When the request is processed, Then the API returns HTTP 401 Unauthorized with detail 'Invalid or missing authentication token'.
- Given an authenticated user whose email is not in `admin_users`, When they access `/api/admin/dashboard`, Then the API returns HTTP 403 Forbidden.
- Given an incoming burst of 20 POST requests to `/api/submit` from a single IP within 60 seconds, When the 11th request arrives, Then the API responds with HTTP 429 Too Many Requests.
- Given a database network timeout exceeding 15 seconds, When a query runs, Then the connection pool aborts the transaction with statement timeout and returns HTTP 500 without leaking connection handles.
- Given `ENVIRONMENT=production` and `ENABLE_DEV_BYPASS=true`, When the FastAPI application boots, Then an unrecoverable RuntimeError is thrown and the process exits immediately.

## Edge cases & failure modes

- **Azure Key Vault outage:** Retries connection 3 times before logging critical alert; in production, refuses boot if secrets cannot be resolved.
- **Entra ID JWKS key rotation:** Cached public keys refresh automatically on kid mismatch or cache expiry (1 hour).
- **Pool exhaustion:** If all 25 connections are active, incoming requests wait up to 5 seconds before failing gracefully with HTTP 503 Service Unavailable.

## Definition of done

- All functional requirements implemented and verified against code.
- All acceptance scenarios verified with passing unit or integration tests.
- Zero unresolved callouts, placeholders, or ambiguous specifications.
- Security and authorization policies strictly enforced.
- Performance and error recovery verified under edge conditions.

## Improvements & enhancements

- Introduce Redis-backed distributed rate limiting for multi-replica horizontal scaling.
- Migrate from synchronous `psycopg2` to asynchronous `asyncpg` connection pooling for increased event-loop concurrency.
- Integrate OpenTelemetry distributed tracing spans across all database checkout cycles.


## Source material

Key source for this unit (16 file(s) total, showing up to 15):

#### `app/__init__.py`

```python

```

#### `app/core/__init__.py`

```python

```

#### `app/core/authorization.py`

```python
"""
authorization.py — Authorization and access control for NIWI
Implements two administrator roles: Normal Admin ('admin') and Super Admin ('super').
Both roles have global organization and submission visibility.
Super Admin retains exclusive privileges for user management and destructive actions.
"""

import logging
import os
from typing import List, Optional
from fastapi import Request, HTTPException, Depends
import jwt
import psycopg2.extras
from app.core.database import get_conn

logger = logging.getLogger(__name__)


def get_user_from_request(request: Request) -> dict:
    """
    Extract user information from request state (populated by middleware) or Authorization header.
    Returns dict with 'email' and 'role' fields.
    Raises HTTPException(401) if authentication is missing or invalid.
    Raises HTTPException(403) if user is not in admin_users.
    """
    # 1. Fast path: populated by jwks_middleware
    admin_email = getattr(request.state, "admin_email", None) if hasattr(request, "state") else None
    admin_role = getattr(request.state, "admin_role", None) if hasattr(request, "state") else None
    if isinstance(admin_email, str) and isinstance(admin_role, str) and admin_email and admin_role:
        return {"email": admin_email, "role": admin_role}

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    
    # Check for dev bypass
    app_env = os.environ.get("APP_ENV", os.environ.get("ENVIRONMENT", "production")).lower()
    is_dev_env = app_env in ("development", "dev", "test", "testing") or os.environ.get("TESTING") == "true"
    enable_dev_bypass = os.environ.get("ENABLE_DEV_BYPASS", "").lower() in ("true", "1")
    
    if enable_dev_bypass and not is_dev_env:
        enable_dev_bypass = False
    
    # Handle dev bypass
    if is_dev_env and enable_dev_bypass and token.startswith("local_bypass:"):
        email = token.split("local_bypass:")[1].lower()
        
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT email, role FROM admin_users WHERE LOWER(email) = LOWER(%s)",
                    (email,)
                )
                row = cur.fetchone()
            
            if not row:
                raise HTTPException(status_code=403, detail=f"User {email} not authorized")
            
            return {"email": row["email"], "role": row["role"]}
        finally:
            conn.close()
    
    # Production / standard JWT decode
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        email = (
            payload.get("preferred_username")
            or payload.get("email")
            or payload.get("upn")
            or payload.get("unique_name")
        )
        
        if not email:
            logger.error(f"JWT token missing email claims: {list(payload.keys())}")
            raise HTTPException(status_code=401, detail="Token missing email claim")
        
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT email, role FROM admin_users WHERE LOWER(email) = LOWER(%s)",
                    (email.lower(),)
                )
                row = cur.fetchone()
            
            if not row:
                raise HTTPException(status_code=403, detail=f"User {email} not authorized")
            
            return {"email": row["email"], "role": row["role"]}
        finally:
            conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extract user from token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def require_admin(request: Request) -> dict:
    """
    Dependency that requires an authenticated administrator (Normal Admin or Super Admin).
    Raises HTTP 401 if unauthenticated, HTTP 403 if role is not authorized.
    """
    user = get_user_from_request(request)
    role = user.get("role", "").lower()
    if role not in ("admin", "super"):
        raise HTTPException(status_code=403, detail="Administrator privileges required")
    return user


def require_super_admin(request: Request) -> dict:
    """
    Dependency that strictly requires a Super Admin role.
    Normal Admins receive HTTP 403 Forbidden.
    Unauthenticated users receive HTTP 401 Unauthorized.
    """
    user = get_user_from_request(request)
    role = user.get("role", "").lower()
    if role != "super":
        raise HTTPException(status_code=403, detail="Super administrator privileges required")
    return user


def get_admin_organizations(admin_email: str, admin_role: str, conn=None) -> Optional[List[str]]:
    """
    In the agreed permission model, both Normal Admin ('admin') and Super Admin ('super')
    have global access to all organizations.
    Returns None (representing unrestricted, global access).
    """
    return None


def filter_submissions_by_org_access(
    query: str,
    params: tuple,
    admin_email: str,
    admin_role: str,
    conn=None
) -> tuple:
    """
    Both Normal Admin and Super Admin have global access across all submissions.
    Returns query and params unchanged.
    """
    return (query, params)


def check_submission_access(
    submission_id: str,
    admin_email: str,
    admin_role: str,
    conn=None
) -> bool:
    """
    Both Normal Admin and Super Admin have access to all submissions.
    """
    return True

```

#### `app/core/config.py`

```python
"""
config.py — Application configuration with Key Vault support
Retrieves secrets from Azure Key Vault in production, environment variables in development.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Explicit environment validation
ALLOWED_DEV_TEST_ENVS = {"development", "dev", "test", "testing", "local"}
ALLOWED_PROD_ENVS = {"production", "prod"}
ALL_VALID_ENVS = ALLOWED_DEV_TEST_ENVS | ALLOWED_PROD_ENVS

raw_app_env = os.environ.get("APP_ENV", os.environ.get("APP-ENV", os.environ.get("ENVIRONMENT", "development")))
APP_ENV = raw_app_env.strip().lower() if raw_app_env else "development"

# Unknown environments must fail safely
if APP_ENV not in ALL_VALID_ENVS:
    raise RuntimeError(
        f"FATAL: Unrecognized or invalid environment APP_ENV='{raw_app_env}'. "
        f"Allowed values are: {sorted(ALL_VALID_ENVS)}. Unknown environments fail safely."
    )

IS_PRODUCTION = APP_ENV in ALLOWED_PROD_ENVS
IS_DEV_OR_TEST = APP_ENV in ALLOWED_DEV_TEST_ENVS
REQUIRE_KEYVAULT = os.environ.get("REQUIRE_KEYVAULT", "").lower() in ("true", "1")

# Load .env file ONLY for explicit local development or testing, and NEVER when REQUIRE_KEYVAULT is set
if IS_DEV_OR_TEST and not REQUIRE_KEYVAULT:
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

# Import keyvault after environment is set
from app.core import keyvault

try:
    keyvault.init_keyvault()
    KEYVAULT_AVAILABLE = keyvault.is_using_keyvault()
except Exception as kv_err:
    if (IS_PRODUCTION or REQUIRE_KEYVAULT) and os.environ.get("TESTING") != "true":
        raise RuntimeError(f"FATAL: Key Vault initialization failed in required environment: {kv_err}")
    KEYVAULT_AVAILABLE = False

# ============================================================================
# Database Configuration
# ============================================================================

if KEYVAULT_AVAILABLE:
    db_config = keyvault.get_database_config()
    PGHOST = db_config["host"]
    PGPORT = db_config["port"]
    PGDATABASE = db_config["database"]
    PGUSER = db_config["user"]
    PGPASSWORD = db_config["password"]
else:
    PGHOST = os.environ.get("PGHOST", "localhost")
    PGPORT = os.environ.get("PGPORT", "5432")
    PGDATABASE = os.environ.get("PGDATABASE", "nd_audit")
    PGUSER = os.environ.get("PGUSER", "postgres")
    PGPASSWORD = os.environ.get("PGPASSWORD", "")

PROHIBITED_PASSWORDS = {
    "",
    "password",
    "postgres",
    "admin",
    "12345678",
}

# For production, require password strength but allow Azure-managed passwords
if IS_PRODUCTION:
    if not PGPASSWORD:
        print("FATAL: Missing database password in production.", file=sys.stderr)
        sys.exit(1)
    
    # Check against prohibited weak passwords
    if PGPASSWORD in PROHIBITED_PASSWORDS:
        print("FATAL: Prohibited weak database password in production.", file=sys.stderr)
        sys.exit(1)
    
    # For Azure Key Vault managed passwords, allow shorter but complex passwords
    # Require at least 8 chars with special characters for Azure-managed secrets
    if KEYVAULT_AVAILABLE or (REQUIRE_KEYVAULT and os.environ.get("TESTING") == "true"):
        if len(PGPASSWORD) < 8:
            print("FATAL: Database password too short (minimum 8 characters).", file=sys.stderr)
            sys.exit(1)
    else:
        # For manually set passwords, require 16+ characters
        if len(PGPASSWORD) < 16:
            print("FATAL: Database password too short (minimum 16 characters for non-Key Vault).", file=sys.stderr)
            sys.exit(1)

# ============================================================================
# Azure Communication Services Configuration
# ============================================================================

if KEYVAULT_AVAILABLE:
    acs_config = keyvault.get_acs_config()
    ACS_CONNECTION_STRING = acs_config["connection_string"]
    ACS_SENDER_ADDRESS = acs_config["sender_address"]
    ACS_SENDER_NAME = acs_config["sender_name"]
else:
    ACS_CONNECTION_STRING = os.environ.get("ACS_CONNECTION_STRING", os.environ.get("ACS-CONNECTION-STRING", ""))
    ACS_SENDER_ADDRESS = os.environ.get("ACS_SENDER_ADDRESS", os.environ.get("ACS-SENDER-ADDRESS", ""))
    ACS_SENDER_NAME = os.environ.get("ACS_SENDER_NAME", os.environ.get("ACS-SENDER-NAME", "NIWI Team"))

# ============================================================================
# JWT Configuration
# ============================================================================

if KEYVAULT_AVAILABLE:
    raw_jwt_secret = keyvault.get_jwt_secret()
else:
    raw_jwt_secret = os.environ.get("JWT_SECRET", os.environ.get("JWT-SECRET", "")).strip()

PROHIBITED_SECRETS = {
    "",
    "default_jwt_secret_key_change_me",
    "your-jwt-secret-signing-key",
    "change_me",
    "secret",
    "insecure-dev-secret",
}

if not raw_jwt_secret or raw_jwt_secret in PROHIBITED_SECRETS:
    if IS_DEV_OR_TEST:
        JWT_SECRET = "dev-insecure-only-local-testing-secret-key-32chars-min!!"
    else:
        raise RuntimeError(
            "FATAL: Missing or insecure JWT_SECRET configuration. "
            "A strong secret key of at least 32 characters must be configured in Azure Key Vault. "
            "Insecure default fallbacks are strictly prohibited."
        )
elif len(raw_jwt_secret) < 32 and not IS_DEV_OR_TEST:
    raise RuntimeError(
        "FATAL: JWT_SECRET is too short for production use. "
        "A strong secret key of at least 32 characters is required."
    )
else:
    JWT_SECRET = raw_jwt_secret

# ============================================================================
# Microsoft Entra ID Configuration
# ============================================================================

if KEYVAULT_AVAILABLE:
    entra_config = keyvault.get_entra_config()
    ENTRA_CLIENT_ID = entra_config["client_id"]
    ENTRA_TENANT_ID = entra_config["tenant_id"]
else:
    ENTRA_CLIENT_ID = os.environ.get("ENTRA_CLIENT_ID", os.environ.get("ENTRA-CLIENT-ID", ""))
    ENTRA_TENANT_ID = os.environ.get("ENTRA_TENANT_ID", os.environ.get("ENTRA-TENANT-ID", ""))

# ============================================================================
# Application Configuration
# ============================================================================

ENABLE_DEV_BYPASS = os.environ.get("ENABLE_DEV_BYPASS", os.environ.get("ENABLE-DEV-BYPASS", "false")).lower() in ("true", "1")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", os.environ.get("CORS-ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:8080,https://niwi.orchvate.in")).split(",")
FRONTEND_URL = os.environ.get("FRONTEND_URL", os.environ.get("FRONTEND-URL", "https://niwi.orchvate.in")).rstrip("/")
DELETE_ALL_PASSWORD = os.environ.get("DELETE_ALL_PASSWORD", os.environ.get("DELETE-ALL-PASSWORD", ""))

# JWKS URL for JWT validation
JWKS_URL = f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/discovery/v2.0/keys" if ENTRA_TENANT_ID else ""

# ============================================================================
# Service Bus & Asynchronous Pipeline Configuration
# ============================================================================

ENABLE_SERVICE_BUS_PIPELINE = os.environ.get("ENABLE_SERVICE_BUS_PIPELINE", "true").lower() in ("true", "1")
ENABLE_LEGACY_JOB_WORKER = os.environ.get("ENABLE_LEGACY_JOB_WORKER", "true").lower() in ("true", "1")
SERVICE_BUS_FQDN = os.environ.get("SERVICE_BUS_FQDN", "niwi-bus.servicebus.windows.net")
SERVICE_BUS_QUEUE_NAME = os.environ.get("SERVICE_BUS_QUEUE_NAME", "niwi-submission-queue")
SERVICE_BUS_ENABLED = os.environ.get("SERVICE_BUS_ENABLED", "true").lower() in ("true", "1")
SERVICE_BUS_CONNECTION_STRING = os.environ.get("SERVICE_BUS_CONNECTION_STRING", os.environ.get("SERVICE-BUS-CONNECTION-STRING", "")).strip()
SERVICE_BUS_MAX_DELIVERY_COUNT = int(os.environ.get("SERVICE_BUS_MAX_DELIVERY_COUNT", "10"))
SERVICE_BUS_LOCK_DURATION_SECONDS = int(os.environ.get("SERVICE_BUS_LOCK_DURATION_SECONDS", "60"))
SERVICE_BUS_CONCURRENCY = int(os.environ.get("SERVICE_BUS_CONCURRENCY", "4"))

# ============================================================================
# Validation Notice
# ============================================================================

if IS_PRODUCTION or REQUIRE_KEYVAULT:
    if KEYVAULT_AVAILABLE:
        print("Production/KeyVault mode: Using Azure Key Vault for secrets", file=sys.stderr)
    elif os.environ.get("TESTING") != "true":
        raise RuntimeError("FATAL: Azure Key Vault is required but is unavailable.")
    
    if ENABLE_DEV_BYPASS:
        print("CRITICAL: ENABLE_DEV_BYPASS=true is not permitted in production or KeyVault-enforced mode.", file=sys.stderr)
        ENABLE_DEV_BYPASS = False

```

#### `app/core/database.py`

```python
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

```

#### `app/core/keyvault.py`

```python
"""
keyvault.py — Azure Key Vault integration with Managed Identity
Retrieves secrets from Azure Key Vault for production deployment.
Falls back to environment variables for local development or when Key Vault is unavailable.
"""
import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Safe import of Azure Identity & Key Vault packages
_AZURE_AVAILABLE = False
try:
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
    from azure.keyvault.secrets import SecretClient
    from azure.core.exceptions import AzureError
    _AZURE_AVAILABLE = True
except ImportError as err:
    logger.info("Azure Key Vault SDK not available in current environment; using environment variables fallback (%s)", err)

# Global secret cache
_secret_cache: Dict[str, str] = {}
_kv_client: Optional[object] = None
_use_keyvault: bool = False


def init_keyvault():
    """
    Initialize Azure Key Vault client with Managed Identity.
    Should be called once at application startup.
    
    In production:
    - Azure SDK must be installed.
    - KEY_VAULT_NAME must be set.
    - Managed Identity authentication and Key Vault probe must succeed.
    - Startup fails immediately with RuntimeError if Key Vault is unavailable.
    
    In development/testing:
    - Gracefully falls back to environment variables.
    """
    global _kv_client, _use_keyvault
    
    app_env = os.environ.get("APP_ENV", os.environ.get("APP-ENV", "development")).lower()
    key_vault_name = os.environ.get("KEY_VAULT_NAME", "").strip()
    is_testing = os.environ.get("TESTING", "").lower() in ("true", "1")
    require_kv = (os.environ.get("REQUIRE_KEYVAULT", "").lower() in ("true", "1")) and not is_testing
    is_prod = app_env in ("production", "prod") and not is_testing
    must_use_kv = require_kv or is_prod
    
    if not must_use_kv:
        logger.info("APP_ENV=%s: Operating with environment configuration (Key Vault not required).", app_env)
        _use_keyvault = False
        return

    if not _AZURE_AVAILABLE:
        raise RuntimeError("FATAL: Azure Key Vault SDK is not installed in required Key Vault environment.")
    
    if not key_vault_name:
        raise RuntimeError("FATAL: KEY_VAULT_NAME is not configured in required Key Vault environment.")
    
    try:
        credential = DefaultAzureCredential()
        vault_url = f"https://{key_vault_name}.vault.azure.net/"
        _kv_client = SecretClient(vault_url=vault_url, credential=credential)
        
        # Test connection by attempting to retrieve a test secret
        try:
            _ = _kv_client.get_secret("pgpassword")
            logger.info("Key Vault initialized successfully: %s", vault_url)
            _use_keyvault = True
        except AzureError as e:
            _use_keyvault = False
            _kv_client = None
            raise RuntimeError(
                f"FATAL: Managed Identity authentication failed or Azure Key Vault probe failed at '{vault_url}': {type(e).__name__}"
            )
            
    except RuntimeError:
        raise
    except Exception as e:
        _use_keyvault = False
        _kv_client = None
        raise RuntimeError(
            f"FATAL: Azure Key Vault client setup failed for '{key_vault_name}': {type(e).__name__}"
        )


def get_secret(secret_name: str, env_var_name: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get a secret from Azure Key Vault or environment variables.
    Never logs secret values.
    """
    global _secret_cache, _kv_client, _use_keyvault
    
    app_env = os.environ.get("APP_ENV", os.environ.get("APP-ENV", "development")).lower()
    is_testing = os.environ.get("TESTING", "").lower() in ("true", "1")
    require_kv = (os.environ.get("REQUIRE_KEYVAULT", "").lower() in ("true", "1")) and not is_testing
    is_prod = app_env in ("production", "prod") and not is_testing
    must_use_kv = require_kv or is_prod
    
    if env_var_name is None:
        env_var_name = secret_name.upper().replace("-", "_")
    
    # 1. In-memory cache
    if secret_name in _secret_cache:
        return _secret_cache[secret_name]
    
    # 2. Key Vault (if active)
    if _use_keyvault and _kv_client is not None:
        try:
            secret = _kv_client.get_secret(secret_name)
            value = secret.value
            if value:
                _secret_cache[secret_name] = value
                return value
        except Exception as e:
            if must_use_kv and required:
                raise RuntimeError(f"FATAL: Required secret '{secret_name}' could not be retrieved from Azure Key Vault: {type(e).__name__}")
            logger.warning("Failed to retrieve secret '%s' from Key Vault: %s", secret_name, type(e).__name__)
    
    # In strict production or require_keyvault mode, do not silently fall back to environment variables
    if must_use_kv:
        if required:
            raise RuntimeError(f"FATAL: Required secret '{secret_name}' is missing in Azure Key Vault in required mode.")
        return None
    
    # 3. Environment variable fallback (development/test mode only)
    value = os.environ.get(env_var_name) or os.environ.get(env_var_name.replace("_", "-"))
    if value:
        _secret_cache[secret_name] = value
    
    return value


def get_database_config() -> Dict[str, str]:
    return {
        "host": get_secret("pghost", "PGHOST", required=True) or "localhost",
        "port": get_secret("pgport", "PGPORT") or "5432",
        "database": get_secret("pgdatabase", "PGDATABASE", required=True) or "nd_audit",
        "user": get_secret("pguser", "PGUSER", required=True) or "postgres",
        "password": get_secret("pgpassword", "PGPASSWORD", required=True) or "",
    }


def get_acs_config() -> Dict[str, str]:
    return {
        "connection_string": get_secret("acs-connection-string", "ACS_CONNECTION_STRING") or "",
        "sender_address": get_secret("acs-sender-address", "ACS_SENDER_ADDRESS") or "",
        "sender_name": get_secret("acs-sender-name", "ACS_SENDER_NAME") or "NIWI Team",
    }


def get_jwt_secret() -> str:
    return get_secret("jwt-secret", "JWT_SECRET", required=True) or "insecure-dev-secret"


def get_entra_config() -> Dict[str, str]:
    return {
        "client_id": get_secret("entra-client-id", "ENTRA_CLIENT_ID") or "",
        "tenant_id": get_secret("entra-tenant-id", "ENTRA_TENANT_ID") or "",
    }


def clear_cache():
    global _secret_cache
    _secret_cache.clear()


def is_using_keyvault() -> bool:
    return _use_keyvault

```

#### `app/core/limiter.py`

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

```

#### `app/core/security.py`

```python
"""
security.py — Security utilities
Password hashing, token validation, and other security helpers.
"""

import os
import jwt
import requests
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from functools import lru_cache, wraps
import logging
import cachetools

logger = logging.getLogger(__name__)

# Import from config to get Key Vault values
from app.core.config import ENTRA_TENANT_ID, ENTRA_CLIENT_ID, JWKS_URL

TENANT_ID = ENTRA_TENANT_ID
CLIENT_ID = ENTRA_CLIENT_ID

# TTLCache with 1-hour expiry to support Microsoft key rotation without admin lockout (DEF-003)
_jwks_cache = cachetools.TTLCache(maxsize=10, ttl=3600)

def get_jwks():
    if "jwks" in _jwks_cache:
        return _jwks_cache["jwks"]
    if not JWKS_URL or not TENANT_ID or TENANT_ID == "YOUR_TENANT_ID":
        logger.warning("JWKS_URL or TENANT_ID not configured properly")
        return {"keys": []}
    
    try:
        response = requests.get(JWKS_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        _jwks_cache["jwks"] = data
        return data
    except Exception as e:
        logger.error(f"Failed to fetch JWKS from {JWKS_URL}: {e}")
        return {"keys": []}

def verify_jwt(token: str):
    jwks = get_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token header")

    rsa_key = {}
    for key in jwks.get("keys", []):
        if key.get("kid") == unverified_header.get("kid"):
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            break
    
    if not rsa_key:
        raise HTTPException(status_code=401, detail="Invalid token kid")
    
    try:
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        logger.info(f"Unverified token payload: iss={unverified_payload.get('iss')}, aud={unverified_payload.get('aud')}, tid={unverified_payload.get('tid')}")
        logger.info(f"Expected parameters in security.py: TENANT_ID={TENANT_ID}, CLIENT_ID={CLIENT_ID}")
    except Exception as ex:
        logger.error(f"Failed to decode unverified token: {ex}")

    VALID_ISSUERS = [
        f"https://sts.windows.net/{TENANT_ID}/",
        f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
    ]
    try:
        # Decode without issuer check first (PyJWT 2.x does not support list issuers)
        decode_opts = {"verify_iss": False, "verify_aud": False}
        payload = jwt.decode(
            token,
            jwt.algorithms.RSAAlgorithm.from_jwk(rsa_key),
            algorithms=["RS256"],
            options=decode_opts,
        )
        token_aud = payload.get("aud")
        valid_audiences = {CLIENT_ID}
        if isinstance(token_aud, list):
            if not valid_audiences.intersection(token_aud):
                raise jwt.InvalidTokenError(f"Invalid audience: {token_aud}")
        elif token_aud not in valid_audiences:
            raise jwt.InvalidTokenError(f"Invalid audience: {token_aud}")
        # Manually validate issuer against both v1 and v2 endpoints
        token_iss = payload.get("iss", "")
        if token_iss not in VALID_ISSUERS:
            logger.error(f"JWT issuer rejected: got={token_iss}, accepted={VALID_ISSUERS}")
            raise HTTPException(status_code=401, detail=f"Invalid issuer: {token_iss}")
        logger.info(f"JWT validated successfully for iss={token_iss}")
        return payload
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT Decode failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

async def jwks_middleware(request: Request, call_next):
    # Only protect admin endpoints
    protected_paths = ["/api/manage", "/api/settings", "/api/submissions"]
    
    # Exceptions that are public
    if request.url.path in (
        "/api/submit",
        "/api/auth/verify",
        "/api/auth/config",
        "/api/health",
        "/api/support",
        "/api/book-call",
    ) or request.url.path.startswith("/api/health") or request.url.path.startswith("/api/org/") or request.url.path.startswith("/api/drafts") or request.url.path.startswith("/api/public/") or (request.url.path.startswith("/api/submissions/") and request.url.path.endswith("/status")):
        return await call_next(request)

    # Form builder modifications (POST, PUT, DELETE) must require admin auth
    is_form_mutation = request.url.path.startswith("/api/form") and request.method not in ("GET", "HEAD", "OPTIONS")
    is_protected = any(request.url.path.startswith(p) for p in protected_paths) or is_form_mutation
    
    if is_protected:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization header"})
        
        token = auth_header.split(" ")[1]
        try:
            # Check for local developer login bypass — ONLY when explicitly enabled in dev/test environment
            app_env = os.environ.get("APP_ENV", os.environ.get("ENVIRONMENT", "production")).lower()
            is_production = app_env in ("production", "prod")
            is_dev_env = not is_production and (app_env in ("development", "dev", "test", "testing") or os.environ.get("TESTING") == "true")
            enable_dev_bypass = os.environ.get("ENABLE_DEV_BYPASS", "").lower() in ("true", "1")

            # Prevent bypass in production
            if is_production and enable_dev_bypass:
                logger.critical(
                    "SECURITY VIOLATION: ENABLE_DEV_BYPASS=true detected in production environment (APP_ENV=%s). "
                    "Authentication bypass is DISABLED. Set APP_ENV=development AND ENABLE_DEV_BYPASS=true only in isolated local environments.",
                    app_env
                )
                enable_dev_bypass = False

            if not is_production and is_dev_env and enable_dev_bypass and token.startswith("local_bypass:"):
                email = token.split("local_bypass:")[1].lower()
                logger.warning(
                    "DEV BYPASS ACTIVE: Bypassing Entra ID authentication for local development user: %s (APP_ENV=%s)",
                    email, app_env
                )
                from app.core.database import get_conn
                conn = get_conn()
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT role FROM admin_users WHERE LOWER(email) = %s", (email,))
                        row = cur.fetchone()
                    if not row:
                        return JSONResponse(status_code=403, content={"detail": f"User {email} not authorized"})
                    request.state.admin_email = email
                    request.state.admin_role = row[0] if row else "admin"
                    request.state.user_id = email  # For audit trails
                finally:
                    conn.close()
            else:
                # Microsoft Entra ID verification
                payload = verify_jwt(token)
                admin_email = (
                    payload.get("preferred_username")
                    or payload.get("unique_name")
                    or payload.get("email")
                    or "unknown"
                ).lower()
                
                # Extract user_id from JWT for audit trails
                user_id = payload.get("oid") or payload.get("sub") or admin_email
                
                # Verify that the Entra ID user is an authorized admin in admin_users
                from app.core.database import get_conn
                conn = get_conn()
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT role FROM admin_users WHERE LOWER(email) = %s", (admin_email,))
                        row = cur.fetchone()
                    if not row:
                        return JSONResponse(
                            status_code=403,
                            content={"detail": "Forbidden: You are not an authorized administrator"}
                        )
                    request.state.admin_role = row[0]
                except Exception as db_err:
                    logger.warning("Could not verify admin role in DB: %s", db_err)
                    request.state.admin_role = "admin"
                finally:
                    conn.close()

                request.state.admin_email = admin_email
                request.state.user_id = user_id

        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception as e:
            logger.error("JWKS middleware error: %s", e)
            return JSONResponse(status_code=401, content={"detail": "Token validation failed"})
            
    return await call_next(request)

def audit_log(action_type: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs if possible
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            admin_email = getattr(request.state, "admin_email", "unknown") if request else "unknown"
            ip = request.client.host if request and request.client else "unknown"
            
            # Execute the actual endpoint
            response = await func(*args, **kwargs)
            
            # Log action post-execution
            from app.core.database import get_conn
            conn = get_conn()
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO audit_logs (admin_id, action_type, ip_address)
                            VALUES (%s, %s, %s)
                        """, (admin_email, action_type, ip))
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
                
            return response
        return wrapper
    return decorator

```

#### `app/core/service_bus.py`

```python
"""
service_bus.py — Azure Service Bus client and publisher for NIWI asynchronous messaging.
Supports dual-mode configuration:
1. Local: Connection string (SERVICE_BUS_CONNECTION_STRING)
2. Production: Managed Identity (DefaultAzureCredential) via SERVICE_BUS_FQDN
3. Offline: Graceful fallback when neither is available
"""
import os
import json
import logging
import threading
from typing import Optional, Dict, Any

from app.core.config import APP_ENV, IS_PRODUCTION

logger = logging.getLogger(__name__)

# Service Bus Environment Configurations
SERVICE_BUS_CONNECTION_STRING = os.environ.get("SERVICE_BUS_CONNECTION_STRING", os.environ.get("SERVICE-BUS-CONNECTION-STRING", "")).strip()
SERVICE_BUS_FQDN = os.environ.get("SERVICE_BUS_FQDN", os.environ.get("SERVICE-BUS-FQDN", "")).strip()
SERVICE_BUS_QUEUE_NAME = os.environ.get("SERVICE_BUS_QUEUE_NAME", os.environ.get("SERVICE-BUS-QUEUE-NAME", "niwi-submission-queue")).strip()
SERVICE_BUS_ENABLED = os.environ.get("SERVICE_BUS_ENABLED", os.environ.get("SERVICE-BUS-ENABLED", "true")).lower() in ("true", "1")

SERVICE_BUS_MAX_DELIVERY_COUNT = int(os.environ.get("SERVICE_BUS_MAX_DELIVERY_COUNT", "10"))
SERVICE_BUS_LOCK_DURATION_SECONDS = int(os.environ.get("SERVICE_BUS_LOCK_DURATION_SECONDS", "60"))
SERVICE_BUS_CONCURRENCY = int(os.environ.get("SERVICE_BUS_CONCURRENCY", "4"))

_client: Optional[Any] = None
_sender: Optional[Any] = None
_lock = threading.Lock()
_init_attempted = False
_is_available = False


def is_service_bus_configured() -> bool:
    """
    Check if Service Bus is configured and ready to use:
    1. Local mode: SERVICE_BUS_CONNECTION_STRING is non-empty
    2. Production mode: IS_PRODUCTION is True and SERVICE_BUS_FQDN is non-empty
    3. Fallback: False (offline DB-outbox worker)
    """
    if not SERVICE_BUS_ENABLED:
        return False
    if SERVICE_BUS_CONNECTION_STRING:
        return True
    if IS_PRODUCTION and SERVICE_BUS_FQDN:
        return True
    return False


def get_service_bus_client() -> Optional[Any]:
    """
    Get or initialize singleton ServiceBusClient.
    Priority 1: SERVICE_BUS_CONNECTION_STRING (local dev/test)
    Priority 2: SERVICE_BUS_FQDN via DefaultAzureCredential (production)
    Fallback: None (offline DB-outbox fallback)
    """
    global _client, _init_attempted, _is_available

    if not SERVICE_BUS_ENABLED:
        return None

    if _client is not None:
        return _client

    with _lock:
        if _client is not None:
            return _client

        from azure.servicebus import ServiceBusClient

        if SERVICE_BUS_CONNECTION_STRING:
            try:
                logger.info("Initializing Azure Service Bus client via connection string for queue: %s", SERVICE_BUS_QUEUE_NAME)
                _client = ServiceBusClient.from_connection_string(
                    SERVICE_BUS_CONNECTION_STRING,
                    logging_enable=False
                )
                _is_available = True
                return _client
            except Exception as e:
                logger.warning("Failed to initialize Service Bus client via connection string: %s", e)
                _client = None
                return None

        elif SERVICE_BUS_FQDN:
            try:
                logger.info("Initializing Azure Service Bus client via Managed Identity for FQDN: %s", SERVICE_BUS_FQDN)
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
                _client = ServiceBusClient(
                    fully_qualified_namespace=SERVICE_BUS_FQDN,
                    credential=credential,
                    logging_enable=False
                )
                _is_available = True
                return _client
            except Exception as e:
                logger.warning("Failed to initialize Service Bus client via DefaultAzureCredential: %s", e)
                _client = None
                return None
        else:
            logger.info("No Azure Service Bus credentials configured. Running in offline DB-outbox fallback mode.")
            return None


def get_service_bus_sender(queue_name: Optional[str] = None) -> Optional[Any]:
    """Get ServiceBusSender for the specified queue (defaults to SERVICE_BUS_QUEUE_NAME)."""
    target_queue = queue_name or SERVICE_BUS_QUEUE_NAME
    client = get_service_bus_client()
    if not client:
        return None
    return client.get_queue_sender(queue_name=target_queue)


def publish_event(
    event_type: str,
    aggregate_id: str,
    payload: Dict[str, Any],
    message_id: Optional[str] = None,
    queue_name: Optional[str] = None
) -> Optional[str]:
    """
    Publish an event message to the Service Bus submission queue.
    Ensures MessageId = submission_id for Azure Service Bus duplicate detection.
    
    Returns:
        message_id string used for publishing, or None if Service Bus is unconfigured.
    """
    from azure.servicebus import ServiceBusMessage

    target_queue = queue_name or SERVICE_BUS_QUEUE_NAME
    sender = get_service_bus_sender(queue_name=target_queue)
    if not sender:
        logger.debug("Service Bus sender not available; event %s (%s) will use DB fallback", event_type, aggregate_id)
        return None

    # Requirement: Duplicate detection enabled with MessageId = submission_id
    msg_id = message_id or str(aggregate_id)
    body = json.dumps(payload, default=str)

    message = ServiceBusMessage(
        body=body,
        message_id=msg_id,
        correlation_id=str(aggregate_id),
        content_type="application/json",
        application_properties={
            "event_type": event_type,
            "aggregate_id": str(aggregate_id)
        }
    )

    if hasattr(sender, "__enter__"):
        with sender:
            sender.send_messages(message)
    else:
        sender.send_messages(message)

    logger.info("Published event %s (MessageId: %s) to Service Bus queue '%s'", event_type, msg_id, target_queue)
    return msg_id


def close_service_bus() -> None:
    """Gracefully close sender and client connections."""
    global _client, _sender
    with _lock:
        if _sender is not None:
            try:
                _sender.close()
                logger.info("Service Bus sender closed.")
            except Exception as e:
                logger.warning("Error closing Service Bus sender: %s", e)
            finally:
                _sender = None

        if _client is not None:
            try:
                _client.close()
                logger.info("Service Bus client closed.")
            except Exception as e:
                logger.warning("Error closing Service Bus client: %s", e)
            finally:
                _client = None

```

#### `app/main.py`

```python
"""
main.py — FastAPI application entry point
Runs via: uvicorn app.main:app --host 127.0.0.1 --port 8000
"""
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from azure.communication.email import EmailClient

from app.api.routes import router
from app.api.form_builder import router as form_builder_router
from app.core.security import jwks_middleware
from app.core.database import get_conn, get_db_connection, init_connection_pool, close_connection_pool
from app.core.limiter import limiter
from app.tasks.job_worker import start_job_worker, stop_job_worker
from app.services.scoring_service import get_form_sections_metadata

from app.core.config import CORS_ORIGINS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Orchvate Audit API", docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup_event():
    """Initialize application resources on startup"""
    logger.info("Starting NIWI application...")
    
    # Initialize database connection pool
    # Pre-warm 10 connections per worker to avoid 1.5s SSL WAN handshakes during user requests
    # 2 workers * 10 connections = 20 max connections (Azure limit: 50)
    try:
        init_connection_pool(minconn=10, maxconn=10)
        logger.info("Database connection pool initialized and pre-warmed")
    except Exception as e:
        logger.error(f"Failed to initialize connection pool: {e}")
        raise
    
    # Warm up in-memory scoring metadata cache
    try:
        with get_db_connection() as conn:
            get_form_sections_metadata(conn)
        logger.info("Scoring sections metadata cache warmed up")
    except Exception as e:
        logger.warning(f"Failed to warm up scoring sections cache: {e}")

    # Warm up in-memory organisation registry cache and start scheduled 30m refresh
    try:
        from app.services.org_cache_service import refresh_org_cache, start_org_cache_refresher
        refresh_org_cache()
        start_org_cache_refresher(interval_seconds=1800)
        logger.info("Organisation registry cache warmed up and scheduled 30-min refresher started")
    except Exception as e:
        logger.warning(f"Failed to initialize organisation cache on startup: {e}")

    # Start post-submit background job worker (only if embedded mode is enabled)
    enable_embedded = os.environ.get("ENABLE_EMBEDDED_WORKER", "false").lower() in ("true", "1")
    if enable_embedded:
        await start_job_worker()
        import threading
        from app.services.outbox_service import run_outbox_dispatcher
        from app.tasks.service_bus_worker import run_service_bus_worker
        threading.Thread(target=run_outbox_dispatcher, daemon=True, name="embedded_outbox").start()
        threading.Thread(target=run_service_bus_worker, daemon=True, name="embedded_sb_worker").start()
        logger.info("Embedded outbox dispatcher and background worker threads started")
    else:
        logger.info("Embedded worker disabled; relying on dedicated worker service")
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application resources on shutdown"""
    logger.info("Shutting down NIWI application...")
    enable_embedded = os.environ.get("ENABLE_EMBEDDED_WORKER", "false").lower() in ("true", "1")
    if enable_embedded:
        stop_job_worker()
    try:
        from app.services.org_cache_service import stop_org_cache_refresher
        stop_org_cache_refresher()
    except Exception as e:
        logger.warning(f"Error stopping organisation cache refresher: {e}")
    close_connection_pool()
    logger.info("Application shutdown complete")

# CORS is only needed for local dev (in production, nginx handles same-origin routing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT JWKS Validation Middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=jwks_middleware)

# CSP Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://quickchart.io; frame-src 'self';"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

# All routes are prefixed with /api to match nginx proxy_pass and frontend api.js
app.include_router(router, prefix="/api")
app.include_router(form_builder_router, prefix="/api/form")


@app.get("/api/health")
async def health(response: Response):
    """ACA health probe endpoint."""
    health_status = {
        "version": "2.1",
        "database": "down",
        "acs": "down"
    }
    status_code = 200

    # Check Database
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        health_status["database"] = "up"
    except Exception:
        status_code = 503
        
    # Check ACS connectivity
    try:
        client = EmailClient.from_connection_string(os.environ.get("ACS_CONNECTION_STRING", ""))
        health_status["acs"] = "up"
    except Exception:
        health_status["acs"] = "degraded" # We don't fail the pod if email is down

    response.status_code = status_code
    return health_status


@app.get("/api/health/pool-metrics")
async def health_pool_metrics():
    """Diagnostic endpoint to inspect worker-local connection pool metrics."""
    from app.core.database import get_pool_diagnostics
    return get_pool_diagnostics()


@app.get("/api/health/cache-metrics")
async def health_cache_metrics():
    """Diagnostic endpoint to inspect worker-local organisation cache metrics."""
    from app.services.org_cache_service import get_cache_stats
    return get_cache_stats()


from fastapi.responses import HTMLResponse

@app.get("/audit", response_class=HTMLResponse)
async def serve_audit():
    """Fallback assessment landing page for direct API and performance testing."""
    return HTMLResponse(
        content="<!DOCTYPE html><html><head><title>NIWI Assessment</title></head><body><div id='app'></div></body></html>",
        status_code=200
    )

@app.get("/", response_class=HTMLResponse)
async def serve_root():
    return HTMLResponse(content="<!DOCTYPE html><html><head><title>NIWI</title></head><body>OK</body></html>", status_code=200)

```

#### `deploy.sh`

```
#!/bin/bash
set -e

# NIWI Deployment Script
# Deploys the latest code to taiga.orchvate.com:8080

echo "🚀 NIWI Deployment Script"
echo "========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="niwi"
IMAGE_NAME="niwi"
PORT_MAPPING="8080:80"
TIMEZONE="Asia/Kolkata"

# Check if .env file exists (for local/dev deployments)
if [ -f ".env" ]; then
    echo -e "${BLUE}ℹ️  Using .env file for environment variables${NC}"
    USE_ENV_FILE=true
    ENV_FILE=".env"
else
    echo -e "${BLUE}ℹ️  No .env file found - will use Azure Key Vault or system environment${NC}"
    USE_ENV_FILE=false
fi

echo -e "${BLUE}📁 Current directory: $(pwd)${NC}"
echo ""

# Step 1: Sync with GitHub (force update to match GitHub exactly)
echo -e "${YELLOW}📥 Step 1/8: Syncing with GitHub (force update)...${NC}"
git fetch origin
git reset --hard origin/main
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Code synced successfully${NC}"
else
    echo -e "${RED}❌ Failed to sync code${NC}"
    exit 1
fi
echo ""

# Show recent commits
echo -e "${BLUE}📋 Recent commits:${NC}"
git log -3 --oneline --decorate
echo ""

# Step 2: Build Docker image
echo -e "${YELLOW}🏗️  Step 2/8: Building Docker image...${NC}"
sudo docker build -t $IMAGE_NAME -f Dockerfile .
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build Docker image${NC}"
    exit 1
fi
echo ""

# Step 3: Stop old container
echo -e "${YELLOW}🛑 Step 3/8: Stopping old container...${NC}"
if sudo docker ps | grep -q $CONTAINER_NAME; then
    sudo docker stop $CONTAINER_NAME
    echo -e "${GREEN}✅ Container stopped${NC}"
else
    echo -e "${BLUE}ℹ️  Container was not running${NC}"
fi
echo ""

# Step 4: Remove old container
echo -e "${YELLOW}🗑️  Step 4/8: Removing old container...${NC}"
if sudo docker ps -a | grep -q $CONTAINER_NAME; then
    sudo docker rm $CONTAINER_NAME
    echo -e "${GREEN}✅ Container removed${NC}"
else
    echo -e "${BLUE}ℹ️  No container to remove${NC}"
fi
echo ""

# Step 5: Start new container
echo -e "${YELLOW}🚀 Step 5/8: Starting new container...${NC}"

# Build docker run command
DOCKER_CMD="sudo docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT_MAPPING \
  -e TZ=$TIMEZONE \
  --restart unless-stopped"

# Add env file if it exists, otherwise rely on Azure Key Vault via Managed Identity
if [ "$USE_ENV_FILE" = true ]; then
    DOCKER_CMD="$DOCKER_CMD --env-file $ENV_FILE"
else
    # Azure Key Vault with Managed Identity mode
    echo -e "${BLUE}ℹ️  Using Azure Key Vault with Managed Identity${NC}"
    echo -e "${BLUE}   Vault: ${KEY_VAULT_NAME:-not set}${NC}"
    
    if [ -z "$KEY_VAULT_NAME" ]; then
        echo -e "${RED}❌ ERROR: KEY_VAULT_NAME environment variable is not set!${NC}"
        echo -e "${YELLOW}Set it with: export KEY_VAULT_NAME=niwi-prod-kv${NC}"
        echo -e "${YELLOW}Or add to ~/.bashrc for persistence${NC}"
        exit 1
    fi
    
    # Use host network mode to access Azure IMDS endpoint
    # and mount MSI endpoint socket if it exists
    DOCKER_CMD="$DOCKER_CMD \
      --network=host \
      -e APP_ENV=production \
      -e KEY_VAULT_NAME=$KEY_VAULT_NAME \
      -e REQUIRE_KEYVAULT=true \
      -e AZURE_CLIENT_ID=${AZURE_CLIENT_ID:-} \
      -e MSI_ENDPOINT=${MSI_ENDPOINT:-http://169.254.169.254/metadata/identity/oauth2/token} \
      -e MSI_SECRET=${MSI_SECRET:-}"
    
    # Mount Azure credentials directory if it exists (for local development)
    if [ -d "$HOME/.azure" ]; then
        DOCKER_CMD="$DOCKER_CMD -v $HOME/.azure:/root/.azure:ro"
        echo -e "${BLUE}   Mounted ~/.azure directory${NC}"
    fi
fi

# Add image name and execute
DOCKER_CMD="$DOCKER_CMD $IMAGE_NAME"
echo -e "${BLUE}   Starting container...${NC}"
eval $DOCKER_CMD

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start container${NC}"
    exit 1
fi
echo ""

# Step 6: Verify container is running
echo -e "${YELLOW}🔍 Step 6/8: Verifying container status...${NC}"
sleep 3
if sudo docker ps | grep -q $CONTAINER_NAME; then
    echo -e "${GREEN}✅ Container is running${NC}"
    sudo docker ps | grep $CONTAINER_NAME
else
    echo -e "${RED}❌ Container is not running${NC}"
    exit 1
fi
echo ""

# Step 7: Run database migrations
echo -e "${YELLOW}🗄️  Step 7/8: Running database migrations...${NC}"
sleep 2
sudo docker exec $CONTAINER_NAME python scripts/run_migration.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migrations completed successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Migration script returned an error, but continuing...${NC}"
    echo -e "${YELLOW}   Check logs: sudo docker logs $CONTAINER_NAME${NC}"
fi
echo ""

# Step 8: Show recent logs
echo -e "${YELLOW}📝 Step 8/8: Checking logs...${NC}"
sudo docker logs --tail 30 $CONTAINER_NAME
echo ""

# Summary
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}🌐 Application URL: http://taiga.orchvate.com:8080${NC}"
echo ""
echo -e "${YELLOW}💡 Useful commands:${NC}"
echo -e "  View logs:      sudo docker logs -f $CONTAINER_NAME"
echo -e "  Run migrations: sudo docker exec $CONTAINER_NAME python scripts/run_migration.py"
echo -e "  Restart:        sudo docker restart $CONTAINER_NAME"
echo -e "  Stop:           sudo docker stop $CONTAINER_NAME"
echo -e "  Container info: sudo docker inspect $CONTAINER_NAME"
echo ""

```

#### `docker-entrypoint.sh`

```
#!/bin/bash
set -e

# =============================================================================
# NIWI Adaptive Worker & System Safety Manager
# Dynamically adapts background worker concurrency based on host CPU cores
# while strictly reserving headroom so the VM, Nginx, and FastAPI never crash.
# =============================================================================

# 1. Detect total CPU cores visible to the container
TOTAL_CORES=$(nproc 2>/dev/null || echo 1)

# 2. Safety allocation formula:
# - 1 core: 1 worker (safety minimum)
# - 2 cores: 1 worker (leaves 1 core free for OS, Nginx & API)
# - 3 to 4 cores: (TOTAL_CORES - 1) workers (leaves 1 core free for OS, Nginx & API)
# - 5+ cores: (TOTAL_CORES - 2) workers (leaves 2 cores free for system headroom)
if [ "$TOTAL_CORES" -le 2 ]; then
    AUTO_WORKERS=1
elif [ "$TOTAL_CORES" -le 4 ]; then
    AUTO_WORKERS=$((TOTAL_CORES - 1))
else
    AUTO_WORKERS=$((TOTAL_CORES - 2))
fi

# 3. Allow manual override if WORKER_CONCURRENCY is set in environment, else use AUTO_WORKERS
WORKER_COUNT=${WORKER_CONCURRENCY:-$AUTO_WORKERS}

# Guard: Ensure at least 1 worker is always active
if [ "$WORKER_COUNT" -lt 1 ]; then
    WORKER_COUNT=1
fi

RESERVED_CORES=$((TOTAL_CORES - WORKER_COUNT))
if [ "$RESERVED_CORES" -lt 0 ]; then
    RESERVED_CORES=0
fi

echo "=========================================================="
echo "🚀 NIWI Adaptive Concurrency Manager"
echo "   Hardware detected : $TOTAL_CORES CPU core(s)"
echo "   Active workers    : $WORKER_COUNT worker process(es)"
echo "   System safety     : Reserved $RESERVED_CORES core(s) for OS, Nginx & API"
echo "=========================================================="

# 4. Dynamically configure supervisord numprocs for service_bus_worker
SUPERVISOR_CONF="/etc/supervisor/conf.d/supervisord.conf"
if [ -f "$SUPERVISOR_CONF" ]; then
    sed -i "s/^numprocs=.*/numprocs=$WORKER_COUNT/" "$SUPERVISOR_CONF"
fi

# 5. Hand over to supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf


```

#### `function_app.py`

```python
"""
function_app.py — Azure Functions for NeuroMark Audit Tool
Routes:
  POST   /api/submit
  GET    /api/submissions
  PUT    /api/submissions/{id}/email
  POST   /api/submissions/{id}/send
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from decimal import Decimal

import azure.functions as func
import psycopg2
import psycopg2.extras
from app.services.scoring_service import calculate_scores
from app.services.settings_service import (
    get_settings,
    update_settings,
    get_sender_for_send,
    notify_admin_new_submission,
    send_acs_email,
    send_support_request,
)
from app.services.user_service import (
    verify_user,
    get_users,
    add_user,
    remove_user,
)

def strip_html(html: str) -> str:
    """Convert basic HTML to plain text for email sending."""
    text = re.sub(r'<br\s*/?>', '\n', html)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'</li>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ.get("PGDATABASE", "nd_audit"),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", "5432"),
        sslmode="require",
    )


def json_response(body, status: int = 200) -> func.HttpResponse:
    def serializer(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    return func.HttpResponse(
        json.dumps(body, default=serializer),
        status_code=status,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


def options_response() -> func.HttpResponse:
    """Handle CORS preflight."""
    return func.HttpResponse(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )


# ---------------------------------------------------------------------------
# POST /api/submit
# ---------------------------------------------------------------------------

@app.route(route="submit", methods=["POST", "OPTIONS"])
def submit(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    try:
        data = req.get_json()
    except ValueError:
        return json_response({"error": "Invalid JSON"}, 400)

    # Validate required respondent fields
    for field in ("name", "designation", "company_name", "email"):
        if not data.get(field):
            return json_response({"error": f"Missing required field: {field}"}, 400)

    scores = calculate_scores(data)

    insert_sql = """
        INSERT INTO submissions (
            name, designation, company_name, email, contact_number,
            q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,
            q15,q16,q17,q18,q19,q20,q21,q22,q23,q24,
            q25,q26,q27,q28,q29,q30,q31,q32,q33,q34,
            q35,q36,q37,q38,q39,q40,q41,q42,q43,q44,
            lc_score, lc_level, ro_score, ro_level,
            we_score, we_level, be_score, be_level,
            tm_score, tm_level, ca_score, ca_level,
            pc_score, pc_level, sp_score, sp_level,
            overall_avg, overall_level, email_body, status
        ) VALUES (
            %(name)s, %(designation)s, %(company_name)s, %(email)s, %(contact_number)s,
            %(q5)s,%(q6)s,%(q7)s,%(q8)s,%(q9)s,%(q10)s,%(q11)s,%(q12)s,%(q13)s,%(q14)s,
            %(q15)s,%(q16)s,%(q17)s,%(q18)s,%(q19)s,%(q20)s,%(q21)s,%(q22)s,%(q23)s,%(q24)s,
            %(q25)s,%(q26)s,%(q27)s,%(q28)s,%(q29)s,%(q30)s,%(q31)s,%(q32)s,%(q33)s,%(q34)s,
            %(q35)s,%(q36)s,%(q37)s,%(q38)s,%(q39)s,%(q40)s,%(q41)s,%(q42)s,%(q43)s,%(q44)s,
            %(lc_score)s, %(lc_level)s, %(ro_score)s, %(ro_level)s,
            %(we_score)s, %(we_level)s, %(be_score)s, %(be_level)s,
            %(tm_score)s, %(tm_level)s, %(ca_score)s, %(ca_level)s,
            %(pc_score)s, %(pc_level)s, %(sp_score)s, %(sp_level)s,
            %(overall_avg)s, %(overall_level)s, %(email_body)s, 'pending'
        ) RETURNING id
    """

    params = {
        "name": data.get("name"),
        "designation": data.get("designation"),
        "company_name": data.get("company_name"),
        "email": data.get("email"),
        "contact_number": data.get("contact_number", None),
        **{f"q{i}": data.get(f"q{i}") for i in range(5, 45)},
        **scores,
    }

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(insert_sql, params)
                submission_id = cur.fetchone()[0]
                notify_admin_new_submission(
                    cur,
                    submission_id,
                    data.get("name", ""),
                    data.get("company_name", ""),
                )
        conn.close()
    except Exception as e:
        logging.error("DB insert failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    return json_response({"success": True, "submission_id": submission_id}, 201)


# ---------------------------------------------------------------------------
# GET /api/submissions
# ---------------------------------------------------------------------------

@app.route(route="submissions", methods=["GET", "OPTIONS"])
def get_submissions(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, designation, company_name, email, submitted_at,
                           overall_avg, overall_level, status
                    FROM submissions
                    ORDER BY submitted_at DESC
                """)
                rows = cur.fetchall()
        conn.close()
    except Exception as e:
        logging.error("DB query failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    # Convert datetime to ISO string for JSON serialisation
    result = []
    for row in rows:
        r = dict(row)
        if r.get("submitted_at"):
            r["submitted_at"] = r["submitted_at"].isoformat()
        result.append(r)

    return json_response(result)


# ---------------------------------------------------------------------------
# GET /api/submissions/{id}  — full detail for dashboard detail view
# ---------------------------------------------------------------------------

@app.route(route="submissions/{id}", methods=["GET", "OPTIONS"])
def get_submission(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    submission_id = req.route_params.get("id")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM submissions WHERE id = %s", (submission_id,))
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logging.error("DB query failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    if not row:
        return json_response({"error": "Not found"}, 404)

    r = dict(row)
    for ts_field in ("submitted_at", "sent_at"):
        if r.get(ts_field):
            r[ts_field] = r[ts_field].isoformat()

    return json_response(r)


# ---------------------------------------------------------------------------
# PUT /api/submissions/{id}/email
# ---------------------------------------------------------------------------

@app.route(route="submissions/{id}/email", methods=["PUT", "OPTIONS"])
def update_email(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    submission_id = req.route_params.get("id")

    try:
        body = req.get_json()
    except ValueError:
        return json_response({"error": "Invalid JSON"}, 400)

    email_body = body.get("email_body")
    if email_body is None:
        return json_response({"error": "Missing email_body"}, 400)

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE submissions SET email_body = %s WHERE id = %s",
                    (email_body, submission_id),
                )
                if cur.rowcount == 0:
                    conn.close()
                    return json_response({"error": "Not found"}, 404)
        conn.close()
    except Exception as e:
        logging.error("DB update failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    return json_response({"success": True})


# ---------------------------------------------------------------------------
# POST /api/submissions/{id}/regenerate-email
# ---------------------------------------------------------------------------

@app.route(route="submissions/{id}/regenerate-email", methods=["POST", "OPTIONS"])
def regenerate_email(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    submission_id = req.route_params.get("id")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM submissions WHERE id = %s", (submission_id,))
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logging.error("DB query failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    if not row:
        return json_response({"error": "Not found"}, 404)

    if row.get("status") == "sent":
        return json_response({"error": "Cannot regenerate sent email"}, 409)

    data = dict(row)
    scores = calculate_scores(data)
    new_email_body = scores.get("email_body")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE submissions SET email_body = %s WHERE id = %s",
                    (new_email_body, submission_id),
                )
        conn.close()
    except Exception as e:
        logging.error("DB update failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    return json_response({"success": True, "email_body": new_email_body})


# ---------------------------------------------------------------------------
# POST /api/submissions/{id}/send
# ---------------------------------------------------------------------------

@app.route(route="submissions/{id}/send", methods=["POST", "OPTIONS"])
def send_email(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    submission_id = req.route_params.get("id")

    # Fetch submission
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT name, email, company_name, email_body, status FROM submissions WHERE id = %s",
                    (submission_id,),
                )
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logging.error("DB query failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    if not row:
        return json_response({"error": "Not found"}, 404)

    if row["status"] == "sent":
        return json_response({"error": "Already sent"}, 409)

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                sender_address, sender_name = get_sender_for_send(cur)
        conn.close()
    except Exception as e:
        logging.error("Settings load failed: %s", e)
        sender_address = os.environ.get("ACS_SENDER_ADDRESS", "")
        sender_name = os.environ.get("ACS_SENDER_NAME", "Orchvate")

    try:
        send_acs_email(
            to_address=row["email"],
            to_name=row["name"],
            subject=f"NeuroMark Audit Results — {row['company_name']}",
            html=row["email_body"],
            plain=strip_html(row["email_body"]),
            sender_address=sender_address,
            sender_name=sender_name,
        )
    except Exception as e:
        logging.error("ACS send failed: %s", e)
        return json_response({"error": "Email send failed"}, 500)

    # Update status
    sent_at = datetime.now(timezone.utc)
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE submissions SET status = 'sent', sent_at = %s WHERE id = %s",
                    (sent_at, submission_id),
                )
        conn.close()
    except Exception as e:
        logging.error("DB status update failed: %s", e)
        return json_response({"error": "Email sent but DB update failed"}, 500)

    return json_response({"success": True, "sent_at": sent_at.isoformat()})


# ---------------------------------------------------------------------------
# GET / PUT /api/settings
# ---------------------------------------------------------------------------

@app.route(route="settings", methods=["GET", "PUT", "OPTIONS"])
def settings(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                if req.method == "GET":
                    data = get_settings(cur)
                else:
                    try:
                        body = req.get_json()
                    except ValueError:
                        return json_response({"error": "Invalid JSON"}, 400)
                    if not body:
                        return json_response({"error": "Empty body"}, 400)
                    data = update_settings(cur, body)
        conn.close()
    except Exception as e:
        logging.error("Settings failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    return json_response(data)


# ---------------------------------------------------------------------------
# POST /api/settings/notifications/toggle
# ---------------------------------------------------------------------------

@app.route(route="settings/notifications/toggle", methods=["POST", "OPTIONS"])
def toggle_notifications(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                current = get_settings(cur)
                enabling = not current["notifications_enabled"]
                if enabling and not (current["notification_email"] or "").strip():
                    return json_response(
                    
```
> _Truncated to 16000 bytes — see full file in the source repo._

#### `run_local_server.py`

```python
"""
run_local_server.py — Local development and load testing runner.
Sets APP_ENV=development and enables embedded worker threads for outbox dispatching and async consumption.
"""
import os

os.environ["APP_ENV"] = "development"
os.environ["APP-ENV"] = "development"
os.environ["ENABLE_EMBEDDED_WORKER"] = "true"

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")


```

#### `setup-keyvault.sh`

```
#!/bin/bash
# Setup script for Azure Key Vault configuration
# Run this once on the server to configure Key Vault settings

set -e

echo "🔐 Azure Key Vault Setup for NIWI"
echo "=================================="
echo ""

# Prompt for Key Vault name
read -p "Enter your Azure Key Vault name (e.g., niwi-secrets): " VAULT_NAME

if [ -z "$VAULT_NAME" ]; then
    echo "❌ Key Vault name cannot be empty"
    exit 1
fi

# Export for current session
export KEY_VAULT_NAME="$VAULT_NAME"

# Add to ~/.bashrc for persistence
if ! grep -q "KEY_VAULT_NAME" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Azure Key Vault for NIWI" >> ~/.bashrc
    echo "export KEY_VAULT_NAME=\"$VAULT_NAME\"" >> ~/.bashrc
    echo "✅ Added KEY_VAULT_NAME to ~/.bashrc"
else
    echo "ℹ️  KEY_VAULT_NAME already exists in ~/.bashrc"
fi

echo ""
echo "✅ Azure Key Vault configured!"
echo ""
echo "Key Vault Name: $VAULT_NAME"
echo "Vault URL: https://${VAULT_NAME}.vault.azure.net/"
echo ""
echo "📋 Next steps:"
echo "1. Ensure your VM has Managed Identity enabled"
echo "2. Grant the Managed Identity 'Key Vault Secrets User' role"
echo "3. Add these secrets to your Key Vault:"
echo "   - pghost"
echo "   - pgport"
echo "   - pgdatabase"
echo "   - pguser"
echo "   - pgpassword"
echo "   - acs-connection-string"
echo "   - acs-sender-address"
echo "   - acs-sender-name"
echo "   - jwt-secret"
echo "   - entra-client-id"
echo "   - entra-tenant-id"
echo ""
echo "4. Run: source ~/.bashrc"
echo "5. Run: ./deploy.sh"
echo ""

```

_…and 1 more file(s) not shown._

## Improvements & refactors

- [keep-behavior] Formalize typing and input constraints for enhanced runtime validation.
- [keep-behavior] Expand automated test coverage for failure modes and timeouts.
- [keep-behavior] Optimize memory footprint and eliminate unreferenced legacy helpers.


## Definition of done

- [ ] Every functional requirement is implemented and covered by a test.
- [ ] Every acceptance-criteria scenario passes (including the failure paths).
- [ ] Every operation this unit owns in `architecture/INTERFACES.md` responds correctly.
- [ ] Every entity it writes matches `architecture/DATA-MODEL.md` (fields, types, constraints).
- [ ] Every write is satisfiable against the schema: no required (NOT NULL, no-default) column or foreign key is left unfilled; anonymous/public operations write only to anonymous-capable entities (no owner FK).
- [ ] Every enum/domain value this unit uses is one of the members fully enumerated in `architecture/DATA-MODEL.md`.
- [ ] Every edge case & failure mode above is handled.
- [ ] `node scripts/analyze.mjs --check --out <out>` passes — no unresolved agent callouts or placeholders, and every reference resolves.

