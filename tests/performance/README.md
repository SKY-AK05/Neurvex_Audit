# NIWI Repeatable Performance Testing Suite (10 / 25 / 50 / 75 / 100 VUs)

A production-grade, repeatable performance testing suite built with **Grafana k6** to measure the concurrency limits, response times, database connection stability, and throughput of the NIWI (Neuro-Inclusive Workplace Index) assessment application.

---

## 1. Fixed Test Organisation Specification (Mandatory)

All performance test executions are strictly bound to one verified organisation already existing in the NIWI database. No secondary organisations will be accessed, created, modified, or deleted.

* **Assessment Entry URL:**  
  `https://niwi.orchvate.in/audit?org=New%20Company%200746ed32-957c-4b16-bdfc-f6d52e9a88e1`
* **Canonical Organisation Name in Database:**  
  `New Company 0746ed32-957c-4b16-bdfc-f6d52e9a88e1`
* **Verified Database UUID (`organizations.id`):**  
  `de4a0f39-b695-4c56-9f5f-d7a3645e42c8`
* **Target Environment:**  
  Live Production Application (`niwi.orchvate.in` / IP: `52.240.143.40`)

> [!IMPORTANT]
> **Organisation ID Verification & Auto-Creation Prevention:**  
> The backend `POST /api/submit` route automatically creates a new organisation if an unrecognized organisation name is submitted without an explicit ID. To prevent accidental organisation pollution, our test suite executes an automated preflight check against `/api/public/organisations/validate` before any virtual user generates traffic. If the organisation fails to resolve to `de4a0f39-b695-4c56-9f5f-d7a3645e42c8`, the test halts immediately.

---

## 2. Realistic Employee Assessment Workflow

The test suite mirrors the exact sequence executed by a real employee when visiting the application:

```
[Employee Browser] ── 1. GET /audit?org=New%20Company... ─────────► [Nginx / Frontend HTML]
[Employee Browser] ── 2. GET /api/form/sections ─────────────────► [FastAPI / PostgreSQL]
[Employee Browser] ── 3. POST /api/public/organisations/validate ─► [FastAPI / PostgreSQL]
[Employee Browser] ── (Think Time: Completes 40 Questions) ─────► [Client State]
[Employee Browser] ── 4. POST /api/submit ────────────────────────► [FastAPI / Scoring Engine / DB]
```

### Discovered API Payload Structure (`POST /api/submit`):
* `name`: Synthetic employee full name (e.g., `Synthetic Employee VU1-0`)
* `company_name`: `New Company 0746ed32-957c-4b16-bdfc-f6d52e9a88e1`
* `organization_id`: `de4a0f39-b695-4c56-9f5f-d7a3645e42c8`
* `email`: `loadtest_<runId>_vu<VUID>_it<ITER>@example.com` (RFC 2606 safe domain)
* `contact_number`: `+44 7700 900000` (Ofcom test allocation)
* `consent_given`: `true`
* `function` & `role`: Valid selections from application demographics
* `country`: `India`, `state_ut`: `Maharashtra`
* `is_pwd`, `is_neurodivergent`, `is_marginalized`: Valid demographic responses
* `has_physical_workspace`: `Yes`, `has_suppliers`: `Yes`
* `q5` through `q44`: 40 question fields with valid answers (`Yes`, `Partially`, `No`, `Not Sure`, and `q37` supporting `N/A`)

---

## 3. Directory Structure

```text
tests/
└── performance/
    ├── config.js              # Centralized configuration, preflight check, & synthetic user generator
    ├── metrics.js             # Custom k6 counters, latency trends, and acceptance thresholds
    ├── report-generator.js    # Automated JSON and executive Markdown summary generator
    ├── niwi-smoke.js          # 1-User end-to-end functional smoke test
    ├── niwi-submission-load.js# 10 / 25 / 50 / 75 / 100 concurrent user load test
    ├── niwi-sustained-load.js # Long-duration sustained soak/endurance load test
    ├── niwi-browser-load.js   # Real headless browser simulation (k6/browser)
    ├── README.md              # Documentation, operational guide, and monitoring
    └── reports/               # Auto-saved JSON and Markdown execution reports
```

---

## 4. Test Execution Commands (PowerShell)

### One-User Smoke Test
Validates the entire pipeline, organisation verification, and submission processing for a single employee:
```powershell
& 'C:\Program Files\k6\k6.exe' run -e BASE_URL=https://niwi.orchvate.in tests/performance/niwi-smoke.js
```

### 10 Concurrent Users (Baseline Load)
Simulates 10 employees completing and submitting assessments concurrently:
```powershell
& 'C:\Program Files\k6\k6.exe' run -e BASE_URL=https://niwi.orchvate.in -e VUS=10 tests/performance/niwi-submission-load.js
```

### 25 Concurrent Users (Stage 2 Load)
```powershell
& 'C:\Program Files\k6\k6.exe' run -e BASE_URL=https://niwi.orchvate.in -e VUS=25 tests/performance/niwi-submission-load.js
```

### 50 Concurrent Users (Stage 3 Load)
```powershell
& 'C:\Program Files\k6\k6.exe' run -e BASE_URL=https://niwi.orchvate.in -e VUS=50 tests/performance/niwi-submission-load.js
```

### 75 Concurrent Users (Stage 4 Load)
```powershell
& 'C:\Program Files\k6\k6.exe' run -e BASE_URL=https://niwi.orchvate.in -e VUS=75 tests/performance/niwi-submission-load.js
```

### 100 Concurrent Users (Stage 5 Load)
```powershell
& 'C:\Program Files\k6\k6.exe' run -e BASE_URL=https://niwi.orchvate.in -e VUS=100 tests/performance/niwi-submission-load.js
```

### Sustained Soak Test (3-Minute Continuous Traffic)
```powershell
& 'C:\Program Files\k6\k6.exe' run -e BASE_URL=https://niwi.orchvate.in -e VUS=20 -e DURATION=3m tests/performance/niwi-sustained-load.js
```

### Real Browser UI Test (Headless Chromium)
```powershell
& 'C:\Program Files\k6\k6.exe' run -e BASE_URL=https://niwi.orchvate.in -e BROWSER_VUS=2 tests/performance/niwi-browser-load.js
```

---

## 5. Performance Acceptance Targets (Requirement 13)

| Criterion | Target | Description |
|---|:---:|---|
| **Submission Success Rate** | **100%** | Every valid synthetic submission must be processed and persisted. |
| **HTTP Error Rate** | **< 1.0%** | Network, gateway, or application failures must remain below 1%. |
| **P95 Response Time** | **< 3,000 ms** | 95% of all HTTP requests must complete in under 3 seconds. |
| **P99 Response Time** | **< 5,000 ms** | 99% of all HTTP requests must complete in under 5 seconds. |
| **Lost Submissions** | **0** | Zero unhandled drops or silent failures. |
| **Duplicate Submissions** | **0** | Unique emails prevent duplicate-submission 429 errors. |
| **Organisation Mismatches** | **0** | All records strictly bind to `de4a0f39-b695-4c56-9f5f-d7a3645e42c8`. |

---

## 6. Infrastructure & Database Monitoring Guide

When executing load tests against the target host, monitor the backend Azure infrastructure:

### 1. PostgreSQL Active Connections & Pool Status
Execute on the PostgreSQL server during load test execution:
```sql
-- Check total connections by state
SELECT state, count(*) 
FROM pg_stat_activity 
WHERE datname = 'nd_audit' 
GROUP BY state;

-- Check waiting queries and lock contention
SELECT pid, wait_event_type, wait_event, query 
FROM pg_stat_activity 
WHERE wait_event IS NOT NULL AND datname = 'nd_audit';

-- Check connection pool utilization (max_connections is typically 100 in default Postgres)
SELECT count(*) * 100.0 / current_setting('max_connections')::integer AS pool_utilization_pct 
FROM pg_stat_activity;
```

### 2. Azure Virtual Machine CPU & Memory
* **CPU Utilisation:** Monitor using Azure Portal / Metrics (`Percentage CPU`). High CPU (> 85%) during 50–100 VU runs indicates Uvicorn worker saturation or scoring calculation compute bottlenecks.
* **Memory Utilisation:** Monitor available memory. Memory spikes indicate unclosed database cursors or in-memory cache growth.

### 3. Application & Web Server Logs
* **FastAPI / Uvicorn:** `journalctl -u niwi-backend -f` (or Docker logs). Check for unhandled exceptions or database pool exhaustion (`psycopg2.pool.PoolError`).
* **Nginx:** `/var/log/nginx/error.log`. Look for HTTP 502 (Bad Gateway) or HTTP 504 (Gateway Timeout), which occur if Uvicorn workers fail to respond within Nginx's proxy timeout.

---

## 7. Critical Safety & Rate-Limiting Caveats

1. **Backend Rate Limiter (`slowapi` in `routes.py`):**
   In `app/api/routes.py`, the `/submit` endpoint has:
   ```python
   @limiter.limit("100/hour")  # Per IP - allows shared office IPs
   @limiter.limit("1000/day")  # Daily safety limit per IP
   ```
   *Running more than 100 submissions within a 1-hour window from a single client IP will trigger HTTP 429 (Too Many Requests).*
   *Recommendation:* When running the 100-user test against staging or production, temporarily adjust the limiter setting or execute from a whitelisted proxy IP.

2. **Outbound Email Protection:**
   All synthetic employee emails generated by this suite strictly use the RFC 2606 reserved domain `example.com` (e.g. `loadtest_<runId>_vu1_it0@example.com`). Real mail exchangers do not route to real individuals on this IANA-reserved domain, while satisfying Pydantic `EmailStr` formatting rules.

3. **Test Data Identification & Reviewable Cleanup:**
   Every test submission is tagged with the unique run ID in its synthetic email and name. If cleanup of test records is desired on a test/staging database:
   ```sql
   -- Review synthetic submissions created during a test run:
   SELECT id, name, email, company_name, organization_id, submitted_at 
   FROM submissions 
   WHERE email LIKE 'loadtest_%@example.com'
   ORDER BY submitted_at DESC;

   -- Remove ONLY synthetic test submissions from an approved non-production database:
   -- DELETE FROM org_submission_links WHERE submission_id IN (SELECT id FROM submissions WHERE email LIKE 'loadtest_%@example.com');
   -- DELETE FROM submissions WHERE email LIKE 'loadtest_%@example.com';
   ```
   *Note: Never execute DELETE statements against production without explicit written sign-off.*
