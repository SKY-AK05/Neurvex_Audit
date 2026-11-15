# NIWI — Reconstruction Overview

| Setting | Value |
| --- | --- |
| Mode | `preserve` |
| Level | `complex` |
| Fidelity | `embed` |
| Generated with | `reconstruct@2.29.16` |

## Product summary

The **Neuro-Inclusive Workplace Index (NIWI)** is an enterprise assessment, benchmarking, and organizational intelligence platform engineered by Orchvate. NIWI enables enterprises to evaluate, score, and systematically enhance workplace inclusion for neurodivergent professionals (encompassing Autism, ADHD, Dyslexia, Dyspraxia, and Sensory Processing differences). Respondents complete a comprehensive 40-question assessment spanning 8 foundational inclusion dimensions alongside demographic metadata. The platform delivers instant, personalized reflection insights to individual respondents while aggregating organizational data to calculate an objective inclusion maturity score (0–160 aggregate, 0–20 per pillar) mapped to five progression tiers (Foundational, Early Progress, Developing, Proficient, Leading).

Engineered for enterprise scale, data privacy, and zero respondent deanonymization, NIWI isolates sensitive individual submissions from reporting analytics. Architecturally, public survey submissions are ingested asynchronously with sub-25ms response times (`HTTP 202 Accepted`) using an atomic transactional outbox pattern in PostgreSQL backed by a decoupled background processor. Multi-tenant corporate access is secured via Microsoft Entra ID (Azure AD) OAuth2 OIDC with RS256 JWKS validation, enterprise secrets are sealed in Azure Key Vault via Managed Identity, and organizational administrators access real-time participation tracking, invitation links, radar analytics, and exportable executive roadmaps.

## Tech stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn, Psycopg2 (Connection Pooling)
- **Frontend:** Vue 3 (Composition API), Vite, Vue Router, Pinia, Custom CSS Design System
- **Database:** PostgreSQL 14+ (Flexible Server), 22 Schema Migrations
- **Background Processing:** Python Multi-Process Worker + Transactional Outbox Pattern (`SELECT ... FOR UPDATE SKIP LOCKED`), Supervisord
- **Security & Secrets:** Microsoft Entra ID (JWKS / PyJWT), Azure Key Vault (`kv-niwi-prod`), SlowAPI Rate Limiting, OWASP Hardened
- **External Integrations:** Azure Communication Services (Transactional Email), HubSpot CRM (Lead Sync)
- **Testing & Quality:** Pytest, Playwright (E2E), Concurrency Tests, SQL Injection / Security Verification

## Metrics

- Files analyzed: **236** (62498 lines)
- Features/modules: **13**
- Routes: **80**
- Locales: **0**
- Tracked env vars: **45**

## Feature index

- [`01-core`](../features/01-core/PRD.md) — **Core**: Application boot, database pooling, security middleware, JWT validation, configuration, and rate limiting.
- [`02-project-setup`](../features/02-project-setup/PRD.md) — **Project Setup & Tooling**: Docker, Docker Compose, Nginx ingress, Supervisord daemon supervision, environment templates, and package manifests.
- [`03-migrations`](../features/03-migrations/PRD.md) — **Migrations**: 22 sequential SQL migration scripts establishing core schemas, outbox, dynamic forms, and performance indexes.
- [`04-sql`](../features/04-sql/PRD.md) — **Sql**: Auxiliary and administrative notification and support database scripts.
- [`05-models`](../features/05-models/PRD.md) — **Models**: Pydantic and domain models for audits, users, RBAC, form definitions, and validation schemas.
- [`06-utils`](../features/06-utils/PRD.md) — **Utils**: CSV report export, token generation, cryptographic validation, and branded email formatting.
- [`07-services`](../features/07-services/PRD.md) — **Services**: Core deterministic scoring engine (8 pillars, 5 tiers), organization analytics, outbox processing, email policy, and settings.
- [`08-api`](../features/08-api/PRD.md) — **API**: REST endpoints for survey submission, administrative dashboards, organization management, invitations, drafts, and system telemetry.
- [`09-frontend`](../features/09-frontend/PRD.md) — **Frontend**: Vue 3 SPA with responsive survey flows, draft auto-save, executive dashboards, radar charts, and admin management portals.
- [`10-scripts`](../features/10-scripts/PRD.md) — **Scripts**: Database initialization, seeding, synthetic data import, schema reconciliation, and operational utilities.
- [`11-tasks`](../features/11-tasks/PRD.md) — **Tasks**: Daemon workers for outbox dispatching and Service Bus background message scoring and email notifications.
- [`12-tests`](../features/12-tests/PRD.md) — **Tests**: Exhaustive test suite covering unit tests, API tests, concurrency safety, security verification, and performance benchmarks.
- [`13-documentation`](../features/13-documentation/PRD.md) — **Documentation**: Operational guides, deployment runbooks, and codebase architecture references.

## How to use this output

1. Read `architecture/ARCHITECTURE.md` for the overall shape, then `architecture/INTERFACES.md` (the full interface surface) and `architecture/DATA-MODEL.md` (entities & relations).
2. Rebuild feature by feature using each `features/<slug>/PRD.md`, in the order listed in `REBUILD.md`.
3. Use `data/` (translations, schema, config) and — when present — `source/` as ground truth.
