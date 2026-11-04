# NIWI — Pre-Implementation Architecture Audit

**Date:** November 4, 2026  
**System Target:** NIWI Organizational Inclusion & Maturity Assessment Platform (`https://niwi.orchvate.in`)  
**Objective:** Baseline audit of existing repository architecture, database schemas, processing flows, identified defects, and technical specifications prior to Azure Service Bus SDK integration and transactional outbox implementation.

---

## 1. Existing System Architecture

### 1.1 High-Level Component Topology

```
                  Client Browser (Employee / Admin)
                                 │
                                 │ HTTPS (Port 443 / TLS)
                                 ▼
                     Host Reverse Proxy: Caddy
                                 │
                                 │ HTTP (Port 8080)
                                 ▼
        ┌────────────────────────────────────────────────────────┐
        │ Docker Container: niwi (Port 8080 -> 80)               │
        │                                                        │
        │   Nginx (Port 80)                                      │
        │     ├── /        -> Static Vue.js 3 Dist (/app/dist)   │
        │     └── /api/*   -> Uvicorn via Unix Socket            │
        │                                                        │
        │   Process Supervisor (Supervisord)                     │
        │     ├── [program:nginx] (PID 8, 10, 11)                │
        │     ├── [program:uvicorn] (PID 9, 13, 14 - 2 workers)  │
        │     │     ├── ThreadedConnectionPool (min=10, max=10)  │
        │     │     └── Embedded Worker: Disabled                │
        │     └── [program:job_worker] (PID 7 - Standalone)      │
        │           ├── ThreadedConnectionPool (min=1, max=3)    │
        │           └── Job Polling Loop (SKIP LOCKED)           │
        └────────────────────────┬───────────────────────────────┘
                                 │
                                 │ TLS / WAN Link (~185 ms RTT)
                                 │ Chicago, USA -> Hong Kong, HK
                                 ▼
        ┌────────────────────────────────────────────────────────┐
        │ Azure Database for PostgreSQL Flexible Server          │
        │  - Host: generative-ai.postgres.database.azure.com     │
        │  - Region: East Asia (Hong Kong) [IP: 20.2.146.109]    │
        │  - max_connections: 50 (Shared instance)               │
        │  - Active application connections: 22 / 50             │
        └────────────────────────────────────────────────────────┘
```

### 1.2 Azure Service Bus Infrastructure Baseline

The external Azure Service Bus infrastructure was verified during Phase 0:

| Resource Property | Configured Value | Verification Status |
| :--- | :--- | :---: |
| **Subscription** | Microsoft Azure Sponsorship (`e2d35239-5448-45ae-b156-d3309a9052a9`) | Verified |
| **Resource Group** | `Aakash_ML` | Verified |
| **Namespace** | `niwi-bus` | Verified |
| **Namespace Hostname** | `niwi-bus.servicebus.windows.net` | Verified |
| **Region** | East Asia (Hong Kong) | Verified |
| **SKU** | Standard | Verified |
| **Queue** | `niwi-submission-queue` | Verified |
| **Auth Mode** | Azure Managed Identity (`DefaultAzureCredential`) | **Verified via IMDS (Token Acquired)** |
| **VM Client ID** | `1f4b521a-e3ea-4b6a-b796-62f550008e49` | Verified |
| **Queue REST Probe** | Peek/Receive probe returned `HTTP 204 No Content` | **Verified (Permissions Confirmed)** |
| **Duplicate Detection**| 10-minute window | Verified |
| **Lock Duration** | 1 minute | Verified |
| **Max Delivery Count**| 10 attempts | Verified |

---

## 2. Existing Processing Flow & Lifecycle Analysis

### 2.1 Submission Ingestion (`POST /api/submit`)
1. **Entry Point:** Handled by `submit` in `Audit/app/api/routes.py`.
2. **Rate Limiting:** Enforced per IP using SlowAPI (`@limiter.limit("100/hour")` and `1000/day`).
3. **In-Memory Scoring (Pre-DB):** 
   - Metadata cached in `scoring_service.py` via `get_form_sections_metadata(None)`.
   - `scores = calculate_scores_pure(data)` runs entirely in-memory with zero network overhead (`scoring_ms = 0.09 ms`).
4. **Organisation & Invitation Resolution:**
   - If `invitation_token` is present: hashes token, queries `organization_invitations`, checks expiry/limits.
   - If `organization_id` is present: validates against `organizations`.
   - If `company_name` is present without ID: looks up or creates approved organization under an advisory lock.
5. **Atomic CTE Execution:**
   - Single SQL transaction executing:
     1. `duplicate_check`: Checks for submissions within 5 minutes.
     2. `idempotent_check`: Checks for matching `idempotency_key`.
     3. `org_lookup`: Verifies active organisation.
     4. `new_sub`: Inserts into `submissions` (`ON CONFLICT (idempotency_key) DO NOTHING`).
     5. `new_link`: Inserts into `org_submission_links`.
     6. `new_email_job`: Inserts into `post_submit_jobs` (`job_type='email'`).
     7. `new_crm_job`: Inserts into `post_submit_jobs` (`job_type='crm'`) if `crm_sync_enabled = TRUE`.
     8. `new_admin_job`: Inserts into `post_submit_jobs` (`job_type='admin_notify'`).
     9. `update_invitation`: Increments `submission_count`.
     10. `update_draft`: Marks draft `submitted = TRUE`.
   - Returns 4-tuple: `(new_id, existing_idempotent_id, duplicate_id, valid_org_id)`.
6. **Connection Hold Time:** ~560 ms across the Pacific WAN link.

### 2.2 Background Worker Ownership & Execution
- **Current Worker:** `job_worker.py` runs as process PID 7 under Supervisord (`[program:job_worker]`).
- **Web Workers:** Embedded background worker is disabled in `app/main.py`.
- **Claiming Mechanism:** `claim_next_job` uses `SELECT ... FROM post_submit_jobs WHERE status IN ('PENDING', 'RETRY') AND next_attempt_at <= NOW() ORDER BY created_at ASC LIMIT 1 FOR UPDATE SKIP LOCKED`.
- **Processing Logic:**
  - `email`: Reads persisted submission scores, calls `build_email` to render SVG radial charts and HTML body, writes `submissions.email_body`, dispatches via `send_acs_email`, marks job `DONE`.
  - `crm`: Calls `sync_to_hubspot`, searches/updates contact, creates deal, associates deal with contact, marks job `DONE`.
  - `admin_notify`: Dispatches notification email to admin, marks job `DONE`.
- **Retry Mechanism:** `fail_or_retry_job` uses exponential backoff: $5 \times 2^{\text{attempts}-1}$ seconds (capped at 300s). Marks `FAILED` when `attempts >= 5`.
- **Reclamation:** `reclaim_stranded_jobs` runs every 60 seconds to reclaim jobs stuck in `PROCESSING` longer than 5 minutes.

---

## 3. Existing PostgreSQL Schema Reference

### Table: `submissions`
| Column | Type | Constraints / Purpose |
| :--- | :--- | :--- |
| `id` | `uuid` | Primary Key, `DEFAULT gen_random_uuid()` |
| `name`, `designation`, `company_name`, `email`, `contact_number` | `varchar` | Demographic user data |
| `q5` through `q44` | `varchar` | Normalized 40 question responses ("Yes", "Partially", "No", "NA") |
| `lc_score` through `sp_score` | `numeric` | 8 pillar maturity scores (0.0 to 20.0) |
| `lc_level` through `sp_level` | `varchar` | Maturity tier labels |
| `overall_avg`, `overall_level` | `numeric`, `varchar` | Overall assessment average score and tier |
| `email_body` | `text` | Rendered HTML audit report |
| `status` | `varchar` | Lifecycle status (`pending`, `sent`, etc.) |
| `organization_id` | `uuid` | Foreign key to `organizations(id)` |
| `answers` | `jsonb` | Dynamic responses dictionary |
| `dimension_scores` | `jsonb` | Dimension score dictionary and visibility metadata |
| `idempotency_key` | `varchar` | Unique partial index `WHERE idempotency_key IS NOT NULL` |
| `submitted_at` | `timestamp` | Timestamp with index `(email, submitted_at DESC)` |

### Table: `post_submit_jobs`
| Column | Type | Constraints / Purpose |
| :--- | :--- | :--- |
| `id` | `uuid` | Primary Key, `DEFAULT gen_random_uuid()` |
| `submission_id` | `uuid` | Foreign key to `submissions(id)` |
| `job_type` | `varchar` | Job type (`email`, `crm`, `admin_notify`) |
| `status` | `varchar` | `PENDING`, `PROCESSING`, `RETRY`, `DONE`, `FAILED` |
| `payload` | `jsonb` | Job payload parameters |
| `attempts`, `max_attempts` | `integer` | Current attempts and maximum threshold (default 5) |
| `next_attempt_at` | `timestamptz` | Scheduled execution time with polling index |
| `last_error` | `text` | Traceback/message of last failure |
| `locked_at`, `locked_by` | `timestamptz`, `varchar` | Concurrency lease tracking |

---

## 4. Identified Defects Requiring Remediation (Phase 1)

During independent verification, four specific defects were identified:

### Defect 1: Concurrent Duplicate Email Race Condition
- **Problem:** When 10 concurrent requests with the identical email arrive at the exact same millisecond without an `idempotency_key`, all 10 pass the CTE's `SELECT id FROM submissions WHERE email = ... AND submitted_at > NOW() - INTERVAL '5 minutes'` under PostgreSQL `READ COMMITTED` isolation, inserting 10 duplicate submissions.
- **Fix:** Serialize submissions for the same email using a transaction-scoped advisory lock derived from the normalized email:
  ```sql
  SELECT pg_advisory_xact_lock(hashtext(LOWER(TRIM(%(email)s))));
  ```

### Defect 2: Parallel Idempotency-Key Collision HTTP 500
- **Problem:** When 10 concurrent requests arrive simultaneously with the exact same `idempotency_key`, PostgreSQL enforces the unique index via `ON CONFLICT (idempotency_key) DO NOTHING`. The winning request inserts the row, but the 9 losing requests receive `new_id = NULL` from `RETURNING id`. Because the winner's row is not yet visible to the losers' initial snapshot, `existing_idempotent_id` is also `NULL`, triggering an unhandled `HTTP 500: Database error persisting submission`.
- **Fix:** Before raising HTTP 500 in `routes.py`, execute a fallback query `SELECT id FROM submissions WHERE idempotency_key = %(idempotency_key)s` if `idempotency_key` is present. Return `HTTP 200` with the winner's `submission_id`.

### Defect 3: Fragile Connection Status Inspection & Leak on Broken Sockets
- **Problem:** 
  1. `database.py` checks `conn.status != STATUS_READY` directly, causing `AttributeError` on test mocks and wrapped connection objects.
  2. If an `OperationalError` occurs (e.g., broken TCP socket to Azure), `PooledConnection.close()` terminates `conn.close()` without calling `self._pool.putconn(self._conn, close=True)`, causing psycopg2 to permanently burn a connection slot in `self._used`.
- **Fix:** 
  1. Use `getattr(conn, "status", None)`.
  2. Catch `psycopg2.OperationalError` and invoke `self._pool.putconn(self._conn, close=True)`.

### Defect 4: Test Harness Out-of-Sync
- **Problem:** `tests/conftest.py` has no pattern matchers in `MockCursor` for the atomic `WITH duplicate_check AS` CTE query, and `MockConnection` lacks the `.status` attribute. This causes 20 unit test failures in the offline test suite despite production running cleanly.
- **Fix:** Update `conftest.py` mock cursor and connection to support the CTE query syntax, advisory locks, and status checks.

---

## 5. Target Architecture: Azure Service Bus & Transactional Outbox

```
 [Client / User]
       │
       │ POST /api/submit
       ▼
 [FastAPI API Route]
       │
       │ 1. In-Memory Score Computation (< 0.1 ms)
       │ 2. Single Atomic PostgreSQL Transaction:
       │    ├── Acquire Advisory Lock on Email Hash
       │    ├── Check Duplicate Email Window & Idempotency Key
       │    ├── INSERT INTO submissions
       │    ├── INSERT INTO org_submission_links
       │    ├── INSERT INTO post_submit_jobs (Legacy Fallback / Tracking)
       │    └── INSERT INTO service_bus_outbox (status = 'PENDING')
       │ 3. COMMIT Transaction (Single RTT across WAN)
       ▼
 [PostgreSQL Database] (Source of Truth)
       │
       │ Polled by Dispatcher via FOR UPDATE SKIP LOCKED
       ▼
 [Outbox Dispatcher Process] (Standalone Supervisor Program)
       │
       │ 1. Claims outbox batch (status = 'CLAIMED', lease = 60s)
       │ 2. Publishes to Azure Service Bus (MessageId = outbox.id)
       │ 3. Receives send confirmation from Service Bus
       │ 4. Updates outbox (status = 'PUBLISHED')
       ▼
 [Azure Service Bus Queue: niwi-submission-queue]
       │
       │ PeekLock Mode (lock duration = 60s, max delivery count = 10)
       ▼
 [Dedicated Service Bus Worker Process] (Standalone Supervisor Program)
       │
       │ 1. Receives message in PeekLock mode
       │ 2. Checks idempotency (has event already been processed?)
       │ 3. Atomically claims processing state in PostgreSQL
       │ 4. Executes side effects:
       │    ├── Renders HTML email & saves to submissions.email_body
       │    ├── Dispatches email via ACS
       │    ├── Dispatches admin notification
       │    └── Syncs contact & deal to HubSpot CRM (if enabled)
       │ 5. Updates processing record (status = 'COMPLETED')
       │ 6. Completes Service Bus message (settlement)
```

---

## 6. Files Requiring Modification & Creation

| File | Type | Purpose |
| :--- | :---: | :--- |
| `migrations/016_service_bus_outbox.sql` | **New** | DDL migration for `service_bus_outbox` table and indexes |
| `app/core/config.py` | **Modify** | Add Service Bus configuration settings & feature flags |
| `app/core/database.py` | **Modify** | Fix defensive `status` check and dead connection handling (`close=True`) |
| `app/core/service_bus.py` | **New** | Service Bus client singleton, Managed Identity credential management |
| `app/services/outbox_service.py` | **New** | Outbox dispatcher service with `SKIP LOCKED` and batch publishing |
| `app/tasks/service_bus_worker.py`| **New** | Dedicated PeekLock message receiver, idempotency check, and processor |
| `app/api/routes.py` | **Modify** | Advisory lock on email, parallel idempotency fallback, atomic outbox insert |
| `app/api/submission_status.py` | **New** | `GET /api/submissions/{id}/status` endpoint with tenant isolation |
| `app/tasks/job_worker.py` | **Modify** | Feature-flagged backward compatibility for legacy jobs |
| `supervisord.conf` | **Modify** | Add `[program:outbox_dispatcher]` and `[program:service_bus_worker]` |
| `requirements.txt` | **Modify** | Add `azure-servicebus>=7.12.0` |
| `tests/conftest.py` | **Modify** | Update mock engine for CTE, advisory locks, status, and outbox |

---

## 7. Migration, Rollback & Safety Strategy

### Safe Rollback Procedure
1. **Source of Truth Rule:** PostgreSQL remains the definitive source of truth at all times.
2. **Backward Compatibility:** All existing records in `post_submit_jobs` remain active. The legacy worker process continues running to drain pending jobs.
3. **Feature Flag (`ENABLE_SERVICE_BUS_PIPELINE`):**
   - When `false`: Submissions are processed through the existing `post_submit_jobs` and `job_worker` pipeline.
   - When `true`: Submissions insert into both `post_submit_jobs` (flagged as `ROUTED_TO_SB`) and `service_bus_outbox`.
   - Emergency Rollback: Setting `ENABLE_SERVICE_BUS_PIPELINE=false` and restarting containers immediately reverts all traffic to the legacy database queue without data loss.
4. **No Premature Deletions:** Neither `post_submit_jobs` nor legacy worker logic will be deleted.

---

## 8. Phase 0 Audit Sign-Off

The baseline audit is complete. All prerequisites, Managed Identity permissions, database tables, and defect root causes have been verified with live evidence. Proceed to Phase 1.

