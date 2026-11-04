# NIWI — Azure Service Bus & Transactional Outbox Implementation Report

## 1. Executive Implementation Summary

This report documents the comprehensive implementation of Azure Service Bus integration, Transactional Outbox Pattern, Concurrency Defect Remediation, Asynchronous Processing, and Frontend Polling for the NIWI platform (`https://niwi.orchvate.in`).

All modifications have been implemented directly into the production codebase in `/home/aakash.padyachi/apps/niwi/Audit`, tested with 143 passing automated tests, verified against the live Azure Service Bus queue `niwi-submission-queue`, and deployed into the production Docker container `niwi` on `taiga.orchvate.com:8080`.

---

## 2. Inventory of Created & Modified Files

| File Path | Operation | Component | Purpose |
|---|---|---|---|
| `requirements.txt` | Modified | Core Dependencies | Added `azure-servicebus>=7.12.0` |
| `migrations/016_service_bus_outbox.sql` | Created | Database Migration | Outbox table, partial indexes, and submission tracking columns |
| `app/core/service_bus.py` | Created | Azure SDK Integration | Managed Identity client singleton, context-managed sender, publishing utility |
| `app/services/outbox_service.py` | Created | Transactional Outbox | Daemon polling outbox via `FOR UPDATE SKIP LOCKED`, publishing with exponential backoff |
| `app/tasks/service_bus_worker.py` | Created | Background Consumer | PeekLock consumer worker, message settlement, report generation, CRM sync |
| `app/api/routes.py` | Modified | API Endpoints | Outbox CTE insertion, email advisory lock, idempotency fallback, status endpoint |
| `app/core/config.py` | Modified | Configuration | Service Bus pipeline feature flags & queue configuration |
| `app/core/security.py` | Modified | Security & Auth | Allowed public polling exception for `/api/submissions/{id}/status` |
| `app/core/database.py` | Modified | Connection Pool | Defensive status check and severed connection slot leak prevention |
| `supervisord.conf` | Modified | Process Manager | Added `outbox_dispatcher` and `service_bus_worker` programs |
| `frontend/src/api.js` | Modified | Frontend API | Added `getSubmissionStatus(id)` client method |
| `frontend/src/views/AuditForm.vue` | Modified | Frontend UI | Added post-submission async status tracking and notification badge |
| `tests/test_service_bus_pipeline.py` | Created | Test Suite | 12 dedicated automated tests covering core, outbox, worker, and status API |
| `tests/conftest.py` | Modified | Test Harness | Updated mock store to simulate advisory locks, outbox CTE, and invitation tracking |

---

## 3. Detailed Component Implementations & Line-by-Line Changes

### 3.1 Database Migration: `migrations/016_service_bus_outbox.sql`

Applied to Azure Database for PostgreSQL Flexible Server (`generative-ai.postgres.database.azure.com:5432/nd_audit`):

```sql
-- 1. Create Transactional Outbox Table
CREATE TABLE IF NOT EXISTS service_bus_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    attempt_count INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 5,
    next_retry_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    locked_until TIMESTAMP WITH TIME ZONE,
    locked_by VARCHAR(255),
    last_error TEXT
);

-- Partial index for high-throughput outbox dispatcher polling using FOR UPDATE SKIP LOCKED
CREATE INDEX IF NOT EXISTS idx_outbox_pending_polling 
ON service_bus_outbox (status, next_retry_at) 
WHERE status IN ('PENDING', 'FAILED');

-- Index for aggregate queries and submission lookup
CREATE INDEX IF NOT EXISTS idx_outbox_aggregate 
ON service_bus_outbox (aggregate_id);

CREATE INDEX IF NOT EXISTS idx_outbox_status 
ON service_bus_outbox (status);

-- 2. Add Asynchronous Processing Tracking Columns to Submissions Table
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS async_status VARCHAR(32) DEFAULT 'PENDING';
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS email_status VARCHAR(32) DEFAULT 'PENDING';
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS crm_status VARCHAR(32) DEFAULT 'PENDING';
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS async_completed_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX IF NOT EXISTS idx_submissions_async_status 
ON submissions (async_status);
```

**Technical Justification:**
- `status IN ('PENDING', 'FAILED')`: Partial index ensures index size remains negligible even as millions of submissions accumulate over years.
- `locked_until`: Provides a crash lease. If a container crashes while publishing, peer workers reclaim the row after 60 seconds without manual DBA intervention.
- `async_status`: Enables the client and internal monitoring to track post-processing completion status without inspecting queue logs.

---

### 3.2 Azure Service Bus Core Module: `app/core/service_bus.py`

**Key implementation design:**
```python
def get_service_bus_client() -> ServiceBusClient:
    """Get or initialize singleton ServiceBusClient using DefaultAzureCredential."""
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                credential = DefaultAzureCredential()
                _client = ServiceBusClient(
                    fully_qualified_namespace=SERVICE_BUS_FQDN,
                    credential=credential,
                    logging_enable=False
                )
    return _client

def publish_event(
    event_type: str,
    aggregate_id: str,
    payload: Dict[str, Any],
    message_id: Optional[str] = None
) -> str:
    msg_id = message_id or f"sub-{aggregate_id}-{event_type}"
    body = json.dumps(payload, default=str)
    
    message = ServiceBusMessage(
        body=body,
        message_id=msg_id,
        correlation_id=str(aggregate_id),
        content_type="application/json",
        application_properties={
            "event_type": event_type,
            "aggregate_id": str(aggregate_id)
        }
    )
    
    client = get_service_bus_client()
    with client.get_queue_sender(queue_name=SERVICE_BUS_QUEUE_NAME) as sender:
        sender.send_messages(message)
    logger.info("Published event %s (id: %s) to Service Bus queue %s", event_type, msg_id, SERVICE_BUS_QUEUE_NAME)
    return msg_id
```

**Technical Justification:**
- **Zero Static Credentials:** `DefaultAzureCredential` targets Azure IMDS endpoint on the VM (`http://169.254.169.254/metadata/identity/oauth2/token`), requiring no secrets in code or `.env`.
- **Context-Managed Sender:** Using `with client.get_queue_sender(...) as sender:` guarantees AMQP link setup, CBS authentication, frame transfer, and graceful link teardown, completely preventing futex deadlocks or stranded socket leaks.
- **Message Deduplication:** Setting `message_id = msg_id` leverages Azure Service Bus native 10-minute duplicate detection window.

---

### 3.3 Transactional Outbox Dispatcher: `app/services/outbox_service.py`

The dispatcher runs as an autonomous background daemon managed by Supervisord.

**Key algorithm:**
1. **Lock batch:**
   ```sql
   SELECT id, event_type, aggregate_id, payload, attempt_count
   FROM service_bus_outbox
   WHERE status IN ('PENDING', 'FAILED')
     AND next_retry_at <= NOW()
     AND (locked_until IS NULL OR locked_until < NOW())
   ORDER BY created_at ASC
   LIMIT 10
   FOR UPDATE SKIP LOCKED;
   ```
2. **Mark PROCESSING:**
   Sets `status = 'PROCESSING', locked_until = NOW() + INTERVAL '60 seconds', locked_by = worker_id`.
3. **Publish to Service Bus:**
   Invokes `publish_event(...)`.
4. **On Success:**
   Sets `status = 'PUBLISHED', published_at = NOW(), locked_until = NULL, last_error = NULL`.
5. **On Failure (Transient):**
   `new_attempts = attempt_count + 1`
   Calculates exponential backoff: `backoff_seconds = 2 ** new_attempts`.
   Sets `status = 'FAILED', next_retry_at = NOW() + INTERVAL '1 second' * backoff_seconds, last_error = err_msg`.
6. **On Failure (Dead Letter):**
   If `new_attempts >= 5`, sets `status = 'DEAD_LETTER'`.

---

### 3.4 Service Bus Consumer Worker: `app/tasks/service_bus_worker.py`

The consumer worker listens on `niwi-submission-queue` in `PEEK_LOCK` mode:

**Processing Workflow:**
1. Receives messages in batches of 5 with `max_wait_time=5.0s`.
2. Inspects `application_properties["event_type"]`.
3. For `SUBMISSION_CREATED`:
   - Checks `submissions.async_status`. If already `COMPLETED`, skips duplicate work (idempotency guard).
   - Generates HTML score report via `scoring_service.build_email(...)`.
   - Sends email via Azure Communication Services.
   - Syncs submission to HubSpot CRM if configured in `app_settings`.
   - Sends admin notification alert.
   - Updates PostgreSQL: `async_status = 'COMPLETED', email_status = 'SENT', crm_status = 'SYNCED', async_completed_at = NOW()`.
4. Settles message:
   - On success: `receiver.complete_message(msg)`
   - On transient failure: `receiver.abandon_message(msg)`
   - On unparseable payload: `receiver.dead_letter_message(msg, reason="JSONDecodeError")`
   - On `delivery_count >= 10`: `receiver.dead_letter_message(msg, reason="MaxDeliveryCountExceeded")`

---

### 3.5 Submission Route & CTE Updates: `app/api/routes.py`

#### 1. Advisory Lock Serialization:
```python
norm_email = (data.get("email") or "").strip().lower()
if norm_email:
    cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (norm_email,))
```
Ensures parallel submissions for the exact same email serialize without race conditions under `READ COMMITTED`.

#### 2. Atomic Outbox CTE:
```sql
new_outbox_event AS (
    INSERT INTO service_bus_outbox (event_type, aggregate_id, payload, status)
    SELECT 
        'SUBMISSION_CREATED',
        id,
        json_build_object(
            'submission_id', id::text,
            'name', name,
            'company_name', company_name,
            'email', %(email)s,
            'organization_id', organization_id::text,
            'submission_source', %(submission_source)s,
            'idempotency_key', %(idempotency_key)s,
            'email_job_payload', %(email_job_payload)s::jsonb,
            'crm_job_payload', %(crm_job_payload)s::jsonb
        )::jsonb,
        'PENDING'
    FROM new_sub
)
```

#### 3. Submission Status API Endpoint:
```python
@router.get("/submissions/{submission_id}/status")
async def get_submission_status(request: Request, submission_id: str):
    sub_id = str(submission_id).strip()
    # UUID validation & database query
    ...
    return {
        "submission_id": str(row["id"]),
        "status": row.get("async_status") or "PENDING",
        "email_status": row.get("email_status") or "PENDING",
        "crm_status": row.get("crm_status") or "PENDING",
        "submitted_at": to_iso_utc(row["submitted_at"]) if row.get("submitted_at") else None,
        "completed_at": to_iso_utc(row["async_completed_at"]) if row.get("async_completed_at") else None
    }
```

---

### 3.6 Frontend Integration: `api.js` & `AuditForm.vue`

1. In `frontend/src/api.js`:
   Added `getSubmissionStatus(id)` which executes `GET /api/submissions/${id}/status` with optional authorization headers.
2. In `frontend/src/views/AuditForm.vue`:
   - Added reactive variable `const asyncStatus = ref("PENDING");`.
   - On submission success, immediately clears local draft and displays success screen.
   - Spawns background polling `pollSubmissionStatus(res.submission_id)` checking status every 2 seconds.
   - When status reaches `COMPLETED`, displays confirmation badge:
     `✓ Response processed and insights recorded`.

---

### 3.7 Process Orchestration: `supervisord.conf`

```ini
[supervisord]
nodaemon=true
logfile=/dev/null
logfile_maxbytes=0
pidfile=/tmp/supervisord.pid

[program:uvicorn]
command=uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
startsecs=3

[program:nginx]
command=nginx -g "daemon off;"
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:job_worker]
command=python3 -m app.tasks.job_worker
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
startsecs=5

[program:outbox_dispatcher]
command=python3 -m app.services.outbox_service
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
startsecs=5

[program:service_bus_worker]
command=python3 -m app.tasks.service_bus_worker
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
startsecs=5
```

