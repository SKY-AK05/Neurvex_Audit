# NIWI — Azure Service Bus Deployment, Operations & Rollback Runbook

## 1. Overview & Operational Principles

This runbook provides actionable procedures for deploying, monitoring, operating, and rolling back the Azure Service Bus and Transactional Outbox pipeline on the production NIWI platform (`https://niwi.orchvate.in`).

### Core Operational Principles
- **Dual-Run Safety:** The application concurrently supports both the modern Service Bus pipeline (`service_bus_outbox`) and the legacy queue (`post_submit_jobs`) during transition.
- **Zero-Downtime Migration:** Applying database migrations is strictly additive (new tables, new columns, partial indexes) with zero table locks on `submissions` or `organizations`.
- **Instantaneous Rollback:** If any unforeseen issue occurs with Azure Service Bus, switching the pipeline back to legacy operation requires only an environment flag update or supervisor command without code deployment or data loss.

---

## 2. Pre-Deployment Verification Checklist

Before deploying changes, verify the following prerequisites on host VM (`52.240.143.40`):

```bash
# 1. Verify Azure IMDS token acquisition for Service Bus namespace
curl -s -H "Metadata:true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fniwi-bus.servicebus.windows.net" \
  | grep -q "access_token" && echo "✅ Managed Identity IMDS Token OK" || echo "❌ IMDS Token Failed"

# 2. Verify network connectivity to Azure Service Bus over AMQPS (5671) and HTTPS (443)
nc -zv -w 3 niwi-bus.servicebus.windows.net 5671
nc -zv -w 3 niwi-bus.servicebus.windows.net 443

# 3. Verify PostgreSQL Flexible Server connectivity
python3 -c "
import psycopg2, os
from app.core.keyvault import init_keyvault, get_database_config
init_keyvault()
cfg = get_database_config()
conn = psycopg2.connect(host=cfg['host'], dbname=cfg['database'], user=cfg['user'], password=cfg['password'], port=cfg['port'], sslmode='require')
print('✅ PostgreSQL Connection OK:', conn.server_version)
conn.close()
"
```

---

## 3. Deployment Procedure (Step-by-Step)

### Step 1: Run Database Migration
Execute the migration script to create `service_bus_outbox` and tracking columns:

```bash
cd /home/aakash.padyachi/apps/niwi/Audit

APP_ENV=production KEY_VAULT_NAME=niwi-prod-kv python3 scripts/run_migration.py migrations/016_service_bus_outbox.sql
```
*Expected output: `✅ Migration applied successfully: migrations/016_service_bus_outbox.sql`*

### Step 2: Build Updated Production Docker Image
Build the unified Docker image with Vue frontend and Python backend:

```bash
cd /home/aakash.padyachi/apps/niwi/Audit
docker build -t niwi .
```

### Step 3: Recreate Container with Managed Identity & Production Configuration

```bash
# Gracefully stop and remove existing container
docker stop niwi
docker rm niwi

# Launch updated container
docker run -d \
  --name niwi \
  -p 8080:80 \
  -e APP_ENV=production \
  -e KEY_VAULT_NAME=niwi-prod-kv \
  -e REQUIRE_KEYVAULT=true \
  -e ENABLE_SERVICE_BUS_PIPELINE=true \
  -e ENABLE_LEGACY_JOB_WORKER=true \
  --restart unless-stopped \
  niwi
```

### Step 4: Verify Process Health & Daemons
Verify that all 5 daemons under Supervisord are in the `RUNNING` state:

```bash
sleep 5
docker exec niwi supervisorctl status
```

*Expected Output:*
```
job_worker                       RUNNING   pid 7, uptime 0:00:15
nginx                            RUNNING   pid 8, uptime 0:00:15
outbox_dispatcher                RUNNING   pid 9, uptime 0:00:15
service_bus_worker               RUNNING   pid 10, uptime 0:00:15
uvicorn                          RUNNING   pid 11, uptime 0:00:15
```

### Step 5: Execute Smoke Health Check
```bash
# Check local container proxy
curl -s http://127.0.0.1:8080/api/health

# Check public production URL
curl -s https://niwi.orchvate.in/api/health
```
*Expected response: `{"version":"2.1","database":"up","acs":"degraded"}`*

---

## 4. Monitoring & Operations Runbook

### 4.1 Log Inspection

```bash
# View combined logs in real-time
docker logs -f --tail 100 niwi

# View outbox dispatcher logs specifically
docker logs niwi 2>&1 | grep "outbox_dispatcher" | tail -n 30

# View Service Bus consumer worker logs specifically
docker logs niwi 2>&1 | grep "service_bus_worker" | tail -n 30
```

### 4.2 Inspecting Outbox Queue Depth in PostgreSQL

```sql
-- Check count of events by status
SELECT status, COUNT(*) 
FROM service_bus_outbox 
GROUP BY status;

-- Check pending events waiting to be dispatched
SELECT id, event_type, aggregate_id, attempt_count, next_retry_at, created_at
FROM service_bus_outbox
WHERE status IN ('PENDING', 'FAILED')
ORDER BY created_at ASC;

-- Check any dead-lettered outbox records
SELECT id, aggregate_id, attempt_count, last_error, created_at
FROM service_bus_outbox
WHERE status = 'DEAD_LETTER';
```

### 4.3 Re-driving Dead-Lettered Outbox Records

If outbox events were marked `DEAD_LETTER` due to an extended cloud outage, reset them to `PENDING` after resolving the incident:

```sql
UPDATE service_bus_outbox
SET status = 'PENDING',
    attempt_count = 0,
    next_retry_at = NOW(),
    locked_until = NULL,
    locked_by = NULL
WHERE status = 'DEAD_LETTER';
```

### 4.4 Inspecting Azure Service Bus Queue Depth via CLI / REST

To inspect the queue status directly using the VM's Managed Identity:

```bash
# 1. Acquire token
TOKEN=$(curl -s -H "Metadata:true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fniwi-bus.servicebus.windows.net" \
  | jq -r .access_token)

# 2. Peek next message from queue head
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "https://niwi-bus.servicebus.windows.net/niwi-submission-queue/messages/head" -I
```

---

## 5. Rollback Procedures

If an emergency arises where Azure Service Bus is unresponsive or experiencing an extended Microsoft Azure outage, execute one of the following rollback options:

### Option A: Operational Rollback via Feature Flag (No Rebuild Required)

To immediately disable Service Bus dispatching and rely exclusively on the legacy database queue:

```bash
# Stop outbox dispatcher and Service Bus consumer in container
docker exec niwi supervisorctl stop outbox_dispatcher service_bus_worker

# Verify legacy worker continues processing post_submit_jobs
docker exec niwi supervisorctl status job_worker
```

*Impact:* Submissions continue inserting into `submissions` and `post_submit_jobs`. The legacy `job_worker` immediately handles emails and HubSpot sync via database polling. Client experience is 100% uninterrupted.

---

### Option B: Full Container Rollback to Previous Image

If an immediate container rollback to the previous known good Docker image is required:

```bash
# 1. Stop current container
docker stop niwi
docker rm niwi

# 2. Launch previous image (tag: niwi:previous or by sha256)
docker run -d \
  --name niwi \
  -p 8080:80 \
  -e APP_ENV=production \
  -e KEY_VAULT_NAME=niwi-prod-kv \
  -e REQUIRE_KEYVAULT=true \
  --restart unless-stopped \
  niwi:previous
```

---

### Option C: Database Migration Rollback (Optional)

Because migration `016_service_bus_outbox.sql` is strictly non-breaking (adding a new table and non-null-with-default columns), database rollback is **not required** during application rollback.

However, if a clean database state is explicitly required:

```sql
-- 1. Drop partial indexes
DROP INDEX IF EXISTS idx_outbox_pending_polling;
DROP INDEX IF EXISTS idx_outbox_aggregate;
DROP INDEX IF EXISTS idx_outbox_status;
DROP INDEX IF EXISTS idx_submissions_async_status;

-- 2. Drop outbox table
DROP TABLE IF EXISTS service_bus_outbox;

-- 3. Drop tracking columns from submissions
ALTER TABLE submissions DROP COLUMN IF EXISTS async_status;
ALTER TABLE submissions DROP COLUMN IF EXISTS email_status;
ALTER TABLE submissions DROP COLUMN IF EXISTS crm_status;
ALTER TABLE submissions DROP COLUMN IF EXISTS async_completed_at;
```

---

## 6. Verification of Rollback Readiness

All components were architected with backward-compatible defaults:
1. `post_submit_jobs` continues receiving inserts inside `/api/submit` during dual-run.
2. The legacy `job_worker` runs continuously alongside the new workers.
3. If Service Bus goes offline, outbox events persist safely in `service_bus_outbox` until reconnected.
4. Database connection pool and advisory locks operate independently of the message broker.

