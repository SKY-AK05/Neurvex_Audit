# NIWI — API Dependency Map & End-to-End Sequence Workflows

This document models the interaction flows, service choreography, database dependencies, and external integrations across the NIWI application.

---

## 1. End-to-End Submission Pipeline Flow

The following sequence diagram traces an audit assessment from public respondent entry, through dynamic schema retrieval, validation, pure scoring, short atomic database transaction, and asynchronous background worker processing:

```mermaid
sequenceDiagram
    autonumber
    actor User as Assessment Respondent
    participant Browser as Vue 3 Single Page App
    participant Nginx as Nginx Gateway (:80/443)
    participant FastAPI as FastAPI Router (:8000)
    participant Cache as In-Memory Cache (TTL 300s)
    participant Scoring as Pure Scoring Service
    participant DB as Azure PostgreSQL (Flexible)
    participant Worker as Background Job Worker
    participant ACS as Azure Communication Services
    participant HubSpot as HubSpot CRM (Optional)

    User->>Browser: Opens /audit?org=SKY11
    Browser->>Nginx: GET /api/form/sections
    Nginx->>FastAPI: Proxy /api/form/sections
    FastAPI->>Cache: Check _cached_sections
    alt Cache Hit (Warm)
        Cache-->>FastAPI: Return cached sections JSON (<5ms)
    else Cache Miss (Cold / Expired)
        FastAPI->>DB: Single Joined Query (LEFT JOIN + json_agg)
        DB-->>FastAPI: 8 sections + 40 questions
        FastAPI->>Cache: Populate cache (TTL 300s)
    end
    FastAPI-->>Browser: Sections and Questions JSON
    Browser-->>User: Renders Dynamic Stepper Questionnaire

    User->>Browser: Completes questionnaire & clicks Submit
    Browser->>Browser: Generate UUIDv4 idempotency_key
    Browser->>Nginx: POST /api/submit
    Nginx->>FastAPI: Proxy POST /api/submit

    Note over FastAPI,Scoring: Step 1: Zero-DB In-Memory Scoring
    FastAPI->>Scoring: calculate_scores_pure(payload, sections)
    Scoring-->>FastAPI: 8 pillar scores + overall_avg + overall_level

    Note over FastAPI,DB: Step 2: Atomic DB Transaction (<25ms)
    FastAPI->>DB: Borrow connection from ThreadedConnectionPool
    FastAPI->>DB: Check idempotency_key conflict
    FastAPI->>DB: Check 5-minute email duplicate window
    FastAPI->>DB: Resolve / Auto-create Organisation
    FastAPI->>DB: INSERT INTO submissions (status = 'pending')
    FastAPI->>DB: Enqueue post_submit_jobs (type='email', payload)
    opt CRM Enabled in app_settings
        FastAPI->>DB: Enqueue post_submit_jobs (type='crm', payload)
    end
    FastAPI->>DB: COMMIT & Return connection to pool
    FastAPI-->>Browser: HTTP 201 Created {"success": true, "submission_id": "..."}
    Browser-->>User: Displays Audit Completion & Benchmark Screen

    Note over Worker,ACS: Step 3: Asynchronous Post-Submit Processing
    loop Every 5 Seconds (SKIP LOCKED)
        Worker->>DB: SELECT ... FROM post_submit_jobs FOR UPDATE SKIP LOCKED
        DB-->>Worker: Claim next pending job
        alt Job Type == 'email'
            Worker->>Worker: Render executive HTML report email template
            Worker->>ACS: Dispatch email to respondent
            ACS-->>Worker: HTTP 202 Accepted
            Worker->>DB: UPDATE submissions SET status = 'sent', sent_at = NOW()
            Worker->>DB: UPDATE post_submit_jobs SET status = 'COMPLETED'
        else Job Type == 'crm'
            Worker->>HubSpot: Create / Update CRM Contact & Deal
            HubSpot-->>Worker: HTTP 200 OK
            Worker->>DB: UPDATE post_submit_jobs SET status = 'COMPLETED'
        end
    end
```

---

## 2. Administrative Authentication & Review Workflow

This diagram maps how administrators authenticate using Microsoft Entra ID and perform report generation, score overrides, and email dispatches:

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Orchvate Administrator
    participant Browser as Vue 3 Admin Dashboard
    participant MS as Microsoft Entra ID (OIDC)
    participant FastAPI as FastAPI Router
    participant JWKS as Azure JWKS Discovery Cache
    participant DB as Azure PostgreSQL

    Admin->>Browser: Clicks "Sign in with Microsoft"
    Browser->>FastAPI: GET /api/auth/config
    FastAPI-->>Browser: {"clientId": "...", "tenantId": "..."}
    Browser->>MS: Interactive PKCE Login
    MS-->>Browser: ID Token (RS256 JWT)
    Browser->>FastAPI: POST /api/auth/verify {"email": "admin@orchvate.com"}
    FastAPI->>DB: SELECT role FROM admin_users WHERE email = ...
    DB-->>FastAPI: role: "super"
    FastAPI-->>Browser: {"authorized": true, "role": "super"}
    Browser->>Browser: Store nd_auth_token in sessionStorage

    Admin->>Browser: Navigates to /admin/submissions
    Browser->>FastAPI: GET /api/submissions (Authorization: Bearer <idToken>)
    FastAPI->>JWKS: Fetch / Verify public RSA key matching token kid
    JWKS-->>FastAPI: Key Validated
    FastAPI->>DB: Verify email in admin_users
    DB-->>FastAPI: Admin confirmed
    FastAPI->>DB: SELECT ... FROM submissions ORDER BY submitted_at DESC
    DB-->>FastAPI: List of submissions
    FastAPI-->>Browser: Submissions List JSON
    Browser-->>Admin: Renders Interactive Data Table
```

---

## 3. Client Organisation Portal Workflow (Passwordless Magic Link)

```mermaid
sequenceDiagram
    autonumber
    actor Client as Corporate Client Employee
    participant Browser as Vue 3 Organisation Portal
    participant FastAPI as FastAPI Router
    participant ACS as Azure Communication Services
    participant DB as Azure PostgreSQL

    Client->>Browser: Enters work email at /org/login
    Browser->>FastAPI: POST /api/org/register {"email": "sarah@acme.com"}
    FastAPI->>DB: Find organisation matching domain @acme.com
    DB-->>FastAPI: Found org_id: c7d5efb5-...
    FastAPI->>FastAPI: Generate crypto token & SHA-256 hash
    FastAPI->>DB: INSERT INTO org_magic_links (token_hash, expires_at)
    FastAPI->>ACS: Send email with link /org/verify?token=...
    FastAPI-->>Browser: {"success": true, "message": "Magic link sent"}

    Client->>Browser: Clicks magic link in email
    Browser->>FastAPI: GET /api/org/verify?token=...
    FastAPI->>DB: Verify token_hash, expiration, and used_at IS NULL
    FastAPI->>DB: UPDATE org_magic_links SET used_at = NOW()
    FastAPI->>FastAPI: Mint OrgMemberJWT (role: org_member, org_id)
    FastAPI-->>Browser: {"token": "<org_jwt>", "org_name": "Acme Corp"}

    Browser->>FastAPI: GET /api/org/dashboard (Authorization: Bearer <org_jwt>)
    FastAPI->>DB: SELECT historical submissions WHERE organization_id = ...
    DB-->>FastAPI: Historical score data
    FastAPI-->>Browser: Maturity Dashboard Data JSON
    Browser-->>Client: Renders Historical Trendline & Benchmark Charts
```

---

## 4. Frontend Component to Backend API Mapping Matrix

| Frontend Component / View | Trigger Event | Backend Endpoint | HTTP Method | Service / Persistence Layer |
| :--- | :--- | :--- | :---: | :--- |
| `AuditForm.vue` | Mount | `/api/form/sections` | `GET` | `form_sections` (Cached) |
| `AuditForm.vue` | Pre-submission | `/api/public/organisations/validate` | `POST` | `organizations` table |
| `AuditForm.vue` | Submit Click | `/api/submit` | `POST` | `calculate_scores_pure`, `submissions` |
| `useDraftSaving.js` | Stepper Change | `/api/drafts/save` | `POST` | `draft_submissions` |
| `ResumeDraft.vue` | Mount | `/api/drafts/resume` | `GET` | `draft_submissions` |
| `AdminLogin.vue` | MSAL Redirect | `/api/auth/verify` | `POST` | `admin_users` |
| `Overview.vue` | Mount | `/api/submissions` | `GET` | `submissions` table |
| `Submissions.vue` | Filter Apply | `/api/submissions/filter` | `POST` | `submissions` multi-column SQL |
| `SubmissionDetail.vue` | Score Edit | `/api/submissions/{id}/scores` | `PATCH` | `submissions`, `audit_logs` |
| `SubmissionDetail.vue` | Send Click | `/api/submissions/{id}/send` | `POST` | Azure Communication Services |
| `Organisations.vue` | Mount | `/api/manage/orgs` | `GET` | `organizations` with counts |
| `Organisations.vue` | Campaign Gen | `/api/manage/orgs/{id}/invitations` | `POST` | `organization_invitations` |
| `UserManagement.vue` | Add User | `/api/manage/users` | `POST` | `admin_users` (Super Admin) |
| `Settings.vue` | Save | `/api/settings` | `PUT` | `app_settings` |
| `FormBuilder.vue` | Add Question | `/api/form/sections/{id}/questions` | `POST` | `form_questions`, cache invalidation |

