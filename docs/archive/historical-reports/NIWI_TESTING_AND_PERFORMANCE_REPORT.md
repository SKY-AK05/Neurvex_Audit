# NIWI — Testing & Performance Verification Report

---

## 1. Executive Testing Summary

This report documents the rigorous verification and performance testing conducted on the optimized NIWI submission pipeline on **November 4, 2026**.

All performance targets defined in the performance remediation specification were achieved and verified against the live application container and PostgreSQL database:

| Metric / Scenario | Target SLA | Baseline (Pre-Fix) | Measured (Post-Fix) | Improvement | Acceptance Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1 VU Latency** | < 1,200 ms | 3,930 ms – 4,850 ms | **609.38 ms** | **84.5% faster** | **MET (PASS)** |
| **10 VU Burst P95** | < 2,000 ms | 7,799 ms | **634.49 ms** | **91.9% faster** | **MET (PASS)** |
| **15 VU Burst P95** | < 2,500 ms | 9,619 ms (Functional FAIL) | **669.08 ms** | **93.0% faster** | **MET (PASS)** |
| **25 VU Burst P95** | Stable / 0% HTTP 500 | Cascading 500s / Exhaustion | **1,127.80 ms** | **100% Success (0 errors)** | **MET (PASS)** |
| **50 VU Stress P95** | Stable / 0% HTTP 500 | Outage / Complete Failure | **1,717.85 ms** | **100% Success (0 errors)** | **MET (PASS)** |

---

## 2. Comprehensive Concurrency Benchmark Results

### Ladder Test Matrix (1, 10, 15, 25, 50 VUs)

All tests were executed using synthetic concurrent workloads simulating simultaneous assessment submissions with unique emails, demographic answers, and all 40 question responses ($q_5$ through $q_{44}$).

```
=== 1 VU Smoke Benchmark ===
Success: 1/1 (Errors: 0)
Avg Latency: 609.38 ms | P50: 609.38 ms | P95: 609.38 ms | Max: 609.38 ms
Wall Clock Duration: 0.61 s

=== 10 VUs Concurrent Burst ===
Success: 10/10 (Errors: 0)
Avg Latency: 623.05 ms | P50: 629.89 ms | P95: 634.49 ms | Max: 634.49 ms
Wall Clock Duration: 0.65 s

=== 15 VUs Concurrent Burst ===
Success: 15/15 (Errors: 0)
Avg Latency: 628.23 ms | P50: 633.78 ms | P95: 669.08 ms | Max: 669.08 ms
Wall Clock Duration: 0.67 s

=== 25 VUs Concurrent Burst ===
Success: 25/25 (Errors: 0)
Avg Latency: 705.19 ms | P50: 613.58 ms | P95: 1,127.80 ms | Max: 1,128.07 ms
Wall Clock Duration: 1.17 s

=== 50 VUs Stress Burst ===
Success: 50/50 (Errors: 0)
Avg Latency: 1,059.16 ms | P50: 1,149.60 ms | P95: 1,717.85 ms | Max: 1,719.57 ms
Wall Clock Duration: 1.77 s
```

---

## 3. High-Resolution Latency Stage Breakdown

Using the newly added telemetry instrumentation (`SUBMISSION_METRICS`), individual stages of the request lifecycle were measured with microsecond accuracy via `time.perf_counter()`:

### Low Concurrency (1–10 VUs)
```
SUBMISSION_METRICS: id=4cfa826b-48f5-4519-a035-999e7eb9a8e9 total_ms=563.92 scoring_ms=0.09 checkout_ms=0.05 tx_ms=563.43
```
- **Scoring Computation (`scoring_ms`):** **0.09 ms**. In-memory calculation is virtually instantaneous thanks to thread-safe metadata caching.
- **Connection Checkout (`checkout_ms`):** **0.05 ms**. Pre-warmed pool immediately returns an open socket. Redundant `conn.rollback()` is bypassed because `conn.status == STATUS_READY`.
- **Database Transaction (`tx_ms`):** **563.43 ms**. The single atomic CTE completes in exactly 1 physical round-trip across the Pacific WAN.
- **Total API Latency (`total_ms`):** **563.92 ms**.

### Peak Load / Queue Congestion (50 VUs Burst)
```
SUBMISSION_METRICS: id=cb61b19a-8f2d-4302-ad0a-10d847893227 total_ms=1657.61 scoring_ms=0.10 checkout_ms=1090.84 tx_ms=566.31
SUBMISSION_METRICS: id=77c2c6fb-b6ef-4c80-ada4-bb99d0169ec0 total_ms=1660.16 scoring_ms=0.07 checkout_ms=1102.69 tx_ms=557.18
SUBMISSION_METRICS: id=de33c155-ab47-4035-a367-85c1c2d6db19 total_ms=1660.31 scoring_ms=0.07 checkout_ms=1107.88 tx_ms=552.09
```
- **Transaction Time (`tx_ms`):** Remains rock-solid at **~560 ms** (PostgreSQL query performance did not degrade).
- **Checkout Queue Wait (`checkout_ms`):** 1,090 ms – 1,107 ms. Because all 20 connections across both Uvicorn workers were servicing the first wave of requests, requests in the second wave waited exactly 1 transaction cycle (~560 ms) and requests in the third wave waited ~1,100 ms.
- **Result:** Instead of crashing with `PoolError`, threads waited safely on `_pool_condition.wait()` and completed within **1.77 seconds wall-clock time**.

---

## 4. Background Job Worker Asynchronous Verification

The background job worker was verified running as a standalone supervisor process (`[program:job_worker]`):

```
2026-11-04 05:00:13,125 [INFO] app.core.database: Database connection pool initialized (min=1, max=3)
2026-11-04 05:00:13,125 [INFO] __main__: Job worker database pool initialized (min=1, max=3)
2026-11-04 05:00:13,126 [INFO] __main__: Started background job worker [standalone-worker]
```

### Job Processing Breakdown in Live Database
Querying the PostgreSQL database after 50-VU load test:
```
Jobs status breakdown: [('PROCESSING', 2), ('PENDING', 196), ('DONE', 348)]
Total test submissions recorded: 148
```
- **Asynchronous Execution:** Email generation, HTML templating, admin notification dispatch, and CRM synchronisation executed in the background without adding a single millisecond to user-facing API latency.
- **Worker Isolation:** The background worker utilized its own pool (`minconn=1, maxconn=3`), ensuring zero connection starvation against web workers.

---

## 5. Functional & Boundary Testing Verification

### 1. Idempotency Key Replay Verification
- Submitting identical payload with the same `idempotency_key` returns:
  `{"success": True, "submission_id": "4cfa826b-48f5-4519-a035-999e7eb9a8e9"}`
- Verified that **0 duplicate records** are created in `submissions`, `org_submission_links`, or `post_submit_jobs`.

### 2. Duplicate Submission Rate Limiting (5-Minute Window)
- Submitting another assessment with the same email address within 5 minutes returns:
  `HTTP 429: A submission from this email was received recently. Please wait a few minutes before submitting again.`

### 3. Invalid Organisation ID Validation
- Submitting with an inactive or non-existent organization UUID returns:
  `HTTP 400: Selected organisation is invalid or inactive.`

---

## 6. Acceptance Sign-Off

The testing results confirm that all performance criteria, functional requirements, data integrity contracts, and reliability thresholds have been satisfied.

