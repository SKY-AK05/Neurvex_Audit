# NIWI Product Audit — Documentation Package (Version 2.1)
## Master Index & Technical Handover Reference
### Prepared for: Executive Leadership, Engineering Teams, QA Auditors & External Reviewers
### Document ID: DOC-00-INDEX
### Platform Operator: Orchvate | Production URL: https://niwi.orchvate.in
### Audit Date: November 2026 | Audit Scope: Full System & Mathematical Formula Verification

---

## 1. About the NIWI Platform

The **Neurodiversity Inclusion Workplace Index (NIWI)**, commercially branded as the **NeuroMark Audit Platform**, is an enterprise B2B SaaS platform engineered by **Orchvate**. It provides organisations with an automated, scientifically grounded mechanism to evaluate, quantify, and advance their workplace inclusion practices for neurodivergent professionals (individuals with ADHD, Autism, Dyslexia, Dyspraxia, Tourette's, and related neurodivergent identities).

The platform combines:
- An accessible, multi-step public audit questionnaire completed by employees and organizational representatives.
- A deterministic mathematical scoring engine evaluating 8 distinct organizational pillars.
- An administrative reporting and customer relationship management suite.
- A tenant-isolated organizational reporting portal with weighted multi-respondent aggregation.

The platform is live in production at **`https://niwi.orchvate.in`**.

---

## 2. Complete Document Inventory

The documentation package in `docs/product-audit/` consists of **seven interconnected, standalone technical documents**:

| # | Document Title | File Name | Primary Target Audience | Core Technical & Business Purpose |
|---|---|---|---|---|
| **00** | **Audit Master Index** *(this file)* | [`README.md`](./README.md) | All Stakeholders | Navigation guide, reading order, executive highlights, and audit scope boundaries. |
| **01** | **Executive Product Audit Summary** | [`EXECUTIVE_AUDIT_SUMMARY.md`](./EXECUTIVE_AUDIT_SUMMARY.md) | Executive Leadership, Board, PMs | High-level business overview, capability matrix, critical risks, and official readiness verdict. |
| **02** | **Product Requirements Document (PRD)** | [`01_PRODUCT_REQUIREMENTS_DOCUMENT.md`](./01_PRODUCT_REQUIREMENTS_DOCUMENT.md) | Product Managers, QA, Engineers | Comprehensive 17-point requirement specifications, business problems, user journeys, and traceability matrix. |
| **03** | **Frontend Technical Documentation** | [`02_FRONTEND_TECHNICAL_DOCUMENTATION.md`](./02_FRONTEND_TECHNICAL_DOCUMENTATION.md) | Frontend Engineers, UI/UX, QA | Vue 3 + Vite SPA architecture, route security guards, component-by-component deep dive, and WCAG accessibility standards. |
| **04** | **Backend Technical Documentation** | [`03_BACKEND_TECHNICAL_DOCUMENTATION.md`](./03_BACKEND_TECHNICAL_DOCUMENTATION.md) | Backend Engineers, SRE, Architects | FastAPI architecture, complete API endpoint inventory, ERD database schema, and security threat mitigations. |
| **05** | **System Workflow & Architecture** | [`04_SYSTEM_WORKFLOW_AND_ARCHITECTURE.md`](./04_SYSTEM_WORKFLOW_AND_ARCHITECTURE.md) | Software Architects, DevOps, SRE | 12 detailed Mermaid diagrams mapping authentication, concurrency advisory locks, submission processing, and container build pipelines. |
| **06** | **Testing, QA & Performance Report** | [`05_TESTING_QA_AND_PERFORMANCE_REPORT.md`](./05_TESTING_QA_AND_PERFORMANCE_REPORT.md) | QA Directors, SRE, Tech Leads | Empirical k6 performance benchmark data (1 VU vs 10 VUs), functional test inventory, defect register, and SLA compliance. |
| **07** | **Formula & Calculation Logic Reference** | [`06_FORMULA_AND_CALCULATION_LOGIC.md`](./06_FORMULA_AND_CALCULATION_LOGIC.md) | Data Analysts, Math/QA Auditors, Devs | Comprehensive mathematical reference: LaTeX formulas for CALC-001 through CALC-017, worked numerical examples, and consistency audits. |

---

## 3. Recommended Reading Paths

Depending on your organizational role, navigate the documentation package along these recommended paths:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXECUTIVE / GOVERNANCE PATH                            │
│ 1. README.md (Master Index)                                                 │
│ 2. EXECUTIVE_AUDIT_SUMMARY.md (Business value, risks, and readiness rating) │
│ 3. 06_FORMULA_AND_CALCULATION_LOGIC.md (Section 3: Metric interpretation)   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      ENGINEERING & ARCHITECTURE PATH                        │
│ 1. README.md                                                                │
│ 2. 04_SYSTEM_WORKFLOW_AND_ARCHITECTURE.md (End-to-end component flows)      │
│ 3. 02_FRONTEND_TECHNICAL_DOCUMENTATION.md (Vue 3 client implementation)     │
│ 4. 03_BACKEND_TECHNICAL_DOCUMENTATION.md (FastAPI & PostgreSQL schema)      │
│ 5. 06_FORMULA_AND_CALCULATION_LOGIC.md (Pure scoring algorithms)           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      QA, SRE & PERFORMANCE ENGINEERING PATH                 │
│ 1. README.md                                                                │
│ 2. 05_TESTING_QA_AND_PERFORMANCE_REPORT.md (Empirical k6 data & defects)   │
│ 3. 01_PRODUCT_REQUIREMENTS_DOCUMENT.md (Traceability matrix & acceptance)   │
│ 4. 06_FORMULA_AND_CALCULATION_LOGIC.md (Formula boundary test proofs)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Key Audit Findings & Strategic Highlights

1. **Deterministic Mathematical Scoring (100% Consistent):**
   The scoring engine across all 8 operational dimensions is fully deterministic, transparent, and verified. Scores are computed from discrete mappings ($+4, +2, 0\text{ pts}$), dynamically rescaled for non-applicable questions, and aggregated into a Weighted Organizational Index with explicit Context Applicability reconciliation. (See [`06_FORMULA_AND_CALCULATION_LOGIC.md`](./06_FORMULA_AND_CALCULATION_LOGIC.md).)
2. **Robust Multi-Tenant Security & Identity:**
   Administrative access is guarded by Microsoft Entra ID with cryptographic JWKS signature verification. Client organizational members access tenant-isolated dashboards via single-use, 15-minute magic links stored exclusively as SHA-256 hashes. PostgreSQL advisory locks (`pg_advisory_xact_lock`) guarantee zero duplicate organizations during concurrent signups. (See [`03_BACKEND_TECHNICAL_DOCUMENTATION.md`](./03_BACKEND_TECHNICAL_DOCUMENTATION.md) and [`04_SYSTEM_WORKFLOW_AND_ARCHITECTURE.md`](./04_SYSTEM_WORKFLOW_AND_ARCHITECTURE.md).)
3. **Critical Performance Bottleneck Under Load (SLA Breach):**
   Empirical k6 benchmark reports confirm that at a concurrency of just 10 Virtual Users, the submission success rate drops to **40.0%** (6 lost submissions) and P95 latency spikes to **30,000.73 ms** (a 10x breach of the 3,000 ms SLA). This is caused by database connection pool starvation (`maxconn=10`) and synchronous in-flight QuickChart operations. (See [`05_TESTING_QA_AND_PERFORMANCE_REPORT.md`](./05_TESTING_QA_AND_PERFORMANCE_REPORT.md).)
4. **High Feature Completeness (~95%):**
   All core capabilities (assessment wizard, draft save/resume, automated scoring, QuickChart radar charts, ACS transactional emails with dead-letter queueing, and admin analytics) are fully implemented and verified in the source code. AI-based narrative recommendations exist as an unintegrated code stub (`app/services/ai_service.py`), deferred by design. (See [`01_PRODUCT_REQUIREMENTS_DOCUMENT.md`](./01_PRODUCT_REQUIREMENTS_DOCUMENT.md).)
5. **Frontend View Complexity:**
   The primary assessment form component (`AuditForm.vue`, 5,456 lines) and organization management portal (`Organisations.vue`, 5,896 lines) have grown into monolithic files that present maintainability risks. (See [`02_FRONTEND_TECHNICAL_DOCUMENTATION.md`](./02_FRONTEND_TECHNICAL_DOCUMENTATION.md).)

---

## 5. Official Readiness Determination

```
================================================================================
                         OVERALL READINESS RATING:
                           READY WITH CONDITIONS
================================================================================
```

### Mandatory Conditions for Unconditional Production Release:
1. **(P0 Blocker) Resolve Concurrency Bottleneck (DEF-001 / DEF-002):**
   Decouple `POST /api/submit` to immediately commit raw answers and return an HTTP 202 Accepted, offloading scoring, chart generation, and email dispatch to asynchronous background workers. Configure PgBouncer and increase database pool connections to `maxconn=40`. Re-run k6 benchmarks at 50 VUs to prove P95 latency $< 2,500\text{ ms}$ and 0% submission drops.
2. **(P1 Security) Implement TTLCache for Entra ID JWKS (DEF-003):**
   Replace unexpiring `@lru_cache` in `app/core/security.py` with a 1-hour time-to-live cache to prevent administrative lockout during Microsoft signing key rotation.
3. **(P1 Assurance) Execute pytest Suite Against Real PostgreSQL:**
   Run the 17 automated test suites against a containerized PostgreSQL instance to establish a verifiable passing test execution report.

---
*Documentation Package compiled, certified, and archived in `docs/product-audit/`.*
