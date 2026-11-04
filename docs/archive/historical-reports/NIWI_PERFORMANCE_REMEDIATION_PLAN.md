# NIWI — Performance Remediation Plan & Engineering Design

---

## 1. Overview & Remediation Goals

This plan outlines the concrete technical changes required to eliminate submission latency bottlenecks in NIWI, stabilise concurrency up to 50 virtual users (VUs), and reduce database connection hold times by over **85%**.

### Key Target Metrics

| Metric | Current Baseline | Remediation Target | Target Concurrency |
| :--- | :---: | :---: | :---: |
| **Single-User Latency** | 4,115 ms (remote) / 3,930 ms (local) | **$< 1,200\text{ ms}$** | 1 VU |
| **10 VU Burst P95** | 7,799 ms | **$< 2,000\text{ ms}$** | 10 VUs |
| **15 VU Sustained P95** | 9,619 ms | **$< 2,500\text{ ms}$** | 15 VUs |
| **50 VU Stress P95** | $> 12,000\text{ ms}$ (with failures) | **$< 3,000\text{ ms}$ (0% errors)** | 50 VUs |
| **Database Connection Hold Time** | 2,377 ms – 2,411 ms | **$< 350\text{ ms}$** | All loads |
| **Sequential SQL Round Trips** | 8 sequential trips | **1–2 trips** | All loads |
| **Metadata Cache Miss Latency** | 4,108 ms ($N+1$ loop + DDL) | **$< 200\text{ ms}$** | All loads |

---

## 2. Identified Bottlenecks & Code References

### Bottleneck 1: 8 Sequential WAN Database Round Trips
- **Location:** [`Audit/app/api/routes.py:126-418`](file:///home/aakash.padyachi/apps/niwi/Audit/app/api/routes.py#L126-L418)
- **Root Cause:** The database connection is held while 6 sequential queries, 1 connection reset, and 1 commit execute sequentially across the 185 ms WAN link between Chicago (VM) and Hong Kong (Azure PG).
- **Impact:** Connection hold time is ~2.4 seconds, forcing concurrent requests into serialized queues.

### Bottleneck 2: Legacy $N+1$ Query Fallback in Scoring Metadata Cache
- **Location:** [`Audit/app/services/scoring_service.py:150-209`](file:///home/aakash.padyachi/apps/niwi/Audit/app/services/scoring_service.py#L150-L209)
- **Root Cause:** `get_form_sections_metadata(None)` was not updated with the Finding 1 optimization. When the 5-minute cache expires, it executes `get_settings()` (with DDL checks), `SELECT * FROM form_sections`, and a Python loop querying `form_questions` 8 times sequentially.
- **Impact:** Any request arriving upon cache expiration halts for 4,108 ms.

### Bottleneck 3: Zero-Wait Connection Pool Exhaustion
- **Location:** [`Audit/app/core/database.py:216-224`](file:///home/aakash.padyachi/apps/niwi/Audit/app/core/database.py#L216-L224)
- **Root Cause:** `ThreadedConnectionPool.getconn()` raises `PoolError` immediately when all 10 worker connections are busy, with no FIFO waiting queue.
- **Impact:** Sudden bursts above 10 concurrent requests per worker immediately produce HTTP 500 errors.

### Bottleneck 4: Duplicated Background Worker in API Processes
- **Location:** [`Audit/app/main.py:62`](file:///home/aakash.padyachi/apps/niwi/Audit/app/main.py#L62) & [`Audit/app/tasks/job_worker.py`](file:///home/aakash.padyachi/apps/niwi/Audit/app/tasks/job_worker.py)
- **Root Cause:** `await start_job_worker()` is called in `main.py` startup, running a polling loop in *both* Uvicorn worker processes.
- **Impact:** Redundant polling (`SELECT ... FOR UPDATE SKIP LOCKED` every 5 seconds) competes with user web traffic for pool connections.

### Bottleneck 5: Table DDL Checks in Request Call Chain
- **Location:** [`Audit/app/services/settings_service.py:75-90`](file:///home/aakash.padyachi/apps/niwi/Audit/app/services/settings_service.py#L75-L90)
- **Root Cause:** `ensure_settings_row` and `ensure_settings_table` run `information_schema` queries on every call to `get_settings()`.
- **Impact:** Adds 1.2s to `_bg_notify_admin`.

---

## 3. Detailed Proposed Changes

### Phase 1 (P0): Collapse Submission Persistence into a Single CTE Query
Replace the sequential write operations inside `submit()` with a single atomic PostgreSQL Common Table Expression (CTE):
```sql
WITH pre_check AS (
    SELECT id FROM submissions
    WHERE LOWER(TRIM(email)) = LOWER(TRIM(%(email)s))
      AND submitted_at > NOW() - INTERVAL '5 minutes'
    LIMIT 1
),
valid_org AS (
    SELECT id, name FROM organizations
    WHERE id = %(organization_id)s::uuid
      AND is_deleted = FALSE AND is_active = TRUE
),
new_sub AS (
    INSERT INTO submissions (
        name, designation, company_name, email, contact_number,
        has_physical_workspace, has_suppliers,
        q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,
        q15,q16,q17,q18,q19,q20,q21,q22,q23,q24,
        q25,q26,q27,q28,q29,q30,q31,q32,q33,q34,
        q35,q36,q37,q38,q39,q40,q41,q42,q43,q44,
        lc_score, lc_level, ro_score, ro_level,
        we_score, we_level, be_score, be_level,
        tm_score, tm_level, ca_score, ca_level,
        pc_score, pc_level, sp_score, sp_level,
        overall_avg, overall_level, email_body, status,
        consent_given, consent_timestamp, organization_id,
        submission_source, invitation_id, dimension_scores, answers,
        idempotency_key
    )
    SELECT
        %(name)s, %(designation)s, vo.name, %(email)s, %(contact_number)s,
        %(has_physical_workspace)s, %(has_suppliers)s,
        %(q5)s,%(q6)s,%(q7)s,%(q8)s,%(q9)s,%(q10)s,%(q11)s,%(q12)s,%(q13)s,%(q14)s,
        %(q15)s,%(q16)s,%(q17)s,%(q18)s,%(q19)s,%(q20)s,%(q21)s,%(q22)s,%(q23)s,%(q24)s,
        %(q25)s,%(q26)s,%(q27)s,%(q28)s,%(q29)s,%(q30)s,%(q31)s,%(q32)s,%(q33)s,%(q34)s,
        %(q35)s,%(q36)s,%(q37)s,%(q38)s,%(q39)s,%(q40)s,%(q41)s,%(q42)s,%(q43)s,%(q44)s,
        %(lc_score)s, %(lc_level)s, %(ro_score)s, %(ro_level)s,
        %(we_score)s, %(we_level)s, %(be_score)s, %(be_level)s,
        %(tm_score)s, %(tm_level)s, %(ca_score)s, %(ca_level)s,
        %(pc_score)s, %(pc_level)s, %(sp_score)s, %(sp_level)s,
        %(overall_avg)s, %(overall_level)s, NULL, 'pending',
        %(consent_given)s, %(consent_timestamp)s, vo.id,
        %(submission_source)s, %(invitation_id)s, %(dimension_scores)s::jsonb, %(answers)s::jsonb,
        %(idempotency_key)s
    FROM valid_org vo
    WHERE NOT EXISTS (SELECT 1 FROM pre_check)
    ON CONFLICT (idempotency_key) WHERE idempotency_key IS NOT NULL DO NOTHING
    RETURNING id, organization_id
),
new_link AS (
    INSERT INTO org_submission_links (org_id, submission_id, weight, linked_by)
    SELECT organization_id, id, 1.0, NULL FROM new_sub
    ON CONFLICT (org_id, submission_id) DO NOTHING
),
new_job AS (
    INSERT INTO post_submit_jobs (submission_id, job_type, payload)
    SELECT id, 'email', %(email_job_payload)s::jsonb FROM new_sub
    ON CONFLICT (submission_id, job_type) DO NOTHING
)
SELECT 
    (SELECT id FROM new_sub) AS new_id,
    (SELECT id FROM pre_check) AS duplicate_id,
    (SELECT id FROM valid_org) AS valid_org_id;
```
**Benefits:**
- Reduces SQL round trips from 6 to 1.
- Validates organization and duplicate status atomically.
- Automatically rolls back if organization is invalid.
- Persists submission, org link, and outbox job in a single network transmission.

### Phase 2 (P0): Consolidate Form Sections Metadata Caching
- Replace `get_form_sections_metadata` in `app/services/scoring_service.py` to import or mirror the single `json_agg` query from `form_builder.py`.
- Remove `get_settings()` DDL calls from the metadata refresh path.
- Cache threshold and sections in a thread-safe structure with 5-minute TTL.

### Phase 3 (P0): Connection Pool Queue & State Management
- Add a bounded waiting queue to `get_conn()`:
  - If all 10 connections in the worker are busy, wait up to `checkout_timeout = 5.0` seconds using a `threading.Condition` or `queue.Queue` before raising an error.
  - Avoid calling `conn.rollback()` on checkout if the connection was already cleanly rolled back/committed on return (saving 1 WAN round trip of ~185 ms).

### Phase 4 (P1): Decouple Background Worker from Uvicorn API
- Update `supervisord.conf`:
  ```ini
  [program:worker]
  command=python3 -m app.tasks.job_worker
  directory=/app
  autostart=true
  autorestart=true
  stdout_logfile=/dev/stdout
  stdout_logfile_maxbytes=0
  stderr_logfile=/dev/stderr
  stderr_logfile_maxbytes=0
  ```
- Remove `await start_job_worker()` from `app/main.py:startup_event()`.
- The background worker runs as a single dedicated operating system process, eliminating dual-worker polling contention.

### Phase 5 (P1): Cache `app_settings` in Memory
- Cache `app_settings` with a 60-second TTL in `settings_service.py`.
- Eliminate DDL checks (`ensure_settings_table`) during standard application requests.

---

## 4. Implementation Order & Safety Gates

```
  Step 1: Fix Scoring Service Metadata Cache (P0)
     │   └── Verify zero N+1 queries on cache miss.
     ▼
  Step 2: Optimize Submission SQL via CTE (P0)
     │   └── Verify atomic persistence of submission, org link, and outbox job.
     ▼
  Step 3: Implement Connection Pool Bounded Waiting Queue (P0)
     │   └── Verify zero PoolError on sudden concurrent spikes.
     ▼
  Step 4: Cache App Settings & Eliminate DDL on Request Path (P1)
     │   └── Verify _bg_notify_admin runs in < 25 ms without DB lock.
     ▼
  Step 5: Decouple Background Worker into Supervisord Process (P1)
     │   └── Verify worker starts once and claims jobs cleanly.
     ▼
  Step 6: Deploy Container & Run Validation Benchmarks (P0)
         └── Run 1, 10, 15, 25, 50 VU performance tests.
```

---

## 5. Risk Assessment & Rollback Strategy

| Risk | Likelihood | Impact | Mitigation Strategy |
| :--- | :---: | :---: | :--- |
| **CTE Syntax or Type Mismatch** | Low | High | Validate SQL parameter types explicitly (`::uuid`, `::jsonb`); test against test DB before deployment. |
| **Duplicate Check Behavior Drift** | Low | Medium | Replicate exact 5-minute window and case-insensitive email matching in CTE. |
| **Worker Process Failure** | Low | High | Supervisord manages `job_worker` with `autorestart=true`; outbox pattern ensures uncompleted jobs remain PENDING. |
| **Stale Cache on Admin Updates** | Low | Low | Invalidation hooks already exist on admin mutation endpoints in `form_builder.py`. |

