# Orchvate Audit — Single Container ACA Deployment Guide

## Architecture

```
Internet
   │
   ▼
Azure Container Apps (single container, port 80)
   │
   ├── nginx (port 80)
   │     ├── /          → serves Vue SPA from /app/dist
   │     └── /api/*     → proxy_pass to 127.0.0.1:8000
   │
   └── uvicorn (127.0.0.1:8000, internal only)
         └── FastAPI app
               ├── Azure PostgreSQL Flexible Server
               └── Azure Communication Services
```

supervisord manages both nginx and uvicorn inside the container.
MSAL auth runs entirely in the browser — no backend involvement.

---

## Environment Variables

### Backend (set as ACA secrets/env vars — never in the image)
| Variable | Description |
|---|---|
| `PGHOST` | Azure PostgreSQL hostname |
| `PGDATABASE` | Database name |
| `PGUSER` | DB username |
| `PGPASSWORD` | DB password (use ACA secret) |
| `PGPORT` | DB port (default 5432) |
| `ACS_CONNECTION_STRING` | ACS connection string (use ACA secret) |
| `ACS_SENDER_ADDRESS` | Sender email address |
| `ACS_SENDER_NAME` | Sender display name |

### Frontend (baked into the image at build time via Docker build args)
| Variable | Description |
|---|---|
| `VITE_MSAL_CLIENT_ID` | Azure AD app client ID |
| `VITE_MSAL_TENANT_ID` | Azure AD tenant ID |

These are public values (they appear in the browser bundle) — safe to pass as build args.

---

## Local Development

```bash
# Test the full single-container build locally
docker compose up --build

# App available at: http://localhost:8080
# PostgreSQL at: localhost:5432
```

For hot-reload frontend dev, run Vite separately:
```bash
cd frontend
npm run dev   # http://localhost:5173
```
And run the backend separately:
```bash
uvicorn app.main:app --reload --port 8000
```
Set `VITE_API_BASE=http://localhost:8000/api` in `frontend/.env` for local dev.

---

## One-Time Azure Setup

```bash
# Login
az login

# Create resource group (if needed)
az group create --name orchvate-rg --location eastus

# Create container registry
az acr create --resource-group orchvate-rg --name orchvateregistry --sku Basic --admin-enabled true
az acr login --name orchvateregistry

# Create ACA environment
az extension add --name containerapp --upgrade
az containerapp env create --name orchvate-audit-env --resource-group orchvate-rg --location eastus
```

---

## Build & Deploy

```bash
# Build with MSAL vars baked in (these are public — safe in build args)
docker build \
  --build-arg VITE_MSAL_CLIENT_ID=2f900af5-c166-4fdb-90f1-1eaee09eeff2 \
  --build-arg VITE_MSAL_TENANT_ID=ea77fe37-fd2c-4294-87c3-8746bce6625a \
  -t orchvateregistry.azurecr.io/orchvate-audit:latest .

docker push orchvateregistry.azurecr.io/orchvate-audit:latest
```

### First deploy
```bash
az containerapp create \
  --name orchvate-audit \
  --resource-group orchvate-rg \
  --environment orchvate-audit-env \
  --image orchvateregistry.azurecr.io/orchvate-audit:latest \
  --registry-server orchvateregistry.azurecr.io \
  --target-port 80 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 5 \
  --secrets \
    pgpassword="Coffee!92" \
    acsconnstring="endpoint=https://orchvatecommunicationservice..." \
  --env-vars \
    PGHOST=generative-ai.postgres.database.azure.com \
    PGDATABASE=nd_audit \
    PGUSER=orchvate_admin \
    PGPASSWORD=secretref:pgpassword \
    PGPORT=5432 \
    ACS_CONNECTION_STRING=secretref:acsconnstring \
    ACS_SENDER_ADDRESS=founders@orchvate.in \
    "ACS_SENDER_NAME=Geethanjali & Panchali"
```

`--min-replicas 0` enables scale-to-zero — the app costs nothing when idle.

### Subsequent deploys (after code changes)
```bash
docker build \
  --build-arg VITE_MSAL_CLIENT_ID=2f900af5-c166-4fdb-90f1-1eaee09eeff2 \
  --build-arg VITE_MSAL_TENANT_ID=ea77fe37-fd2c-4294-87c3-8746bce6625a \
  -t orchvateregistry.azurecr.io/orchvate-audit:latest .

docker push orchvateregistry.azurecr.io/orchvate-audit:latest

az containerapp update \
  --name orchvate-audit \
  --resource-group orchvate-rg \
  --image orchvateregistry.azurecr.io/orchvate-audit:latest
```

---

## GitHub Actions Auto-Deploy (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to ACA

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Azure login
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: ACR login
        run: az acr login --name orchvateregistry

      - name: Build and push
        run: |
          docker build \
            --build-arg VITE_MSAL_CLIENT_ID=${{ secrets.VITE_MSAL_CLIENT_ID }} \
            --build-arg VITE_MSAL_TENANT_ID=${{ secrets.VITE_MSAL_TENANT_ID }} \
            -t orchvateregistry.azurecr.io/orchvate-audit:${{ github.sha }} \
            -t orchvateregistry.azurecr.io/orchvate-audit:latest .
          docker push orchvateregistry.azurecr.io/orchvate-audit:${{ github.sha }}
          docker push orchvateregistry.azurecr.io/orchvate-audit:latest

      - name: Deploy to ACA
        run: |
          az containerapp update \
            --name orchvate-audit \
            --resource-group orchvate-rg \
            --image orchvateregistry.azurecr.io/orchvate-audit:${{ github.sha }}
```

GitHub secrets to set: `AZURE_CREDENTIALS`, `VITE_MSAL_CLIENT_ID`, `VITE_MSAL_TENANT_ID`

---

## Estimated Monthly Cost (scale-to-zero)

| Service | Tier | Est. Cost |
|---|---|---|
| Azure Container Apps | Consumption (scale-to-zero) | ~$3–10/mo |
| Azure Container Registry | Basic | ~$5/mo |
| Azure PostgreSQL | Already exists | $0 extra |
| **Total** | | **~$8–15/mo** |

Half the cost of the previous two-container setup.
