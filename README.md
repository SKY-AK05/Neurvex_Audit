# NIWI — Neurodiversity Inclusion Workplace Index

[![Backend Tests](https://img.shields.io/badge/backend%20tests-93%20passed-brightgreen.svg)]()
[![Type Check](https://img.shields.io/badge/typescript-clean-brightgreen.svg)]()
[![Security Audit](https://img.shields.io/badge/security%20audit-passed-brightgreen.svg)]()

NIWI (Neurodiversity Inclusion Workplace Index) is Orchvate's enterprise audit platform designed to evaluate, score, benchmark, and report organizational neurodiversity maturity across modern workplaces.

---

## 1. Project Overview

NIWI provides organizations with a structured 40-question assessment covering 8 core inclusion dimensions. It automatically calculates quantitative scores, derives categorical maturity levels (Developing, Maturing, Champion), provides real-time benchmarking, and empowers administrators to review submissions, generate customized PDF executive reports, and manage multi-organization assessments.

The application operates under a unified two-role administrative security model, supporting both direct public submissions and secure invitation-token employee cohort surveys.

---

## 2. Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientLayer [Client Layer]
        BrowserUser[Public / Org Member Browser]
        BrowserAdmin[Administrator Browser]
    end

    subgraph EntryPoint [Edge & Ingress (Port 80)]
        Nginx[Nginx Reverse Proxy]
        StaticDist[Vue 3 Static SPA Assets]
    end

    subgraph BackendApp [FastAPI Application (Port 8000)]
        Uvicorn[Uvicorn Process Manager (2 Workers)]
        AuthMiddleware[Security & JWKS Middleware]
        RBAC[Two-Role Authorization Engine]
        APIRoutes[REST Endpoints (/api)]
        FilterService[Dynamic Query Builder]
        ScoringEngine[Scoring & Maturity Engine]
    end

    subgraph StorageAndCloud [Data & Azure Services]
        KeyVault[Azure Key Vault (Managed Identity)]
        PostgreSQL[(Azure PostgreSQL Flexible Server)]
        ACS[Azure Communication Services (Email)]
        HubSpot[HubSpot CRM (Optional Sync)]
    end

    BrowserUser -->|HTTP / HTTPS| Nginx
    BrowserAdmin -->|HTTP / HTTPS| Nginx

    Nginx -->|SPA Static Requests| StaticDist
    Nginx -->|/api/* Reverse Proxy| Uvicorn

    Uvicorn --> AuthMiddleware
    AuthMiddleware --> RBAC
    RBAC --> APIRoutes

    APIRoutes --> ScoringEngine
    APIRoutes --> FilterService

    APIRoutes -->|Key Retrieval (Prod Startup)| KeyVault
    APIRoutes -->|ThreadedConnectionPool (2-10 per worker)| PostgreSQL
    APIRoutes -->|Transactional Notifications| ACS
    APIRoutes -->|Background Tasks| HubSpot
```

---

## 3. Tech Stack

- **Frontend:**
  - **Framework:** Vue 3 (Composition API, `<script setup>`)
  - **Tooling:** Vite 5, TypeScript 5.3
  - **Styling:** Tailwind CSS 3.4
  - **State & Routing:** Vue Router 4
  - **Auth Integration:** Microsoft MSAL Browser (`@azure/msal-browser`)
  - **Charts & Reports:** Chart.js, HTML2Canvas, JSPDF
- **Backend:**
  - **Framework:** FastAPI 0.115.5
  - **Runtime & Server:** Python 3.11 / 3.13, Uvicorn 0.32.1 (Multi-worker)
  - **Validation & Schemas:** Pydantic v2
  - **Rate Limiting:** SlowAPI (Token Bucket Limiter)
  - **Caching:** Cachetools TTLCache
- **Database & Pooling:**
  - **Engine:** PostgreSQL 14+ (Azure Database for PostgreSQL Flexible Server)
  - **Driver:** `psycopg2-binary` 2.9.10
  - **Pool Manager:** Process-isolated `ThreadedConnectionPool` (2 min, 10 max per worker = 20 max connections total)
- **Security & Cloud Infrastructure:**
  - **Secrets Management:** Azure Key Vault via Managed Identity (`azure-identity`, `azure-keyvault-secrets`)
  - **Identity Provider:** Microsoft Entra ID (Azure AD) via JWKS verification
  - **Transactional Email:** Azure Communication Services (ACS) Email SDK
  - **Containerization:** Multi-stage Docker image (Node 20 build -> Python 3.11-slim + Nginx + Supervisord)

---

## 4. Two-Role Permission Model

NIWI enforces a global two-role permission architecture. Administrators manage all organizations globally without artificial per-organization ownership lockouts.

```
+-------------------------------------------------------------+
|                     SYSTEM PERMISSIONS                      |
+-------------------------------------------------------------+
|                                                             |
|   [Normal Admin]                                            |
|   - View, create, edit, activate/deactivate organisations   |
|   - Soft-delete organisations (preserves audit data)        |
|   - Restore soft-deleted organisations                      |
|   - View all submissions globally across organisations      |
|   - Reassign submissions between organisations              |
|   - Create, edit, and revoke invitation links               |
|   - View analytics, scoring, and report previews            |
|   - Download and send audit reports                         |
|                                                             |
|   [Super Admin] (Inherits all Normal Admin capabilities)    |
|   + Create, list, and delete administrator accounts         |
|   + Change administrator roles (promote/demote)             |
|   + Protection of last active Super Admin                   |
|   + Delete all submissions with explicit confirmation       |
|                                                             |
+-------------------------------------------------------------+
```

### Authorization Enforcement
All role authorization is enforced at the backend level via [`app/core/authorization.py`](file:///app/core/authorization.py) and [`app/core/security.py`](file:///app/core/security.py). Frontend UI controls reflect these restrictions, while unauthorized API requests receive immediate `HTTP 401 Unauthorized` or `HTTP 403 Forbidden` responses.

---

## 5. Assessment Submission Flows

NIWI supports two distinct entry pathways:

### Method A: Direct Website Submission
1. Respondent navigates to the public audit interface (`/`).
2. Respondent enters personal details and organization name.
3. The backend checks for duplicate recent submissions (5-minute rolling window per email).
4. Organization lookup:
   - If existing organization name matches (case-insensitive, trimmed), submission is linked.
   - If new company name, organization is auto-created with `is_active=TRUE`, `is_deleted=FALSE`, and `approval_status='approved'`.
5. Submission source is recorded as `DIRECT`.

### Method B: Invitation Link Entry
1. Administrator creates a scoped invitation link for an organization with an optional expiration date and submission quota.
2. The invitation token URL (`/audit?invitation=<token>`) is distributed to organization members.
3. Upon submission:
   - Server validates token hash against `organization_invitations`.
   - Verifies organization is active and not soft-deleted.
   - Verifies invitation is active, not revoked, not expired, and below `max_submissions`.
   - Organization identity is server-derived from the token (user input cannot override company name).
   - Atomically increments `submission_count`.
4. Submission source is recorded as `INVITATION`.

---

## 6. Key Features

- **Standardized Maturity Scoring:** 40 Likert-scale questions across 8 dimensions scored on 1-25 scales with weighted maturity bands.
- **Save & Resume Drafts:** Tokenized draft storage allowing users to resume in-progress assessments securely via email magic links.
- **Unified Submissions Dashboard:** Dynamic multi-field filter builder supporting text search, range queries, date comparisons, and submission source filtering (`ALL`, `DIRECT`, `INVITATION`).
- **Audit Reassignment Trail:** Audit movement between organizations updates both `organization_id` and `company_name` simultaneously, appending immutable records to `submission_reassignments`.
- **Soft Deletion & Recovery:** Deleting an organization sets `is_deleted=TRUE`, deactivates invitations, and strictly preserves historical submissions, answers, scores, and links. Organizations can be restored via `POST /api/manage/orgs/{id}/restore`.
- **Destructive Operation Safety:** Bulk submission deletion is strictly restricted to Super Admins and requires the explicit payload string `DELETE ALL SUBMISSIONS`.

---

## 7. Project Structure

```
NIWI/
├── .dockerignore                # Container build exclusions
├── .gitignore                   # Comprehensive git ignore rules
├── Dockerfile                   # Multi-stage production container build
├── README.md                    # Canonical platform documentation
├── deploy.sh                    # Container deployment automation
├── docker-compose.yml           # Local multi-service compose definition
├── nginx.conf                   # Standalone reverse proxy configuration
├── package.json                 # Workspace metadata
├── pytest.ini                   # Pytest runner configuration
├── requirements.txt             # Locked Python production dependencies
├── supervisord.conf             # Production multi-process supervisor (Nginx + Uvicorn)
│
├── app/                         # Backend Application Source
│   ├── main.py                  # FastAPI initialization, lifespans & exception handlers
│   ├── api/                     # REST API Endpoint Routers
│   │   ├── drafts.py            # Draft save and resume endpoints
│   │   ├── form_builder.py      # Custom question and dynamic form endpoints
│   │   ├── org.py               # Organization registration & magic link routes
│   │   ├── orgs.py              # Canonical organisation management & invitations
│   │   ├── public.py            # Public system health and status endpoints
│   │   ├── routes.py            # Submissions, reassignment, reporting & dashboard
│   │   └── settings.py          # Application settings & Super Admin delete-all
│   ├── core/                    # Core Infrastructure & Cross-Cutting Concerns
│   │   ├── authorization.py     # Two-Role authorization enforcement
│   │   ├── config.py            # Strict environment configuration & password policy
│   │   ├── database.py          # ThreadedConnectionPool & test isolation guards
│   │   ├── keyvault.py          # Azure Key Vault fail-safe client
│   │   └── security.py          # Entra ID JWKS token verification & dev bypass
│   ├── models/                  # Pydantic Schemas & DTOs
│   │   └── audit.py             # Submission, response & report data contracts
│   └── services/                # Business Logic Services
│       ├── crm_service.py       # HubSpot CRM synchronization
│       ├── dashboard_service.py # Submission analytics and aggregations
│       ├── filter_service.py    # SQL query AST and filter condition compiler
│       ├── scoring_service.py   # Dimension scores and maturity level engine
│       ├── settings_service.py  # Application settings table persistence
│       └── user_service.py      # Admin user CRUD and Super Admin safeguards
│
├── frontend/                    # Vue 3 Frontend SPA
│   ├── index.html               # Entry HTML shell
│   ├── package.json             # Frontend dependencies & scripts
│   ├── tsconfig.json            # TypeScript configuration
│   ├── vite.config.js           # Vite build pipeline & dev proxy
│   └── src/
│       ├── api.js               # Centralized Axios client & auth interceptor
│       ├── App.vue              # Main Vue application component
│       ├── main.js              # Application bootstrapping & MSAL init
│       ├── router/index.js      # Route definitions & navigation guards
│       ├── components/          # Reusable UI components
│       └── views/               # Application Views (AuditForm, Submissions,
│                                # Organisations, Overview, Settings, etc.)
│
├── migrations/                  # Sequentially Numbered SQL Migrations
│   ├── 002_app_settings.sql
│   ├── 003_support_email.sql
│   ├── 004_designation.sql
│   ├── 005_rbac.sql
│   ├── 006_org_scoring.sql
│   ├── 007_fix_score_columns.sql
│   ├── 008_dynamic_forms.sql
│   ├── 009_question_dependencies.sql
│   ├── 010_saved_filters.sql
│   ├── 011_verify_submission_id_type.sql
│   ├── 012_dual_entry_invitations.sql
│   ├── 013_organization_admins.sql
│   └── 014_submission_reassignments.sql
│
├── scripts/                     # Operational & Migration Utilities
│   ├── migrate.py               # Canonical database migration runner
│   ├── seed_db.py               # Test database seeding utility
│   └── setup_db.py              # Initial schema bootstrapper
│
└── tests/                       # Automated Test Suite (100% Isolated)
    ├── conftest.py              # In-memory mock engine, safety fixtures & setup
    ├── test_complete_security.py
    ├── test_complete_submission_flow.py
    ├── test_database_pooling.py
    ├── test_db_mock.py
    ├── test_drafts.py
    ├── test_filter_builder.py
    ├── test_org.py
    ├── test_org_authorization.py
    ├── test_p0_security_fixes.py
    ├── test_permissions_and_reliability.py
    ├── test_scoring.py
    ├── test_security_auth.py
    └── test_settings.py
```

---

## 8. Prerequisites

- **Python:** 3.11 or higher (3.13 recommended)
- **Node.js:** v20.x LTS or higher and npm 10+
- **PostgreSQL:** Version 14 or higher
- **Azure Account (Production):** Azure Container Apps / App Service, Azure Key Vault, Azure PostgreSQL Flexible Server, Azure Communication Services.

---

## 9. Local Development Setup

### 9.1 Clone and Prepare Workspace
```bash
git clone <repository_url>
cd NIWI
```

### 9.2 Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pytest
```

### 9.3 Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### 9.4 Local Environment Configuration
Create `.env` in the root directory based on `.env.example`:
```ini
APP_ENV=development
ENABLE_DEV_BYPASS=true

PGHOST=localhost
PGPORT=5432
PGDATABASE=nd_audit_dev
PGUSER=postgres
PGPASSWORD=your_local_secure_password

JWT_SECRET=development_secret_minimum_32_characters_long_key!
FRONTEND_URL=http://localhost:5173
ACS_CONNECTION_STRING=endpoint=https://mock.communication.azure.com/;accesskey=mock==
```

### 9.5 Run Local Development Servers
```bash
# Terminal 1: Backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

## 10. Environment Variables Reference

| Variable Name | Environment | Purpose | Required in Prod |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | All | Application environment (`development`, `test`, `production`). | Yes |
| `KEY_VAULT_NAME` | Production | Azure Key Vault resource name for Managed Identity retrieval. | Yes |
| `PGHOST` | All | PostgreSQL server hostname. | Yes |
| `PGPORT` | All | PostgreSQL port (defaults to `5432`). | No |
| `PGDATABASE` | All | PostgreSQL database name (default `nd_audit`). | Yes |
| `PGUSER` | All | Database administrative user. | Yes |
| `PGPASSWORD` | Dev / Test | Database password. In production, loaded via Key Vault or env. Must be >= 16 chars and not in blocklist. | Yes |
| `JWT_SECRET` | All | Minimum 32-character symmetric secret for draft tokens. In prod, loaded from Key Vault. | Yes |
| `AZURE_CLIENT_ID` | Production | Entra ID Application (Client) ID. | Yes |
| `AZURE_TENANT_ID` | Production | Entra ID Tenant ID. | Yes |
| `ACS_CONNECTION_STRING` | Production | Azure Communication Services connection string for transactional emails. | Yes |
| `FRONTEND_URL` | All | Base URL of frontend for resume links and CORS origins. | Yes |
| `ENABLE_DEV_BYPASS` | Dev / Test | Enables developer bypass auth tokens (`Bearer local_bypass:<email>`). **Strictly blocked in production.** | Never in Prod |

---

## 11. Database Migrations

### Migration Strategy
Database migrations are strictly idempotent and forward-only (`IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`). Migrations are stored in `migrations/` and numbered sequentially (`002` through `014`).

### Running Migrations
To execute all pending migrations against the configured database:
```bash
python scripts/migrate.py
```

### Migration History
- `002_app_settings.sql`: Application configuration & notification settings table.
- `003_support_email.sql`: Support contact configuration.
- `004_designation.sql`: Designation / role field addition.
- `005_rbac.sql`: Administrative roles and authorization tables.
- `006_org_scoring.sql`: Dimension scores JSON and summary fields.
- `007_fix_score_columns.sql`: Numeric scoring constraints.
- `008_dynamic_forms.sql`: Configurable form schema support.
- `009_question_dependencies.sql`: Conditional question branching logic.
- `010_saved_filters.sql`: Administrator saved dashboard queries.
- `011_verify_submission_id_type.sql`: UUID primary key verification.
- `012_dual_entry_invitations.sql`: Invitations, quotas, and dual entry tracking.
- `013_organization_admins.sql`: Historical admin mapping support.
- `014_submission_reassignments.sql`: Reassignment audit trail and attribution.

---

## 12. Testing

### Automated Test Suite
The NIWI test suite includes 93 comprehensive unit and integration tests covering security, permissions, database pooling, submission flows, and filter queries.

### Test Isolation Guard
Automated tests are 100% isolated from live production databases. 
- [`app/core/database.py`](file:///app/core/database.py) includes `check_test_isolation_guard()`, which throws `RuntimeError` immediately if tests attempt to target `*.postgres.database.azure.com` or databases containing `generative-ai`.
- Tests run against an in-memory mock engine defined in [`tests/conftest.py`](file:///tests/conftest.py) with simulated transactions, rollbacks, and connection checkout/checkin.

### Running Backend Tests
```bash
# Run complete test suite with verbose output
pytest tests/ -v
```

### Running Frontend Checks
```bash
cd frontend
# TypeScript verification
npm run type-check

# Production build test
npm run build
```

---

## 13. Production Deployment Guide

### Azure Architecture
In production, NIWI runs as a containerized workload on **Azure Container Apps** (or Azure App Service for Containers) integrated with **Azure Database for PostgreSQL Flexible Server** and **Azure Key Vault**.

### Production Startup & Key Vault Fail-Safe
When `APP_ENV=production`:
1. The application verifies Managed Identity (`DefaultAzureCredential`).
2. Connects to `https://<KEY_VAULT_NAME>.vault.azure.net/` and performs an active ping test.
3. Retrieves required secrets: `PGPASSWORD`, `JWT_SECRET`, `ACS_CONNECTION_STRING`.
4. **Fail-Safe Rule:** If Managed Identity fails, Key Vault is unreachable, or required secrets are missing, application startup **fails immediately with `sys.exit(1)`**. It strictly refuses to fall back silently to local `.env` files.
5. In production, `ENABLE_DEV_BYPASS` is forcibly rejected and terminated.

### Deploying the Container
```bash
# Build the unified container
docker build -t niwi-app:latest .

# Run container locally for testing
docker run -p 80:80 \
  -e APP_ENV=production \
  -e KEY_VAULT_NAME=kv-niwi-prod \
  -e PGHOST=your-db.postgres.database.azure.com \
  -e PGDATABASE=nd_audit \
  -e PGUSER=auditadmin \
  niwi-app:latest
```

---

## 14. Security Architecture

- **Authentication:** Microsoft Entra ID (Azure AD) tokens verified against Microsoft's public JWKS endpoints with cache TTL, audience validation, and signature verification.
- **Authorization:** Two-Role RBAC enforced strictly at the API layer. All administrative mutation endpoints require Super Admin or Normal Admin authentication.
- **SQL Injection Prevention:** 100% parameterized queries via Psycopg2. Dynamic filters in [`filter_service.py`](file:///app/services/filter_service.py) use strict whitelist validation for column identifiers and operators.
- **Input Sanitization & Validation:** Pydantic v2 data models with UUID validation, email syntax checking, and explicit input trimming.
- **Audit Logging:** Administrative operations (reassignments, organization status changes, invitations) are logged with timestamp, user ID, email, IP address, and operation outcome.
- **Connection Leak Safeguard:** All database acquisitions use `PooledConnection` context managers ensuring `putconn()` returns connections to the pool idempotently on all exit and exception paths.

---

## 15. Monitoring and Operations

### Health Check Endpoint
- **URL:** `GET /health` or `GET /api/public/health`
- **Output:** Returns JSON status verifying API responsiveness and live database connectivity:
```json
{
  "status": "ok",
  "database": "connected",
  "environment": "production"
}
```

### Logging
Application logs are formatted as structured JSON output to `stdout` and `stderr`, streaming directly into Azure Log Analytics / Container Apps System Logs.

### Common Troubleshooting
1. **Startup fails with `Azure Key Vault is unavailable`:**
   - Verify Azure Managed Identity is assigned to the Container App.
   - Verify Key Vault Access Policies / Azure RBAC grant "Key Vault Secrets User" to the managed identity.
2. **Database pool exhausted (`PoolError`):**
   - Check active worker count and PostgreSQL `max_connections`.
   - Verify all database acquisitions wrap connections inside `with get_db_connection() as conn:`.
3. **HTTP 401 on Admin endpoints:**
   - Confirm Entra ID token has not expired and contains valid audience (`AZURE_CLIENT_ID`).
