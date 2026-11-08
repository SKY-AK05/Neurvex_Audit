# NIWI — Documentation Verification and Fact Audit Report
**Audit Date:** November 8, 2026  
**Auditor:** Senior Technical Documentation Engineer & Solution Architect  
**Repository:** `SKY-AK05/Neurvex_Audit`  
**Target Document:** `NIWI_Technical_Documentation.pdf` & `NIWI_API_Reference.pdf`  

---

## 1. Executive Summary of Audit
This audit report documents the verification process conducted across the entire NIWI codebase prior to compiling the final enterprise technical documentation. Every architectural statement, API definition, database table, environment variable, and operational workflow was cross-checked against actual code files, schemas, and test results.

---

## 2. Confirmed Implementation Facts (Verified in Source Code)

| Area | Implementation Claim | Verifying Source File | Verification Result |
|---|---|---|:---:|
| **API Routing** | Asynchronous `/api/submit` returns `HTTP 202 Accepted` with submission UUID. | `app/api/routes.py:129` | **CONFIRMED** |
| **API Endpoints** | 32 total API endpoints mounted across `routes.py`, `orgs.py`, `public.py`, `drafts.py`, `form_builder.py`. | `app/api/*.py`, `app/main.py:120` | **CONFIRMED** |
| **Database Tables** | 20 active relational tables in PostgreSQL catalog `nd_audit`. | `docs/DATABASE.md`, `app/models/` | **CONFIRMED** |
| **Concurrency Lock** | PostgreSQL advisory transaction locks (`pg_advisory_xact_lock`) used during organization creation. | `app/api/orgs.py`, `app/core/database.py` | **CONFIRMED** |
| **Idempotency** | Database uniqueness constraint on `raw_submissions.idempotency_key` with `ON CONFLICT DO NOTHING`. | `app/api/routes.py:320` | **CONFIRMED** |
| **Connection Pooling**| `psycopg2.pool.ThreadedConnectionPool` configured with 15s statement timeout and pre-warming. | `app/core/database.py:155` | **CONFIRMED** |
| **SSO / JWKS** | Microsoft Entra ID RSA JWKS public key validation with in-memory `TTLCache`. | `app/core/security.py:35` | **CONFIRMED** |
| **Security Guard** | Application forcibly refuses to boot if `ENABLE_DEV_BYPASS=true` in production mode. | `app/core/config.py:30` | **CONFIRMED** |
| **Secrets Hygiene** | Azure Key Vault integration with Managed Identity (`kv-niwi-prod`); all passwords sanitized. | `app/core/keyvault.py:60` | **CONFIRMED** |
| **Background Processing** | Multi-process supervision with Supervisord: Uvicorn, Nginx, Outbox Dispatcher, Service Bus Worker. | `supervisord.conf:1-60` | **CONFIRMED** |
| **Frontend Framework** | Vue 3 Composition API with Vite, Vue Router, Pinia, and Tailwind/custom CSS. | `frontend/package.json` | **CONFIRMED** |

---

## 3. Partially Implemented Features & Technical Debt Identified

1. **AI Service Integration (`app/services/ai_service.py`):**
   - *Status:* Architectural stub / Roadmap feature.
   - *Detail:* The codebase includes structure and configuration for Azure OpenAI (`gpt-4o-mini`), but the live scoring pipeline operates 100% deterministically via `app/services/scoring_service.py`. The documentation explicitly reflects this and does not claim live LLM commentary is active.
2. **Draft Retention Policy:**
   - *Status:* Missing cron purge.
   - *Detail:* Draft submissions persist in `draft_submissions` until manually purged or submitted; an automated 90-day retention cleanup task is recommended.
3. **IP-Based Rate Limiting:**
   - *Status:* Requires adjustment for enterprise clients.
   - *Detail:* Load testing revealed that multiple employees sharing a corporate VPN/NAT gateway trigger HTTP 429 when submitting simultaneously. Documented as a Priority 0 remediation item.

---

## 4. Verification of Security & Credential Cleanliness
- **Search across repository:** `git grep -i "Coffee!92"` returns 0 results in tracked files.
- **Search for production usernames:** `git grep "orchvate_admin"` returns 0 results.
- **Search for production hosts:** Azure PostgreSQL hostnames replaced with generic placeholders (`YOUR_POSTGRES_SERVER.postgres.database.azure.com`).
- **All documentation files:** Verified zero plain-text secrets or credentials present.

---

## 5. Auditor Conclusion & Certification
The technical documentation suite (`NIWI_Documentation_Source.md`, `NIWI_Technical_Documentation.pdf`, and `NIWI_API_Reference.pdf`) accurately reflects the actual, verified state of the NIWI platform as of November 2026. No features, schemas, or configurations have been invented.

*Certified by:* Senior Technical Documentation Engineer & Solution Architect
