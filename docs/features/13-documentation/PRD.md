# Technical Documentation & Operational Runbooks

> Unit `13-documentation` · kind: feature

## Summary

System architecture specifications, deployment guides, database runbooks, and operator references.

## Context & goal

The Documentation unit maintains high-fidelity operational guides, architecture references, and operator instructions. It ensures that engineers, architects, and security auditors have immediate access to verifiable documentation for deployment, troubleshooting, and maintenance.

## User stories

- As a New Engineer, I consult documentation to understand application architecture and complete local setup in under 30 minutes.
- As an Operator on Call, I follow runbooks to diagnose database connection pool alerts and dead-letter queue backlogs.

## Functional requirements

- 1. Architecture & Design Documentation [confirmed]: Maintain high-level system diagrams, sequence flows, and ER diagrams.
- 2. API & Data Model Reference [confirmed]: Provide exact endpoint contracts, payload schemas, and database table definitions.
- 3. Operational Runbooks [confirmed]: Document deployment procedures, Azure Key Vault configuration, and disaster recovery workflows.


## Interfaces & data

Serves as the specification for the entire NIWI repository.

## Acceptance criteria

- Given a newly onboarded engineer, When following the setup guide, Then they can successfully run and verify the test suite.
- Given an auditor reviewing security, When inspecting documentation, Then all cryptographic protocols and secret storage patterns are fully documented.

## Edge cases & failure modes

- **Documentation drift:** Automated reconstruction validation ensures documentation stays in sync with code updates.

## Definition of done

- All functional requirements implemented and verified against code.
- All acceptance scenarios verified with passing unit or integration tests.
- Zero unresolved callouts, placeholders, or ambiguous specifications.
- Security and authorization policies strictly enforced.
- Performance and error recovery verified under edge conditions.

## Improvements & enhancements

- Integrate automated documentation builds with VitePress or MkDocs for searchable web publishing.


## Source material

Key source for this unit (4 file(s) total, showing up to 15):

#### `README.md`

````
# NIWI — Neurodiversity Inclusion Workplace Index

> **In plain words:**  
> NIWI is an enterprise digital audit platform that helps companies measure, benchmark, and improve how well they support neurodivergent employees (such as individuals with ADHD, Autism, or Dyslexia). It replaces vague diversity claims with an automated 40-question assessment, mathematical scoring across 8 workplace pillars, and actionable executive scorecards.
>
> **Last updated:** November 5, 2026  
> **Platform Operator:** Orchvate | **Production URL:** [https://niwi.orchvate.in](https://niwi.orchvate.in)  

---

## 1. Why This Exists

For decades, organizations have wanted to support neurodiversity, but had no objective way to measure their progress. Standard HR surveys ask generic satisfaction questions that overlook critical barriers like sensory overload, interview biases, or lengthy accommodation delays. Furthermore, company executives often rate their culture as highly inclusive, while frontline neurodivergent staff experience significant everyday friction.

NIWI solves this problem by acting as an objective, digital "medical checkup" for workplace inclusion. It gives employers verified mathematical scores across 8 dimensions, highlights perception gaps between leadership and staff, and outlines concrete steps to attract and retain top neurodivergent talent.

---

## 2. What NIWI Can Do Today

- **40-Question Guided Assessment:** Accessible, sensory-conscious questionnaire covering 8 core organizational pillars.
- **Dynamic Context Gating:** Skips irrelevant questions (such as physical office or supplier procurement) for remote companies without penalizing scores.
- **Save & Magic Resume:** Allows employees to save an in-progress assessment and resume later via a secure, tokenized email link.
- **Deterministic 8-Pillar Scoring:** Calculates transparent 0–20 point scores and maturity levels in < 1ms with 0% AI hallucination risk.
- **Multi-Respondent Weighted Scoring:** Aggregates scores across an entire company, supporting custom role weights (e.g., 1.5× for leadership).
- **Perception Gap Analysis:** Instantly highlights score variances between executive leadership and frontline neurodivergent staff.
- **Asynchronous Ingestion Pipeline:** Acknowledges survey submissions in under 500ms using a transactional PostgreSQL outbox and background worker fleet.
- **Operations Command Dashboard:** Gives Super Admins real-time telemetry on queue depth, active worker processes, latency metrics, and one-click Dead-Letter Queue (DLQ) replay.
- **5-Minute Batched Admin Digest:** Automatically aggregates audit notifications by organization into a consolidated 5-minute summary email.
- **Two-Role Administrative Security:** Enforces strict role-based access control backed by Microsoft Entra ID (Azure AD) Single Sign-On.

---

## 3. High-Level Architecture

```mermaid
flowchart LR
    User[Respondent / Employee] -->|HTTP /audit| Nginx[Nginx Ingress (Port 80)]
    Admin[HR / System Admin] -->|HTTP /portal| Nginx
    
    Nginx -->|Static Assets| Vue3[Vue 3 SPA (Vite)]
    Nginx -->|/api/* Requests| FastAPI[FastAPI Backend (Port 8000)]
    
    FastAPI -->|Fast 201 Ingest| PG[(Azure PostgreSQL Flexible Server)]
    FastAPI -.->|JWKS Auth| EntraID[Microsoft Entra ID SSO]
    
    PG -.->|Transactional Outbox| Workers[Adaptive Worker Fleet (nproc - 1)]
    Workers -->|Scoring & Org Linking| PG
    Workers -->|5-Min Consolidated Digest| ACS[Azure Communication Services]
```

---

## 4. Documentation Map

Every part of the NIWI platform is thoroughly documented across specialized, dual-audience guides:

| Document | Plain Words Purpose |
|---|---|
| [**PRD (Product Requirements)**](../../00-overview/PRD.md) | The vision, user stories, personas, features, and success metrics explaining what the product does. |
| [**API Keys & Integrations**](../../architecture/ARCHITECTURE.md) | Complete guide to external services (Azure PostgreSQL, ACS, Key Vault, Entra ID) and environment variables. |
| [**Frontend Technical Guide**](../../architecture/DESIGN-SYSTEM.md) | Deep dive into the Vue 3 Single Page Application, components, router, styling, and user flows. |
| [**Backend Technical Guide**](../../architecture/ARCHITECTURE.md) | Complete FastAPI reference cataloging every API endpoint, scoring service, and worker process. |
| [**Database Architecture**](../../architecture/DATA-MODEL.md) | PostgreSQL schema, table layouts, ER diagrams, indexes, connection pooling, and lifecycle rules. |
| [**System Design & Architecture**](../../architecture/ARCHITECTURE.md) | Comprehensive systems architecture, outbox pattern, ADRs, deployment topology, and security threat model. |
| [**Testing & QA Report (Kiwi vs. Fiwi)**](../../features/12-tests/PRD.md) | Real empirical test data, k6 benchmarks, and side-by-side performance analysis of Kiwi vs. Fiwi. |

---

## 5. Quick Start Guide

### Prerequisites
- **Python:** Version 3.11 or 3.13
- **Node.js:** Version 18 or 20+ (with npm)
- **Database:** PostgreSQL 14+ instance running locally or on Azure

---

### Step 1: Clone and Configure Environment
```bash
# 1. Clone the repository
git clone https://github.com/orchvate/niwi.git
cd niwi

# 2. Copy the template configuration file
cp .env.example .env
```

Open `.env` in your text editor and ensure development mode is enabled:
```ini
APP_ENV=development
ENABLE_DEV_BYPASS=true
PGHOST=localhost
PGPORT=5432
PGDATABASE=nd_audit
PGUSER=postgres
PGPASSWORD=YOUR_DATABASE_PASSWORD
JWT_SECRET=dev-insecure-only-local-testing-secret-key-32chars-min!!
FRONTEND_URL=http://localhost:5173
```

---

### Step 2: Database Setup & Migrations
```bash
# 1. Install Python backend dependencies
pip install -r requirements.txt

# 2. Execute all sequential database migrations
python scripts/migrate.py
```

---

### Step 3: Run the Application Locally

#### Terminal 1 — Backend API Server:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
*API interactive documentation will be available at:* `http://127.0.0.1:8000/docs`

#### Terminal 2 — Frontend Development Server:
```bash
cd frontend
npm install
npm run dev
```
*Frontend web application will be live at:* `http://localhost:5173`

---

### Step 4: Run the Automated Test Suite
```bash
# Run the complete test suite
pytest tests/

# Run the Super Admin Operations Dashboard tests specifically
pytest tests/test_super_admin_dashboard.py
```

---

## 6. Project Folder Structure

```
NIWI/
├── app/                         # FastAPI backend application source code
│   ├── api/                     # REST API route controllers
│   ├── core/                    # Security, database pooling, configuration & Key Vault
│   ├── models/                  # Pydantic data schemas and validation contracts
│   ├── services/                # Deterministic scoring, outbox, filter compiler & business logic
│   └── tasks/                   # Background worker fleet and process heartbeat tracker
├── frontend/                    # Vue 3 Single Page Application (Composition API)
│   ├── public/                  # Static web assets (logos, illustrations, favicon)
│   └── src/                     # Vue source code (views, components, router, api gateway)
├── docs/                        # Canonical platform documentation suite
├── migrations/                  # Sequentially numbered SQL schema migration files
├── scripts/                     # Operational scripts (database migration runner, seeders)
├── tests/                       # Automated pytest test suites and k6 performance suites
├── supervisord.conf             # Multi-process production supervisor (Nginx + Uvicorn + Workers)
├── docker-entrypoint.sh         # Adaptive CPU core detector and worker pool scaler
├── Dockerfile                   # Multi-stage production container build definition
└── deploy.sh                    # Host server automated deployment script
```

---

## 7. Support & Governance

- **Platform Operator:** Orchvate ([https://orchvate.com](https://orchvate.com))
- **Support & Inquiries:** `support@orchvate.in`
- **License Information:** Proprietary Enterprise Platform. All rights reserved by Orchvate. Unauthorized copying, distribution, or commercial use is strictly prohibited.

````

#### `infrastructure/userlist.txt`

```
"pguser" "md5_hashed_password"

```

#### `sql/README.md`

````
# SQL scripts — NeuroMark Audit

Run these on your PostgreSQL database **`nd_audit`**.

## Quick start (everything)

```bash
psql -h YOUR_HOST -U YOUR_USER -d nd_audit -f sql/install_all.sql
```

Creates `submissions`, `app_settings`, notification columns, and support inbox defaults.

## Run step by step

| File | Purpose |
|------|---------|
| `01_admin_notifications.sql` | Admin **bell** alerts when a new audit is submitted |
| `02_support_requests.sql` | **Support** page form emails |
| `install_all.sql` | Full schema + both features (recommended for new installs) |

```bash
psql -h YOUR_HOST -U YOUR_USER -d nd_audit -f sql/01_admin_notifications.sql
psql -h YOUR_HOST -U YOUR_USER -d nd_audit -f sql/02_support_requests.sql
```

## Default admin inbox

Both scripts default to:

`aakash.padyachi@rochvate.com`

Change this in the SQL files before running, or update later in **NeuroMark → Settings**.

## App settings columns

| Column | Used for |
|--------|----------|
| `sender_name` | From name on outgoing audit result emails |
| `sender_address` | From address (Azure Communication Services verified domain) |
| `notification_email` | New audit alerts (bell icon must be ON) |
| `notifications_enabled` | `TRUE` = bell alerts active |
| `support_email` | Support form submissions |

## After running SQL

1. Restart the Azure Functions API  
2. In the app: **Settings** → confirm emails and from address  
3. Click the **bell** to enable new-audit notifications  
4. Test **Support** page with a sample message  

````

#### `sql/archive/README.md`

````
# SQL Archive

This directory contains SQL scripts that have been superseded by the migration system or were one-time operations.

---

## Archived Scripts

### `create_table.sql`
**Status**: Superseded by migrations  
**Original Purpose**: Initial schema creation  
**Superseded By**: Migrations 002-019 (see `../migrations/`)  
**Archived**: November 2026

The authoritative schema is now defined by the sequential migrations in the `migrations/` directory. This script is preserved for historical reference.

### `install_all.sql`
**Status**: Superseded by `scripts/migrate.py`  
**Original Purpose**: Batch migration runner  
**Superseded By**: `../scripts/migrate.py` and `../scripts/run_migration.py`  
**Archived**: November 2026

The canonical migration runner is now `scripts/migrate.py`, which provides idempotent migration execution with proper error handling.

### `fix_missing_columns.sql`
**Status**: One-time fix (likely already applied)  
**Original Purpose**: Schema repair for missing columns  
**Applied**: Pre-November 2026 (historical)  
**Archived**: November 2026

This was a one-time schema fix. The corrections have been incorporated into the proper migrations. Preserved for historical reference.

---

## Active SQL Scripts

For current SQL operations, see:

- **Migrations**: `../migrations/` - All schema changes (migrations 002-019)
- **Functions**: `../01_admin_notifications.sql`, `../02_support_requests.sql`
- **Migration Runner**: `../scripts/migrate.py`

---

## Migration System

NIWI uses sequential, idempotent SQL migrations stored in `migrations/`:

```
migrations/
├── 002_app_settings.sql
├── 003_support_email.sql
├── 004_designation.sql
├── 005_rbac.sql
├── 006_org_scoring.sql
├── 007_fix_score_columns.sql
├── 008_dynamic_forms.sql
├── 009_question_dependencies.sql
├── 010_saved_filters.sql
├── 011_verify_submission_id_type.sql
├── 012_dual_entry_invitations.sql
├── 013_organization_admins.sql
├── 014_submission_reassignments.sql
├── 015_performance_jobs_and_idempotency.sql
├── 016_service_bus_outbox.sql
├── 017_per_operation_idempotency.sql
├── 018_assessment_access_tokens.sql
├── 019_system_security_settings.sql
├── 01_remediation.sql
└── 02_features_migration.sql
```

All migrations use `IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS` patterns for idempotency.

To run migrations:
```bash
python scripts/migrate.py
```

---

**Archived**: November 4, 2026  
**Reason**: Superseded by migration system

````


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

