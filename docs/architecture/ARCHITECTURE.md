# Architecture

| Setting | Value |
| --- | --- |
| Mode | `preserve` |
| Level | `complex` |
| Fidelity | `embed` |
| Generated with | `reconstruct@2.29.16` |

## Detected stack

FastAPI · Python 3.11+ · Vue 3 · Vite · PostgreSQL 14+

**Libraries:** Playwright, Psycopg2-binary, PyJWT, SlowAPI, Pydantic, Axios, Pinia

## Top-level layout

- `.github/` — GitHub Actions workflows for continuous integration and automated testing.
- `app/` — FastAPI application root:
  - `core/` — Database connection pooling, JWT security middleware, Key Vault integration, settings, rate limiting, and exception handlers.
  - `api/` — HTTP routers for submissions, organizations, public resolution, drafts, form builder, and administration.
  - `models/` — Pydantic request/response schemas and domain models.
  - `services/` — Business logic: scoring calculations, outbox transactions, organization aggregation, email dispatch, and cache management.
  - `tasks/` — Background daemons: outbox dispatcher and worker loop.
  - `utils/` — Helper functions for CSV generation, email formatting, token generation, and input validation.
  - `main.py` — Application entry point, CORS configuration, middleware assembly, and health checks.
- `frontend/` — Vue 3 Single Page Application:
  - `src/` — Components, views, router configuration, Pinia state stores, and unified CSS design system (`style.css`).
  - `vite.config.js` — Vite build and dev server configuration.
- `infrastructure/` — Infrastructure deployment scripts, Nginx configurations, and Azure VM setup runbooks.
- `migrations/` — 22 numbered SQL migration files establishing database schemas, constraints, and performance indexes.
- `scripts/` — Database setup, test runner, synthetic audit ingestion, and reconciliation utilities.
- `sql/` — Standalone DDL definitions and administrative notification/support schemas.
- `tests/` — Comprehensive test suite covering unit tests, API tests, security verification, and concurrency testing.
- root files: `.dockerignore`, `.env.example`, `.gitignore`, `Dockerfile`, `README.md`, `deploy.sh`, `docker-compose.yml`, `docker-entrypoint.sh`, `function_app.py`, `host.json`, `nginx.conf`, `package.json`, `pytest.ini`, `requirements.txt`, `run_local_server.py`, `setup-keyvault.sh`, `supervisord.conf`.

## Dependencies

- **npm** (`package.json`): Vue 3, Vite, Vue Router, Pinia, Axios, Lucide Icons.
- **pip** (`requirements.txt`): FastAPI (0.104+), Uvicorn (0.24+), Psycopg2-binary (2.9+), PyJWT (2.8+), Cryptography, SlowAPI, Pydantic, Python-dotenv, Azure-identity, Azure-keyvault-secrets, Azure-communication-email.

## Data & schema

- `app/models/__init__.py`
- `app/models/audit.py`
- `app/models/form_builder.py`
- `app/models/user.py`
- `migrations/002_app_settings.sql`
- `migrations/003_support_email.sql`
- `migrations/004_designation.sql`
- `migrations/005_rbac.sql`
- `migrations/006_org_scoring.sql`
- `migrations/007_fix_score_columns.sql`
- `migrations/008_dynamic_forms.sql`
- `migrations/009_question_dependencies.sql`
- `migrations/010_saved_filters.sql`
- `migrations/011_verify_submission_id_type.sql`
- `migrations/012_dual_entry_invitations.sql`
- `migrations/013_organization_admins.sql`
- `migrations/014_submission_reassignments.sql`
- `migrations/015_performance_jobs_and_idempotency.sql`
- `migrations/016_service_bus_outbox.sql`
- `migrations/017_per_operation_idempotency.sql`
- `migrations/018_assessment_access_tokens.sql`
- `migrations/019_system_security_settings.sql`
- `migrations/01_remediation.sql`
- `migrations/020_raw_submissions_and_dlq.sql`
- `migrations/021_super_admin_dashboard_and_workers.sql`
- `migrations/022_performance_indexes.sql`
- `migrations/02_features_migration.sql`
- `sql/01_admin_notifications.sql`
- `sql/02_support_requests.sql`
- `sql/archive/create_table.sql`
- `sql/archive/fix_missing_columns.sql`
- `sql/archive/install_all.sql`

## Internationalization

_No multi-language i18n required; English (en-US) default._

## External services & integrations

1. **Microsoft Entra ID (Azure Active Directory OIDC / JWKS):**
   - **Provider:** Microsoft Azure Identity.
   - **Protocol & Shape:** OpenID Connect (OIDC) Bearer Tokens (RS256). Backend fetches signing keys from `https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys`.
   - **Timeout:** 5 seconds connect/read timeout with an in-memory `TTLCache` (1 hour TTL) caching public keys.
   - **Failure Behavior:** If JWKS fails to refresh and key is not cached, protected endpoints return `HTTP 401 Unauthorized` with `{"detail": "Unable to verify authentication credentials"}`.

2. **Azure Key Vault (`kv-niwi-prod`):**
   - **Provider:** Azure Key Vault via `DefaultAzureCredential` / System-Assigned Managed Identity.
   - **Purpose:** Secure retrieval of database passwords, API signing secrets, and external integration tokens at service startup.
   - **Timeout:** 10 seconds timeout.
   - **Failure Behavior:** Fallback to local `.env` environment variables when running in local development mode (`ENVIRONMENT=development`). In production (`ENVIRONMENT=production`), boot halts immediately to prevent credential leaks.

3. **Azure Communication Services (Transactional Email):**
   - **Provider:** Azure Communication Services Email SDK.
   - **Purpose:** Asynchronous delivery of audit assessment results, benchmark summaries, and organization invitation links (`donotreply@orchvate.in`).
   - **Contract:** Dispatches HTML email payloads containing audit score cards, pillar breakdowns, and recommendations.
   - **Timeout:** 15 seconds network timeout.
   - **Failure Behavior:** Executed asynchronously inside `service_bus_worker.py`. On network error, messages increment `retry_count` in `submission_operation_states` up to 3 times with exponential backoff (30s, 120s, 300s). Failures beyond max retries transition to dead-letter queue (`status='failed'`) without failing respondent HTTP requests.

4. **HubSpot CRM (Lead Synchronization):**
   - **Provider:** HubSpot REST API v3.
   - **Purpose:** Synchronize completed audit lead contact information and corporate domain names for prospective client follow-up.
   - **Timeout:** 5 seconds timeout.
   - **Failure Behavior:** Best-effort asynchronous execution. Any HTTP 4xx/5xx from HubSpot is logged as a non-blocking warning and does not impact survey persistence or respondent feedback.

5. **Azure PostgreSQL Flexible Server (`nd_audit`):**
   - **Provider:** Managed PostgreSQL 14+ with SSL enforcement (TLS 1.2+).
   - **Connection Pool:** `ThreadedConnectionPool` configured with min=5, max=25 connections, `statement_timeout=15000` (15 seconds), and TCP keepalives.
   - **Failure Behavior:** Transient disconnects trigger retry loop up to 3 attempts with connection recycle. Unrecoverable outages return `HTTP 503 Service Unavailable`.

## Cross-cutting policies

1. **Rate Limiting (SlowAPI):**
   - **Engine:** SlowAPI memory/redis limiter keyed on client IP address (`get_remote_address`).
   - **Policies:**
     - Public assessment submission (`POST /api/submit`): `10/minute`.
     - Authentication verification (`POST /api/auth/verify`): `5/minute`.
     - Draft auto-save (`POST /api/drafts/save`): `30/minute`.
     - General authenticated administrative reads: `120/minute`.
     - Public organization validation: `60/minute`.
   - **Response on Exceeded:** `HTTP 429 Too Many Requests` with `Retry-After` header.

2. **Security & Ingress Headers:**
   - **CORS:** Restricted to explicitly configured origins in `ALLOWED_ORIGINS` (e.g., `https://niwi.orchvate.in`, `http://localhost:5173`). Credentials permitted (`allow_credentials=True`).
   - **HTTP Headers:** Injected by Nginx reverse proxy:
     - `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com;`
     - `X-Frame-Options: DENY`
     - `X-Content-Type-Options: nosniff`
     - `Strict-Transport-Security: max-age=31536000; includeSubDomains`

3. **Authentication & Authorization (RBAC):**
   - Two administrator tiers stored in `admin_users`:
     - `admin` (Organization Admin): Can view submissions, access analytics, configure invited organizations, re-trigger reports.
     - `super` (Super Admin): Exclusive access to user management, deleting all records, replaying dead-lettered outbox queues, and modifying global security parameters.
   - Dev Bypass Protection: Code explicitly verifies `ENABLE_DEV_BYPASS` is strictly disabled if `ENVIRONMENT=production`.

4. **Survey Submission Validation & Ingestion Contract:**
   - Assessment requires exactly 4 demographic inputs: Organization Name, Respondent Role/Designation, Department, and Email (optional for 100% anonymous mode).
   - Exactly 40 Likert scale question inputs (values 1–5 inclusive).
   - Client sends unique UUID in `Idempotency-Key` HTTP header. Database enforces uniqueness in `raw_submissions.idempotency_key` via `ON CONFLICT DO NOTHING`.
   - Ingestion acknowledgement SLA: `< 25ms` returning `HTTP 202 Accepted` with `submission_id`.

## Reconstruction guidance (preserve)

Reproduce the structure above as-is. Keep the same directory layout, framework, routing strategy, and data layer.

### Recommended Architectural Improvements:
1. **Frontend Modernization:** Progressively introduce TypeScript typing into Vue 3 Pinia stores and component props to guarantee runtime type safety across all 40 question models.
2. **Database Migration Tooling:** Wrap raw SQL migrations with an Alembic or Flyway runner to allow bidirectional rollback capabilities and migration checksum validation in automated CI pipelines.
3. **Structured Distributed Tracing:** Instrument FastAPI endpoints and background worker tasks with OpenTelemetry SDK and Azure Application Insights for end-to-end request tracing and latency waterfall analysis.
4. **Queue Decoupling:** When throughput exceeds 10,000 daily submissions, transition PostgreSQL transactional outbox table polling to native Azure Service Bus queues while maintaining the existing idempotent message consumer interface.
