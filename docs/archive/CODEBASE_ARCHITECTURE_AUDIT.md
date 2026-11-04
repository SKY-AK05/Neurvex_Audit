# NIWI — Codebase Architecture Audit Report

**Date**: November 4, 2026  
**Repository**: NIWI (Neurodiversity Inclusion Workplace Index)  
**Original Commit**: `57a4e92e4ba0b52acbe18e6b428400c24707ba2f`  
**Branch**: `maintenance/niwi-codebase-cleanup`

---

## Executive Summary

This document provides a comprehensive audit of the NIWI application architecture, identifying all active production components, their dependencies, and their purposes. This audit was performed as the foundation for Phase 1 codebase cleanup to establish a clean, understandable, maintainable codebase.

### Key Findings

- **Backend**: 8 API routers, 14 services, 3 background workers, fully functional FastAPI application
- **Frontend**: Vue 3 SPA with 17 views, 6 components, complete MSAL authentication integration
- **Database**: 21 migrations (002-019 + 2 feature migrations), ThreadedConnectionPool architecture
- **Infrastructure**: Multi-stage Docker build, Supervisor process management, Nginx reverse proxy
- **Documentation**: 120+ markdown files across multiple directories (significant consolidation opportunity)
- **Performance Reports**: 100+ JSON/MD performance test reports (needs archival strategy)

---

## 1. Complete Application Architecture

### 1.1 System Overview

NIWI is a production enterprise audit platform deployed as a containerized application on Azure Container Apps. The architecture consists of:

```
┌──────────────────────────────────────────────────────────────┐
│                      Azure Container                          │
│                                                               │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │   Nginx    │→ │   Uvicorn    │  │  Outbox Dispatcher │  │
│  │   (Port 80)│  │   (2 workers)│  │                    │  │
│  └────────────┘  └──────────────┘  └────────────────────┘  │
│                                                               │
│                  ┌────────────────────┐                      │
│                  │ Service Bus Worker │                       │
│                  └────────────────────┘                      │
└──────────────────────────────────────────────────────────────┘
         ↓                    ↓                      ↓
    ┌────────┐         ┌───────────┐        ┌──────────────┐
    │  Vue 3 │         │PostgreSQL │        │ Azure Service│
    │  SPA   │         │ Flexible  │        │     Bus      │
    │ Assets │         │  Server   │        └──────────────┘
    └────────┘         └───────────┘
```

**Process Management**: Supervisor runs 4 concurrent processes:
1. **nginx**: Reverse proxy (port 80) - routes `/api/` to uvicorn, serves static assets
2. **uvicorn**: FastAPI backend (2 workers on port 8000)
3. **outbox_dispatcher**: Polls `service_bus_outbox` table and dispatches to Azure Service Bus
4. **service_bus_worker**: Consumes messages from Azure Service Bus submission queue

---

## 2. Backend Architecture

### 2.1 Application Entry Point

**File**: `app/main.py`

**Responsibilities**:
- FastAPI application initialization
- Middleware registration (CORS, JWKS, CSP security headers)
- Database connection pool initialization (10 min, 10 max per worker = 20 total)
- Organization cache warming and scheduled refresh (30-minute intervals)
- API router registration
- Health check endpoints
- Lifecycle management (startup/shutdown)

**Key Middleware Stack** (execution order):
1. CORS middleware (local dev only)
2. JWKS JWT validation middleware (`app/core/security.py`)
3. CSP security headers middleware
4. SlowAPI rate limiting

### 2.2 API Routers

All routers are registered under `/api` prefix. Complete endpoint inventory:

#### Router: `app/api/routes.py` (Main Router)
**Endpoints**:
- `POST /api/submit` - Primary audit submission endpoint (rate limited)
- `GET /api/submissions` - List all submissions (admin auth)
- `GET /api/submissions/{id}` - Get single submission detail (admin auth)
- `PUT /api/submissions/{id}` - Update submission fields (admin auth)
- `POST /api/submissions/{id}/send` - Send assessment report email (admin auth)
- `POST /api/submissions/{id}/reassign` - Reassign submission to different org (admin auth)
- `DELETE /api/submissions/{id}` - Delete single submission (super admin)
- `POST /api/submissions/query` - Advanced filtered query with dynamic filter builder (admin auth)
- `GET /api/reports/{id}` - Generate PDF report (admin auth)
- `GET /api/analytics/benchmark` - Benchmark analytics (admin auth)
- `GET /api/analytics/trends` - Trend analytics (admin auth)

#### Router: `app/api/drafts.py`
**Endpoints**:
- `POST /api/drafts` - Save draft submission with JWT token
- `GET /api/drafts/{token}` - Resume draft by token
- `PUT /api/drafts/{token}` - Update existing draft

#### Router: `app/api/org.py` (Organization Public API)
**Endpoints**:
- `POST /api/org/register` - Register new organization
- `POST /api/org/send-magic-link` - Send magic link for org member login
- `POST /api/org/verify-magic-link` - Verify magic link token
- `POST /api/org/members/{id}/remove` - Remove org member

#### Router: `app/api/orgs.py` (Organization Management - Admin)
**Endpoints**:
- `GET /api/manage/orgs` - List all organizations (admin auth)
- `POST /api/manage/orgs` - Create organization (admin auth)
- `GET /api/manage/orgs/{id}` - Get organization details (admin auth)
- `PUT /api/manage/orgs/{id}` - Update organization (admin auth)
- `DELETE /api/manage/orgs/{id}` - Soft-delete organization (admin auth)
- `POST /api/manage/orgs/{id}/restore` - Restore soft-deleted org (admin auth)
- `POST /api/manage/orgs/{id}/invitations` - Create invitation token (admin auth)
- `GET /api/manage/orgs/{id}/invitations` - List invitations (admin auth)
- `PUT /api/manage/orgs/{id}/invitations/{inv_id}` - Update invitation (admin auth)
- `DELETE /api/manage/orgs/{id}/invitations/{inv_id}` - Revoke invitation (admin auth)
- `GET /api/manage/orgs/{id}/submissions` - Get org submissions (admin auth)
- `POST /api/manage/orgs/{id}/access-tokens` - Create secure assessment token (admin auth)
- `GET /api/manage/orgs/{id}/access-tokens` - List access tokens (admin auth)
- `PUT /api/manage/orgs/{id}/access-tokens/{token_id}` - Update token (admin auth)
- `DELETE /api/manage/orgs/{id}/access-tokens/{token_id}` - Revoke token (admin auth)

#### Router: `app/api/public.py`
**Endpoints**:
- `GET /api/public/health` - Public health check
- `POST /api/support` - Submit support request
- `POST /api/book-call` - Book consultation call

#### Router: `app/api/form_builder.py`
**Endpoints**:
- `GET /api/form/questions` - Get all form questions
- `POST /api/form/questions` - Create custom question (admin auth)
- `PUT /api/form/questions/{id}` - Update question (admin auth)
- `DELETE /api/form/questions/{id}` - Delete question (admin auth)
- `GET /api/form/sections` - Get form section metadata

#### Router: `app/api/auth.py`
**Endpoints**:
- `POST /api/auth/verify` - Verify admin JWT from Entra ID
- `GET /api/auth/config` - Get MSAL configuration for frontend

### 2.3 Services Layer

**Location**: `app/services/`

| Service File | Purpose | Production Critical |
|---|---|---|
| `audit_service.py` | Email body generation, audit report HTML rendering | ✅ Yes |
| `scoring_service.py` | Score calculation (CALC-001 through CALC-006), maturity level determination | ✅ Yes |
| `org_cache_service.py` | In-memory TTL cache for organization lookups (<10ms), scheduled refresh every 30min | ✅ Yes |
| `org_scoring_service.py` | Organization-level aggregate scoring | ✅ Yes |
| `filter_service.py` | Dynamic SQL query builder with whitelist validation | ✅ Yes |
| `token_service.py` | Secure assessment token generation and validation | ✅ Yes |
| `email_policy_service.py` | Corporate email validation, disposable domain blocking | ✅ Yes |
| `rate_limit_service.py` | Dynamic rate limit calculation based on traffic classification | ✅ Yes |
| `outbox_service.py` | Transactional outbox dispatcher (runs as standalone process) | ✅ Yes |
| `user_service.py` | Admin user CRUD, super admin safeguards | ✅ Yes |
| `settings_service.py` | Application settings persistence | ✅ Yes |
| `crm_service.py` | HubSpot CRM synchronization | ✅ Yes (optional feature) |
| `ai_service.py` | AI-powered features | ⚠️ Needs review |

### 2.4 Background Workers

#### Worker 1: Outbox Dispatcher (`app/services/outbox_service.py`)
**Process**: Standalone Python process managed by Supervisor  
**Purpose**: Polls `service_bus_outbox` table using `SELECT ... FOR UPDATE SKIP LOCKED`, dispatches events to Azure Service Bus  
**Execution**: Continuous polling loop with exponential backoff  
**Dependencies**: `app/core/service_bus.py`, `app/core/database.py`

#### Worker 2: Service Bus Consumer (`app/tasks/service_bus_worker.py`)
**Process**: Standalone Python process managed by Supervisor  
**Purpose**: Consumes `SUBMISSION_CREATED` events from Azure Service Bus submission queue  
**Execution**: Long-running receiver with message settling (complete/abandon/dead-letter)  
**Operations**: Triggers report generation, email delivery (manual), CRM sync (if enabled)

#### Worker 3: Job Worker (`app/tasks/job_worker.py`)
**Process**: Optional embedded asyncio task (disabled in production)  
**Purpose**: Legacy background job processor  
**Status**: **UNUSED IN PRODUCTION** (ENABLE_EMBEDDED_WORKER=false)  
**Recommendation**: **CANDIDATE FOR REMOVAL** - superseded by Service Bus architecture

### 2.5 Core Infrastructure

**Location**: `app/core/`

| Module | Purpose | Dependencies |
|---|---|---|
| `config.py` | Environment configuration, password validation | dotenv |
| `database.py` | ThreadedConnectionPool (10 min, 10 max per worker), connection lifecycle, test isolation guard | psycopg2 |
| `security.py` | Entra ID JWKS verification, dev bypass (dev/test only), JWT validation | PyJWT, requests |
| `authorization.py` | Two-role RBAC (normal admin, super admin) | security.py |
| `keyvault.py` | Azure Key Vault client with fail-safe production startup | azure-keyvault-secrets |
| `service_bus.py` | Azure Service Bus publisher/subscriber | azure-servicebus |
| `limiter.py` | SlowAPI rate limiter instance | slowapi |

### 2.6 Data Models

**Location**: `app/models/`

| Module | Purpose |
|---|---|
| `audit.py` | Pydantic schemas for submissions, responses, reports |
| `form_builder.py` | Schemas for dynamic form questions and dependencies |
| `user.py` | Admin user and authentication schemas |

---

## 3. Frontend Architecture

### 3.1 Vue 3 Application Structure

**Entry Point**: `frontend/src/main.js`

**Initialization Flow**:
1. MSAL instance initialization (`@azure/msal-browser`)
2. Handle OAuth redirect callback
3. Complete admin login verification (checks `admin_users` table)
4. Mount Vue application
5. Router navigation

**Build Tool**: Vite 5  
**TypeScript**: 5.3  
**Styling**: Tailwind CSS 3.4

### 3.2 Router Configuration

**File**: `frontend/src/router/index.js`

**Total Routes**: 20+

| Route Path | Component | Auth Required | Purpose |
|---|---|---|---|
| `/` | AuditForm.vue | Public | Primary assessment form |
| `/audit` | AuditForm.vue | Public | Assessment with optional invitation token |
| `/book-a-call` | BookCall.vue | Public | Consultation booking |
| `/portal`, `/GPadmin`, `/admin` | AdminLogin.vue | Public | Admin authentication entry |
| `/admin/dashboard` | Overview.vue | Admin | Main admin dashboard |
| `/admin/submissions` | Submissions.vue | Admin | Submissions list with filters |
| `/admin/submissions/:id` | SubmissionDetail.vue | Admin | Single submission detail view |
| `/admin/analytics` | Analytics.vue | Admin | Analytics and benchmarking |
| `/admin/settings` | Settings.vue | Admin | Application settings |
| `/admin/support` | Support.vue | Admin | Support ticket management |
| `/admin/users` | UserManagement.vue | Super Admin | User management |
| `/admin/organisations` | Organisations.vue | Admin | Organization management |
| `/admin/form-builder` | FormBuilder.vue | Admin | Dynamic form configuration |
| `/invite/:token` | AuditForm.vue | Public | Invitation-based submission |
| `/resume` | ResumeDraft.vue | Public | Resume draft by magic link |
| `/org/login` | OrgLogin.vue | Public | Org member login |
| `/org/verify` | OrgVerify.vue | Public | Org member verification |
| `/org/dashboard` | OrgDashboard.vue | Org Member | Organization member dashboard |

### 3.3 Views Inventory

**Location**: `frontend/src/views/`

| View File | Lines | Purpose | Production Status |
|---|---|---|---|
| `AuditForm.vue` | ~800 | Primary 40-question assessment form with draft save/resume | ✅ Active |
| `AdminLogin.vue` | ~150 | MSAL authentication and admin verification | ✅ Active |
| `Overview.vue` | ~400 | Admin dashboard with submission stats | ✅ Active |
| `Submissions.vue` | ~600 | Submissions list with dynamic filter builder | ✅ Active |
| `SubmissionDetail.vue` | ~500 | Single submission review and report dispatch | ✅ Active |
| `Analytics.vue` | ~350 | Benchmark and trend analytics | ✅ Active |
| `Settings.vue` | ~300 | Application settings management | ✅ Active |
| `Support.vue` | ~250 | Support ticket interface | ✅ Active |
| `UserManagement.vue` | ~400 | Admin user CRUD (super admin only) | ✅ Active |
| `Organisations.vue` | ~700 | Organization management with invitations and tokens | ✅ Active |
| `FormBuilder.vue` | ~450 | Dynamic form question editor | ✅ Active |
| `ResumeDraft.vue` | ~200 | Resume saved draft by token | ✅ Active |
| `OrgLogin.vue` | ~180 | Organization member magic link login | ✅ Active |
| `OrgVerify.vue` | ~150 | Org member verification handler | ✅ Active |
| `OrgDashboard.vue` | ~350 | Organization member dashboard | ✅ Active |
| `BookCall.vue` | ~200 | Consultation booking form | ✅ Active |
| `Dashboard.vue` | ? | **NEEDS REVIEW** - potentially duplicate of Overview.vue | ⚠️ Unknown |

### 3.4 Components Inventory

**Location**: `frontend/src/components/`

| Component File | Purpose | Used By | Status |
|---|---|---|---|
| `AnimatedSelect.vue` | Custom animated dropdown | Multiple views | ✅ Active |
| `RichEditor.vue` | WYSIWYG editor for form builder | FormBuilder.vue | ✅ Active |
| `SaveContinueButton.vue` | Assessment form save/continue button | AuditForm.vue | ✅ Active |
| `ScoreTable.vue` | Score visualization table | SubmissionDetail.vue | ✅ Active |
| `SearchableSelect.vue` | Searchable dropdown component | Multiple views | ✅ Active |
| `ServiceNowFilterBuilder.vue` | Advanced filter builder UI | Submissions.vue | ✅ Active |
| `components/archive/` | Archived components | None | ⚠️ Review for deletion |

### 3.5 API Service Layer

**File**: `frontend/src/api.js`

**Purpose**: Centralized Axios client with:
- Bearer token injection from sessionStorage
- Base URL configuration
- Request/response interceptors
- Error handling

**Dependencies**: axios

---

## 4. Database Architecture

### 4.1 Connection Pooling Strategy

**Implementation**: `psycopg2.pool.ThreadedConnectionPool`  
**Configuration**: 
- **Min connections per worker**: 10
- **Max connections per worker**: 10
- **Total workers**: 2 (uvicorn)
- **Total max connections**: 20

**Rationale**: Pre-warming eliminates dynamic 1.5s SSL handshakes during user requests

**Safety Guards**:
- Test isolation guard prevents tests from connecting to production Azure databases
- Connection status inspection and rollback on checkout
- Bounded wait queue (10s timeout)
- Graceful degradation to direct connection if pool unavailable

### 4.2 Database Migrations

**Location**: `migrations/`

**Total Migrations**: 21 production migrations

#### Sequential Migrations (002-019)

| Migration | Purpose | Applied | Critical |
|---|---|---|---|
| `002_app_settings.sql` | Application configuration table | ✅ Yes | ✅ Yes |
| `003_support_email.sql` | Support contact configuration | ✅ Yes | ✅ Yes |
| `004_designation.sql` | Designation/role field | ✅ Yes | ✅ Yes |
| `005_rbac.sql` | Admin roles and authorization | ✅ Yes | ✅ Yes |
| `006_org_scoring.sql` | Organization dimension scores | ✅ Yes | ✅ Yes |
| `007_fix_score_columns.sql` | Numeric scoring constraints | ✅ Yes | ✅ Yes |
| `008_dynamic_forms.sql` | Configurable form schema | ✅ Yes | ✅ Yes |
| `009_question_dependencies.sql` | Conditional question branching | ✅ Yes | ✅ Yes |
| `010_saved_filters.sql` | Admin saved dashboard queries | ✅ Yes | ✅ Yes |
| `011_verify_submission_id_type.sql` | UUID primary key verification | ✅ Yes | ✅ Yes |
| `012_dual_entry_invitations.sql` | Invitation tokens and quotas | ✅ Yes | ✅ Yes |
| `013_organization_admins.sql` | Historical admin mapping | ✅ Yes | ✅ Yes |
| `014_submission_reassignments.sql` | Reassignment audit trail | ✅ Yes | ✅ Yes |
| `015_performance_jobs_and_idempotency.sql` | Background job tracking | ✅ Yes | ✅ Yes |
| `016_service_bus_outbox.sql` | Transactional outbox table | ✅ Yes | ✅ Yes |
| `017_per_operation_idempotency.sql` | Per-operation state tracking | ✅ Yes | ✅ Yes |
| `018_assessment_access_tokens.sql` | Secure assessment tokens | ✅ Yes | ✅ Yes |
| `019_system_security_settings.sql` | System security configuration | ✅ Yes | ✅ Yes |

#### Feature Migrations

| Migration | Purpose | Applied | Critical |
|---|---|---|---|
| `01_remediation.sql` | Performance remediation schema changes | ✅ Yes | ✅ Yes |
| `02_features_migration.sql` | Feature flags and configuration | ✅ Yes | ✅ Yes |

**Status**: All migrations are production-critical and must be preserved.

### 4.3 SQL Scripts

**Location**: `sql/`

| Script | Purpose | Production Use |
|---|---|---|
| `create_table.sql` | Initial schema bootstrap | ⚠️ Superseded by migrations |
| `fix_missing_columns.sql` | Schema repair script | ⚠️ One-time fix |
| `install_all.sql` | Batch migration runner | ⚠️ Superseded by migrate.py |
| `01_admin_notifications.sql` | Admin notification function | ⚠️ Review if used |
| `02_support_requests.sql` | Support request function | ⚠️ Review if used |
| `README.md` | SQL documentation | ✅ Keep |

**Recommendation**: Archive superseded scripts, verify if notification/support functions are in active use.

---

## 5. Infrastructure and Deployment

### 5.1 Docker Configuration

**File**: `Dockerfile` (multi-stage build)

**Stage 1**: Frontend Build (Node 20 Alpine)
- Install npm dependencies
- Build Vue 3 production bundle
- Bake MSAL client ID and tenant ID into build

**Stage 2**: Production Image (Python 3.11 Slim)
- Install nginx + supervisor
- Install Python dependencies
- Copy backend source (`app/`)
- Copy migrations and scripts
- Copy built frontend (`dist/`)
- Copy nginx and supervisor configs
- Expose port 80

**Size Optimization**: Multi-stage build discards Node build tools (~400MB savings)

### 5.2 Nginx Configuration

**Files**:
- **Root**: `nginx.conf` (standalone configuration)
- **Frontend**: `frontend/nginx.conf` (container configuration)

**Purpose**: Reverse proxy routing
- `/api/*` → `http://127.0.0.1:8000/api/`
- `/` → Vue SPA static assets from `/app/dist`
- History mode fallback to `index.html`
- Asset caching (1 year for hashed assets)
- Security headers (X-Frame-Options, X-Content-Type-Options, CSP)

**Status**: `frontend/nginx.conf` is ACTIVE in production. Root `nginx.conf` may be obsolete.

### 5.3 Supervisor Configuration

**File**: `supervisord.conf`

**Managed Processes**:
1. `uvicorn` - FastAPI backend (2 workers)
2. `nginx` - Reverse proxy
3. `outbox_dispatcher` - Outbox polling daemon
4. `service_bus_worker` - Azure Service Bus consumer

**Process Dependencies**: Nginx starts 3 seconds after uvicorn to ensure backend is ready

### 5.4 CI/CD Pipeline

**File**: `.github/workflows/deploy.yml`

**Trigger**: Push to `main` branch

**Steps**:
1. Azure login with service principal
2. ACR login
3. Docker build with MSAL credentials as build args
4. Push to Azure Container Registry (SHA tag + latest)
5. Deploy to Azure Container Apps (`neurvex-app`)

**Status**: Active production deployment pipeline

### 5.5 Deployment Scripts

**Location**: `scripts/`

| Script | Purpose | Production Use |
|---|---|---|
| `migrate.py` | Canonical migration runner | ✅ Active |
| `run_migration.py` | Migration execution wrapper | ✅ Active |
| `seed_db.py` | Test database seeding | ❌ Dev/Test only |
| `setup_db.py` | Initial schema bootstrapper | ⚠️ One-time use |
| `deploy.sh` | Manual deployment script | ⚠️ Review if used |
| `check-auth-config.sh` | Auth configuration checker | ⚠️ Dev tool |
| `fix-vm-env.sh` | VM environment fixer | ⚠️ Dev tool |
| `inspect_schema.py` | Schema inspection tool | ⚠️ Dev tool |
| `set_super.py` | Promote user to super admin | ⚠️ Admin tool |
| `verify_import.py` | Import verification | ⚠️ Dev tool |
| `test_real_postgres_concurrency.py` | Concurrency test | ❌ Test only |
| `import_nexora_audit.py` | Data import utility | ⚠️ One-time use |

**Root-Level Scripts**:
- `deploy.sh` (root) - **DUPLICATE** of `scripts/deploy.sh`
- `create_siwi_org.py` - **UNTRACKED** - needs review
- `create_siwi_orgs.py` - **UNTRACKED** - needs review
- `generate_audit_tokens.py` - **UNTRACKED** - needs review

---

## 6. Testing Infrastructure

### 6.1 Backend Tests

**Location**: `tests/`

**Test Runner**: pytest  
**Configuration**: `pytest.ini`

**Test Files** (30 test modules):

| Test File | Purpose | Lines | Status |
|---|---|---|---|
| `conftest.py` | In-memory mock engine, fixtures | ~150 | ✅ Active |
| `test_complete_submission_flow.py` | End-to-end submission tests | ~300 | ✅ Active |
| `test_complete_security.py` | Security and authorization tests | ~400 | ✅ Active |
| `test_api.py` | API endpoint tests | ~250 | ✅ Active |
| `test_auth.py` | Authentication tests | ~200 | ✅ Active |
| `test_scoring.py` | Scoring calculation tests | ~350 | ✅ Active |
| `test_org.py` | Organization tests | ~200 | ✅ Active |
| `test_org_authorization.py` | Org authorization tests | ~180 | ✅ Active |
| `test_org_cache.py` | Organization cache tests | ~150 | ✅ Active |
| `test_org_lifecycle.py` | Org lifecycle tests | ~200 | ✅ Active |
| `test_drafts.py` | Draft save/resume tests | ~150 | ✅ Active |
| `test_email_policy.py` | Email validation tests | ~120 | ✅ Active |
| `test_filter_builder.py` | Dynamic filter tests | ~200 | ✅ Active |
| `test_rate_limits.py` | Rate limiting tests | ~150 | ✅ Active |
| `test_secure_tokens.py` | Secure token tests | ~180 | ✅ Active |
| `test_database_pooling.py` | Connection pool tests | ~200 | ✅ Active |
| `test_service_bus_pipeline.py` | Service Bus integration tests | ~250 | ✅ Active |
| `test_p0_security_fixes.py` | P0 security regression tests | ~150 | ✅ Active |
| `test_permissions_and_reliability.py` | Permission and reliability tests | ~200 | ✅ Active |
| `test_reliability_remediation.py` | Reliability remediation tests | ~180 | ✅ Active |
| `test_concurrent_submissions.py` | Concurrency tests | ~200 | ✅ Active |
| `test_e2e_secure_flow.py` | End-to-end secure flow tests | ~180 | ✅ Active |
| `test_scoring_regression_fixtures.py` | Scoring regression fixtures | ~100 | ✅ Active |
| `test_settings.py` | Settings service tests | ~120 | ✅ Active |
| `test_v31_upgrades.py` | Version 3.1 upgrade tests | ~150 | ✅ Active |
| `test_keyvault_fail_safe.py` | Key Vault fail-safe tests | ~100 | ✅ Active |
| `test_db_mock.py` | Database mock tests | ~80 | ✅ Active |
| `test_disposable_postgres.py` | Disposable DB tests | ~100 | ⚠️ Review |

**Test Isolation**: All tests use in-memory mock engine. Production database access is strictly blocked by safety guard.

**Test Coverage**: 93 tests passed (per README badge)

### 6.2 Performance Testing

**Tool**: k6 (load testing)  
**Location**: `tests/performance/`

**Configuration Files**:
- `config.js` - k6 configuration
- `niwi-submission-load.js` - Load test scenario
- `README.md` - Performance testing documentation

**Test Scripts** (PowerShell):
- `run-workflow-tests.ps1` - **UNTRACKED**
- `run-manual-workflow-tests.ps1` - **UNTRACKED**
- `run-token-workflow-tests.ps1` - **UNTRACKED**

**Performance Reports**: `tests/performance/reports/`
- **Total Reports**: 100+ JSON/MD report pairs
- **VU Levels Tested**: 1, 10, 15, 20, 25, 40, 50, 60, 80, 100
- **Time Range**: January 2024 - Present

**Recommendation**: Archive historical reports, keep only most recent baseline for each VU level.

---

## 7. Documentation Architecture

### 7.1 Root-Level Documentation

**Location**: Repository root

**Active Production Documentation**:
- `README.md` - **PRIMARY** canonical project documentation (~700 lines)
- `DEPLOYMENT_GUIDE.md` - Deployment procedures

**Implementation Reports** (Historical):
- `NIWI_IMPLEMENTATION_REPORT.md`
- `NIWI_SERVICE_BUS_IMPLEMENTATION_REPORT.md`
- `NIWI_CURRENT_ARCHITECTURE_AUDIT.md`
- `NIWI_PRE_IMPLEMENTATION_AUDIT.md`
- `NIWI_POST_DEPLOYMENT_VERIFICATION.md`
- `NIWI_INDEPENDENT_PRODUCTION_VERIFICATION_REPORT.md`
- `NIWI_FINAL_RELIABILITY_AUDIT.md`

**Performance and Optimization Reports** (Historical):
- `NIWI_TESTING_AND_PERFORMANCE_REPORT.md`
- `NIWI_PERFORMANCE_REMEDIATION_PLAN.md`
- `NIWI_DATABASE_OPTIMISATION_REPORT.md`

**Architecture Documentation** (Active):
- `NIWI_AZURE_SERVICE_BUS_ARCHITECTURE.md`
- `NIWI_SERVICE_BUS_TEST_REPORT.md`
- `NIWI_SERVICE_BUS_DEPLOYMENT_AND_ROLLBACK.md`
- `NIWI_DEPLOYMENT_AND_ROLLBACK_GUIDE.md`

**Upgrade Documentation**:
- `upgrade_v3_1 (1).md` - **DUPLICATE** filename with space

**Status**: Significant consolidation opportunity. Many reports document historical development phases and can be archived.

### 7.2 Docs Directory Structure

**Location**: `docs/`

#### `docs/api/` - API Documentation
- `API.md` - Main API documentation
- `API_INDEX.md` - API endpoint index
- `API_DOCUMENTATION_AUDIT.md` - API documentation audit
- `API_DEPENDENCY_MAP.md` - API dependency mapping
- `API_ERROR_REFERENCE.md` - Error code reference
- `API_REQUEST_RESPONSE_EXAMPLES.md` - API examples
- `API_TESTING_GUIDE.md` - API testing guide
- `AUTHENTICATION_AND_AUTHORIZATION.md` - Auth documentation
- `OPENAPI_SPECIFICATION.md` - OpenAPI spec

**Status**: Comprehensive but potentially duplicative with root README.

#### `docs/product-audit/` - Product Audit Documentation
- `README.md` - Product audit index
- `01_PRODUCT_REQUIREMENTS_DOCUMENT.md` - PRD
- `02_FRONTEND_TECHNICAL_DOCUMENTATION.md` - Frontend tech docs
- `03_BACKEND_TECHNICAL_DOCUMENTATION.md` - Backend tech docs
- `04_SYSTEM_WORKFLOW_AND_ARCHITECTURE.md` - System architecture
- `05_TESTING_QA_AND_PERFORMANCE_REPORT.md` - Testing report
- `06_FORMULA_AND_CALCULATION_LOGIC.md` - Calculation documentation
- `EXECUTIVE_AUDIT_SUMMARY.md` - Executive summary

**Status**: Comprehensive audit documentation. Keep as authoritative reference.

#### `docs/archive/` - Archived Documentation
- 31 historical markdown files
- Legacy deployment guides
- Historical feature documentation
- Old setup instructions
- Theme tweaker tool

**Status**: Correctly archived. Review for further cleanup.

#### Other Documentation
- `docs/NEUROMARK_TECHNICAL_DOCUMENTATION.md` - **DUPLICATE** (also in archive)
- `docs/SETUP.md` - Setup instructions
- `docs/upgrade_phase0_diagnosis.md` - Upgrade diagnosis
- `docs/upgrade_v3_1_implementation_report.md` - Upgrade implementation

### 7.3 Documentation Consolidation Recommendations

**Proposed Structure**:
```
docs/
├── README.md (Index)
├── architecture/
│   ├── SYSTEM_ARCHITECTURE.md (Consolidated from product-audit + root reports)
│   ├── BACKEND_ARCHITECTURE.md
│   ├── FRONTEND_ARCHITECTURE.md
│   ├── DATABASE_ARCHITECTURE.md
│   └── SERVICE_BUS_ARCHITECTURE.md
│
├── api/
│   └── (Keep current structure, consolidate duplicates)
│
├── operations/
│   ├── DEPLOYMENT.md (Consolidate deployment guides)
│   ├── MONITORING.md
│   └── TROUBLESHOOTING.md
│
├── product/
│   └── (Keep product-audit docs)
│
├── calculations/
│   └── FORMULA_LOGIC.md
│
└── archive/
    ├── historical-reports/ (Move all NIWI_*_REPORT.md files here)
    ├── upgrades/ (Move upgrade docs)
    └── legacy/ (Keep existing archive)
```

---

## 8. Identified Architectural Issues

### 8.1 Duplicate Implementations

None identified. The architecture has been properly refactored with Service Bus replacing the embedded worker.

### 8.2 Obsolete Components

| Component | Status | Reason | Recommendation |
|---|---|---|---|
| `app/tasks/job_worker.py` | Obsolete | Superseded by Service Bus architecture | Remove |
| Root `nginx.conf` | Possibly obsolete | `frontend/nginx.conf` used in production | Verify and potentially remove |
| Root `deploy.sh` | Duplicate | Duplicate of `scripts/deploy.sh` | Remove duplicate |
| `sql/create_table.sql` | Superseded | Migrations are authoritative | Archive |
| `sql/install_all.sql` | Superseded | `migrate.py` is authoritative | Archive |

### 8.3 Configuration Files

**Active**:
- `.env` (local dev, not in repo)
- `.env.example` (template)
- `frontend/.env.example` (template)
- `pytest.ini` (test configuration)
- `tsconfig.json` (TypeScript configuration)
- `frontend/vite.config.js` (Vite configuration)
- `frontend/package.json` (frontend dependencies)
- `package.json` (root workspace metadata)

**Temporary**:
- `frontend/vite.config.js.timestamp-*.mjs` (3 files) - **REMOVE** (Vite build artifacts)

### 8.4 Generated Assets

**Frontend Build Artifacts**:
- `frontend/dist/` - **EXCLUDED FROM GIT** (correct)
- `node_modules/` - **EXCLUDED FROM GIT** (correct)
- `frontend/node_modules/` - **EXCLUDED FROM GIT** (correct)

**Python Virtual Environments**:
- `.venv/` - **EXCLUDED FROM GIT** (correct)
- `.venv311/` - **TRACKED** - should be excluded

**Test Artifacts**:
- `.pytest_cache/` - **TRACKED** - should be excluded
- Performance JSON reports - **100+ UNTRACKED** - need archival strategy

---

## 9. Dependency Analysis

### 9.1 Backend Dependencies

**File**: `requirements.txt`

**Core Dependencies** (Production):
```
fastapi==0.115.5
uvicorn[standard]==0.32.1
psycopg2-binary==2.9.10
azure-communication-email==1.0.0
python-multipart==0.0.12
PyJWT==2.8.0
cryptography==42.0.5
requests==2.31.0
slowapi==0.1.9
cachetools==5.3.3
email-validator>=2.1.1
azure-identity==1.15.0
azure-keyvault-secrets==4.7.0
azure-servicebus>=7.12.0
```

**Dev Dependencies** (Not in requirements.txt):
- pytest (tests)
- playwright (E2E tests - `package.json` devDependency)

**Status**: All dependencies are actively used. No unused packages identified.

### 9.2 Frontend Dependencies

**File**: `frontend/package.json`

**Core Dependencies**:
```json
{
  "vue": "^3.4.21",
  "vue-router": "^4.3.0",
  "@azure/msal-browser": "^3.7.1",
  "axios": "^1.6.7",
  "chart.js": "^4.4.2",
  "html2canvas": "^1.4.1",
  "jspdf": "^2.5.1"
}
```

**Dev Dependencies**:
```json
{
  "@vitejs/plugin-vue": "^5.0.4",
  "vite": "^5.1.6",
  "autoprefixer": "^10.4.18",
  "postcss": "^8.4.35",
  "tailwindcss": "^3.4.1",
  "typescript": "^5.3.3"
}
```

**Status**: All dependencies are actively used.

### 9.3 Root Package Dependencies

**File**: `package.json`

**Purpose**: Workspace scripts for concurrent dev server execution

**Dependencies**:
```json
{
  "concurrently": "^9.2.5",
  "playwright": "^1.64.1"
}
```

**Status**: Active for local development.

---

## 10. Critical File Dependencies

### 10.1 Docker Build Dependencies

**Referenced by Dockerfile**:
- `frontend/package*.json` (COPY)
- `frontend/**` (COPY for build)
- `requirements.txt` (COPY)
- `app/` (COPY entire directory)
- `scripts/run_migration.py` (COPY)
- `scripts/migrate.py` (COPY)
- `migrations/` (COPY entire directory)
- `frontend/nginx.conf` (COPY to /etc/nginx/conf.d/)
- `supervisord.conf` (COPY to /etc/supervisor/conf.d/)

**Status**: All files are production-critical. Do not delete.

### 10.2 Supervisor Dependencies

**Referenced by supervisord.conf**:
- `app.main:app` (uvicorn WSGI application)
- `app.services.outbox_service` (Python module)
- `app.tasks.service_bus_worker` (Python module)
- `nginx` (system binary)

**Status**: All are production-critical.

### 10.3 CI/CD Dependencies

**Referenced by .github/workflows/deploy.yml**:
- `Dockerfile` (docker build)
- All Dockerfile dependencies (transitive)

**Status**: Pipeline is active and production-critical.

---

## 11. Assessment and Recommendations

### 11.1 Architecture Health

**Overall Assessment**: ✅ **HEALTHY**

The NIWI application has a well-structured, production-ready architecture with:
- Clear separation of concerns
- Proper infrastructure-as-code
- Comprehensive testing
- Solid deployment pipeline
- Secure authentication and authorization
- Scalable background processing

### 11.2 Code Quality

**Strengths**:
- Type hints in Python
- Pydantic validation
- Consistent code organization
- Comprehensive error handling
- Security-first design

**Areas for Improvement**:
- Documentation consolidation (120+ markdown files)
- Performance test report archival
- Removal of obsolete job_worker.py
- `.venv311/` and `.pytest_cache/` should be gitignored

### 11.3 Production Safety

**Critical Files** (NEVER DELETE):
- All files in `app/` directory
- All files in `migrations/` directory
- All files in `frontend/src/` directory
- `Dockerfile`, `supervisord.conf`, `frontend/nginx.conf`
- `requirements.txt`, `frontend/package.json`
- `.github/workflows/deploy.yml`
- Root `README.md`

**Safe to Archive/Remove**:
- Historical implementation reports (move to archive)
- Obsolete `app/tasks/job_worker.py` (verify ENABLE_EMBEDDED_WORKER is false everywhere)
- Duplicate `deploy.sh` (root vs scripts/)
- Temporary Vite timestamp files
- Old performance test reports (keep latest baseline only)
- `sql/create_table.sql` and `sql/install_all.sql` (superseded by migrations)

### 11.4 Documentation Debt

**Current State**: 120+ markdown files across multiple locations

**Consolidation Priority**: **HIGH**

**Recommended Actions**:
1. Move all `NIWI_*_REPORT.md` files to `docs/archive/historical-reports/`
2. Consolidate root README with product-audit documentation
3. Create authoritative `docs/architecture/` directory
4. Update `docs/README.md` as documentation index
5. Remove duplicate documentation

---

## 12. Conclusion

The NIWI codebase is in good architectural health with a production-ready implementation. The primary cleanup opportunities are:

1. **Documentation Consolidation** - Reduce 120+ files to organized, authoritative structure
2. **Performance Report Archival** - Archive 100+ historical test reports, keep recent baselines
3. **Obsolete Worker Removal** - Remove `job_worker.py` after verification
4. **Git Hygiene** - Add `.venv311/` and `.pytest_cache/` to `.gitignore`
5. **Duplicate Removal** - Remove duplicate `deploy.sh` and Vite timestamp files

**No production-critical business logic, authentication, authorization, or data integrity changes are required or recommended.**

---

**Next Steps**: Proceed to Phase B (Complete File Inventory) and Phase C (Identify Duplicate and Unused Code).
