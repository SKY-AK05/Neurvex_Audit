// =============================================================================
// NIWI Interactive Architecture Visualizations Dataset
// Drives the Interactive Flow Explorer matching NIWI's exact UI design system
// =============================================================================

export const ARCHITECTURE_NODES = [
  {
    id: "respondent",
    name: "Public Survey Respondent",
    tier: "Tier 1: Client Interfaces",
    layer: "Client",
    category: "client",
    badge: "Public Client",
    icon: "user",
    tech: "Mobile / Desktop Browser",
    protocol: "HTTPS / TLS 1.3",
    status: "Active",
    statusText: "Anonymous • Zero-Tracking",
    desc: "Individual completing the 40-question confidential neuro-inclusion assessment. Submissions receive immediate reflection insights with zero respondent deanonymization risk.",
    inbound: [],
    outbound: ["nginx"],
    files: ["frontend/src/views/AuditForm.vue"],
    flowTags: ["all", "ingestion"]
  },
  {
    id: "orgadmin",
    name: "Organization Admin Portal",
    tier: "Tier 1: Client Interfaces",
    layer: "Client",
    category: "client",
    badge: "Authenticated Portal",
    icon: "building",
    tech: "Vue 3 SPA • Pinia",
    protocol: "HTTPS / TLS 1.3",
    status: "Active",
    statusText: "HR / DEI Leader Access",
    desc: "Administrative portal for enterprise leaders to monitor participation rates, generate unique invitation links, and inspect departmental inclusion radar scores.",
    inbound: [],
    outbound: ["nginx"],
    files: ["frontend/src/views/Overview.vue", "frontend/src/views/OrgAdmin.vue"],
    flowTags: ["all", "auth"]
  },
  {
    id: "superadmin",
    name: "Orchvate Super Admin Command",
    tier: "Tier 1: Client Interfaces",
    layer: "Client",
    category: "client",
    badge: "Restricted Command",
    icon: "shield",
    tech: "Vue 3 SPA • Telemetry",
    protocol: "HTTPS / TLS 1.3",
    status: "Secured",
    statusText: "Master Tenant & Queue Operations",
    desc: "Executive command center overseeing multi-tenant directory, replaying dead-lettered queues, tuning rate limits, and inspecting system architecture specifications.",
    inbound: [],
    outbound: ["nginx"],
    files: ["frontend/src/views/SuperDashboard.vue", "frontend/src/views/SystemDocs.vue"],
    flowTags: ["all", "auth"]
  },
  {
    id: "nginx",
    name: "Nginx Ingress Reverse Proxy",
    tier: "Tier 2: Ingress & Edge Proxy",
    layer: "Edge Proxy",
    category: "edge",
    badge: "Edge Ingress",
    icon: "server",
    tech: "Nginx 1.24+ • Alpine",
    protocol: "Port 80 / 8080 (TLS Termination)",
    status: "Active",
    statusText: "Proxy • Static Cache • Sub-1ms",
    desc: "Terminates inbound TLS traffic, applies security headers (HSTS, CSP, X-Frame-Options), serves static SPA assets directly from /app/dist, and proxies API traffic to Uvicorn.",
    inbound: ["respondent", "orgadmin", "superadmin"],
    outbound: ["vuespa", "fastapi"],
    files: ["frontend/nginx.conf", "Dockerfile"],
    flowTags: ["all", "ingestion", "auth"]
  },
  {
    id: "vuespa",
    name: "Vue 3 Single Page Application",
    tier: "Tier 3: Core Application Runtime",
    layer: "Frontend Runtime",
    category: "runtime",
    badge: "Client Engine",
    icon: "layout",
    tech: "Vue 3.4 • Vite 5 • Pinia",
    protocol: "Static Bundle (/app/dist)",
    status: "Ready",
    statusText: "Client-Side Hydration • Accessible",
    desc: "Fast responsive client interface featuring accessible design (WCAG 2.1 AA), state stores, dynamic Likert scoring widgets, and offline documentation viewer.",
    inbound: ["nginx"],
    outbound: [],
    files: ["frontend/src/App.vue", "frontend/src/router/index.js"],
    flowTags: ["all"]
  },
  {
    id: "fastapi",
    name: "FastAPI REST API Engine",
    tier: "Tier 3: Core Application Runtime",
    layer: "Application Core",
    category: "runtime",
    badge: "REST Controller",
    icon: "cpu",
    tech: "FastAPI • Python 3.11 • Uvicorn",
    protocol: "127.0.0.1:8000 (Internal IPC)",
    status: "Active",
    statusText: "33 REST Endpoints • <25ms SLA",
    desc: "High-performance asynchronous REST backend. Manages Pydantic serialization, SlowAPI IP rate limiting, RS256 JWKS token validation, and transactional outbox persistence.",
    inbound: ["nginx"],
    outbound: ["postgres", "entraid", "keyvault"],
    files: ["app/main.py", "app/api/routes.py"],
    flowTags: ["all", "ingestion", "auth"]
  },
  {
    id: "outboxworker",
    name: "Outbox Dispatcher Daemon",
    tier: "Tier 4: Background Processing Fleet",
    layer: "Background Worker",
    category: "worker",
    badge: "Outbox Daemon",
    icon: "repeat",
    tech: "Async Python Daemon",
    protocol: "5s Polling • SKIP LOCKED",
    status: "Running",
    statusText: "ACID Guaranteed • Zero Loss",
    desc: "Continuously polls service_bus_outbox using PostgreSQL row-level locks (SELECT FOR UPDATE SKIP LOCKED). Guarantees at-least-once delivery to downstream processors.",
    inbound: [],
    outbound: ["postgres", "queueworker"],
    files: ["app/services/outbox_service.py", "supervisord.conf"],
    flowTags: ["all", "scoring"]
  },
  {
    id: "queueworker",
    name: "Background Processor Worker",
    tier: "Tier 4: Background Processing Fleet",
    layer: "Scoring Engine",
    category: "worker",
    badge: "Scoring Worker",
    icon: "activity",
    tech: "Python Worker • Supervisord",
    protocol: "Threaded Queue Consumer",
    status: "Running",
    statusText: "Deterministic Scoring • ACS Dispatch",
    desc: "Calculates mathematical scores across the 8 inclusion dimensions (0–160 total), stores finalized scorecards in submissions, and triggers transactional emails via ACS.",
    inbound: ["outboxworker"],
    outbound: ["postgres", "acs", "hubspot"],
    files: ["app/tasks/service_bus_worker.py", "app/services/scoring_service.py"],
    flowTags: ["all", "scoring", "cloud"]
  },
  {
    id: "postgres",
    name: "Azure PostgreSQL Flexible Server",
    tier: "Tier 5: Persistence & Security",
    layer: "Persistence",
    category: "database",
    badge: "Relational DB",
    icon: "database",
    tech: "PostgreSQL 14+ • Flexible Server",
    protocol: "Port 5432 (Pool 5–25 conns)",
    status: "Connected",
    statusText: "19 Tables • ACID Isolation",
    desc: "Authoritative relational persistence for organizations, users, raw submissions, outbox events, and audit logs. Connection pooling with 15s statement timeout.",
    inbound: ["fastapi", "outboxworker", "queueworker"],
    outbound: [],
    files: ["app/database.py", "migrations/"],
    flowTags: ["all", "ingestion", "scoring"]
  },
  {
    id: "keyvault",
    name: "Azure Key Vault (kv-niwi-prod)",
    tier: "Tier 5: Persistence & Security",
    layer: "Security & Secrets",
    category: "security",
    badge: "Key Vault",
    icon: "key",
    tech: "Azure Key Vault REST API",
    protocol: "Managed Identity (HTTPS)",
    status: "Secured",
    statusText: "System-Assigned Managed Identity",
    desc: "Hardware Security Module (HSM) backed store holding database credentials, JWT secrets, and Azure Communication Services tokens. Zero hard-coded secrets.",
    inbound: ["fastapi"],
    outbound: [],
    files: ["app/services/key_vault_service.py"],
    flowTags: ["all", "auth"]
  },
  {
    id: "entraid",
    name: "Microsoft Entra ID (Azure AD)",
    tier: "Tier 5: Persistence & Security",
    layer: "Identity Provider",
    category: "security",
    badge: "OAuth2 / OIDC",
    icon: "lock",
    tech: "OpenID Connect • RS256 JWKS",
    protocol: "HTTPS JWKS Endpoint (1h cache)",
    status: "Secured",
    statusText: "Enterprise SSO • RBAC Validation",
    desc: "Central corporate identity provider issuing signed JWT tokens. Validated server-side via RS256 public keys fetched from Microsoft's discovery endpoint with 1-hour memory caching.",
    inbound: ["fastapi"],
    outbound: [],
    files: ["app/services/auth_service.py", "app/middleware/jwks_middleware.py"],
    flowTags: ["all", "auth"]
  },
  {
    id: "acs",
    name: "Azure Communication Services",
    tier: "Tier 5: Persistence & Security",
    layer: "Cloud Email",
    category: "integration",
    badge: "Transactional Email",
    icon: "mail",
    tech: "ACS Python SDK",
    protocol: "HTTPS REST API (Port 443)",
    status: "Ready",
    statusText: "donotreply@orchvate.in",
    desc: "Enterprise email delivery service used to dispatch customized HTML audit scorecards, inclusion roadmaps, and administrative notifications.",
    inbound: ["queueworker"],
    outbound: [],
    files: ["app/services/email_service.py"],
    flowTags: ["all", "scoring", "cloud"]
  },
  {
    id: "hubspot",
    name: "HubSpot CRM",
    tier: "Tier 5: Persistence & Security",
    layer: "External CRM",
    category: "integration",
    badge: "CRM Sync",
    icon: "globe",
    tech: "HubSpot REST API v3",
    protocol: "HTTPS Bearer Token",
    status: "Optional",
    statusText: "Lead Ingestion • Asynchronous",
    desc: "Synchronizes prospective organizational audit leads with Orchvate's CRM pipeline to support executive follow-ups and enterprise workshops.",
    inbound: ["queueworker"],
    outbound: [],
    files: ["app/services/hubspot_service.py"],
    flowTags: ["all", "cloud"]
  }
];

export const FLOW_PRESETS = [
  { id: "all", label: "All Architecture Nodes", count: 13, icon: "▦", desc: "Complete end-to-end component topology" },
  { id: "ingestion", label: "⚡ Ingestion Flow (<25ms)", count: 5, icon: "⚡", desc: "Public Survey Respondent → Nginx Proxy → FastAPI Engine → PostgreSQL Outbox" },
  { id: "scoring", label: "🔄 Scoring & Outbox Pipeline", count: 5, icon: "🔄", desc: "Outbox Dispatcher → Background Processor → PostgreSQL Submissions → ACS Email" },
  { id: "auth", label: "🛡️ Entra ID & Secrets Auth", count: 5, icon: "🛡️", desc: "Admin Clients → Nginx Proxy → FastAPI → Microsoft Entra ID → Azure Key Vault" },
  { id: "cloud", label: "☁️ External Cloud Services", count: 4, icon: "☁️", desc: "Background Processor → Azure Communication Services + HubSpot CRM" }
];

export const DIAGRAM_METADATA = [
  {
    id: "1-high-level-system-architecture",
    title: "1. High-Level System Architecture",
    type: "Topology",
    icon: "layers",
    summary: "End-to-end client-to-cloud topology spanning 5 architectural tiers, Docker runtime, and Azure services.",
    keyMetrics: [
      { label: "Target Latency", value: "<25ms HTTP 202" },
      { label: "Connection Pool", value: "5–25 conns" },
      { label: "Outbox Poll", value: "Every 5 sec" },
      { label: "Secret Hygiene", value: "Key Vault HSM" }
    ]
  },
  {
    id: "2-frontend-backend-communication-sequence",
    title: "2. Frontend-Backend Communication",
    type: "Sequence",
    icon: "git-commit",
    summary: "7-step request-response sequence with idempotency keys, rate limiting, and in-memory cache bypass.",
    steps: [
      { num: 1, from: "User / Browser", to: "Vue 3 SPA", action: "Interacts with survey form or admin dashboard", latency: "<1ms" },
      { num: 2, from: "Vue 3 SPA", to: "Axios Client (api.js)", action: "Injects Idempotency-Key & Bearer JWT token", latency: "<1ms" },
      { num: 3, from: "Axios Client", to: "Nginx Proxy", action: "HTTP POST /api/submit (Port 80/8080)", latency: "2–5ms" },
      { num: 4, from: "Nginx Proxy", to: "FastAPI Engine", action: "proxy_pass 127.0.0.1:8000; SlowAPI rate limiter", latency: "1–3ms" },
      { num: 5, from: "FastAPI Engine", to: "PostgreSQL", action: "Atomic write to raw_submissions & service_bus_outbox", latency: "8–12ms" },
      { num: 6, from: "FastAPI Engine", to: "Vue 3 SPA", action: "Returns HTTP 202 Accepted with submission_id", latency: "<25ms SLA" },
      { num: 7, from: "Vue 3 SPA", to: "User / Browser", action: "Renders instant reflection score & submission card", latency: "Immediate" }
    ]
  },
  {
    id: "3-microsoft-entra-id-authentication-flow",
    title: "3. Microsoft Entra ID Authentication",
    type: "Security Flow",
    icon: "lock",
    summary: "Enterprise OAuth2 OIDC sign-in with RS256 JWKS public key validation and 1-hour in-memory cache.",
    steps: [
      { num: 1, from: "Admin User", to: "Browser", action: "Navigates to /admin and clicks Microsoft Entra ID Login" },
      { num: 2, from: "Browser", to: "Entra ID", action: "Redirects to login.microsoftonline.com; user completes MFA" },
      { num: 3, from: "Entra ID", to: "Vue SPA", action: "Returns authorization code and acquires RS256 ID/Access Token" },
      { num: 4, from: "Vue SPA", to: "FastAPI API", action: "Sends request with Authorization: Bearer <token>" },
      { num: 5, from: "FastAPI Middleware", to: "Entra ID JWKS", action: "Validates signature against cached JWKS keys (1h TTL)" },
      { num: 6, from: "FastAPI Engine", to: "Vue SPA", action: "Grants Super Admin / Org Admin scoped access token" }
    ]
  },
  {
    id: "4-database-entity-relationship-diagram-er",
    title: "4. Database ER Diagram",
    type: "Data Model",
    icon: "database",
    summary: "Relational architecture spanning 19 normalized tables across surveys, organizations, outbox, and RBAC.",
    entities: [
      { name: "organizations", role: "Tenant entity representing audited company", pk: "id (UUID)", count: "Multi-tenant" },
      { name: "submissions", role: "Final scored audit records with 8 pillar scores", pk: "id (UUID)", count: "Indexed" },
      { name: "raw_submissions", role: "Immutable ingestion log of raw audit inputs", pk: "id (UUID)", count: "Append-only" },
      { name: "service_bus_outbox", role: "Transactional staging table for background worker", pk: "id (UUID)", count: "Queue" },
      { name: "users", role: "Administrative user accounts with RBAC roles", pk: "id (UUID)", count: "Secured" }
    ]
  },
  {
    id: "5-submission-lifecycle-transactional-outbox",
    title: "5. Submission Lifecycle (Outbox)",
    type: "State Lifecycle",
    icon: "repeat",
    summary: "Sub-25ms synchronous acceptance decoupled from background scoring and report generation.",
    steps: [
      { num: 1, title: "1. Synchronous Ingestion", desc: "POST /api/submit writes raw input to raw_submissions and service_bus_outbox in one ACID transaction.", badge: "HTTP 202" },
      { num: 2, title: "2. Immediate Respondent Response", desc: "Respondent receives confirmation in <25ms with submission_id and instant client-side summary.", badge: "<25ms" },
      { num: 3, title: "3. Outbox Dispatcher Claim", desc: "Daemon polls staged records every 5s using SELECT ... FOR UPDATE SKIP LOCKED to prevent duplicate processing.", badge: "Skip Locked" },
      { num: 4, title: "4. Deterministic Scoring", desc: "Scoring engine computes 8 dimensional scores (0–20) and overall index score (0–160).", badge: "0–160 Scale" },
      { num: 5, title: "5. Scorecard & Notification", desc: "Final scores committed to submissions; outbox marked completed; email dispatched via ACS.", badge: "Completed" }
    ]
  },
  {
    id: "6-background-processing-architecture",
    title: "6. Background Processing Fleet",
    type: "Worker Architecture",
    icon: "cpu",
    summary: "Supervisord-managed daemon processes operating with SKIP LOCKED concurrency and dead-letter queues.",
    steps: [
      { num: 1, title: "Staged Outbox Record", desc: "Message inserted with status='pending', attempts=0, and next_retry_at=NOW()." },
      { num: 2, title: "Lock-Free Polling", desc: "SELECT * FROM service_bus_outbox WHERE status='pending' FOR UPDATE SKIP LOCKED LIMIT 10." },
      { num: 3, title: "Worker Execution", desc: "Worker marks record 'processing' and executes calculation and email tasks." },
      { num: 4, title: "Successful Finalization", desc: "On success, status set to 'completed' and processed_at timestamp is committed." },
      { num: 5, title: "Failure & Dead-Letter Queue", desc: "On error, attempts incremented; after 3 failures, moved to dead_letter for manual Super Admin replay." }
    ]
  },
  {
    id: "7-api-request-lifecycle-middleware-pipeline",
    title: "7. API Request & Middleware Pipeline",
    type: "Pipeline",
    icon: "filter",
    summary: "Incoming HTTP request lifecycle passing through CORS, Rate Limiter, JWKS Auth, and Pydantic validation.",
    steps: [
      { num: 1, title: "Ingress", desc: "Nginx forwards HTTP request to Uvicorn at 127.0.0.1:8000." },
      { num: 2, title: "CORS Middleware", desc: "Verifies origin against allowed CORS_ORIGINS whitelist." },
      { num: 3, title: "Rate Limiter", desc: "SlowAPI checks IP request quota against route thresholds (e.g. 60/min)." },
      { num: 4, title: "JWKS Authenticator", desc: "If route requires auth, validates Bearer JWT token against Entra ID keys." },
      { num: 5, title: "Pydantic Validator", desc: "Parses and validates payload schema against Pydantic BaseModel." },
      { num: 6, title: "Controller & Pool", desc: "Executes business logic using checked-out PostgreSQL connection." },
      { num: 7, title: "Egress Response", desc: "Returns JSON response with Security and Cache-Control headers." }
    ]
  },
  {
    id: "8-azure-cloud-deployment-architecture",
    title: "8. Azure Cloud Deployment Architecture",
    type: "Infrastructure",
    icon: "cloud",
    summary: "Single-container deployment with Supervisord, Azure PostgreSQL Flexible Server, Key Vault, and ACS.",
    entities: [
      { name: "Azure Container Apps / VM", role: "Hosts NIWI single container (Docker with Nginx, Uvicorn, Supervisord)", count: "Container" },
      { name: "Azure PostgreSQL Flexible Server", role: "Managed database with automated backups, SSL/TLS, and read replicas", count: "Flexible 14+" },
      { name: "Azure Key Vault (kv-niwi-prod)", role: "Zero-credential secrets store accessed via System-Assigned Managed Identity", count: "HSM" },
      { name: "Azure Communication Services", role: "Managed transactional email relay for audit scorecards", count: "ACS" }
    ]
  },
  {
    id: "9-error-handling-dead-letter-queue-recovery",
    title: "9. Error Handling & DLQ Recovery",
    type: "Resilience",
    icon: "alert-triangle",
    summary: "Multi-tier failure contracts: client validation, transactional rollback, exponential backoff, and DLQ replay.",
    steps: [
      { num: 1, title: "Transient Error Detection", desc: "Database connection timeouts or ACS API errors caught by worker error boundary." },
      { num: 2, title: "Exponential Backoff", desc: "Retry delay calculated as 2^(attempts) * 5 seconds (5s, 10s, 20s)." },
      { num: 3, title: "Max Retries Reached", desc: "After 3 failed executions, record status transitions to 'dead_letter' with error stack trace." },
      { num: 4, title: "Super Admin Alert", desc: "Queue alert rendered on Super Admin Dashboard with error classification." },
      { num: 5, title: "One-Click DLQ Replay", desc: "Super Admin triggers POST /api/admin/outbox/replay to re-enqueue failed records." }
    ]
  }
];

