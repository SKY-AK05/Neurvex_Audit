# QA & Security Validation Report

| # | Fix Name | Status | Evidence | Gap Description |
|---|----------|--------|----------|-----------------|
| 1 | SQL Injection | PASS | `app/models/audit.py` contains `AuditSubmission` with regex validations. `app/api/routes.py` uses `%s` psycopg2 parameters and Pydantic validation. | None. |
| 2 | JWT Middleware | PASS | `app/core/security.py` has `jwks_middleware` verifying Entra ID JWKS. Applied in `app/main.py`. Intercepts all backend admin paths (`/api/manage`, `/api/settings`, `/api/submissions`). | None. |
| 3 | Rate Limiting | **FAIL** | `slowapi` is configured in `app/core/limiter.py` and `app/main.py`. However, the limit applied to `/api/submit` in `app/api/routes.py` is `"5/minute"`. | The requested limit was `5 per IP per hour`. Currently configured as `5/minute`. |
| 4 | XSS Prevention | PASS | No `v-html` found in `frontend/src/views/AuditForm.vue` or other components. CSP headers added in `app/main.py` blocking inline scripts. | None. |
| 5 | IDOR and UUID Migration | **PARTIAL** | `migrations/01_remediation.sql` creates `UUIDv4` columns. Vue router maps `[0-9a-fA-F]{8}-...` in `frontend/src/router/index.js`. FastAPI endpoints accept `UUID`. | **FAIL:** The `/api/submissions/{id}` route does not enforce ownership checks. Any admin with a valid JWT can access any submission UUID. |
| 6 | GDPR Consent | PASS | `frontend/src/views/AuditForm.vue` requires `consent_given`. `AuditSubmission` model requires it. `01_remediation.sql` adds the columns. | None. |
| 7 | PgBouncer | **PARTIAL** | `infrastructure/pgbouncer.ini` and `userlist.txt` created. | Azure CLI command to update `DATABASE_URL` is documented but requires manual execution against the Azure Container App. |
| 8 | Email Retry Logic | PASS | `send_acs_email_with_retry` in `app/api/routes.py` implements `[1, 4, 16]` backoff. `app/tasks/email_worker.py` loops over `email_dlq` table. | None. |
| 9 | Health Endpoint | PASS | `GET /api/health` in `app/main.py` checks DB via `SELECT 1` and ACS via `EmailClient`. | Azure Container Apps probe command requires manual execution. |
| 10 | Admin Audit Logs | PASS | `audit_logs` created in `01_remediation.sql`. `@audit_log` decorator used on all state-changing endpoints in `app/api/routes.py`. | None. |
| 11 | Database Indexes | PASS | Indexes for `status`, `submitted_at`, and `email` added to `migrations/01_remediation.sql`. | None. |
| 12 | Async Email | **PARTIAL** | `process_email_dispatch` uses `BackgroundTasks` in `/submissions/{submission_id}/send`. | The framework asks if `/api/submit` returns before the email is sent. The email logic lives in `/send`, not `/submit`, so technically it passes the intent but fails the exact verbiage of the test case. |

### Summary Count
**8 of 12 fixes PASSED** (4 PARTIAL/FAIL)

### Remediation Still Needed
1. **Fix 3 (Rate Limiting):** Change `@limiter.limit("5/minute")` to `@limiter.limit("5/hour")` on the `/api/submit` endpoint in `app/api/routes.py`.
2. **Fix 5 (IDOR and UUID Migration):** Add an ownership check in `GET /api/submissions/{submission_id}` to verify the requesting admin's tenant/ID matches the submission's owner.
3. **Fix 7 (PgBouncer):** Execute the Azure CLI command to update the container's `DATABASE_URL`.
4. **Fix 12 (Async Email):** Verify if email sending needs to occur during `/api/submit` or if it is correctly intended to remain in `/submissions/{submission_id}/send`.

### Overall Security Clearance Verdict
**NOT CLEARED**
**Blockers:** IDOR vulnerability in `/api/submissions/{id}` due to lack of ownership validation. Rate limiting configuration is too loose (`5/minute` instead of `5/hour`).
