# NIWI — Production Deployment & Rollback Guide

---

## 1. Overview & Architecture Reference

This guide provides operational procedures for deploying, verifying, monitoring, and rolling back the performance-optimized NIWI application on the production host.

### Production Environment Reference

| Attribute | Specification |
| :--- | :--- |
| **Production Domain** | `https://niwi.orchvate.in` |
| **Host VM IP** | `52.240.143.40` (Azure `centralus`) |
| **Host Reverse Proxy** | Caddy (terminates TLS on 443, proxies to `http://127.0.0.1:8080`) |
| **Application Container** | `niwi` (maps host `8080` to internal Nginx `80`) |
| **Container Base Image** | `python:3.11-slim` & `node:20-alpine` multi-stage |
| **Process Supervisor** | Supervisord (`nginx`, `uvicorn --workers 2`, `job_worker`) |
| **Database Server** | Azure Database for PostgreSQL Flexible Server (`eastasia`) |
| **PostgreSQL Host** | `generative-ai.postgres.database.azure.com` (max_connections = 50) |

---

## 2. Standard Deployment Procedure

All commands must be executed from the application workspace root:
`/home/aakash.padyachi/apps/niwi/Audit`

### Step 1: Create a Rollback Image Backup
Before building and deploying updates, tag the currently running image as a safety rollback point:
```bash
docker tag niwi:latest niwi:rollback-$(date +%Y%m%d_%H%M%S)
```

### Step 2: Build the Production Docker Image
Build the container image using the multi-stage `Dockerfile`:
```bash
cd /home/aakash.padyachi/apps/niwi/Audit
docker build -t niwi:latest -f Dockerfile .
```

### Step 3: Graceful Container Replacement
Stop and replace the running container:
```bash
docker stop niwi
docker rm niwi
docker run -d \
  --name niwi \
  --restart unless-stopped \
  -p 8080:80 \
  --env-file .env \
  niwi:latest
```

### Step 4: Post-Deployment Startup Verification
Allow approximately 15–20 seconds for the two Uvicorn workers to pre-warm their connection pools across the WAN link, then verify container status:

```bash
docker ps --filter "name=niwi"
```

Inspect supervisor process initialization:
```bash
docker logs --tail 40 niwi
```

**Expected Log Indicators of Success:**
1. Both Uvicorn workers report:
   ```
   [INFO] app.core.database: Database connection pool initialized (min=10, max=10)
   [INFO] app.main: Database connection pool initialized and pre-warmed
   [INFO] app.main: Scoring sections metadata cache warmed up
   [INFO] app.main: Embedded worker disabled; relying on dedicated worker service
   [INFO] app.main: Application startup complete
   ```
2. The standalone background job worker reports:
   ```
   [INFO] app.core.database: Database connection pool initialized (min=1, max=3)
   [INFO] __main__: Job worker database pool initialized (min=1, max=3)
   [INFO] __main__: Started background job worker [standalone-worker]
   ```
3. Nginx reports:
   ```
   [INFO] success: nginx entered RUNNING state
   ```

---

## 3. Post-Deployment Smoke Test

Execute a single-submission smoke test to confirm end-to-end functionality and measure transaction latency:

```bash
docker exec niwi python3 -c '
import urllib.request, json, time, uuid

sub_data = {
    "organization_id": "988a814e-dcb2-4b2d-ba0d-484c00dd67d5",
    "name": "Smoke Test Deploy",
    "email": f"smoke_{uuid.uuid4().hex[:8]}@example.com",
    "contact_number": "9876543210",
    "designation": "QA Engineer",
    "has_physical_workspace": "Yes",
    "has_suppliers": "Yes",
    "submission_source": "direct",
    "consent_given": True,
    "answers": {f"q{i}": 4 for i in range(5, 45)}
}
for i in range(5, 45):
    sub_data[f"q{i}"] = 4

t0 = time.perf_counter()
req = urllib.request.Request(
    "http://127.0.0.1:80/api/submit",
    data=json.dumps(sub_data).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=10) as resp:
    res = json.loads(resp.read().decode("utf-8"))
latency = (time.perf_counter() - t0) * 1000.0

print(f"Smoke Test: Status {resp.status} | Latency {latency:.2f} ms | Result: {res}")
'
```

**Acceptance Criteria:**
- Status: `201 Created`
- Latency: `< 800 ms`
- Response: `{"success": True, "submission_id": "<uuid>"}`

---

## 4. Live Monitoring & Operational Commands

### Monitoring Submission Performance
Stream structured performance metrics in real time:
```bash
docker logs -f niwi | grep "SUBMISSION_METRICS"
```
Healthy log sample:
```
SUBMISSION_METRICS: id=4cfa826b... total_ms=563.92 scoring_ms=0.09 checkout_ms=0.05 tx_ms=563.43
```
- Alert condition: If `checkout_ms` consistently exceeds 2,000 ms, check database connection pool utilization.
- Alert condition: If `tx_ms` consistently exceeds 1,500 ms, check WAN network packet loss or PostgreSQL locks.

### Monitoring PostgreSQL Active Connections
Check active connection counts directly on Azure PostgreSQL:
```bash
docker exec niwi python3 -c '
from app.core.database import get_db_connection
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*), state FROM pg_stat_activity GROUP BY state;")
        print("PG Connection States:", cur.fetchall())
'
```
- Healthy total active connection count: `20 to 26` connections (out of 50 allowed).

### Monitoring Background Job Processing
Check the pending backlog of background tasks:
```bash
docker exec niwi python3 -c '
from app.core.database import get_db_connection
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT status, count(*) FROM post_submit_jobs GROUP BY status;")
        print("Jobs Breakdown:", cur.fetchall())
'
```

---

## 5. Emergency Rollback Procedure

If unexpected regressions or unrecoverable issues occur post-deployment:

### Immediate Fast Rollback (Under 60 Seconds)

1. Find the latest rollback tag:
   ```bash
   docker images | grep "niwi.*rollback"
   ```

2. Stop the running container and launch the rollback image:
   ```bash
   docker stop niwi
   docker rm niwi
   docker run -d \
     --name niwi \
     --restart unless-stopped \
     -p 8080:80 \
     --env-file .env \
     niwi:rollback-<timestamp>
   ```

3. Confirm rollback health:
   ```bash
   docker ps
   docker logs --tail 20 niwi
   curl -I https://niwi.orchvate.in
   ```

---

## 6. Troubleshooting & Incident Runbook

### Issue: `Database connection pool exhausted`
- **Cause:** Sudden surge beyond 100 concurrent submissions, or slow PostgreSQL queries holding connections longer than the 10.0-second queue timeout.
- **Resolution:**
  1. Inspect running queries in PostgreSQL:
     ```sql
     SELECT pid, now() - query_start AS duration, query, state FROM pg_stat_activity WHERE state != 'idle';
     ```
  2. Terminate rogue blocking queries:
     ```sql
     SELECT pg_terminate_backend(<pid>);
     ```

### Issue: Background `job_worker` Process Exits
- **Supervisord Behavior:** Supervisord is configured with `autorestart=true` and automatically restarts `job_worker` if it terminates.
- **Investigation:** Check worker logs via:
  ```bash
  docker logs niwi | grep "job_worker"
  ```

