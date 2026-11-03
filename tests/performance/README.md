# NIWI Dynamic Performance Testing Suite (10 / 25 / 50 / 75 / 100 VUs)

A production-grade, reusable performance testing suite built with **Grafana k6** to measure concurrency limits, response times, database connection pool stability, and submission throughput of the NIWI (Neuro-Inclusive Workplace Index) application.

All organisation configurations and execution parameters are **100% dynamically supplied by the user at runtime**. No organisation details, names, or UUIDs are hardcoded.

---

## 1. User-Configurable Execution Parameters

Supply target parameters using standard k6 `-e` environment variables:

| Parameter | Environment Variable | Required | Description | Example |
|---|---|:---:|---|---|
| **Base Application URL** | `BASE_URL` | **Yes** | Root URL of the target NIWI environment | `https://niwi.orchvate.in` |
| **Organisation Code / Name** | `ORG_CODE` | **Yes** | Target organisation name or identifier to test | `SKY11` |
| **Expected Organisation UUID** | `ORG_ID` | Optional | Target UUID; verified against backend lookup if provided | `c7d5efb5-bd5a-4883-8bb4-6a8deab1c9b8` |
| **Virtual Users (VUs)** | `VUS` | Load tests | Target concurrent users (10, 25, 50, 75, 100) | `10` |
| **Test Duration** | `DURATION` | Sustained | Length of sustained soak test | `3m` |
| **Run Identifier** | `RUN_ID` | Optional | Custom session ID (auto-generated if omitted) | `perf_run_01` |
| **Production Confirmation** | `CONFIRM_PROD` | Production | Explicit guard when targeting live production hosts | `true` |
| **Preflight-Only Mode** | `PREFLIGHT_ONLY`| Optional | Verifies organisation and connectivity without submitting | `true` |

---

## 2. Mandatory Preflight Validation

Before any virtual user generates synthetic traffic:

1. **Parameter Validation:** Ensures `BASE_URL` and `ORG_CODE` are provided; validates `ORG_ID` UUID format if supplied.
2. **Production Safety Check:** Requires `-e CONFIRM_PROD=true` if targeting live production domains (`orchvate.in`).
3. **Assessment Page Connectivity:** Confirms `GET /audit?org=<ORG_CODE>` returns HTTP 200 with HTML content.
4. **Questionnaire Schema Health:** Confirms `GET /api/form/sections` returns the 8 assessment sections.
5. **Backend Organisation Verification:** Queries `POST /api/public/organisations/validate` with `{"name": ORG_CODE}` to retrieve the canonical organisation record from PostgreSQL.
6. **UUID Matching:** Verifies that the resolved database UUID matches `ORG_ID` (if provided).
7. **Fail-Safe Abort:** If validation fails, execution halts immediately. No assessment is submitted, no new organisation is created, and no database records are polluted.

### Preflight Summary Banner
```text
==================================================
NIWI PERFORMANCE TEST — CONFIGURATION
==================================================
Base URL:           https://niwi.orchvate.in
Organisation Code:  SKY11
Organisation ID:    c7d5efb5-bd5a-4883-8bb4-6a8deab1c9b8
Assessment URL:     https://niwi.orchvate.in/audit?org=SKY11
Virtual Users:      1
Test Type:          Smoke Test
Run ID:             run_1793645008462_rfimy
==================================================
```

---

## 3. Directory Structure

```text
tests/
└── performance/
    ├── config.js              # Centralized dynamic configuration, preflight check, & synthetic user generator
    ├── metrics.js             # Custom k6 counters, latency trends, and separated smoke/load thresholds
    ├── report-generator.js    # Automated JSON and executive Markdown summary generator
    ├── niwi-smoke.js          # 1-User end-to-end functional smoke test
    ├── niwi-submission-load.js# 10 / 25 / 50 / 75 / 100 concurrent user load test
    ├── niwi-sustained-load.js # Long-duration sustained soak/endurance load test
    ├── niwi-browser-load.js   # Headless browser simulation (k6/browser)
    ├── README.md              # Documentation and execution guide
    └── reports/               # Auto-saved JSON and Markdown execution reports
```

---

## 4. Execution Commands (PowerShell)

### Scenario A: Preflight Verification Only (Zero Submissions)
Verify organisation connectivity, database resolution, and questionnaire schema without writing any assessment submissions:
```powershell
& "C:\Program Files\k6\k6.exe" run `
  -e BASE_URL=https://niwi.orchvate.in `
  -e ORG_CODE=SKY11 `
  -e PREFLIGHT_ONLY=true `
  tests/performance/niwi-smoke.js
```

### Scenario B: 1-User Smoke Test
Verify end-to-end submission pipeline, scoring calculations, and database persistence for 1 employee:
```powershell
& "C:\Program Files\k6\k6.exe" run `
  -e BASE_URL=https://niwi.orchvate.in `
  -e ORG_CODE=SKY11 `
  -e ORG_ID=c7d5efb5-bd5a-4883-8bb4-6a8deab1c9b8 `
  -e CONFIRM_PROD=true `
  tests/performance/niwi-smoke.js
```

### Scenario C: Concurrent Submission Load Tests (10 / 25 / 50 / 75 / 100 VUs)

#### 10 Concurrent Users (Baseline Profile)
```powershell
& "C:\Program Files\k6\k6.exe" run `
  -e BASE_URL=https://niwi.orchvate.in `
  -e ORG_CODE=SKY11 `
  -e VUS=10 `
  -e CONFIRM_PROD=true `
  tests/performance/niwi-submission-load.js
```

#### 25 Concurrent Users
```powershell
& "C:\Program Files\k6\k6.exe" run `
  -e BASE_URL=https://niwi.orchvate.in `
  -e ORG_CODE=SKY11 `
  -e VUS=25 `
  -e CONFIRM_PROD=true `
  tests/performance/niwi-submission-load.js
```

#### 50 Concurrent Users
```powershell
& "C:\Program Files\k6\k6.exe" run `
  -e BASE_URL=https://niwi.orchvate.in `
  -e ORG_CODE=SKY11 `
  -e VUS=50 `
  -e CONFIRM_PROD=true `
  tests/performance/niwi-submission-load.js
```

#### 75 Concurrent Users
```powershell
& "C:\Program Files\k6\k6.exe" run `
  -e BASE_URL=https://niwi.orchvate.in `
  -e ORG_CODE=SKY11 `
  -e VUS=75 `
  -e CONFIRM_PROD=true `
  tests/performance/niwi-submission-load.js
```

#### 100 Concurrent Users (Maximum Target)
```powershell
& "C:\Program Files\k6\k6.exe" run `
  -e BASE_URL=https://niwi.orchvate.in `
  -e ORG_CODE=SKY11 `
  -e VUS=100 `
  -e CONFIRM_PROD=true `
  tests/performance/niwi-submission-load.js
```

### Scenario D: Sustained Endurance / Soak Load Test
Run continuous traffic for 3 minutes to verify database connection pool stability and memory leak prevention:
```powershell
& "C:\Program Files\k6\k6.exe" run `
  -e BASE_URL=https://niwi.orchvate.in `
  -e ORG_CODE=SKY11 `
  -e VUS=20 `
  -e DURATION=3m `
  -e CONFIRM_PROD=true `
  tests/performance/niwi-sustained-load.js
```

### Scenario E: Frontend Headless Browser Simulation
Simulate a real browser user session navigating AuditForm.vue with headless Chromium:
```powershell
& "C:\Program Files\k6\k6.exe" run `
  -e BASE_URL=https://niwi.orchvate.in `
  -e ORG_CODE=SKY11 `
  -e BROWSER_VUS=1 `
  -e CONFIRM_PROD=true `
  tests/performance/niwi-browser-load.js
```

---

## 5. Performance Acceptance Criteria (SLAs)

| Criterion | Target Metric | Smoke Test (N=1) | Load Tests (10–100 VUs) |
|---|:---:|:---:|:---:|
| **Submission Success Rate** | 100% | Functional Requirement | Functional Requirement |
| **HTTP Error Rate** | < 1.0% | Functional Requirement | Functional Requirement |
| **P95 Response Time** | < 3,000 ms | Informational / Max < 15s | Strict SLA Threshold |
| **P99 Response Time** | < 5,000 ms | Informational / Max < 15s | Strict SLA Threshold |
| **Lost Submissions** | 0 | Functional Requirement | Functional Requirement |
| **Organisation Mismatch Rate** | 0% | Mandatory Integrity Check | Mandatory Integrity Check |

---

## 6. Production Safety & Traceability

1. **Synthetic Isolation:** All generated users use RFC 2606 reserved email addresses (`loadtest_<runId>_vu<VU>_it<ITER>@example.com`), completely preventing outbound email delivery to real recipients.
2. **Organisation Containment:** Every submission payload includes the verified `organization_id` UUID, ensuring submissions link strictly to the intended organisation without creating accidental duplicates.
3. **Traceable Run ID:** Every run generates a unique session ID prefixed in reports and logs.
4. **Automated Reporting:** Every run outputs both structured JSON data and formatted Markdown executive summaries to `tests/performance/reports/`.
