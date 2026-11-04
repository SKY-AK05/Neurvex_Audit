# NIWI — Complete Architecture Audit & Dependency Map

---

## 1. Executive Architecture Summary

NIWI is a multi-tenant organisational inclusion and maturity assessment platform. Employees complete an assessment consisting of **8 core pillars and 40 assessment questions**. The platform evaluates responses, computes maturity scores across the dimensions, generates feedback reports, synchronises client records with HubSpot CRM, and dispatches automated notifications.

### High-Level Topology

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
         │                         │                              │
         │                         ▼                              │
         │   Uvicorn Process Manager (Workers: 2)                 │
         │     ├── Worker 1 (PID 12)                              │
         │     │     ├── FastAPI Routing Engine                   │
         │     │     ├── ThreadedConnectionPool (min=2, max=10)   │
         │     │     ├── In-Memory Scoring Cache (TTL: 300s)      │
         │     │     └── Background Worker Task (job_worker)      │
         │     └── Worker 2 (PID 13)                              │
         │           ├── FastAPI Routing Engine                   │
         │           ├── ThreadedConnectionPool (min=2, max=10)   │
         │           ├── In-Memory Scoring Cache (TTL: 300s)      │
         │           └── Background Worker Task (job_worker)      │
         └─────────────────────────┬──────────────────────────────┘
                                   │ Public WAN TLS (RTT: ~185 ms)
                                   │ Chicago, USA -> Hong Kong, HK
                                   ▼
         ┌────────────────────────────────────────────────────────┐
         │ Azure Database for PostgreSQL Flexible Server          │
         │  - Host: generative-ai.postgres.database.azure.com     │
         │  - Region: East Asia (Hong Kong) [IP: 20.2.146.109]    │
         │  - PostgreSQL Version: 17.11                           │
         │  - max_connections: 50 (Shared across Orchvate apps)   │
         └─────────────────────────┬──────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
       ┌──────────────────────────┐  ┌──────────────────────────┐
       │ Azure Communication Serv │  │ HubSpot CRM Integration  │
       │ (ACS Email Delivery)     │  │ (Deals / Contacts Sync)  │
       └──────────────────────────┘  └──────────────────────────┘
```

---

## 2. Infrastructure & Geographic Topology Audit

A critical geographical mismatch exists between the compute host and the database server:

| Component | Physical Host / Provider | Resolved IP | Geographic Location | Azure Region |
| :--- | :--- | :--- | :--- | :--- |
| **Host VM (`Taiga`)** | Microsoft Azure VM | `52.240.143.40` | Chicago, Illinois, USA | `centralus` / `northcentralus` |
| **PostgreSQL Database** | Azure Flexible Server | `20.2.146.109` | Hong Kong | `eastasia` |
| **Physical Distance** | ~12,500 kilometers (trans-Pacific network route) |
| **Measured Network RTT** | **184.6 ms – 194.0 ms** per single TCP/SQL round trip |

### Shared Host Environment Contention
The host VM (`Taiga`) has **2 vCPUs and 3.8 GiB RAM**, concurrently hosting **12 Docker containers**:
1. `niwi`: NIWI FastAPI backend + Nginx web server.
2. `caddy`: Host-level TLS reverse proxy.
3. `magent-dashboard`: Orchvate Agent management dashboard.
4. `taiga-taiga-back-1`: Django REST backend for Taiga PM.
5. `taiga-taiga-async-1`: Celery worker for Taiga.
6. `taiga-taiga-events-1`: Node.js WebSocket gateway.
7. `taiga-taiga-db-1`: Local PostgreSQL 12.3 database (for Taiga only).
8. `taiga-taiga-events-rabbitmq-1`: RabbitMQ broker.
9. `taiga-taiga-async-rabbitmq-1`: RabbitMQ broker.
10. `taiga-taiga-gateway-1`: Taiga Nginx gateway.
11. `taiga-taiga-protected-1`: Taiga access controller.
12. `taiga-taiga-front-1`: Taiga Vue/Angular frontend.

---

## 3. Technology Stack and Entry Points

### 3.1 Frontend (`frontend/`)
- **Framework:** Vue.js 3 with Vite 5 and TypeScript.
- **Routing:** `vue-router` (`frontend/src/router/`).
- **Authentication:** `@azure/msal-browser` for Microsoft Entra ID admin authentication.
- **Entry Points:**
  - `frontend/index.html` $\rightarrow$ `frontend/src/main.ts`
  - Public Assessment Route: `/audit?org=<CODE>` (`frontend/src/views/AuditView.vue` or equivalent component)
  - API Client: Centralized HTTP client consuming `/api/*`.

### 3.2 Backend (`app/`)
- **Framework:** FastAPI `0.115.5` running on Starlette `0.41.3` and Uvicorn `0.32.1`.
- **Runtime:** Python 3.11.
- **Process Supervisor:** `supervisord` managing Nginx and Uvicorn (`workers: 2`).
- **Entry Point:** `app/main.py:app`.

### 3.3 Database Access & Connection Pool (`app/core/database.py`)
- **Driver:** `psycopg2-binary` 2.9.10.
- **Pool Class:** `ThreadedConnectionPool` wrapped by `PooledConnection` context manager.
- **Pool Size:** `minconn = 2, maxconn = 10` per worker process ($2 \times 10 = 20$ maximum connections across 2 workers).
- **Checkout Behavior:** Non-blocking immediate fail (`PoolError`). No FIFO wait queue.
- **Checkout Reset:** Calls `conn.rollback()` on checkout, adding 1 WAN round trip (~185 ms).

---

## 4. End-to-End Submission Flow Analysis

### Tracing `POST /api/submit`
Endpoint definition: [`Audit/app/api/routes.py:112`](file:///home/aakash.padyachi/apps/niwi/Audit/app/api/routes.py#L112)

```
[Client POST /api/submit]
   │
   ├── 1. Rate Limiting (SlowAPI in-memory: 100/hr, 1000/day)
   │
   ├── 2. Pure Scoring Calculation:
   │      - sections, threshold = get_form_sections_metadata(None)
   │        * CRITICAL DEFECT: If cache expired, triggers N+1 queries over WAN (4.1s)
   │      - calculate_scores_pure(data, ...) -> 0.06 ms
   │
   ├── 3. Database Connection Acquisition:
   │      - with get_db_connection() as conn:
   │        * Checks out connection from pool (0.016 ms)
   │        * Issues conn.rollback() (185 ms)
   │
   ├── 4. Atomic Database Transaction Block (with conn:):
   │      - Query 1: Duplicate email check (371 ms)
   │      - Query 2: Organization verification (185 ms)
   │      - Query 3: Insert submission RETURNING id (188 ms)
   │      - Query 4: Insert org_submission_links (185 ms)
   │      - Query 5: Query app_settings for crm_sync_enabled (185 ms)
   │      - Query 6: Insert post_submit_jobs (185 ms)
   │      - Query 7: Transaction COMMIT (183 ms)
   │      * TOTAL CONNECTION HOLD TIME: 2,377 ms - 2,411 ms
   │
   ├── 5. Connection Return to Pool
   │
   ├── 6. HTTP 201 Response Returned to Client
   │
   ├── 7. Starlette Background Task (_bg_notify_admin):
   │      - Checks out second DB connection
   │      - Runs get_settings() with DDL checks (ensure_settings_table -> 1,200 ms)
   │      - Runs get_sender_for_send() (370 ms)
   │      - Spawns background email dispatch thread
   │
   └── 8. Background Job Worker (job_worker.py):
          - Runs inside both Uvicorn workers
          - Claims jobs from post_submit_jobs via FOR UPDATE SKIP LOCKED
          - Renders email HTML body
          - Updates submissions.email_body and marks job DONE
```

---

## 5. Identified Architectural & Performance Defects

| ID | Component | Defect Description | Impact |
| :--- | :--- | :--- | :--- |
| **DEF-01** | `routes.py:126-418` | **8 Sequential WAN Round Trips:** 6 SQL queries + 1 checkout rollback + 1 commit over 185 ms WAN link. | Connection held for 2.4s; latency balloons under concurrency. |
| **DEF-02** | `scoring_service.py:150` | **Unoptimized Cache Miss in Scoring:** `get_form_sections_metadata(None)` runs legacy $1+8$ query loop and DDL checks. | Periodic 4.1-second latency spikes when 5-min cache expires. |
| **DEF-03** | `database.py:216` | **Zero-Wait Connection Pool:** `ThreadedConnectionPool.getconn()` fails immediately when 10 connections are busy. | HTTP 500 burst failures when concurrency exceeds 10 conns/worker. |
| **DEF-04** | `supervisord.conf` / `main.py` | **Duplicated Embedded Workers:** `job_worker` runs inside both Uvicorn web workers rather than as a dedicated process. | Worker polling competes with web traffic for pool connections. |
| **DEF-05** | `settings_service.py:75` | **DDL Verification on Request Path:** `ensure_settings_table` executes `information_schema` queries on every admin alert. | Wastes 1.2s of connection hold time per submission. |
| **DEF-06** | `niwi-sustained-load.js` | **Premature Test Cutoff in k6:** Sustained k6 test lacked adequate ramp-down grace period for in-flight requests. | False-positive functional FAIL (110/112 report vs 112 DB). |

