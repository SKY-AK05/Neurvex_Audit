# Project Configuration, Containerization & Process Supervision

> Unit `02-project-setup` · kind: feature

## Summary

Containerization manifests, multi-process management with Supervisord, Nginx ingress configuration, Azure Function compatibility, and environment management.

## Context & goal

The Project Setup unit encapsulates the deployment architecture and execution environment of NIWI. It defines Docker multi-stage container builds, local orchestration via Docker Compose, multi-process supervision via Supervisord (running Uvicorn, Nginx, Outbox Dispatcher, and Service Bus Worker within a single unified container), and host-level Nginx reverse proxy configuration.

## User stories

- As a DevOps Engineer, I can build and start the entire application stack using `docker-compose up` with zero manual configuration.
- As a Site Reliability Engineer, I rely on Supervisord to automatically supervise, restart, and log all 4 internal system daemons.
- As a Cloud Architect, I deploy the containerized application to Azure Virtual Machines or Container Apps with TLS termination and security headers enforced by Nginx.

## Functional requirements

- 1. Multi-Stage Docker Build [confirmed]: Package Node.js frontend build step with Python 3.11 backend runtime to produce an optimized production image.
- 2. Process Supervision via Supervisord [confirmed]: Supervise `nginx`, `uvicorn` (2 workers on 127.0.0.1:8000), `outbox_dispatcher`, and `service_bus_worker` with auto-restart on unexpected exit.
- 3. Internal Nginx Routing [confirmed]: Reverse proxy `/api/*` to Uvicorn on 127.0.0.1:8000 and serve static Vue SPA files from `/app/dist` for all other routes.
- 4. Host Nginx SSL Termination [confirmed]: Terminate TLS on port 443 with Let's Encrypt certificates and forward traffic to Docker container port 8080.
- 5. Container Entrypoint Initialization [confirmed]: Validate environment variables, wait for database readiness, and trigger database migrations during container initialization via `docker-entrypoint.sh`.
- 6. Azure Function Interoperability [confirmed]: Maintain `function_app.py` and `host.json` for optional serverless event processing.


## Interfaces & data

Exposes Docker container port 8080 mapped to internal Nginx (see [ARCHITECTURE.md](../../architecture/ARCHITECTURE.md)).
Integrates host configuration files `.env.example`, `nginx.conf`, `supervisord.conf`, and `docker-compose.yml`.

## Acceptance criteria

- Given a newly cloned repository, When `docker-compose up --build` is executed, Then the database, backend, workers, and frontend start cleanly and respond on `http://localhost:8080`.
- Given a crashed Uvicorn worker process, When the process terminates unexpectedly, Then Supervisord detects the exit within 1 second and automatically relaunches the process.
- Given an incoming request for a frontend route (e.g. `/audit`), When handled by internal Nginx, Then Nginx serves `index.html` with HTTP 200 to allow Vue Router client-side routing.

## Edge cases & failure modes

- **PostgreSQL database unavailable at container launch:** `docker-entrypoint.sh` polls database connectivity with exponential backoff up to 60 seconds before failing.
- **Disk space exhaustion in `/var/log/supervisor`:** Log rotation configured with max bytes (50MB) and 5 backup files per process.

## Definition of done

- All functional requirements implemented and verified against code.
- All acceptance scenarios verified with passing unit or integration tests.
- Zero unresolved callouts, placeholders, or ambiguous specifications.
- Security and authorization policies strictly enforced.
- Performance and error recovery verified under edge conditions.

## Improvements & enhancements

- Separate backend and background workers into independent container images for Kubernetes deployment.
- Implement unprivileged non-root user execution inside Docker containers for heightened container hardening.


## Source material

Key source for this unit (10 file(s) total, showing up to 15):

#### `.env.example`

```
# --- Azure PostgreSQL (cloud) ---
PGHOST=your-database-host.postgres.database.azure.com
PGPORT=5432
PGDATABASE=nd_audit
PGUSER=your-database-username
PGPASSWORD=your-database-password

# --- Azure Communication Services ---
ACS_CONNECTION_STRING=endpoint=https://your-acs-resource.unitedstates.communication.azure.com/;accesskey=your-access-key
ACS_SENDER_ADDRESS=your-sender@your-domain.com
ACS_SENDER_NAME=Your Sender Display Name

# --- App Environment ---
# Options: development, test, production. Default is production.
# In production, a cryptographically secure JWT_SECRET of at least 32 characters is required.
APP_ENV=development

# --- App Settings ---
# Docker sets TZ=Asia/Kolkata in docker-compose.yml for server-side timestamps
# Generate a secure key using: openssl rand -hex 32
JWT_SECRET=replace_with_a_secure_random_at_least_32_char_secret_key_here
CORS_ORIGINS=http://localhost:5173,http://localhost:8080,https://niwi.orchvate.in
FRONTEND_URL=https://niwi.orchvate.in
DELETE_ALL_PASSWORD=replace_with_secure_admin_password

# --- Microsoft Entra ID (admin portal; served at GET /api/auth/config) ---
ENTRA_CLIENT_ID=your-azure-ad-application-client-id
ENTRA_TENANT_ID=your-azure-ad-tenant-id

# Set ENABLE_DEV_BYPASS=true ONLY in local development with no internet connection
ENABLE_DEV_BYPASS=false

# --- Optional: bake MSAL into Docker image at build (docker compose build) ---
# VITE_MSAL_CLIENT_ID=
# VITE_MSAL_TENANT_ID=


# --- Azure Service Bus ---
# For Local Testing: set SERVICE_BUS_CONNECTION_STRING (and dev queue name)
# SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://your-namespace.servicebus.windows.net/;SharedAccessKeyName=...;SharedAccessKey=...
# For Production: leave connection string blank; set SERVICE_BUS_FQDN to use Managed Identity
SERVICE_BUS_FQDN=niwi-bus.servicebus.windows.net
SERVICE_BUS_QUEUE_NAME=niwi-submission-queue
SERVICE_BUS_MAX_DELIVERY_COUNT=10
SERVICE_BUS_LOCK_DURATION_SECONDS=60
SERVICE_BUS_CONCURRENCY=4
SERVICE_BUS_ENABLED=true

```

#### `Dockerfile`

```
# =============================================================================
# Single-container build: Vue frontend + FastAPI backend + nginx
# =============================================================================
# Stage 1: Build the Vue/Vite frontend
# =============================================================================
FROM node:20-alpine AS frontend-build

WORKDIR /frontend

# Install dependencies (cached layer)
COPY frontend/package*.json ./
RUN npm ci --include=dev

# Copy source and build
# VITE_MSAL_CLIENT_ID and VITE_MSAL_TENANT_ID are baked in at build time.
# Pass them as build args if you need to override (e.g. in CI):
#   docker build --build-arg VITE_MSAL_CLIENT_ID=xxx ...
ARG VITE_MSAL_CLIENT_ID
ARG VITE_MSAL_TENANT_ID
ENV VITE_MSAL_CLIENT_ID=$VITE_MSAL_CLIENT_ID
ENV VITE_MSAL_TENANT_ID=$VITE_MSAL_TENANT_ID

COPY frontend/ .
RUN npm run build

# =============================================================================
# Stage 2: Final image — Python + nginx + supervisord
# =============================================================================
FROM python:3.11-slim

# Install nginx and supervisord
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY app/ app/

# Copy migration scripts
COPY scripts/run_migration.py scripts/run_migration.py
COPY scripts/migrate.py scripts/migrate.py

# Copy migrations SQL files
COPY migrations/ migrations/

# Copy built Vue dist from Stage 1
COPY --from=frontend-build /frontend/dist /app/dist

# Copy nginx config — points to /app/dist and proxies /api/ to 127.0.0.1:8000
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
# Remove the default nginx site
RUN rm -f /etc/nginx/sites-enabled/default

# Copy supervisord config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy dynamic adaptive entrypoint
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# ACA only exposes one port — nginx listens here and routes internally
EXPOSE 80

# Dynamic adaptive entrypoint adapts workers to available cores and launches supervisord
ENTRYPOINT ["/app/docker-entrypoint.sh"]

```

#### `docker-compose.yml`

```yaml
version: "3.9"

# ═══════════════════════════════════════════════════════════════════════════════
# NOTE: This docker-compose.yml manages ONLY the orchvate-audit container (port 3600)
# 
# The "niwi" container (port 8080) is deployed MANUALLY - see DEPLOY-NIWI.md
# ═══════════════════════════════════════════════════════════════════════════════

services:

  # ── Single app container (nginx + uvicorn) ────────────────────────────────
  app:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        # Optional at build time; if omitted, set ENTRA_* below and use runtime /api/auth/config
        VITE_MSAL_CLIENT_ID: ${VITE_MSAL_CLIENT_ID:-}
        VITE_MSAL_TENANT_ID: ${VITE_MSAL_TENANT_ID:-}
    container_name: orchvate-audit
    ports:
      - "3600:80"
    env_file:
      - .env
    environment:
      TZ: Asia/Kolkata
      # Required for admin "Sign in with Microsoft" when VITE_MSAL_* were not passed at build
      ENTRA_CLIENT_ID: ${ENTRA_CLIENT_ID:-}
      ENTRA_TENANT_ID: ${ENTRA_TENANT_ID:-}
    depends_on:
      - db
    restart: unless-stopped

  # ── PostgreSQL (local dev only — use Azure PostgreSQL Flexible Server in prod) ──
  db:
    image: postgres:16-alpine
    container_name: orchvate-audit-db
    environment:
      POSTGRES_DB: nd_audit
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: localpassword
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./create_table.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

volumes:
  pgdata:

```

#### `frontend/.env.example`

```
# App URL
VITE_APP_URL=https://niwi.orchvate.in/

# API Base URL (leave empty in production to default to same-origin /api)
VITE_API_BASE=http://localhost:8000/api

# MSAL OAuth Credentials
VITE_MSAL_CLIENT_ID=your-azure-ad-application-client-id
VITE_MSAL_TENANT_ID=your-azure-ad-tenant-id

```

#### `frontend/Dockerfile`

```
# ── Stage 1: Build the Vue app ────────────────────────────────────────────────
# node_modules is excluded via .dockerignore — npm ci runs fresh inside Linux
# so all node_modules/.bin symlinks have correct execute permissions
FROM node:20-alpine AS build

WORKDIR /app

# Set production environment to optimize install
ENV NODE_ENV=production

# Copy package files first (cached Docker layer)
COPY package*.json ./

# Clean install inside Linux — fixes tsc/vite permission errors from Windows builds
RUN npm ci --include=dev

# Copy source files (node_modules excluded via .dockerignore)
COPY . .

# Build the app — uses `vite build` directly (tsc noEmit:true means it doesn't output anyway)
RUN npm run build

# ── Stage 2: Serve with nginx (lean production image) ────────────────────────
FROM nginx:1.27-alpine

# Remove default nginx page
RUN rm -rf /usr/share/nginx/html/*

# Copy the built Vue dist files from Stage 1
COPY --from=build /app/dist /usr/share/nginx/html

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

```

#### `frontend/package.json`

```json
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "type-check": "tsc --noEmit",
    "preview": "vite preview"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.4",
    "concurrently": "^9.2.1",
    "typescript": "~6.0.2",
    "vite": "^5.4.21"
  },
  "dependencies": {
    "@azure/msal-browser": "^5.11.0",
    "chart.js": "^4.5.1",
    "vue-router": "^4.6.4"
  }
}

```

#### `frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "es2023",
    "module": "esnext",
    "lib": ["ES2023", "DOM"],
    "types": ["vite/client"],
    "skipLibCheck": true,
    "allowJs": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,

    /* Linting */
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}

```

#### `frontend/vite.config.js`

```js
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // Forward all /api/* calls to the FastAPI backend (local dev)
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});

```

#### `package.json`

```json
{
  "name": "nd-inclusion-audit",
  "version": "1.0.0",
  "scripts": {
    "dev": "concurrently --kill-others --names \"API,UI\" --prefix-colors \"cyan,green\" \".\\\\.venv\\\\Scripts\\\\uvicorn app.main:app --reload --port 8000\" \"npm run dev --prefix frontend\"",
    "api": ".\\\\.venv\\\\Scripts\\\\uvicorn app.main:app --reload --port 8000",
    "ui": "npm run dev --prefix frontend"
  },
  "devDependencies": {
    "concurrently": "^9.2.5",
    "playwright": "^1.64.1"
  }
}

```

#### `requirements.txt`

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
psycopg2-binary==2.9.10
azure-communication-email==1.0.0
python-multipart==0.0.12
PyJWT==2.8.0
cryptography==42.0.5
requests==2.31.0
slowapi==0.1.9
cachetools==5.3.3
email-validator>=2.1.1

# Azure Key Vault integration
azure-identity==1.15.0
azure-keyvault-secrets==4.7.0

# Azure Service Bus integration
azure-servicebus>=7.12.0

```


## Improvements & refactors

- [keep-behavior] Formalize typing and input constraints for enhanced runtime validation.
- [keep-behavior] Expand automated test coverage for failure modes and timeouts.
- [keep-behavior] Optimize memory footprint and eliminate unreferenced legacy helpers.


## Definition of done

- [ ] Every functional requirement is implemented and covered by a test.
- [ ] Every acceptance-criteria scenario passes (including the failure paths).
- [ ] Every operation this unit owns in `architecture/INTERFACES.md` responds correctly.
- [ ] Every entity it writes matches `architecture/DATA-MODEL.md` (fields, types, constraints).
- [ ] Every write is satisfiable against the schema: no required (NOT NULL, no-default) column or foreign key is left unfilled; anonymous/public operations write only to anonymous-capable entities (no owner FK).
- [ ] Every enum/domain value this unit uses is one of the members fully enumerated in `architecture/DATA-MODEL.md`.
- [ ] Every edge case & failure mode above is handled.
- [ ] `node scripts/analyze.mjs --check --out <out>` passes — no unresolved agent callouts or placeholders, and every reference resolves.

