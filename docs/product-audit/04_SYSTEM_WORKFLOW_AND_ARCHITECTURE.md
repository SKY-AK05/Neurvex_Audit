# System Workflow and Architecture Documentation
## NIWI / NeuroMark Audit Platform (Version 2.1)
### Prepared for: Software Architects, System Integrators, Security Auditors & Lead Engineers
### Document ID: DOC-04-SYS-ARCH
### Audit Date: November 2026
### Repository Root: `c:\Users\Aakash\Documents\PROJECT WEB\orchvate\NIWI`

---

## 1. Overall System Architecture

### 1.1 Architectural Model
NIWI is architected as a modular, containerized multi-tenant software system deployed on **Azure Container Apps (ACA)**. The system couples a compiled **Vue 3 Single Page Application (SPA)** with an asynchronous **FastAPI (Python 3.11)** backend, persisted to **Azure Database for PostgreSQL (Flexible Server)**.

The platform is deployed inside a single hardened Docker container managed by `supervisord`:
- **Nginx Web Server (Port 80):** High-speed reverse proxy terminating inbound HTTP traffic, serving static compiled Vue assets, caching static files, and proxying all `/api/*` traffic to the backend.
- **Uvicorn ASGI Server (Port 8000):** Executes the FastAPI application across 4 asynchronous worker processes.
- **Managed Cloud Services:** Production secrets, administrative identity, transactional email dispatches, and CRM updates are handled through native Azure managed integrations (Azure Key Vault, Microsoft Entra ID, and Azure Communication Services).

```mermaid
flowchart TD
    subgraph Clients["Inbound Traffic Tier"]
        C1["Public / Employee Browser\n(Desktop & Mobile)"]
        C2["Client Tenant HR Administrator\n(Magic-Link Authenticated)"]
        C3["Orchvate System Administrator\n(Microsoft Entra ID Authenticated)"]
    end

    subgraph ContainerEdge["Azure Container Apps (niwi.orchvate.in)"]
        NGINX["Nginx Web Server & Reverse Proxy\n(Port 80)"]
        
        subgraph StaticBundle["Frontend Asset Store"]
            VUE["Vue 3 SPA Compiled Distribution\n(/frontend/dist/)"]
        end

        subgraph ASGICluster["Uvicorn ASGI Process Cluster"]
            UVI["Uvicorn Master (Port 8000)"]
            W1["FastAPI Worker 1"]
            W2["FastAPI Worker 2"]
            W3["FastAPI Worker 3"]
            W4["FastAPI Worker 4"]
        end
    end

    subgraph AzureEcosystem["Azure Managed Cloud Ecosystem"]
        KV["Azure Key Vault\n(Dynamic Secrets Engine)"]
        ENTRA["Microsoft Entra ID\n(JWKS OIDC Endpoint)"]
        ACS["Azure Communication Services\n(Transactional Email)"]
        PG[("Azure Database for PostgreSQL\nFlexible Server (Psycopg2 Pool)")]
    end

    subgraph ExternalThirdParty["Third-Party Cloud Services"]
        QC["QuickChart.io API\n(SVG Radar Generator)"]
        HS["HubSpot CRM Cloud\n(Contact Pipeline Sync)"]
    end

    C1 & C2 & C3 -->|HTTPS:443| NGINX
    NGINX -->|Serve Static HTML/JS/CSS| VUE
    NGINX -->|Reverse Proxy /api/*| UVI
    UVI --> W1 & W2 & W3 & W4
    
    W1 & W2 & W3 & W4 <-->|Resolve Secrets at Boot| KV
    W1 & W2 & W3 & W4 <-->|Cryptographic JWKS Validation| ENTRA
    W1 & W2 & W3 & W4 <-->|SQL Queries & Advisory Locks| PG
    W1 & W2 & W3 & W4 -->|Async Email Dispatch| ACS
    W1 & W2 & W3 & W4 -->|QuickChart URL Encoding| QC
    W1 & W2 & W3 & W4 -.->|Best-Effort Async Sync| HS
```

### 1.2 Architectural Interpretation
1. **Network Boundary:** The public internet only communicates with Nginx over standard HTTP/HTTPS. The Uvicorn application processes listen strictly on the internal container loopback (`127.0.0.1:8000`), completely shielding the Python runtime from direct internet exposure.
2. **Process Management:** `supervisord` monitors both Nginx and Uvicorn. If an ASGI worker crashes due to an unhandled operating system signal or memory exhaustion, `supervisord` automatically spawns a replacement worker process.
3. **Stateless App Tier:** The application processes maintain zero local filesystem session state. All session contexts are cryptographically signed within JWT tokens or persisted to Azure PostgreSQL, allowing seamless horizontal container auto-scaling.

---

## 2. High-Level Component Interaction & Communication

The following diagram depicts the precise data flow and interface boundaries between frontend views, backend routers, domain services, database tables, and external integrations:

```mermaid
flowchart LR
    subgraph FrontendViews["Vue 3 Client Layer (frontend/src/views/)"]
        V_Audit["AuditForm.vue"]
        V_Orgs["Organisations.vue"]
        V_Analytics["Analytics.vue"]
        V_Detail["SubmissionDetail.vue"]
    end

    subgraph APIRouters["FastAPI Routers (app/api/)"]
        R_Routes["routes.py (/api/submit, /api/submissions)"]
        R_Orgs["orgs.py (/api/manage/orgs)"]
        R_Drafts["drafts.py (/api/drafts)"]
        R_Org["org.py (/api/org)"]
    end

    subgraph DomainServices["Domain Logic (app/services/)"]
        S_Score["scoring_service.py"]
        S_OrgScore["org_scoring_service.py"]
        S_Filter["filter_service.py"]
        S_Email["settings_service.py"]
    end

    subgraph DataStorage["PostgreSQL Tables"]
        T_Sub["submissions & submission_scores"]
        T_Org["organisations & org_members"]
        T_Draft["drafts"]
        T_DLQ["email_dlq"]
    end

    V_Audit -->|POST /api/submit| R_Routes
    V_Audit -->|POST /api/drafts/save| R_Drafts
    V_Orgs -->|GET /api/manage/orgs/:id/scores| R_Orgs
    V_Analytics -->|GET /api/submissions| R_Routes

    R_Routes --> S_Score --> T_Sub
    R_Orgs --> S_OrgScore --> T_Org
    R_Drafts --> T_Draft
    R_Routes --> S_Email --> T_DLQ
    R_Routes --> S_Filter --> T_Sub
```

---

## 3. Authentication & Authorization Workflows

### 3.1 Administrative SSO Authentication (Microsoft Entra ID)
- **Why It Exists:** To eliminate shared administrative passwords and enforce corporate multi-factor authentication for Orchvate personnel.
- **Initiator:** Orchvate System Administrator accessing `/GPadmin`.
- **Trigger:** Clicking "Sign In with Microsoft".

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Orchvate Administrator
    participant Browser as Vue 3 Client (AdminLogin.vue)
    participant MSAL as @azure/msal-browser
    participant Entra as Microsoft Entra ID
    participant Backend as FastAPI (security.py)
    participant DB as PostgreSQL (admin_users)

    Admin->>Browser: Navigate to /GPadmin & Click Login
    Browser->>MSAL: loginRedirect()
    MSAL->>Entra: OAuth2 / OIDC Authorization Request
    Entra-->>Admin: Prompt for Corporate Credentials & MFA
    Admin->>Entra: Authenticate Successfully
    Entra-->>Browser: Redirect to /GPadmin with ID Token
    Browser->>MSAL: handleRedirectPromise() extracts Bearer JWT
    Browser->>Backend: POST /api/admin/login (Header: Bearer Entra_JWT)
    Backend->>Backend: Fetch & Cache Microsoft JWKS Keys
    Backend->>Backend: Validate Token Signature, Nonce & Expiry
    Backend->>DB: SELECT * FROM admin_users WHERE email = :email
    alt User Not Found or Inactive
        DB-->>Backend: 0 Rows
        Backend-->>Browser: 403 Forbidden ("Unauthorized Admin Email")
    else User Active & Role Verified
        DB-->>Backend: admin_user Record (role = 'admin' or 'super')
        Backend->>Backend: Mint Application-Level Session JWT
        Backend-->>Browser: 200 OK {"token": App_JWT, "user": {...}}
        Browser->>Browser: Store App_JWT in sessionStorage
        Browser->>Browser: Redirect to /admin/overview
    end
```

### 3.2 Client Organisation Member Authentication (Magic Link)
- **Why It Exists:** Enables passwordless, tenant-isolated access for client HR leaders without requiring account registration.
- **Initiator:** Client HR Representative accessing `/org/login`.
- **Trigger:** Submitting work email address.

```mermaid
sequenceDiagram
    autonumber
    actor HR as Client HR Representative
    participant Client as Vue 3 Client (OrgLogin.vue)
    participant Backend as FastAPI (app/api/org.py)
    participant DB as PostgreSQL (organisations, org_tokens)
    participant ACS as Azure Communication Services
    participant Verify as Vue 3 Client (OrgVerify.vue)

    HR->>Client: Enter Email & Company Name
    Client->>Backend: POST /api/org/register-or-login
    Backend->>DB: Query organisation by domain/name
    Backend->>Backend: Generate 32-Byte Cryptographic Nonce
    Backend->>Backend: Compute token_hash = SHA-256(Nonce)
    Backend->>DB: INSERT INTO org_tokens (token_hash, expires_at = NOW() + 15m)
    Backend->>ACS: Send Magic Link Email containing Raw Nonce
    ACS-->>HR: Delivers email with link: /org/verify?token=RawNonce
    HR->>Verify: Clicks Magic Link in Email
    Verify->>Backend: GET /api/org/verify?token=RawNonce
    Backend->>Backend: Compute SHA-256(RawNonce)
    Backend->>DB: SELECT * FROM org_tokens WHERE token_hash = :hash AND NOT is_used
    alt Token Invalid or Expired (>15 mins)
        Backend-->>Verify: 401 Unauthorized ("Magic link expired")
    else Token Valid
        Backend->>DB: UPDATE org_tokens SET is_used = TRUE
        Backend->>Backend: Mint 30-Day Org Member JWT with org_id claim
        Backend-->>Verify: 200 OK {"token": 30Day_JWT, "org": {...}}
        Verify->>Verify: Store 30Day_JWT in localStorage
        Verify->>Verify: Redirect to /org/dashboard
    end
```

---

## 4. Organisation Creation & Management Lifecycle

### 4.1 Automated Linking via Concurrency-Safe Advisory Locks
- **Why It Exists:** When a company rolls out an audit, multiple employees submit surveys within seconds. Without concurrency control, multiple duplicate organization rows are inserted.
- **Mechanism:** PostgreSQL transaction-level advisory locking (`pg_advisory_xact_lock`).

```mermaid
flowchart TD
    A["Incoming Submission with company_name"] --> B["Sanitize & Normalize: trim().lower()"]
    B --> C["Begin PostgreSQL Database Transaction"]
    C --> D["Acquire Transaction Advisory Lock:\nSELECT pg_advisory_xact_lock(hashtext(name))"]
    D --> E{"Does Organisation\nExist in Database?"}
    E -->|Yes| F["Fetch Existing organisation_id"]
    E -->|No| G["INSERT INTO organisations (name, status)\nRETURNING id"]
    G --> F
    F --> H["INSERT INTO organisation_submissions\n(organisation_id, submission_id, weight = 1.0)"]
    H --> I["Commit Transaction (Releases Advisory Lock Automatically)"]
    I --> J["Submission Linked Cleanly with Zero Duplicate Entities"]
```

---

## 5. End-to-End Assessment Lifecycle & Processing

### 5.1 Complete Assessment Submission Sequence
```mermaid
sequenceDiagram
    autonumber
    actor User as Audit Respondent
    participant Form as Vue 3 SPA (AuditForm.vue)
    participant Nginx as Nginx Reverse Proxy
    participant Backend as FastAPI (app/api/routes.py)
    participant ScoreSvc as scoring_service.py
    participant DB as Azure PostgreSQL
    participant QuickChart as QuickChart.io API
    participant ACS as Azure Comm Services
    participant CRM as crm_service.py (HubSpot)

    User->>Form: Completes Questions & Accepts GDPR Consent
    User->>Form: Clicks "Submit Audit"
    Form->>Nginx: POST /api/submit (JSON Payload)
    Nginx->>Backend: Proxy to 127.0.0.1:8000
    Backend->>DB: Check Duplicate IP / Email (5-minute window)
    Backend->>DB: Acquire pg_advisory_xact_lock
    Backend->>ScoreSvc: calculate_scores(payload)
    ScoreSvc->>ScoreSvc: Score 8 Pillars & Evaluate Gating (CALC-001 - CALC-003)
    ScoreSvc->>ScoreSvc: Evaluate Low Visibility Flag (CALC-004)
    ScoreSvc->>ScoreSvc: Compute Overall Average & Maturity Tier (CALC-005, CALC-006)
    ScoreSvc->>QuickChart: Encode Radar Chart Config URL
    ScoreSvc->>ScoreSvc: Compile Branded HTML Email Template
    ScoreSvc-->>Backend: Returns Section Scores, Overall Avg, Email HTML
    Backend->>DB: INSERT into submissions
    Backend->>DB: INSERT into submission_scores (8 Rows)
    Backend->>DB: INSERT into submission_sections (JSON Answers)
    Backend->>DB: Link to Organisation Entity
    Backend-->>Form: 200 OK {"submission_id": "...", "scores": {...}}
    Form-->>User: Display Immediate Diagnostic Scorecard
    
    par Asynchronous Notification Pipeline
        Backend->>ACS: Dispatch Transactional Scorecard Email
        alt ACS Dispatch Fails
            Backend->>DB: INSERT INTO email_dlq (status = 'PENDING')
        end
    and Background CRM Sync
        Backend->>CRM: sync_submission_to_hubspot()
        alt HubSpot Fails
            CRM-->>Backend: Log Error Trace (Silently Discarded)
        end
    end
```

---

## 6. Score Generation & Mathematical Transformation Flow

```mermaid
flowchart TD
    subgraph RawAnswers["Stage 1: User Response Capture"]
        A1["Discrete Question Responses:\n'Yes', 'Partially', 'No', 'Not Sure', 'N/A'"]
        A2["Operational Gating Input:\nhas_physical_workspace, has_suppliers"]
    end

    subgraph QuestionMarking["Stage 2: Discrete Marking (CALC-001)"]
        B1["Score Mapping Engine:\nYes = 4 marks\nPartially = 2 marks\nNo / Not Sure = 0 marks"]
    end

    subgraph SectionAggregation["Stage 3: Dimension Normalization (CALC-002, 003)"]
        C1["Raw Mark Accumulation:\nSum marks across applicable questions"]
        C2{"Were any questions\nmarked 'N/A'?"}
        C3["Direct Score out of 20:\nScore = Raw Score"]
        C4["Rescale Formula:\n(Raw / Max Applicable) * 20"]
        C5["Low Visibility Evaluation:\nIf Not Sure >= 50%, flag Low Visibility"]
    end

    subgraph OverallComposite["Stage 4: Headline Indexing (CALC-005, 006)"]
        D1["Filter out Gated 'NA' Sections"]
        D2["Calculate Arithmetic Mean:\nSum(Valid Section Scores) / Valid Section Count"]
        D3["Maturity Tier Categorization:\nLevel 1: <= 6 | Level 2: <= 14 | Level 3: 15-20"]
    end

    subgraph CorporateWeighting["Stage 5: Multi-Respondent Index (CALC-010 - 014)"]
        E1["Fetch Linked Respondent Weights (w_i)"]
        E2["Compute Weighted Org Average:\nSum(Overall * w_i) / Sum(w_i)"]
        E3["Calculate Context Applicability Adjustment:\nOrgAvg - Sum(PillarAvg * 0.125)"]
    end

    A1 --> B1
    A2 -->|If 'No'| D1
    B1 --> C1
    C1 --> C2
    C2 -->|No| C3
    C2 -->|Yes| C4
    C1 --> C5
    C3 & C4 --> D1
    D1 --> D2 --> D3
    D3 --> E1 --> E2 --> E3
```

---

## 7. Error Handling, Resilience & Recovery Architecture

```mermaid
flowchart TD
    subgraph Failures["Runtime Failure Scenarios"]
        F1["Database Pool Exhaustion\n(maxconn=10 reached)"]
        F2["ACS Email Delivery Outage\n(Network / 5xx Error)"]
        F3["Entra ID JWKS Key Rotation\n(Signature Mismatch)"]
        F4["HubSpot CRM Rate Limiting\n(HTTP 429 Too Many Requests)"]
    end

    subgraph HandlingEngines["Error Handling Strategies"]
        H1["FastAPI Global Exception Handler\n- Rollback active transaction\n- Return 500 JSON payload to client"]
        H2["Email Retry & DLQ Subsystem\n- 3 immediate exponential retries\n- Persist to email_dlq table\n- email_worker.py polls every 60s"]
        H3["Unexpiring LRU Cache Bug\n- 401 Unauthorized returned to admin\n- Requires container restart to recover"]
        H4["CRM Try/Except Block\n- Exception caught and logged\n- Sync silently aborted; no DLQ"]
    end

    F1 --> H1
    F2 --> H2
    F3 --> H3
    F4 --> H4
```

---

## 8. Deployment Architecture & Container Build Pipeline

The application is bundled into a single self-contained Linux container deployed on Azure Container Apps:

```mermaid
flowchart LR
    subgraph BuildPipeline["Vite & Docker Multi-Stage Build"]
        B1["Source Code (Git Repo)"] --> B2["Stage 1: Node.js 20 Build\ncd frontend && npm run build\nEmits /frontend/dist"]
        B2 --> B3["Stage 2: Python 3.11 Runtime\nInstall pip requirements\nCopy dist/ to /app/frontend/dist\nConfigure Nginx & Supervisord"]
        B3 --> B4["Container Image Tagged\nniwi-app:2.1"]
    end

    subgraph AzureRuntime["Azure Container Apps Execution"]
        B4 --> C1["ACA Ingress Controller\n(Managed TLS Termination)"]
        C1 --> C2["Nginx (Port 80)"]
        C2 --> C3["Uvicorn / FastAPI (Port 8000)"]
    end
```

---
*System Workflow and Architecture Documentation certified and verified against source repository.*
