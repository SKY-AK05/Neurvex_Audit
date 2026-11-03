# NIWI Upgrade v3.1 — Phase 0: System Diagnosis & Hypothesis Verification

**Date:** 2026-11-03  
**Status:** COMPLETE (Decision Gate Passed)  
**Target Specification:** `upgrade_v3_1 (1).md`

---

## 1. Current State Inventory

| Component | Setting / Implementation | Source File |
|---|---|---|
| **Uvicorn Worker Count** | 2 workers (`--workers 2`) | `supervisord.conf` line 8 |
| **ACA Replica Scaling** | Single container / scalable | `Dockerfile`, Azure Container Apps |
| **PostgreSQL Connection Pool** | `ThreadedConnectionPool` (min=2, max=10 per worker) | `app/core/database.py` line 38 |
| **Total Possible Connections** | 2 workers × 10 maxconn = 20 connections per container | `app/core/database.py`, `supervisord.conf` |
| **Nginx Proxy Timeouts** | `proxy_read_timeout 60s; proxy_connect_timeout 10s;` | `frontend/nginx.conf` lines 29–30 |
| **Rate Limiter Storage** | In-memory storage (SlowAPI `get_remote_address`) | `app/core/limiter.py` |
| **Email Worker Startup** | `await start_dlq_worker()` in `app.main:startup_event` (runs once per worker) | `app/main.py` line 53 |
| **Stored Email Body Usage** | Built synchronously during `calculate_scores` and inserted with submission | `app/api/routes.py` line 265 |

---

## 2. Hypothesis Verification Matrix

| ID | Hypothesis | Investigation Result | Finding & Impact |
|---|---|---|---|
| **H1** | Advisory lock and connection held across scoring and email build, serializing submissions. | **CONFIRMED** | `routes.py` opens `with get_db_connection() as conn:` before scoring. In addition, nested `with conn:` inside `PooledConnection` prematurely calls `close()` on the pooled connection wrapper, causing connection state corruption across sequential queries. |
| **H2** | 6 lost submissions in k6 load tests were gateway timeouts. | **CONFIRMED** | P95 latency was 30,000.73 ms, matching default proxy/gateway timeout cutoffs. Database workers were still processing queries after client drop-off. |
| **H3** | Handlers are `async def` and execute blocking psycopg2/requests, freezing event loops. | **CONFIRMED** | `submit` and `get_submissions` are `async def` and invoke synchronous `psycopg2` queries on the main thread, freezing the event loop for concurrent requests like `GET /api/form-sections`. |
| **H4** | QuickChart work is an outbound HTTP call. | **DISPROVED / REFINED** | `build_email()` only performs URL encoding (`urllib.parse.quote`) and HTML template generation. However, it consumes CPU and delays transaction commit while holding pooled DB resources. |
| **H5** | Duplicate check and rate limiter block shared office IPs. | **VERIFIED SAFE / REFINED** | The 5-minute duplicate check is email-based (`WHERE email = %s`), not IP-based. SlowAPI rate limits are 100/hr per IP. |
| **H6** | Scoring is pure (no DB or network call) and fast. | **CONFIRMED** | `score_section()` is pure arithmetic ($< 1\text{ ms}$). `calculate_scores()` only touches the DB to load question metadata, which can be cached in-memory. |

---

## 3. Decision Gate & Phase 1 Execution Plan

1. **Keep Submit Contract:** The response returns `{"success": True, "submission_id": "...", "scores": {...}}` immediately.
2. **Pure In-Memory Scoring:** Load/cache form question schema; score in-memory before borrowing any database connection.
3. **Fix PooledConnection Bug:** Ensure `PooledConnection` correctly handles nested context managers without returning connections prematurely while active.
4. **Fix Event Loop Blocking (H3):** Declare synchronous endpoints as plain `def` (or use `run_in_threadpool`) so FastAPI executes them on worker threadpools.
5. **Shorten Lock & Transaction Duration:** Execute single atomic write transaction containing:
   - Submission insert with server-side `idempotency_key`
   - Bulk-inserted scores and answers
   - Normalized organization link with short advisory lock
   - Queued post-commit jobs (`post_submit_jobs`)
6. **Move Slow Work to Background:** Compile email HTML, render QuickChart, dispatch ACS email, and sync HubSpot out-of-band via background worker claiming jobs with `FOR UPDATE SKIP LOCKED`.

