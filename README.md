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
| [**PRD (Product Requirements)**](docs/PRD.md) | The vision, user stories, personas, features, and success metrics explaining what the product does. |
| [**API Keys & Integrations**](docs/API_KEYS_AND_INTEGRATIONS.md) | Complete guide to external services (Azure PostgreSQL, ACS, Key Vault, Entra ID) and environment variables. |
| [**Frontend Technical Guide**](docs/FRONTEND.md) | Deep dive into the Vue 3 Single Page Application, components, router, styling, and user flows. |
| [**Backend Technical Guide**](docs/BACKEND.md) | Complete FastAPI reference cataloging every API endpoint, scoring service, and worker process. |
| [**Database Architecture**](docs/DATABASE.md) | PostgreSQL schema, table layouts, ER diagrams, indexes, connection pooling, and lifecycle rules. |
| [**System Design & Architecture**](docs/SYSTEM_DESIGN.md) | Comprehensive systems architecture, outbox pattern, ADRs, deployment topology, and security threat model. |
| [**Testing & QA Report (Kiwi vs. Fiwi)**](docs/TEST.md) | Real empirical test data, k6 benchmarks, and side-by-side performance analysis of Kiwi vs. Fiwi. |

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
