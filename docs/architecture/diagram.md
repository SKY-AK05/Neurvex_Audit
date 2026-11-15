# System Architecture Diagrams

This document contains the visual architectural specifications for the Neuro-Inclusive Workplace Index (NIWI) platform, covering component topologies, communication protocols, authentication sequences, data models, and deployment infrastructure.

---

## 1. High-Level System Architecture

```mermaid
graph TD
    subgraph Clients["User & Administrative Clients"]
        Respondent["Public Survey Respondent<br/>(Desktop / Mobile Browser)"]
        OrgAdmin["Organization Admin<br/>(Client Portal)"]
        SuperAdmin["Orchvate Super Admin<br/>(Executive Command)"]
    end

    subgraph Edge["Ingress & Edge Proxy"]
        Nginx["Nginx Reverse Proxy<br/>Port 80 / 8080 (TLS Termination)"]
    end

    subgraph AppContainer["NIWI Core Container (Docker / Supervisord)"]
        VueSPA["Vue 3 SPA (Vite / Pinia)<br/>Static Bundle (/app/dist)"]
        FastAPI["FastAPI REST Engine<br/>Uvicorn (127.0.0.1:8000)"]
        OutboxWorker["Outbox Dispatcher<br/>(app.services.outbox_service)"]
        QueueWorker["Background Processor<br/>(app.tasks.service_bus_worker)"]
    end

    subgraph Storage["Persistence & Identity"]
        Postgres[("Azure PostgreSQL Flexible Server<br/>(nd_audit 14+)")]
        KeyVault["Azure Key Vault<br/>(kv-niwi-prod)"]
        EntraID["Microsoft Entra ID<br/>(OAuth2 / JWKS)"]
    end

    subgraph External["External Integrations"]
        ACS["Azure Communication Services<br/>(Transactional Email)"]
        HubSpot["HubSpot CRM<br/>(Lead Synchronization)"]
    end

    Respondent -->|HTTP/HTTPS| Nginx
    OrgAdmin -->|HTTP/HTTPS| Nginx
    SuperAdmin -->|HTTP/HTTPS| Nginx

    Nginx -->|Static Assets| VueSPA
    Nginx -->|/api/* Proxy| FastAPI

    FastAPI -->|Token Verification| EntraID
    FastAPI -->|Secrets / Managed Identity| KeyVault
    FastAPI -->|Connection Pool: 5-25 conns| Postgres

    OutboxWorker -->|Poll staged records| Postgres
    OutboxWorker -->|Enqueue background jobs| QueueWorker
    QueueWorker -->|Calculate & persist scores| Postgres
    QueueWorker -->|Dispatch email reports| ACS
    QueueWorker -->|Sync audit leads| HubSpot
```

---

## 2. Frontend-Backend Communication Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Respondent / Admin
    participant Vue as Vue 3 Client (SPA)
    participant Axios as Axios API Client (api.js)
    participant Nginx as Nginx Reverse Proxy
    participant API as FastAPI Backend (/api/*)
    participant Cache as In-Memory Cache (RAM)
    participant DB as PostgreSQL (nd_audit)

    User->>Vue: Interacts with UI / Submits Form
    Vue->>Axios: api.post('/api/submit', payload)
    Note over Axios: Injects Idempotency-Key & Bearer Token (if auth)
    Axios->>Nginx: HTTP POST /api/submit
    Nginx->>API: proxy_pass 127.0.0.1:8000/api/submit
    API->>API: SlowAPI Rate Limiter & Validation
    alt Cached Read Request
        API->>Cache: Check In-Memory Metadata / Org Cache
        Cache-->>API: Cache Hit (0.1ms)
    else Database Transaction
        API->>DB: Checkout Pooled Connection (<1ms)
        DB-->>API: Atomic Commit / Return Result
    end
    API-->>Nginx: HTTP 202 Accepted / 200 OK
    Nginx-->>Axios: Response Payload
    Axios-->>Vue: Reactive State Update (Pinia)
    Vue-->>User: Visual Confirmation / Dashboard Render
```

---

## 3. Microsoft Entra ID Authentication Flow

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Orchvate Administrator
    participant Browser as Web Browser
    participant MSAL as Microsoft Entra ID
    participant API as FastAPI Backend
    participant JWKS as Entra ID JWKS Endpoint
    participant DB as PostgreSQL

    Admin->>Browser: Access Admin Portal
    Browser->>MSAL: Initiate Login Redirect
    MSAL->>Admin: Corporate Login and MFA
    Admin-->>MSAL: Valid Corporate Credentials
    MSAL-->>Browser: Return ID Token and Access Token
    Browser->>API: Request with Bearer Token
    Note over API: jwks_middleware intercepts request
    API->>JWKS: Fetch Public Signing Keys
    JWKS-->>API: Return RSA Public Keys
    API->>API: Verify Signature Issuer and Audience
    API->>DB: Query admin_users for role assignment
    DB-->>API: Return User Role and Active Status
    API-->>Browser: HTTP 200 with User Context
    Browser->>Admin: Access Granted to Admin Dashboard
```

---

## 4. Database Entity-Relationship Diagram

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ ORG_SUBMISSION_LINKS : "links"
    SUBMISSIONS ||--o{ ORG_SUBMISSION_LINKS : "belongs to"
    ORGANIZATIONS ||--o{ ORGANIZATION_INVITATIONS : "issues"
    ORGANIZATIONS ||--o{ ASSESSMENT_ACCESS_TOKENS : "grants"
    RAW_SUBMISSIONS ||--o{ SERVICE_BUS_OUTBOX : "stages"
    SERVICE_BUS_OUTBOX ||--o{ SUBMISSION_OPERATION_STATES : "tracks"
    FORM_SECTIONS ||--o{ FORM_QUESTIONS : "contains"
    ADMIN_USERS ||--o{ ADMIN_SESSIONS : "authenticates"
    ORGANIZATIONS ||--o{ SUBMISSION_REASSIGNMENTS : "origin/dest"

    ORGANIZATIONS {
        uuid id PK
        varchar name UK
        boolean is_active
        boolean is_deleted
        varchar approval_status
        timestamptz created_at
    }

    SUBMISSIONS {
        uuid id PK
        varchar organisation_name
        varchar designation
        varchar department
        varchar respondent_email
        integer score_total
        varchar maturity_tier
        timestamptz submitted_at
    }

    RAW_SUBMISSIONS {
        uuid submission_id PK
        jsonb payload
        varchar idempotency_key UK
        varchar status
        timestamptz created_at
    }

    SERVICE_BUS_OUTBOX {
        bigserial id PK
        uuid submission_id FK
        varchar topic
        jsonb payload
        varchar status
        integer retry_count
        timestamptz created_at
    }

    SUBMISSION_OPERATION_STATES {
        bigserial id PK
        uuid submission_id FK
        varchar operation_type
        varchar status
        integer attempts
        text last_error
        timestamptz updated_at
    }

    ADMIN_USERS {
        uuid id PK
        varchar email UK
        varchar role
        boolean is_active
        timestamptz created_at
    }

    FORM_SECTIONS {
        integer id PK
        varchar title
        varchar slug UK
        integer display_order
        boolean is_active
    }

    FORM_QUESTIONS {
        integer id PK
        integer section_id FK
        text question_text
        varchar question_type
        integer order_index
        boolean is_required
    }
```

---

## 5. Submission Lifecycle (Asynchronous Ingestion & 202 Flow)

```mermaid
sequenceDiagram
    autonumber
    actor Respondent as Audit Respondent
    participant UI as Vue 3 Single Page App
    participant API as FastAPI Ingestion Layer
    participant DB as PostgreSQL (nd_audit)
    participant Outbox as Outbox Dispatcher
    participant Worker as Background Worker
    participant ACS as Azure Email Service

    Respondent->>UI: Completes 44 Assessment Inputs & Clicks Submit
    UI->>API: HTTP POST /api/submit (Idempotency Key, Payload)
    API->>API: Validate Inputs & Verify Idempotency Cache
    API->>DB: Atomic Transaction: INSERT INTO raw_submissions + service_bus_outbox
    DB-->>API: Transaction Committed
    API-->>UI: HTTP 202 Accepted (submission_id returned in <25ms)
    UI-->>Respondent: Render Instant Confirmation & Local Preview

    Note over Outbox,DB: Decoupled Background Processing Pipeline
    loop Outbox Polling Cycle (Every 5 seconds)
        Outbox->>DB: SELECT FOR UPDATE SKIP LOCKED FROM service_bus_outbox
        DB-->>Outbox: Batch of Pending Staged Records
        Outbox->>Worker: Enqueue Background Scoring Job
    end

    Worker->>Worker: Compute 8 Pillars (0-20), Total (0-160) & Tier
    Worker->>DB: Write Final Record into submissions table
    Worker->>DB: Update Outbox & Operation Status to 'completed'
    Worker->>ACS: Dispatch HTML Scorecard Email (donotreply@orchvate.in)
    ACS-->>Respondent: Executive Scorecard & Action Roadmap Delivered
```

---

## 6. Background Processing & Outbox Dispatch Architecture

```mermaid
flowchart TD
    subgraph Ingestion["Ingestion Phase (Sync - <25ms)"]
        SubmitReq["POST /api/submit"] --> FastValidation["Fast Schema Validation & Idempotency Check"]
        FastValidation --> DBWrite["Atomic DB Write:<br/>1. raw_submissions<br/>2. service_bus_outbox"]
        DBWrite --> HTTP202["Return HTTP 202 Accepted to Client"]
    end

    subgraph Polling["Outbox Dispatcher Daemon"]
        DBWrite -.-> StagedRows[("PostgreSQL Table:<br/>service_bus_outbox")]
        PollTimer["Periodic Poller (Every 5s)"] --> SkipLocked["SELECT ... FOR UPDATE SKIP LOCKED<br/>(Concurrency-Safe Across Replicas)"]
        SkipLocked --> StagedRows
        StagedRows --> ClaimedBatch["Claim Batch & Mark 'processing'"]
    end

    subgraph Execution["Background Processing Worker"]
        ClaimedBatch --> ComputeScore["Compute 8 Pillar Scores & Maturity Tier"]
        ComputeScore --> PersistAudit["Persist into 'submissions' Table"]
        PersistAudit --> EmailFormatting["Render HTML Report Template"]
        EmailFormatting --> SendEmail["Dispatch via Azure Communication Services"]
        SendEmail --> UpdateOutbox["Mark Outbox Record as 'completed'"]
    end

    subgraph DLQ["Dead Letter Queue & Failure Handling"]
        ComputeScore -.->|Exception| RetryCheck{Retry Count < 3?}
        SendEmail -.->|Network Timeout| RetryCheck
        RetryCheck -->|Yes| BackoffQueue["Increment Retry & Exponential Backoff"]
        RetryCheck -->|No| DeadLetter["Mark Outbox Status: 'failed'<br/>(Dead Letter Queue)"]
        DeadLetter --> SuperAdminReplay["Admin Triggers Manual Replay<br/>POST /api/admin/submissions/replay"]
        SuperAdminReplay --> ClaimedBatch
    end
```

---

## 7. API Request & Security Lifecycle

```mermaid
flowchart TD
    ClientReq["Incoming HTTP Request"] --> NginxProxy["Nginx Reverse Proxy (Port 80/8080)"]
    NginxProxy --> SecurityHeaders["Security Headers Injection<br/>(CSP, X-Frame-Options, HSTS)"]
    SecurityHeaders --> SlowAPI["SlowAPI Rate Limiter<br/>(IP & Endpoint Quotas)"]
    
    SlowAPI -->|Quota Exceeded| HTTP429["Return HTTP 429 Too Many Requests"]
    SlowAPI -->|Within Quota| JWKSMiddleware["JWKS Authentication Middleware"]
    
    JWKSMiddleware -->|Protected Route & Invalid/Missing Token| HTTP401["Return HTTP 401 Unauthorized"]
    JWKSMiddleware -->|Public Route OR Valid Token| RouteHandler["FastAPI Route Handler & Pydantic Validation"]
    
    RouteHandler -->|Payload Invalid| HTTP422["Return HTTP 422 Unprocessable Entity"]
    RouteHandler -->|Payload Valid| PoolCheckout["Database Pool Connection Checkout<br/>(Statement Timeout: 15s)"]
    
    PoolCheckout --> DBExecute["Execute SQL Query / Transaction"]
    DBExecute -->|DB Failure / Timeout| Rollback["Rollback Connection & Log Error"]
    Rollback --> HTTP500["Return HTTP 500 Internal Error"]
    
    DBExecute -->|Success| Commit["Commit Transaction & Return to Pool"]
    Commit --> Serialization["Pydantic Response Serialization"]
    Serialization --> HTTPResponse["Return HTTP 200/201/202 Response to Client"]
```

---

## 8. Azure Deployment Topology

```mermaid
graph TD
    subgraph Internet["Public Internet"]
        PublicUsers["Respondents & Administrators<br/>(https://niwi.orchvate.in)"]
    end

    subgraph AzureCloud["Microsoft Azure Cloud Infrastructure (orchvate-rg)"]
        subgraph DNSZone["DNS & Routing"]
            Domain["niwi.orchvate.in<br/>(DNS A-Record)"]
        end

        subgraph ComputeVM["Virtual Machine / Container Host (taiga.orchvate.com)"]
            HostNginx["Host Nginx Proxy<br/>Port 443 (SSL Termination / Certbot)"]
            
            subgraph DockerContainer["Docker Container: niwi (Port 8080:80)"]
                Supervisord["Supervisord Process Manager"]
                ContNginx["Internal Nginx Proxy (Port 80)"]
                UvicornFastAPI["Uvicorn Backend (127.0.0.1:8000, 2 Workers)"]
                OutboxDaemon["Outbox Dispatcher Process"]
                WorkerDaemon["Service Bus Background Worker"]
            end
        end

        subgraph AzureServices["Managed Azure Cloud Services"]
            Postgres[("Azure PostgreSQL Flexible Server<br/>(nd_audit, TLS 1.2+ Required)")]
            KeyVault["Azure Key Vault (kv-niwi-prod)<br/>(Managed Identity Authentication)"]
            ACS["Azure Communication Services<br/>(Verified Sender: donotreply@orchvate.in)"]
            EntraID["Microsoft Entra ID (Azure AD)<br/>(OAuth2 / OIDC Tenant)"]
        end
    end

    PublicUsers -->|HTTPS 443| Domain
    Domain --> HostNginx
    HostNginx -->|HTTP 8080| ContNginx
    ContNginx -->|Static UI /dist| Supervisord
    ContNginx -->|/api/* 8000| UvicornFastAPI
    
    Supervisord --> UvicornFastAPI
    Supervisord --> ContNginx
    Supervisord --> OutboxDaemon
    Supervisord --> WorkerDaemon

    UvicornFastAPI -->|System-Assigned Managed Identity| KeyVault
    UvicornFastAPI -->|SSL / Pool 5-25| Postgres
    UvicornFastAPI -->|Token Verification| EntraID
    
    OutboxDaemon -->|Outbox Poll| Postgres
    WorkerDaemon -->|Scoring & State| Postgres
    WorkerDaemon -->|Email Dispatch| ACS
```

---

## 9. Error Handling & Dead-Letter Queue Recovery

```mermaid
flowchart TD
    ErrorEvent["System Error / Fault Detected"] --> Classify{Fault Classification}

    Classify -->|Rate Limit Exceeded| RLEntry["SlowAPI Throttle Triggered"]
    RLEntry --> RLResp["Return HTTP 429 with Retry-After header"]

    Classify -->|Database WAN Timeout / Failure| DBEntry["psycopg2 OperationalError"]
    DBEntry --> DBPool["Connection Pool Recycle & Transient Retry (15s limit)"]
    DBPool -->|Recovered| ResumeSuccess["Operation Completed Successfully"]
    DBPool -->|Exhausted| Graceful503["Return HTTP 503 Service Unavailable (Circuit Open)"]

    Classify -->|Background Scoring Failure| WorkerEntry["Worker Exception in Job Loop"]
    WorkerEntry --> WorkerRetry["Increment retry_count (Max 3) with Exponential Backoff"]
    WorkerRetry -->|retry <= 3| ReEnqueue["Return message to outbox queue"]
    WorkerRetry -->|retry > 3| MoveDLQ["Mark status: 'failed' in submission_operation_states"]
    MoveDLQ --> AdminAlert["Log CRITICAL error & show in Super Admin DLQ Dashboard"]
    AdminAlert --> ReplayEndpoint["Admin triggers POST /api/admin/submissions/{id}/replay"]
    ReplayEndpoint --> ReEnqueue

    Classify -->|External Email / CRM Timeout| ExtEntry["ACS or HubSpot Timeout"]
    ExtEntry --> ExtDecouple["Audit submission already persisted in DB"]
    ExtDecouple --> ExtRetry["Background task worker schedules outbox retry without user impact"]
```
