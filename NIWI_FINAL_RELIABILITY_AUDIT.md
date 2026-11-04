# NIWI — Final Service Bus Reliability Audit & Idempotency Analysis

**Audit Timestamp:** 2026-11-04 06:53:00 UTC  
**Environment:** Production (`https://niwi.orchvate.in` / `52.240.143.40:8080`)  
**Container:** `niwi` (`fff31cbd42ec`)  
**Database:** Azure Database for PostgreSQL Flexible Server (`20.2.146.109:5432`)  
**Message Broker:** Azure Service Bus Namespace `niwi-bus.servicebus.windows.net` (Queue: `niwi-submission-queue`)  
**Audit Protocol:** STRICT READ-ONLY FORENSICS (No production mutations, code edits, deployments, test submissions, or backfills)

---

## Executive Summary & Overall Verdict

An exhaustive, read-only reliability and idempotency audit was executed across the NIWI codebase, operating system process tables, Azure Service Bus broker telemetry, and PostgreSQL data stores to investigate the five architectural risks highlighted in the post-deployment verification.

### Overall Architecture Verdict

# **OPERATIONAL WITH KNOWN RISKS**

While the core messaging plumbing (PostgreSQL transactional outbox, asynchronous dispatcher, Azure Service Bus broker, and background consumer) is active, operational, and steadily draining events, **the architecture cannot yet be certified as production-ready for high-concurrency workloads or exactly-once external side effects**. 

The system exhibits critical architectural risks that require remediation before running multi-user load benchmarks:
1. **Dual-Worker Race Condition:** Both `job_worker.py` (legacy poller) and `service_bus_worker.py` (Service Bus consumer) run concurrently under Supervisord. Every HTTP submission atomically inserts records into *both* queues, causing both workers to compete and execute redundant work on the same submission.
2. **False-Positive External Delivery Statuses:** Submissions are marked `email_status = 'SENT'` and `crm_status = 'SYNCED'` simply because HTML template generation and internal function calls completed without throwing an exception, despite `ACS_CONNECTION_STRING` and `HUBSPOT_ACCESS_TOKEN` being completely unconfigured in the environment.
3. **Non-Idempotent Side Effects:** If a worker crashes midway or Service Bus redelivers a message, HubSpot CRM deals are duplicated (`POST /crm/v3/objects/deals` has no deduplication key), and admin alert emails are re-sent.
4. **Historical Backfill Hazard:** 772 pre-migration submissions have `async_status = 'PENDING'`. A blind SQL backfill would falsely certify them as delivered when external email delivery and CRM sync never took place.

---

## Investigation 1 — Dual-Worker Execution & Idempotency Analysis

### 1.1 Can both workers process the same submission?
- **Finding:** **YES.** Both workers process every single new submission in parallel.
- **Classification:** **VERIFIED**
- **Risk Severity:** **HIGH**
- **Evidence:**
  1. In [`supervisord.conf`](file:///home/aakash.padyachi/apps/niwi/Audit/supervisord.conf#L33-L64):
     Supervisord launches both worker processes simultaneously on container startup:
     ```ini
     [program:job_worker]
     command=python3 -m app.tasks.job_worker
     autostart=true

     [program:outbox_dispatcher]
     command=python3 -m app.services.outbox_service
     autostart=true

     [program:service_bus_worker]
     command=python3 -m app.tasks.service_bus_worker
     autostart=true
     ```
  2. In [`app/api/routes.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/api/routes.py#L306-L330):
     The submission transaction executes a dual-write into both queues inside the single atomic CTE:
     ```sql
     -- Lines 306-324: Writes legacy jobs
     new_email_job AS (
         INSERT INTO post_submit_jobs (submission_id, job_type, payload)
         SELECT id, 'email', %(email_job_payload)s::jsonb FROM new_sub
     ),
     new_crm_job AS (
         INSERT INTO post_submit_jobs (submission_id, job_type, payload) ...
     ),
     new_admin_job AS (
         INSERT INTO post_submit_jobs (submission_id, job_type, payload) ...
     ),
     -- Lines 325-338: Writes Service Bus outbox event
     new_outbox_event AS (
         INSERT INTO service_bus_outbox (event_type, aggregate_id, payload, status)
         SELECT 'SUBMISSION_CREATED', id, json_build_object(...)::jsonb, 'PENDING'
         FROM new_sub
     )
     ```
  3. **Execution Scenario:**
     When a user completes an assessment:
     - `job_worker.py` (PID 7) polls `post_submit_jobs` via `SELECT ... FOR UPDATE SKIP LOCKED` and claims the `email`, `crm`, and `admin_notify` jobs.
     - Concurrently, `outbox_service.py` (PID 9) claims the outbox event and sends it to Azure Service Bus.
     - `service_bus_worker.py` (PID 10) pulls the message from Azure Service Bus and immediately executes `process_email_job()`, `process_crm_job()`, and `process_admin_notify_job()`.
     - Both worker processes run the exact same tasks for the exact same `submission_id`.

### 1.2 Can they generate duplicate reports?
- **Finding:** **YES.** Both workers invoke the HTML report generation routine for the same submission.
- **Classification:** **VERIFIED**
- **Risk Severity:** **MEDIUM**
- **Evidence:**
  - In [`app/tasks/job_worker.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/tasks/job_worker.py#L128-L158), `process_email_job()` calculates section scores, generates the HTML string via `build_email()`, and executes:
    ```sql
    UPDATE submissions SET email_body = %s WHERE id = %s
    ```
  - In [`app/tasks/service_bus_worker.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/tasks/service_bus_worker.py#L80), `service_bus_worker` imports and invokes the exact same function:
    ```python
    process_email_job(submission_id, email_payload)
    ```
  - **Database Impact:** The HTML body is generated twice on CPU and written twice to PostgreSQL. While the second write overwrites the first with identical HTML (idempotent in data state), it wastes CPU cycles and database connection pool bandwidth.

### 1.3 Can they send duplicate emails?
- **Finding:** **POTENTIALLY YES.** If `ACS_CONNECTION_STRING` is configured, duplicate admin notification emails will be dispatched.
- **Classification:** **VERIFIED**
- **Risk Severity:** **HIGH**
- **Evidence:**
  - User audit report emails are not automatically sent upon submission (they are only generated and stored in `submissions.email_body`; user dispatch is triggered manually by admins via `POST /api/submissions/{id}/send` in [`app/api/routes.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/api/routes.py#L1255-L1300)).
  - However, **Admin Notification Alerts** are triggered automatically upon submission:
    - `job_worker.py` line 316 executes `process_admin_notify_job(sub_id, payload)`, which calls [`notify_admin_new_submission()`](file:///home/aakash.padyachi/apps/niwi/Audit/app/services/settings_service.py#L310) in [`app/services/settings_service.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/services/settings_service.py#L323).
    - `service_bus_worker.py` line 103 independently executes `process_admin_notify_job(submission_id, admin_payload)`.
    - Both workers spawn background threads (`threading.Thread(target=bg_send)`) to call `send_acs_email()`.
    - Currently, duplicate emails do not reach recipient inboxes only because `ACS_CONNECTION_STRING` is unconfigured (`send_acs_email` exits early). As soon as production ACS credentials are provided, **administrators will receive two duplicate alert emails for every single submission**.

### 1.4 Can they perform duplicate CRM updates?
- **Finding:** **YES.** Duplicate Deal records will be created in HubSpot.
- **Classification:** **VERIFIED**
- **Risk Severity:** **HIGH**
- **Evidence:**
  - In [`app/services/crm_service.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/services/crm_service.py#L46-L178), `sync_to_hubspot()` executes:
    1. Search for existing Contact by email (`POST /crm/v3/objects/contacts/search`). If found, it updates via `PATCH` (idempotent).
    2. But for **Deals** (lines 135-156):
       ```python
       deal_url = "https://api.hubapi.com/crm/v3/objects/deals"
       deal_properties = {
           "dealname": f"NeuroMark Audit Deal — {company_name}",
           "dealstage": deal_stage,
           "pipeline": "default", ...
       }
       deal_res = make_hubspot_request("POST", deal_url, {"properties": deal_properties})
       deal_id = deal_res.get("id")
       ```
    3. `POST /crm/v3/objects/deals` does **NOT** check if a deal was already created for `submission_id` and does not supply a HubSpot idempotency token.
    4. When both `job_worker` and `service_bus_worker` call `process_crm_job`, **two separate Deal objects are created in HubSpot for the same customer assessment**.

### 1.5 What prevents duplicate processing after a worker crash?
- **Finding:** **NOTHING.** No checkpointing exists; redelivery causes full re-execution.
- **Classification:** **VERIFIED**
- **Risk Severity:** **HIGH**
- **Evidence:**
  - In [`app/tasks/service_bus_worker.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/tasks/service_bus_worker.py#L55-L75):
    ```python
    cur.execute("SELECT async_status FROM submissions WHERE id = %s", (str(submission_id),))
    sub = cur.fetchone()
    if sub[0] == "COMPLETED":
        return
    ```
  - The deduplication check only tests whether `async_status == "COMPLETED"`.
  - However, `async_status` is updated to `"COMPLETED"` **at the very end of the function** (lines 115-125).
  - If `service_bus_worker.py` crashes after generating reports, after syncing CRM, or after notifying admins—but before the final PostgreSQL commit—the message lock expires in Azure Service Bus.
  - The broker redelivers the message to a surviving worker. The surviving worker sees `async_status == 'PENDING'`, re-runs report generation, re-creates deals in CRM, and re-notifies admins.

### 1.6 Is there a per-side-effect idempotency mechanism?
- **Finding:** **NO.** No side-effect ledger, transition journal, or per-step idempotency keys exist.
- **Classification:** **VERIFIED**
- **Risk Severity:** **HIGH**
- **Evidence:**
  - All status flags (`async_status`, `email_status`, `crm_status`, `async_completed_at`) are written together in a single atomic SQL statement at the conclusion of the worker routine.
  - If any failure or crash occurs during execution, the application possesses zero state records indicating which specific external actions succeeded.

---

## Investigation 2 — Email Delivery Accuracy & Status Reconciliation

### 2.1 Reconciling `acs: degraded` with `email_status = SENT`
- **Finding:** The system records `email_status = 'SENT'` because it equates local HTML report compilation with external email transmission.
- **Classification:** **VERIFIED**
- **Risk Severity:** **CRITICAL**

### Diagnostic Trace & Code Proof

#### 1. Why `https://niwi.orchvate.in/api/health` reports `"acs": "degraded"`
In [`app/main.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/main.py#L124-L130):
```python
# Check ACS connectivity
try:
    client = EmailClient.from_connection_string(os.environ.get("ACS_CONNECTION_STRING", ""))
    health_status["acs"] = "up"
except Exception:
    health_status["acs"] = "degraded" # We don't fail the pod if email is down
```
When `ACS_CONNECTION_STRING` is empty, `EmailClient.from_connection_string("")` raises `ValueError("Invalid connection string")`. The exception handler catches this and returns `"acs": "degraded"`.

#### 2. Why `send_acs_email()` bypasses delivery
In [`app/services/settings_service.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/services/settings_service.py#L244-L248):
```python
def send_acs_email(..., submission_id: str = None) -> None:
    acs_conn = os.environ.get("ACS_CONNECTION_STRING") or os.environ.get("ACS-CONNECTION-STRING", "")
    if not acs_conn:
        logger.warning("ACS_CONNECTION_STRING not configured. Email dispatch bypassed for submission %s", submission_id)
        return
```
When `ACS_CONNECTION_STRING` is missing, `send_acs_email` silently returns `None` without raising an exception.

#### 3. Why `service_bus_worker.py` marks `email_status = 'SENT'`
In [`app/tasks/service_bus_worker.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/tasks/service_bus_worker.py#L76-L110):
```python
# 2. Process Email Job
email_success = False
try:
    email_payload = payload.get("email_job_payload") or {}
    process_email_job(submission_id, email_payload)
    email_success = True
except Exception as e:
    logger.error("Failed to generate/send email for submission %s: %s", submission_id, e)

...

final_email_status = "SENT" if email_success else "FAILED"
final_crm_status = "SYNCED" if crm_success else "FAILED"
overall_status = "COMPLETED" if email_success else "PARTIAL"
```
- `process_email_job()` only generates the HTML report string into `submissions.email_body`. It does not send an email to the user.
- Because `process_email_job()` succeeds without raising an exception, `email_success` evaluates to `True`.
- Line 108 evaluates: `final_email_status = "SENT" if email_success else "FAILED"`.
- The worker writes `email_status = 'SENT'` and `async_status = 'COMPLETED'` to PostgreSQL.

#### 4. Diagnostic Proof: HubSpot CRM Status is similarly misrepresented
In [`app/services/crm_service.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/services/crm_service.py#L51-L54):
```python
if not HUBSPOT_ACCESS_TOKEN:
    logger.info("HubSpot access token not configured, skipping CRM sync for submission %s", submission_id)
    return
```
Because `HUBSPOT_ACCESS_TOKEN` is unset, `sync_to_hubspot()` exits with `None`. Line 91 of `service_bus_worker.py` sets `crm_success = True`, and line 109 sets `final_crm_status = "SYNCED"`.

### Empirical Verdict on Delivery
- **Is ACS configured?** **NO.**
- **Is email delivery bypassed?** **YES.**
- **Does the worker mark emails as `SENT` without sending?** **YES.**
- **Is delivery confirmed by ACS?** **NO.**
- **Are skipped emails represented accurately?** **NO.** Status is mislabeled as `SENT` instead of `SKIPPED` or `NOT_CONFIGURED`.

---

## Investigation 3 — Azure Service Bus Backlog & Live Drain Telemetry

A real-time, non-destructive audit of Azure Service Bus queue `niwi-submission-queue` was performed using `ServiceBusAdministrationClient` and `receiver.peek_messages()`. No messages were consumed, settled, or modified.

### 3.1 Queue Metrics Progression Across the Audit

| Timestamp (UTC) | Active Message Count | Dead-Letter Count | Total Message Count | Drain Status |
|---|---|---|---|---|
| **06:41:15** | 83 | 1 | 84 | Baseline during initial check |
| **06:44:38** | 72 | 1 | 73 | Draining (-11 messages) |
| **06:50:43** | 36 | 1 | 37 | Draining (-36 messages) |
| **06:51:39** | 30 | 1 | 31 | Draining (-6 messages) |
| **06:52:17** | 26 | 1 | 27 | Draining (-4 messages) |
| **06:52:44** | 23 | 1 | 24 | Draining (-3 messages) |

**Conclusion:** The queue is **actively and consistently draining** at a steady rate of approximately 1 message every 8 to 12 seconds (matching the time required to reconstruct section scores and perform PostgreSQL commits).

### 3.2 Age of Active Messages
- **Oldest Active Message in Queue:**
  - ID: `outbox-91a7d2b1-1668-42bb-8e43-d2bc8a6f875e`
  - Sequence Number: `149`
  - Enqueued Time: `2026-11-04 06:38:58.070000 UTC`
  - Age at Inspection: `699.0 s (~11.6 minutes)`
- **Newest Active Message in Queue:**
  - ID: `outbox-803d4103-e237-4a04-a9cb-02285043cb63`
  - Sequence Number: `178`
  - Enqueued Time: `2026-11-04 06:41:30.494000 UTC`
  - Age at Inspection: `546.6 s (~9.1 minutes)`

### 3.3 Message Redelivery & Abandonment Check
- **Delivery Count Inspection:** All peeked active messages have `delivery_count = 0`.
- **Finding:** No messages are failing, crashing, or cycling in retry loops. Messages are being picked up in strict FIFO order on their very first delivery attempt.
- **Classification:** **VERIFIED**

### 3.4 Dead-Letter Queue Inspection
- **DLQ Count:** Exactly **1 message**.
  - Message ID: `test-1793772920.421246`
  - Sequence Number: `2`
  - Enqueued Time: `2026-11-04 06:15:20.518000 UTC`
  - Dead-Letter Reason: `JSONDecodeError`
  - Dead-Letter Description: `Expecting value: line 1 column 1 (char 0)`
- **Finding:** The single DLQ message was an unformatted raw string probe injected during initial plumbing tests. The worker correctly trapped the JSON parse exception and routed the message directly to `$deadletterqueue` without blocking the pipeline.
- **Classification:** **VERIFIED**

### 3.5 Database Mapping Verification
All active message IDs were cross-referenced against PostgreSQL:
```sql
SELECT id, aggregate_id, event_type, status FROM service_bus_outbox WHERE id::text = ANY(...);
SELECT id, email, status, async_status FROM submissions WHERE id::text = ANY(...);
```
- **Outbox Records Found:** **34 / 34 (100.0%)**
- **Submission Records Found:** **34 / 34 (100.0%)**
- **Missing / Orphaned Records:** **ZERO (0)**
- **Classification:** **VERIFIED**

---

## Investigation 4 — Transactional Outbox Consistency

Direct, read-only SQL queries were executed against `service_bus_outbox` and `submissions`.

### 4.1 Outbox Table Distribution (`SELECT status, count(*) FROM service_bus_outbox`)
- `PUBLISHED`: **182**
- `PROCESSING`: **0**
- `PENDING`: **0**
- `FAILED`: **0**
- `DEAD_LETTER`: **0**

### 4.2 Unpublished Events & Lease Expirations
- Oldest Unpublished Event: **None** (100% of outbox events are published).
- Expired Leases (`status = 'PROCESSING' AND locked_until < NOW()`): **0**.
- **Classification:** **VERIFIED**

### 4.3 In-Flight Reconciliation
- `PUBLISHED` events where submission is not yet `COMPLETED`: Exactly **23 events**.
- Active messages in Service Bus queue: Exactly **23 messages**.
- Mathematical Conservation:
  $$\text{Total Published } (182) = \text{Completed Submissions } (158) + \text{In-Flight In Memory } (1) + \text{In Service Bus Queue } (23)$$
  Event conservation is **100.00% exact**. Zero dropped messages, zero orphaned records.
- **Classification:** **VERIFIED**

### 4.4 Duplicate Outbox Records
- Duplicate check query:
  ```sql
  SELECT aggregate_id, count(*) FROM service_bus_outbox GROUP BY aggregate_id HAVING count(*) > 1;
  ```
- Result: **0 rows returned**. Every submission aggregate corresponds to exactly one outbox record.
- **Classification:** **VERIFIED**

---

## Investigation 5 — Historical Submissions Forensic Audit

An in-depth data forensics query was executed to analyze all 954 records in `submissions`, specifically focusing on the 772 records created prior to migration 016.

### 5.1 Submissions Breakdown by Epoch

```sql
SELECT 
    COUNT(*) AS total_submissions,
    COUNT(*) FILTER (WHERE async_status = 'COMPLETED') AS completed_count,
    COUNT(*) FILTER (WHERE async_status = 'PENDING') AS pending_count,
    COUNT(*) FILTER (WHERE async_status = 'PENDING' AND submitted_at < '2026-11-04 06:13:57.878589+00:00') AS pending_pre_migration,
    COUNT(*) FILTER (WHERE async_status = 'PENDING' AND submitted_at >= '2026-11-04 06:13:57.878589+00:00') AS pending_post_migration
FROM submissions;
```

**Diagnostic Results:**
- **Total Submissions in Database:** `954`
- **Currently `COMPLETED`:** `158` (Post-migration Service Bus pipeline)
- **Currently `PENDING`:** `796`
  - **Post-Migration In-Flight Queue:** `24` (Currently draining)
  - **Pre-Migration Historical Records:** `772`

### 5.2 Forensic Audit of the 772 Pre-Migration Records

| Audit Check | SQL Inspection Query | Result / Count | Percentage |
|---|---|---|---|
| **Report HTML Generated?** | `SELECT count(*) FROM submissions WHERE async_status = 'PENDING' AND submitted_at < '2026-11-04 06:13:57' AND email_body IS NOT NULL` | **772** | **100.0%** |
| **Legacy `post_submit_jobs` marked DONE?** | `SELECT count(DISTINCT s.id) FROM submissions s JOIN post_submit_jobs j ON s.id = j.submission_id WHERE s.async_status = 'PENDING' AND j.status = 'DONE'` | **608** | **78.8%** |
| **Pre-queue submissions without jobs?** | `SELECT count(*) FROM submissions s LEFT JOIN post_submit_jobs j ON s.id = j.submission_id WHERE s.async_status = 'PENDING' AND j.id IS NULL` | **164** | **21.2%** |
| **Submissions with legacy status = 'sent'?** | `SELECT count(*) FROM submissions WHERE async_status = 'PENDING' AND status = 'sent'` | **0** | **0.0%** |
| **Submissions with legacy status = 'pending'?** | `SELECT count(*) FROM submissions WHERE async_status = 'PENDING' AND status = 'pending'` | **772** | **100.0%** |

### 5.3 Forensic Interpretation
1. **The HTML Reports Were Generated:** All 772 historical submissions have their HTML assessment bodies generated and stored in `submissions.email_body`.
2. **608 Submissions Were Handled By Legacy Queue:** 608 submissions were processed by the legacy `post_submit_jobs` table (1,066 individual jobs completed and marked `DONE`).
3. **164 Submissions Pre-Date the Queue System:** 164 records were created in early versions of NIWI prior to the introduction of `post_submit_jobs`, where scores were calculated synchronously.
4. **No External Deliveries Occurred:** None of the 772 submissions have `status = 'sent'`. Because `ACS_CONNECTION_STRING` and `HUBSPOT_ACCESS_TOKEN` were unconfigured, **no emails were transmitted and no CRM deals were created**.
5. **Backfill Risk Assessment:**
   Executing `UPDATE submissions SET async_status = 'COMPLETED' WHERE async_status = 'PENDING'` would be **factually incorrect and dangerous**. It would mask the fact that external customer delivery never occurred for these 772 historical submissions.
   - **Recommendation:** **DO NOT EXECUTE THE BACKFILL.** Keep historical submissions in their true state or introduce an explicit status such as `ARCHIVED_UNSENT`.

---

## 6. Comprehensive Findings & Risk Matrix

| Risk ID | Investigation Area | Finding Description | Severity | Status | Remediation Required |
|---|---|---|---|---|---|
| **RSK-01** | Dual Workers | Both `job_worker` and `service_bus_worker` process the same submission concurrently. | **HIGH** | **VERIFIED** | Decommission `job_worker.py` from `supervisord.conf` and delete `post_submit_jobs` CTE writes. |
| **RSK-02** | CRM Duplication | `sync_to_hubspot()` unconditionally executes `POST` on `/crm/v3/objects/deals` without deduplication. | **HIGH** | **VERIFIED** | Search for existing deals by `audit_id` or attach an idempotency key to HubSpot API calls. |
| **RSK-03** | Status Misrepresentation | Submissions are marked `email_status = SENT` when email delivery was actually bypassed. | **CRITICAL** | **VERIFIED** | Update worker to record `SKIPPED` or `NOT_CONFIGURED` when `ACS_CONNECTION_STRING` is unset. |
| **RSK-04** | Crash Redelivery | If worker crashes before `UPDATE submissions`, re-delivery duplicates external side effects. | **HIGH** | **VERIFIED** | Implement fine-grained per-step state transitions or transactional side-effect ledger. |
| **RSK-05** | Historical Data | 772 historical submissions never completed external dispatch. | **MEDIUM** | **VERIFIED** | Reject proposed bulk backfill; maintain accurate legacy audit trail. |
| **RSK-06** | Service Bus Drain | Active messages in queue represent historical test backlog draining steadily. | **LOW** | **VERIFIED** | Monitor until queue reaches 0 active messages; no manual intervention required. |

---

## 7. Actionable Remediation Architecture (Step-by-Step)

The following sequence of non-breaking remediations is recommended before re-commencing load testing:

### Step 1: Establish Single Job Ownership (Decommission Legacy Worker)
1. In [`app/api/routes.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/api/routes.py#L306-L324), remove `new_email_job`, `new_crm_job`, and `new_admin_job` CTE blocks. Only keep `new_outbox_event`.
2. In [`supervisord.conf`](file:///home/aakash.padyachi/apps/niwi/Audit/supervisord.conf#L33-L43), remove `[program:job_worker]`.
3. This guarantees that **exactly one execution path** exists for every submission.

### Step 2: Accurate Status Semantics in Worker
Update [`app/tasks/service_bus_worker.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/tasks/service_bus_worker.py#L108-L111):
```python
acs_configured = bool(os.environ.get("ACS_CONNECTION_STRING"))
hubspot_configured = bool(os.environ.get("HUBSPOT_ACCESS_TOKEN"))

final_email_status = "SENT" if (email_success and acs_configured) else ("SKIPPED" if not acs_configured else "FAILED")
final_crm_status = "SYNCED" if (crm_success and hubspot_configured) else ("SKIPPED" if not hubspot_configured else "FAILED")
overall_status = "COMPLETED" if email_success else "PARTIAL"
```

### Step 3: Implement HubSpot Deal Deduplication
In [`app/services/crm_service.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/services/crm_service.py#L135), search for existing deals with `audit_id == submission_id` before invoking `make_hubspot_request("POST", deal_url, ...)`:
```python
search_deal_url = "https://api.hubapi.com/crm/v3/objects/deals/search"
# If deal with audit_id exists, skip creation or update existing deal
```

### Step 4: Add Supervisord UNIX Socket Block
In [`supervisord.conf`](file:///home/aakash.padyachi/apps/niwi/Audit/supervisord.conf), configure the UNIX socket server so `supervisorctl status` functions normally in future inspections:
```ini
[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock
```

---

## Final Certification Statement

The Azure Service Bus integration is functioning correctly as a transport mechanism, and message flow is demonstrably active and reliable. However, until dual-worker job ownership is unified and external side-effect idempotency is implemented, the architecture is classified as:

### **OPERATIONAL WITH KNOWN RISKS**
*(Do not claim exactly-once processing or run 50–100 VU concurrent load tests until the 4 remediation steps above are deployed).*

