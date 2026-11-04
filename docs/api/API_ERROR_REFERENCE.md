# NIWI — Centralized API Error Reference & Troubleshooting Guide

This document defines all HTTP status codes, error response structures, exception paths, database error states, and troubleshooting remediation procedures across the NIWI platform.

---

## 1. Standard Error Envelope Structure

NIWI returns errors formatted according to modern REST standards using RFC 7807 problem details or standard FastAPI JSON error envelopes:

### Standard Error Schema (`detail` format)
```json
{
  "detail": "Error description message"
}
```

### Validation Error Schema (`422 Unprocessable Entity`)
```json
{
  "detail": [
    {
      "type": "value_error.missing",
      "loc": ["body", "email"],
      "msg": "field required",
      "input": {}
    }
  ]
}
```

### Rate Limiter Error Schema (`429 Too Many Requests`)
```json
{
  "error": "Rate limit exceeded: 100 per 1 hour"
}
```

---

## 2. HTTP Status Code Catalog & Application Mappings

| HTTP Status | Category | When Triggered in NIWI | Typical Detail Message |
| :---: | :--- | :--- | :--- |
| **`400`** | Bad Request | Schema syntax failure, missing required query/path parameters, invalid invitation token, invalid score values ($<0$ or $>20$). | `"Organisation name is required."`<br>`"Score lc_score must be between 0 and 20"`<br>`"Invalid invitation link."` |
| **`401`** | Unauthorized | Missing, expired, or rejected Microsoft Entra ID JWT; invalid token signature; missing `kid` in JWKS cache; missing magic link token. | `"Missing or invalid Authorization header"`<br>`"Invalid token kid"`<br>`"Token expired"` |
| **`403`** | Forbidden | Valid Entra ID user not enrolled in `admin_users` table, or standard `admin` attempting `super` privileged operation. | `"Forbidden: You are not an authorized administrator"`<br>`"Super admin privileges required"` |
| **`404`** | Not Found | Submission UUID, organisation UUID, invitation token, or saved filter ID does not exist in PostgreSQL. | `"Not found"`<br>`"Saved filter not found or cannot be deleted"` |
| **`409`** | Conflict | Concurrent conflict or duplicate action on non-idempotent transition (e.g. attempting to dispatch an email already sent). | `"Already sent or sending"`<br>`"Organisation with this name already exists"` |
| **`422`** | Unprocessable Entity | Pydantic validation failure: malformed email format, invalid enum, non-numeric question values, or bad types. | `{"detail": [{"loc": ["body", "email"], "msg": "value is not a valid email address"}]}` |
| **`429`** | Too Many Requests | SlowAPI IP rate limit exceeded, or 5-minute respondent duplicate email submission guard. | `"Rate limit exceeded: 100 per 1 hour"`<br>`"A submission from this email was received recently. Please wait a few minutes before submitting again."` |
| **`500`** | Internal Server Error | Database connection pool exhaustion, PostgreSQL statement timeout, unhandled runtime exception, or Key Vault failure. | `"Database error"`<br>`"Internal Server Error"` |
| **`503`** | Service Unavailable | Container health check failure: PostgreSQL database unreachable or Azure Communication Services down. | `{"version": "2.1", "database": "down", "acs": "up"}` |

---

## 3. Detailed Error Dictionary & Remediation

### 3.1 Authentication & Authorization Errors

#### ERR-AUTH-001: Missing or Invalid Authorization Header
* **HTTP Code:** `401 Unauthorized`
* **Message:** `{"detail": "Missing or invalid Authorization header"}`
* **Origin:** [`Audit/app/core/security.py:129`](file:///home/aakash.padyachi/apps/niwi/Audit/app/core/security.py#L129) (`jwks_middleware`)
* **Root Cause:** A request to a protected administrative endpoint (`/api/manage/*`, `/api/settings/*`, `/api/submissions/*`) was made without an `Authorization: Bearer <token>` header.
* **Resolution:** Ensure the client obtains an ID token from Microsoft MSAL and includes `Authorization: Bearer <idToken>`.

#### ERR-AUTH-002: Invalid Token Key ID (`kid`)
* **HTTP Code:** `401 Unauthorized`
* **Message:** `{"detail": "Invalid token kid"}`
* **Origin:** [`Audit/app/core/security.py:63`](file:///home/aakash.padyachi/apps/niwi/Audit/app/core/security.py#L63) (`verify_jwt`)
* **Root Cause:**
  1. The token was issued by a different Microsoft Entra ID tenant than the one configured in Azure Key Vault (`ENTRA_TENANT_ID`).
  2. Microsoft rotated signing keys and the local 1-hour `_jwks_cache` contains stale keys.
* **Resolution:** Invalidate the JWKS cache or check that `ENTRA_TENANT_ID` and `ENTRA_CLIENT_ID` match the Azure App Registration.

#### ERR-AUTH-003: Unenrolled Administrator Email
* **HTTP Code:** `403 Forbidden`
* **Message:** `{"detail": "Forbidden: You are not an authorized administrator"}`
* **Origin:** [`Audit/app/core/security.py:188`](file:///home/aakash.padyachi/apps/niwi/Audit/app/core/security.py#L188)
* **Root Cause:** Microsoft authenticated the user successfully, but their email address does not exist in the platform's `admin_users` PostgreSQL table.
* **Resolution:** A Super Administrator must enroll the email via `POST /api/manage/users`.

#### ERR-AUTH-004: Super Admin Privileges Required
* **HTTP Code:** `403 Forbidden`
* **Message:** `{"detail": "Super admin privileges required"}`
* **Origin:** [`Audit/app/core/authorization.py:34`](file:///home/aakash.padyachi/apps/niwi/Audit/app/core/authorization.py#L34) (`require_super_admin`)
* **Root Cause:** A user with role `admin` attempted to access super-admin-only endpoints: `/api/manage/users` or `/api/settings/delete-all-records`.
* **Resolution:** Only users with `role = 'super'` can provision users or purge data.

---

### 3.2 Submission & Assessment Errors

#### ERR-SUB-001: Duplicate Submission Within Cooldown Window
* **HTTP Code:** `429 Too Many Requests`
* **Message:** `{"detail": "A submission from this email was received recently. Please wait a few minutes before submitting again."}`
* **Origin:** [`Audit/app/api/routes.py:152`](file:///home/aakash.padyachi/apps/niwi/Audit/app/api/routes.py#L152) (`submit`)
* **Root Cause:** The respondent email already submitted an assessment within the last 5 minutes (`submitted_at > NOW() - INTERVAL '5 minutes'`).
* **Resolution:** Wait 5 minutes before submitting again, or use unique email addresses during automated load testing.

#### ERR-SUB-002: Invalid or Inactive Organisation Invitation Link
* **HTTP Code:** `400 Bad Request`
* **Message:** `{"detail": "This invitation link has expired."}` / `"This invitation has reached its submission limit."`
* **Origin:** [`Audit/app/api/routes.py:184-195`](file:///home/aakash.padyachi/apps/niwi/Audit/app/api/routes.py#L184-L195)
* **Root Cause:** The invitation token has expired (`expires_at < NOW()`), been revoked (`is_active = FALSE`), or exceeded its allocation (`submission_count >= max_submissions`).
* **Resolution:** Generate a fresh invitation campaign link via `POST /api/manage/orgs/{org_id}/invitations`.

---

### 3.3 Database & Concurrency Errors

#### ERR-DB-001: Connection Pool Exhaustion
* **HTTP Code:** `500 Internal Server Error` (Logs: `ERROR: Database connection pool exhausted`)
* **Origin:** [`Audit/app/core/database.py:119`](file:///home/aakash.padyachi/apps/niwi/Audit/app/core/database.py#L119) (`get_conn`)
* **Root Cause:** More than 10 concurrent requests hit a single Uvicorn worker process while connections were active. Psycopg2 `ThreadedConnectionPool.getconn()` raises `PoolError` immediately with zero wait queue.
* **Resolution:**
  1. Verify warm-cache hits on `/api/form/sections` (Finding 1 fix).
  2. Verify that long-running operations are offloaded to background workers.
  3. Inspect real-time metrics via `GET /api/health/pool-metrics`.

#### ERR-DB-002: PostgreSQL Statement Timeout
* **HTTP Code:** `500 Internal Server Error` (Logs: `QueryCanceled: canceling statement due to statement timeout`)
* **Origin:** PostgreSQL connection session parameter (`statement_timeout = 15000` / 15 seconds)
* **Root Cause:** A query took longer than 15 seconds to execute, typically caused by lock contention on `pg_advisory_xact_lock` or unindexed joins.
* **Resolution:** Check active locks via `pg_stat_activity` and verify that transactions commit in $< 25\text{ ms}$.

