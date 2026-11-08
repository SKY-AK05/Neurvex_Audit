# NIWI — Technical Architecture and System Documentation
**Document Version:** 3.1 Enterprise Production Specification  
**System Name:** Neuro-Inclusive Workplace Index (NIWI)  
**Author / Engineering Organization:** Orchvate Software Engineering & Architecture Team  
**Date of Release:** November 2026  
**Confidentiality Level:** Internal Engineering Reference / Enterprise Client Technical Review  

---

## Document Overview & Target Audience

This technical specification provides the complete architectural, operational, and implementation reference for the **Neuro-Inclusive Workplace Index (NIWI)** platform. It is engineered to serve two distinct audiences simultaneously:
1. **Business Stakeholders, Product Leaders, & Enterprise Clients:** Who require clear, accessible explanations of the platform's mission, compliance posture, data privacy safeguards, and organizational value proposition.
2. **Software Engineers, Architects, DevOps, & QA Leads:** Who require exact, verifiable technical details regarding database schemas, API schemas, concurrency controls, background worker lifecycles, and deployment topologies.

Every major technical component adheres to the five-point architectural rubric:
- **What is it?** Precise technical definition.
- **Why is it needed?** Business and operational rationale.
- **How does it work?** Step-by-step technical mechanics.
- **What does it communicate with?** Component dependencies and network protocols.
- **What happens if it fails?** Blast radius, error status codes, and recovery mechanisms.

---

# Table of Contents
- [Chapter 1: Executive Summary](#chapter-1-executive-summary)
- [Chapter 2: System Overview](#chapter-2-system-overview)
- [Chapter 3: Technology Stack](#chapter-3-technology-stack)
- [Chapter 4: System Architecture](#chapter-4-system-architecture)
- [Chapter 5: Complete Application Workflow](#chapter-5-complete-application-workflow)
- [Chapter 6: API Documentation](#chapter-6-api-documentation)
- [Chapter 7: Database Documentation](#chapter-7-database-documentation)
- [Chapter 8: Authentication and Security](#chapter-8-authentication-and-security)
- [Chapter 9: Submission and Processing Architecture](#chapter-9-submission-and-processing-architecture)
- [Chapter 10: Error Handling and Reliability](#chapter-10-error-handling-and-reliability)
- [Chapter 11: Infrastructure and Azure Deployment](#chapter-11-infrastructure-and-azure-deployment)
- [Chapter 12: Environment Configuration](#chapter-12-environment-configuration)
- [Chapter 13: Monitoring and Performance](#chapter-13-monitoring-and-performance)
- [Chapter 14: Testing and Quality Assurance](#chapter-14-testing-and-quality-assurance)
- [Chapter 15: Developer Setup Guide](#chapter-15-developer-setup-guide)
- [Chapter 16: Troubleshooting Guide](#chapter-16-troubleshooting-guide)
- [Chapter 17: Known Limitations and Technical Debt](#chapter-17-known-limitations-and-technical-debt)
- [Chapter 18: Future Recommendations](#chapter-18-future-recommendations)

---

# Chapter 1: Executive Summary

### In Plain Words
The Neuro-Inclusive Workplace Index (NIWI) is like a comprehensive medical health scan for an entire corporation, but instead of measuring blood pressure and cholesterol, it measures how welcoming, accessible, and supportive a company is for neurodivergent employees (such as people with Autism, ADHD, Dyslexia, or Sensory Sensitivities). Employees complete an assessment answering questions about workplace environment, hiring practices, and day-to-day culture. The system calculates an inclusion score and generates tailored executive roadmaps showing leaders exactly what steps to take next.

### 1.1 The Business Problem
Modern enterprises are increasingly committed to Diversity, Equity, and Inclusion (DEI). However, neurodiversity remains poorly understood and inconsistently supported:
- **Invisible Barriers:** Neurodivergent individuals face significant sensory, cognitive, and social friction in standard corporate office environments (e.g., open-plan office noise, ambiguous interview processes, rigid performance reviews).
- **Subjective Guesswork:** Leadership lacks standardized metrics to measure whether corporate inclusion initiatives are actually working on the ground.
- **Privacy & Stigma:** Employees fear disclosing neurodivergent conditions because they worry about career penalties or disclosure of sensitive personal health information.

### 1.2 The NIWI Solution
NIWI provides a standardized, mathematically rigorous audit platform developed by **Orchvate**:
1. **Confidential 40-Question Assessment:** Employees and leaders evaluate their workplace across eight fundamental inclusion dimensions using Likert scale responses.
2. **Zero-PII Aggregated Benchmarking:** Sensitive individual disclosure is separated from company analytics. Demographic insights are aggregated across teams so individual respondents cannot be deanonymized.
3. **Deterministic 0–20 Scoring Engine:** Proprietary scoring algorithms evaluate organizational maturity across five distinct progression levels (Foundational, Early Progress, Developing, Proficient, Leading).
4. **Instant Actionable Feedback:** Respondents receive instant personalized insights, while executive leadership receives comprehensive cross-organizational analytics and radar visualizations.

### 1.3 Intended User Personas
- **Individual Employees & Contributors:** Complete the 20-minute audit anonymously or with contact details to receive a customized personal reflection report.
- **Organization HR & DEI Leaders:** Manage team participation via dedicated trackable invitation links, monitor departmental response quotas, and review company maturity profiles.
- **Executive C-Suite & Board Members:** Review high-level benchmark reports to prioritize capital expenditures and workplace policy investments.
- **Orchvate Super Administrators:** Oversee global multi-tenant operations, verify new client organizations, audit background ingestion queues, manage rate limit policies, and inspect system telemetry.

### 1.4 Primary Capabilities & System Highlights
- **Sub-25ms Synchronous Ingestion:** Public survey submissions are acknowledged with `HTTP 202 Accepted` within 25 milliseconds using a decoupled transactional outbox pattern.
- **Pre-warmed Connection Pooling:** Background connection management eliminates Azure WAN connection latency.
- **Dual-Layer In-Memory Caching:** Section metadata and organization verification directories are cached in RAM with automated background refresh cycles.
- **Enterprise Microsoft Entra ID (Azure AD) SSO:** Administrative access is gated by corporate OAuth2 OIDC tokens validated via PyJWT and Azure JWKS public keys.
- **Progressive UI & Accessibility:** Vue 3 responsive interface designed to meet WCAG 2.1 AA accessibility guidelines, including full keyboard navigation, high-contrast states, and skeleton loading states.

---

# Chapter 2: System Overview

### In Plain Words
Think of NIWI as a high-speed digital restaurant kitchen. A customer (the employee) walks up to the counter (the web page) and places an order (their survey submission). The cashier stamps a ticket with a unique order number, hands the customer a receipt immediately, and drops the ticket into a kitchen order bin (the transactional outbox). The customer doesn't have to wait in line while the meal is cooked. In the background, specialized chefs (background workers) pull tickets from the bin one by one, prepare the dish (calculate scores), package it into a delivery box (format the HTML email report), and dispatch it to the customer's inbox via a courier service (Azure Communication Services).

### 2.1 End-to-End System Flow
The platform lifecycle proceeds across six primary operational phases:

1. **Discovery & Onboarding:**
   - A prospective client organization registers or is pre-provisioned by Orchvate administrators (`/admin/organisations`).
   - The organization receives dedicated invitation tokens or unique assessment links (`/invite/{token}`).
2. **Assessment Execution:**
   - Employees access `/audit` or `/invite/{token}` on desktop or mobile browsers.
   - The Vue 3 SPA dynamically queries `/api/public/organisations/validate` to verify employer eligibility.
   - Every response is validated client-side and saved into browser local storage or persistent server drafts (`/api/drafts/save`) after 2 seconds of inactivity.
3. **Submission & Instant Acknowledgment:**
   - On completion of all 44 fields (4 demographic questions + 40 core Likert inputs), the browser computes a client-side idempotency key and dispatches an HTTP `POST /api/submit`.
   - The FastAPI backend validates the payload, generates a unique UUID, writes the raw submission atomically into `raw_submissions` and `service_bus_outbox`, and immediately responds with `HTTP 202 Accepted` in under 25ms.
4. **Background Scoring & Ingestion:**
   - The `outbox_dispatcher` daemon claims pending outbox records using PostgreSQL's concurrency-safe `SELECT ... FOR UPDATE SKIP LOCKED`.
   - The `service_bus_worker` computes normalized scores (0–20 points) across the 8 Core Inclusion Pillars.
   - Calculated results are permanently committed to the `submissions` and `org_submission_links` tables.
5. **Executive Reporting & Communication:**
   - The worker renders a responsive, branded HTML email report detailing the respondent's pillar breakdown and prioritized improvement recommendations.
   - The email is dispatched asynchronously via **Azure Communication Services (ACS)**.
   - If configured, respondent contact details and corporate metadata are synced to **HubSpot CRM** for relationship management.
6. **Analytics & Aggregation:**
   - Leadership views real-time aggregated maturity radar charts, department segment analyses, and question-level distribution histograms in the administrative dashboard (`/admin/analytics`).

---

# Chapter 3: Technology Stack

The NIWI application stack has been deliberately chosen for enterprise stability, strict mathematical reproducibility, zero-cost deterministic compute, and compliance readiness:

| Layer / Component | Technology | Version | Purpose | Architectural Rationale & Tradeoffs |
|---|---|---|---|---|
| **Frontend Framework** | **Vue.js 3** (Composition API) | `^3.5.12` | Single Page Application (SPA) | Offers lightweight reactive state management, superior performance over heavy frameworks, and clean SFC (Single File Component) modularity. |
| **Frontend Build Tool** | **Vite** | `^5.4.9` | Development server & production bundler | Sub-second Hot Module Replacement (HMR) and optimized rollup tree-shaking for minimal bundle footprint. |
| **Frontend Routing** | **Vue Router** | `^4.4.5` | Client-side navigation & route guards | Enforces role-based navigation guards (`requiresAuth`, `requiresSuper`, `requiresOrgAuth`) before page rendering. |
| **Backend Framework** | **FastAPI** | `^0.115.0` | Asynchronous REST API Engine | High-performance Python ASGI framework with automatic OpenAPI documentation, strict Pydantic v2 data validation, and native asynchronous support. |
| **ASGI Server** | **Uvicorn** | `^0.31.0` | Web Server Gateway | Production-grade ASGI server utilizing uvloop for high-throughput asynchronous HTTP processing. |
| **Database Engine** | **PostgreSQL** | `14+` (v17.11 on Azure) | Relational ACID Data Store | Enterprise-grade reliability, rich JSONB indexing for flexible survey payloads, atomic advisory locks, and transactional outbox support. |
| **Database Driver** | **psycopg2-binary** | `^2.9.9` | Low-level PostgreSQL driver | Mature, battle-tested C-extensions for high-speed binary protocol communication and robust connection pooling (`ThreadedConnectionPool`). |
| **Authentication** | **Microsoft Entra ID (Azure AD)** | OIDC / OAuth2 | Corporate Single Sign-On | Centralized enterprise identity management, Multi-Factor Authentication (MFA), and cryptographically verified RSA JWKS signatures. |
| **Token Verification** | **PyJWT** & **cryptography** | `^2.9.0` | JWT Signature Validation | High-speed cryptographic validation of Entra ID Bearer tokens with memory-cached JWKS public keys. |
| **Secrets Management** | **Azure Key Vault** | REST API v7.4 | Production Secrets Storage | Eliminates plain-text configuration files; production database passwords and API tokens are retrieved via Azure Managed Identity. |
| **Email Service** | **Azure Communication Services** | `^1.0.0` | Transactional Email Dispatch | Enterprise email delivery infrastructure with high deliverability rates, TLS encryption, and Azure identity integration. |
| **Process Manager** | **Supervisord** | `^4.2.5` | Container Process Supervision | Orchestrates Uvicorn web workers, outbox dispatchers, and queue workers within a single cohesive container envelope. |
| **Reverse Proxy** | **Nginx** | `1.22+` | Ingress Proxy & Static Server | High-performance static asset hosting, gzip compression, SSL termination, and secure internal reverse proxying to Uvicorn. |
| **Containerization** | **Docker** (Multi-Stage) | `24+` | Container Image Packaging | Multi-stage build isolates Node.js frontend compilation from slim Python runtime, reducing production image size and attack surface. |

---

# Chapter 4: System Architecture

The NIWI architecture is organized into five decoupled layers ensuring strict separation of concerns, defensive security boundaries, and high availability.

### 4.1 Ingress & Edge Proxy Layer
All inbound web traffic passes through an **Nginx Reverse Proxy**:
- **Port 80/443 Ingress:** Nginx terminates external HTTP connections and serves static pre-compiled frontend assets (`/app/dist`) directly from the file system.
- **API Proxying:** All URI requests matching `/api/*` are reverse-proxied internally over loopback TCP to `127.0.0.1:8000`. Uvicorn is never bound directly to public network interfaces.
- **Security Headers:** Nginx and FastAPI middleware inject strict security headers on every response:
  - `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://quickchart.io;`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: SAMEORIGIN` / `DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`

### 4.2 Application & Business Logic Layer (FastAPI)
The backend is structured as a modular FastAPI monolith with clean domain boundaries:
- `app/api/`: REST routing modules (`routes.py`, `orgs.py`, `public.py`, `drafts.py`, `form_builder.py`).
- `app/core/`: Foundation services (database pooling `database.py`, configuration `config.py`, Key Vault `keyvault.py`, JWKS security `security.py`, SlowAPI `limiter.py`).
- `app/services/`: Pure business logic (scoring engine `scoring_service.py`, CRM sync `crm_service.py`, token generation `token_service.py`, transactional outbox `outbox_service.py`).
- `app/tasks/`: Asynchronous background workers (`service_bus_worker.py`, `job_worker.py`).

### 4.3 In-Memory High-Speed Caching Layer
To prevent database query thrashing during traffic bursts, the backend maintains two thread-safe, worker-local in-memory caches:
1. **Scoring Sections Cache (`get_form_sections_metadata`):**
   - Stores the active hierarchy of form sections, questions, and weights.
   - Eliminates 40 repeated database queries on every audit submission.
   - Evaluates in under 0.1ms directly from RAM.
2. **Organisation Registry Cache (`org_cache_service.py`):**
   - Pre-warms approved organizations and domain aliases.
   - Refreshed in the background every 30 minutes (`interval_seconds=1800`) via a daemon timer.
   - Supports instantaneous client-side validation as respondents type their employer name.

### 4.4 Data Persistence Layer (Azure PostgreSQL Flexible Server)
- **Database Engine:** PostgreSQL 14+ running on Azure Flexible Server (`nd_audit`).
- **Connection Sizing:** Managed via `psycopg2.pool.ThreadedConnectionPool`.
  - Web API Pool: `minconn=5, maxconn=25` (pre-warmed with 10 connections on startup to eliminate 1.5s Azure SSL handshake latency).
  - Background Worker Pool: `minconn=2, maxconn=6`.
- **Query Safeguards:** Enforced `statement_timeout = 15000` (15 seconds) preventing rogue analytical queries from exhausting connection handles.

### 4.5 External Integrations Layer
- **Azure Key Vault (`kv-niwi-prod`):** In production mode (`APP_ENV=production`), secrets are resolved securely over the Azure Instance Metadata Service (IMDS) using Managed Identity. Plain-text `.env` files are ignored.
- **Azure Communication Services (ACS):** High-volume transactional email client sending executive summaries from verified domain `donotreply@orchvate.in`.
- **HubSpot CRM:** Asynchronous REST client ingesting business leads, respondent emails, and organization maturity levels into Orchvate's CRM pipeline.

---

# Chapter 5: Complete Application Workflow

### Workflow 1: Public Employee Assessment & Submission
1. **Initiation:** Respondent navigates to `https://niwi.orchvate.in/audit` or an invitation URL `https://niwi.orchvate.in/invite/{token}`.
2. **Client Validation:**
   - Vue 3 queries `/api/public/assessment/resolve-link` to verify the invitation token and display the employer's branded header.
   - Respondent enters demographic details (Function, Role, Work Location).
   - Dynamic validation ensures required email formats and valid organization matching.
3. **Draft Autosave:**
   - Every input modification triggers an asynchronous autosave debounced to 2 seconds.
   - Vue dispatches `POST /api/drafts/save`. The server creates or updates a record in `draft_submissions` returning a draft token (`UUID`).
4. **Final Submission Dispatch:**
   - On clicking "Submit Assessment", the browser verifies that all 44 mandatory fields are populated.
   - Vue generates a cryptographic `idempotency_key` (UUID v4) and dispatches `POST /api/submit`.
5. **Synchronous Backend Ingestion:**
   - SlowAPI evaluates the respondent's IP against the rate limit threshold (default: 60 submissions/hour).
   - FastAPI parses the JSON payload against Pydantic schema `AuditSubmission`.
   - The backend checks out a pooled PostgreSQL connection and opens an atomic transaction:
     - Inserts record into `raw_submissions` with status `accepted`.
     - Inserts event into `service_bus_outbox` with status `staged`.
     - Updates `draft_submissions` marking `submitted = true`.
   - The transaction commits in under 25 milliseconds.
   - The server immediately returns `HTTP 202 Accepted` with payload:
     `{"submission_id": "...", "status": "accepted", "message": "Audit submitted successfully and queued for processing"}`.
6. **Asynchronous Background Processing:**
   - The `outbox_dispatcher` picks up the staged outbox record using `SELECT ... FOR UPDATE SKIP LOCKED`.
   - The `scoring_service` executes the deterministic 8-pillar scoring algorithm.
   - The permanent record is inserted into `submissions` and linked to the organization via `org_submission_links`.
   - An executive summary email is formatted and dispatched via Azure Communication Services.
   - The outbox record is marked `processed`.

---

# Chapter 6: API Documentation

NIWI exposes 32 RESTful API endpoints organized into logical functional modules:

### 6.1 Assessment & Submission Module
- **`POST /api/submit`**
  - *Method:* `POST`
  - *Auth:* Public (Rate-limited via SlowAPI)
  - *Status:* `202 Accepted`
  - *Payload:* Full 40-question survey responses + demographics + `idempotency_key`.
  - *Logic:* Synchronously writes to `raw_submissions` and `service_bus_outbox`; enqueues background processing.
- **`GET /api/submissions/{submission_id}/status`**
  - *Method:* `GET`
  - *Auth:* Public (requires valid `submission_id`)
  - *Status:* `200 OK`
  - *Response:* `{"submission_id": "...", "status": "processing" | "completed" | "failed"}`.
- **`POST /api/drafts/save`**
  - *Method:* `POST`
  - *Auth:* Public
  - *Status:* `200 OK`
  - *Logic:* Persists partial questionnaire state to `draft_submissions`.
- **`GET /api/drafts/resume`**
  - *Method:* `GET`
  - *Auth:* Public (Token validated)
  - *Status:* `200 OK`
  - *Logic:* Restores partial survey answers for returning respondents.

### 6.2 Administrative & Analytics Module
- **`GET /api/submissions`**
  - *Method:* `GET`
  - *Auth:* Bearer JWT (`admin` or `super` role)
  - *Status:* `200 OK`
  - *Query Params:* `page`, `limit`, `org_id`, `search`, `start_date`, `end_date`.
- **`POST /api/submissions/filter`**
  - *Method:* `POST`
  - *Auth:* Bearer JWT
  - *Status:* `200 OK`
  - *Logic:* Advanced ServiceNow-style conditional query builder supporting nested AND/OR rules.
- **`PATCH /api/submissions/{submission_id}/scores`**
  - *Method:* `PATCH`
  - *Auth:* Bearer JWT (`super` role)
  - *Status:* `200 OK`
  - *Logic:* Allows super administrators to adjust scoring weights or overrides with mandatory audit logging.
- **`PATCH /api/submissions/{submission_id}/organisation`**
  - *Method:* `PATCH`
  - *Auth:* Bearer JWT
  - *Status:* `200 OK`
  - *Logic:* Reassigns an orphaned or misattributed submission to a new organization, writing to `submission_reassignments`.

### 6.3 Organisation Management Module
- **`GET /api/orgs`**
  - *Method:* `GET`
  - *Auth:* Bearer JWT
  - *Status:* `200 OK`
  - *Logic:* Lists all registered organizations with submission counts and average inclusion scores.
- **`POST /api/orgs`**
  - *Method:* `POST`
  - *Auth:* Bearer JWT
  - *Status:* `201 Created`
  - *Logic:* Creates a new organization profile with uniqueness verification.
- **`GET /api/orgs/{org_id}/assessment-links`**
  - *Method:* `GET`
  - *Auth:* Bearer JWT
  - *Status:* `200 OK`
  - *Logic:* Generates and retrieves trackable invitation tokens with response quotas.

### 6.4 Operations & Dead-Letter Queue (DLQ) Module
- **`GET /api/admin/dashboard`**
  - *Method:* `GET`
  - *Auth:* Bearer JWT (`super` role)
  - *Status:* `200 OK`
  - *Logic:* Returns real-time ingestion queue metrics, processing latency, active workers, and error rates.
- **`GET /api/admin/submissions/dead-lettered`**
  - *Method:* `GET`
  - *Auth:* Bearer JWT (`super` role)
  - *Status:* `200 OK`
  - *Logic:* Lists all submissions that failed 3 background processing attempts.
- **`POST /api/admin/submissions/{submission_id}/replay`**
  - *Method:* `POST`
  - *Auth:* Bearer JWT (`super` role)
  - *Status:* `200 OK`
  - *Logic:* Re-enqueues a dead-lettered submission into the outbox for immediate reprocessing.

---

# Chapter 7: Database Documentation

The NIWI relational schema is deployed on **PostgreSQL 14+** under the database catalog `nd_audit`.

### 7.1 Entity Overview (20 Core Tables)
1. **`organizations`:** Primary corporate tenant profiles (`id` UUID PK, `name`, `is_active`, `approval_status`).
2. **`raw_submissions`:** Ingestion staging area for raw survey responses (`submission_id` UUID PK, `idempotency_key`, `status`, `payload` JSONB).
3. **`submissions`:** Permanent analytical store for scored audits (`id` UUID PK, `overall_score`, `pillar_scores` JSONB, `responses` JSONB).
4. **`org_submission_links`:** Many-to-many relationship linking audits to organizations with weighting factors (`org_id`, `submission_id` Composite PK).
5. **`organization_invitations`:** Trackable survey invitations with quota ceilings and expiration timestamps (`id` UUID PK, `token_hash`, `quota`).
6. **`assessment_access_tokens`:** Hashed tokens granting secure portal access (`id` UUID PK, `token_hash`).
7. **`service_bus_outbox`:** Transactional outbox coordinating asynchronous jobs (`id` UUID PK, `status`, `retry_count`).
8. **`submission_operation_states`:** Granular per-step execution idempotency tracker (`id` UUID PK, `operation`, `status`).
9. **`dashboard_snapshot`:** Cached 2-minute rollups of Super Admin queue performance telemetry.
10. **`workers`:** Heartbeat registry tracking active background ingestion worker processes.
11. **`admin_users`:** Administrative user accounts and role definitions (`id` UUID PK, `email`, `role`).
12. **`admin_sessions`:** Active administrator session tokens and expiry tracking.
13. **`audit_logs`:** Immutable compliance audit trail recording all administrative updates.
14. **`draft_submissions`:** Autosaved survey drafts awaiting final respondent submission.
15. **`saved_filters`:** Saved query filters for the administrative submissions table.
16. **`form_sections`:** Dynamic questionnaire section definitions and visual order.
17. **`form_questions`:** Individual audit questions, options, and branching rules.
18. **`submission_reassignments`:** Audit log recording organizational transfers.
19. **`system_security_settings`:** Dynamic runtime rate limit thresholds and lockout rules.
20. **`app_settings`:** Global application feature toggles.

### 7.2 Database Indexes & Performance Optimization
To guarantee sub-10ms query execution across thousands of audits, the following indexes are actively enforced:
- `idx_submissions_org_created`: `(org_name, created_at DESC)` — Optimizes organization dashboard queries.
- `idx_raw_submissions_idempotency`: `UNIQUE (idempotency_key)` — Enforces hard database-level duplicate submission rejection.
- `idx_outbox_status_created`: `(status, created_at)` — Optimizes worker polling loops with index scans.
- `idx_org_links_composite`: `(org_id, submission_id)` — Guarantees instant join performance between organizations and audit scores.

---

# Chapter 8: Authentication and Security

### 8.1 Microsoft Entra ID (Azure AD) SSO Integration
Administrative identity is secured via Microsoft Entra ID:
- **Authentication Protocol:** OpenID Connect (OIDC) / OAuth2 PKCE flow.
- **Token Format:** Cryptographically signed RSA-256 JSON Web Tokens (JWT).
- **Public Key Resolution (JWKS):** The backend queries Microsoft's well-known keys endpoint:
  `https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys`
  Keys are cached in an in-memory `TTLCache(maxsize=16, ttl=86400)` (24-hour cache), preventing Entra ID API limits from impacting API latency.
- **Cryptographic Validation:** The `jwks_middleware` verifies:
  1. Token cryptographic signature against active Microsoft public keys.
  2. `aud` (Audience) claim matches `ENTRA_CLIENT_ID`.
  3. `iss` (Issuer) claim matches `https://login.microsoftonline.com/{tenant_id}/v2.0`.
  4. Token expiration (`exp`) timestamp.

### 8.2 Development Security Guard
To prevent accidental security bypasses in production:
```python
if IS_PRODUCTION and os.environ.get("ENABLE_DEV_BYPASS", "").lower() == "true":
    print("FATAL: Development bypass is strictly prohibited in production mode.", file=sys.stderr)
    sys.exit(1)
```
The application refuses to boot if developer bypass flags are detected in production environments.

### 8.3 Rate Limiting & Abuse Prevention
- Powered by **SlowAPI** backed by in-memory sliding windows.
- Public submission endpoint `/api/submit` is strictly rate-limited to 60 requests per hour per public IP address.
- Administrative endpoints are limited to 300 requests per minute per authenticated user.

---

# Chapter 9: Submission and Processing Architecture

The core technical differentiator of NIWI is its **Durable Decoupled Ingestion Pipeline**:

```
[ Respondent Browser ]
         │  POST /api/submit (<25ms)
         ▼
[ FastAPI Ingestion Engine ]
         │  Atomic Transaction:
         ├─► Insert raw_submissions (status: accepted)
         └─► Insert service_bus_outbox (status: staged)
         ▼  HTTP 202 Accepted
[ Respondent Browser Receives Confirmation ]

─────────────────────── ASYNCHRONOUS BOUNDARY ───────────────────────

[ Outbox Dispatcher Thread ]
         │  SELECT ... FOR UPDATE SKIP LOCKED
         ▼
[ Background Worker Fleet ]
         ├─► 1. Compute Deterministic 8-Pillar Scoring
         ├─► 2. Persist submissions & org_submission_links
         ├─► 3. Generate Branded HTML Email Report
         ├─► 4. Dispatch via Azure Communication Services
         └─► 5. Sync Lead Details to HubSpot CRM
```

### 9.1 High-Volume Concurrency & In-Flight Idempotency
- **Client Idempotency Key:** When an employee clicks submit, the frontend generates a UUID v4 idempotency token.
- **Atomic Conflict Handling:** The database insert uses `ON CONFLICT (idempotency_key) DO NOTHING`. If a network glitch causes the browser to send two identical requests, the second is safely ignored, returning the existing submission reference without duplicate scoring.
- **Advisory Locks:** Organization registration employs `pg_advisory_xact_lock(hashtext(org_name))` during submission to prevent race conditions when two employees from a new organization submit simultaneously.

---

# Chapter 10: Error Handling and Reliability

The system enforces structured, predictable error recovery across every layer:

| Error Scenario | Root Cause | System Response | Recovery Mechanism |
|---|---|---|---|
| **Rate Limit Exceeded** | Client exceeded 60 submissions/hr. | HTTP 429 Too Many Requests | SlowAPI injects `Retry-After: <seconds>` header; client pauses requests. |
| **Database Network Blip** | WAN latency or Azure maintenance. | Connection checkout retry | Pool manager retries connection twice before returning HTTP 503. |
| **Worker Scoring Failure** | Malformed response structure. | Exception caught in worker loop | Message marked for retry with exponential backoff (2s, 4s, 8s). |
| **Max Retries Exceeded** | Poison payload or persistent failure. | Moved to Dead-Letter Queue | Status set to `failed` in `submission_operation_states`; visible in Super Admin DLQ dashboard. |
| **ACS Email Timeout** | Azure ACS service delay. | Worker task fails gracefully | Submission is already saved; outbox retries email send independently. |

---

# Chapter 11: Infrastructure and Azure Deployment

### 11.1 Infrastructure Topology
- **Host VM:** Azure Virtual Machine (`taiga.orchvate.com`) running Ubuntu 22.04 LTS.
- **Ingress Port:** Host Nginx listens on port 443 with TLS managed by Certbot Let's Encrypt.
- **Application Port:** Container binds to host port `8080:80` (`PORT_MAPPING="8080:80"`).
- **Network Mode:** `--network=host` enabled in production to allow container access to the Azure Instance Metadata Service (`169.254.169.254`) for Managed Identity Key Vault access.

### 11.2 Deployment Process
Deployment is automated via `deploy.sh`:
1. `git fetch origin && git reset --hard origin/main` — Syncs latest verified source code.
2. `docker build -t niwi -f Dockerfile .` — Executes multi-stage build.
3. `docker stop niwi && docker rm niwi` — Stops prior container.
4. `docker run -d --name niwi -p 8080:80 --restart unless-stopped niwi` — Launches new container.
5. Automated health check verification against `http://127.0.0.1:8080/api/health`.

---

# Chapter 12: Environment Configuration

All environment variables used across the platform are documented below. In production, sensitive variables are managed exclusively via Azure Key Vault:

| Variable Name | Description | Environment | Required | Safe Placeholder Example |
|---|---|---|:---:|---|
| `APP_ENV` | Environment classification (`development`, `test`, `production`). | All | Yes | `production` |
| `PGHOST` | PostgreSQL server hostname. | All | Yes | `YOUR_POSTGRES_SERVER.postgres.database.azure.com` |
| `PGPORT` | PostgreSQL TCP port. | All | Yes | `5432` |
| `PGDATABASE` | Database catalog name. | All | Yes | `nd_audit` |
| `PGUSER` | Database administrator username. | All | Yes | `YOUR_POSTGRES_USER` |
| `PGPASSWORD` | Database password (min 16 chars in prod, 8 if KV managed). | All | Yes | `YOUR_SECURE_DB_PASSWORD` |
| `KEY_VAULT_NAME` | Azure Key Vault resource name. | Prod | Yes | `kv-niwi-prod` |
| `REQUIRE_KEYVAULT` | Strict Key Vault enforcement flag. | Prod | No | `true` |
| `JWT_SECRET` | Cryptographic secret for signing administrative HS256 tokens. | All | Yes | `YOUR_32_CHAR_CRYPTOGRAPHIC_KEY_HERE!!` |
| `ENTRA_CLIENT_ID` | Microsoft Entra ID Application Client ID. | Prod | Yes | `00000000-0000-0000-0000-000000000000` |
| `ENTRA_TENANT_ID` | Microsoft Entra ID Directory Tenant ID. | Prod | Yes | `00000000-0000-0000-0000-000000000000` |
| `ENABLE_DEV_BYPASS`| Local development mock authentication toggle. | Dev Only | No | `false` (enforced false in prod) |
| `ACS_CONNECTION_STRING` | Azure Communication Services connection string. | Prod | Yes | `endpoint=https://YOUR_RESOURCE.communication.azure.com/;accesskey=YOUR_KEY` |
| `ACS_SENDER_ADDRESS` | Verified sending email address. | Prod | Yes | `donotreply@orchvate.in` |
| `FRONTEND_URL` | Canonical public application URL. | All | Yes | `https://niwi.orchvate.in` |
| `HUBSPOT_ACCESS_TOKEN`| Private app access token for HubSpot CRM sync. | Prod | No | `pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |

---

# Chapter 13: Monitoring and Performance

### 13.1 Health & Diagnostic Endpoints
- **`/api/health`:** Evaluates end-to-end service readiness:
  - Database ping (`SELECT 1`).
  - Azure Communication Services client verification.
  - Returns `HTTP 200` if operational, `HTTP 503` if database is down.
- **`/api/health/pool-metrics`:** Exposes real-time connection pool telemetry:
  - Active checked-out connections, peak connection count, average hold duration, long hold warnings (&gt;1000ms).
- **`/api/health/cache-metrics`:** Exposes cache hit ratios and refresh latencies for the organisation registry cache.

### 13.2 Real-World Concurrency Benchmark (Grafana k6)
Recent load testing conducted via Grafana Cloud k6 simulated 60 concurrent virtual users submitting full 40-question payloads:
- **Frontend Delivery (`GET /`):** 100% Passed (60/60). Mean response time: 79ms (p95: 169.7ms).
- **Backend Decoupled Ingestion:** Sub-25ms synchronous write times verified when rate limit limits are adjusted for enterprise shared office IPs.

---

# Chapter 14: Testing and Quality Assurance

### 14.1 Comprehensive Test Suite
The repository includes an extensive automated test suite run via `pytest`:
- `tests/test_p0_security_fixes.py`: Validates production bypass guards, password length rules, and JWT extraction.
- `tests/test_disposable_postgres.py`: Validates transaction rollbacks, advisory locks, and safety guards preventing test runs against production databases.
- `tests/test_scoring.py`: Mathematical verification of 8-pillar scoring formulas and maturity level brackets.
- `tests/test_rate_limits.py`: Verifies SlowAPI request throttles.
- `tests/test_service_bus_pipeline.py`: Validates transactional outbox polling and worker execution.

To execute tests locally:
```bash
pytest tests/ -v
```

---

# Chapter 15: Developer Setup Guide

### 15.1 Prerequisites
- Python 3.11+
- Node.js 20+ & npm 10+
- PostgreSQL 14+ (local or Docker container)

### 15.2 Step-by-Step Installation
1. **Clone Repository:**
   ```bash
   git clone https://github.com/SKY-AK05/Neurvex_Audit.git
   cd NIWI
   ```
2. **Backend Setup:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .env\Scriptsctivate
   pip install -r requirements.txt
   cp .env.example .env
   ```
3. **Database Migration:**
   ```bash
   python scripts/run_migration.py
   python scripts/seed_db.py
   ```
4. **Start Backend Server:**
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
5. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` to access the application.

---

# Chapter 16: Troubleshooting Guide

| Issue / Symptom | Possible Cause | Diagnostic Step | Resolution |
|---|---|---|---|
| **HTTP 429 Too Many Requests** | Exceeded IP rate limit threshold. | Inspect client IP address in logs. | Reset rate limit via `/api/settings/rate-limits/reset` or adjust ceiling in Settings. |
| **HTTP 401 Unauthorized on Admin** | Missing or expired Entra ID token. | Inspect `Authorization: Bearer <token>` in browser dev tools. | Re-authenticate via `/GPadmin` or check Entra ID tenant configuration in `.env`. |
| **HTTP 503 on `/api/health`** | PostgreSQL connection failed. | Check database container status and Azure firewall rules. | Ensure host IP is allowlisted in Azure PostgreSQL Flexible Server firewall. |
| **FATAL Key Vault Startup Error** | Managed identity unavailable. | Verify `KEY_VAULT_NAME` and IMDS socket on host. | Ensure VM has assigned Managed Identity with "Key Vault Secrets User" permissions. |
| **Outbox Submissions Stalled** | Background worker thread stopped. | Check Supervisord status: `supervisorctl status`. | Restart worker: `supervisorctl restart service_bus_worker`. |
| **ACS Email Dispatch Fails** | Invalid ACS connection string. | Inspect worker logs for `AzureCommunicationError`. | Check ACS connection string and verified sender domain in Azure Portal. |

---

# Chapter 17: Known Limitations and Technical Debt

1. **Single-Host Container Topology:** The current production deployment executes on a single Azure Virtual Machine via Docker and Supervisord. While adequate for current loads, horizontal auto-scaling requires migration to Azure Container Apps (ACA) or Kubernetes (AKS).
2. **In-Memory Rate Limiting:** Rate limit states are held in memory per worker process rather than in a distributed Redis cache. Multiple container replicas would enforce independent rate limits.
3. **Draft Storage Cleanup:** Unfinished drafts in `draft_submissions` do not currently have an automated cron purge policy for records older than 90 days.

---

# Chapter 18: Future Recommendations

### Priority 0: Critical (Immediate)
- **Implement Rate Limiter Key by Organization/Session:** Modify SlowAPI keying on `/api/submit` to key by session/invitation token rather than raw public IP to prevent throttling enterprise offices on shared NAT gateways.
- **Automated Secret Rotation Pipeline:** Establish automated Azure Key Vault secret rotation alerts and scheduled rotation drills.

### Priority 1: High Priority (Next 30 Days)
- **Distributed Redis Cache:** Introduce Azure Cache for Redis to share connection rate limits, session states, and organization caches across multiple worker replicas.
- **Question-Level Aggregation Views:** Complete frontend data visualization for granular input analysis (Q5–Q44) across demographic segments.

### Priority 2: Medium Priority (Quarterly)
- **Automated Draft Purge Cron:** Implement a scheduled cleanup job removing unsubmitted drafts older than 90 days to maintain database hygiene.
- **Enhanced Export Formats:** Expand export capabilities from standard CSV to customized executive PDF presentations directly generated on the backend.

### Priority 3: Long-Term Enhancements
- **AI-Powered Contextual Roadmaps:** Integrate Azure OpenAI (`gpt-4o-mini`) via background task workers to generate customized qualitative recommendations alongside deterministic numerical scores.

---
*End of Technical Documentation Source.*
