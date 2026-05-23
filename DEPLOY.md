# 🚀 Orchvate Audit — Azure Container Apps Deployment Guide

> **App Name Suggestion:** `orchvate-audit`
> Lowercase, hyphenated — perfect for Azure resource naming rules.

---

## Architecture Overview

```
Internet
   │
   ▼
┌─────────────────────────────────────────────────┐
│  Azure Container Apps Environment                │
│                                                 │
│  ┌───────────────────┐  /api/*  ┌────────────┐  │
│  │   frontend (nginx) │ ──────► │  backend   │  │
│  │   Vue 3 SPA        │         │  (Python   │  │
│  │   Port 80          │         │  Az Funcs) │  │
│  └───────────────────┘         └─────┬──────┘  │
│                                      │          │
└──────────────────────────────────────│──────────┘
                                       │
                                       ▼
                          Azure PostgreSQL Flexible Server
                          (Already exists: generative-ai.postgres...)
```

---

## Pre-requisites

Install these tools on your machine if you don't have them:

```bash
# 1. Docker Desktop
https://www.docker.com/products/docker-desktop

# 2. Azure CLI
https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# 3. Login to Azure
az login
```

---

## Step 1 — Create Azure Container Registry (ACR)

This is like a private Docker Hub but on Azure. You push your images here.

```bash
# Create a resource group (if you don't have one)
az group create --name orchvate-rg --location eastus

# Create the container registry
az acr create \
  --resource-group orchvate-rg \
  --name orchvateregistry \
  --sku Basic \
  --admin-enabled true

# Login to the registry
az acr login --name orchvateregistry
```

---

## Step 2 — Build & Push Docker Images

Run these from the root of your project folder.

### Backend (Python API)
```bash
# Build
docker build -t orchvateregistry.azurecr.io/orchvate-audit-api:latest .

# Push
docker push orchvateregistry.azurecr.io/orchvate-audit-api:latest
```

### Frontend (Vue + nginx)
```bash
# Build
docker build -t orchvateregistry.azurecr.io/orchvate-audit-ui:latest ./frontend

# Push
docker push orchvateregistry.azurecr.io/orchvate-audit-ui:latest
```

---

## Step 3 — Create Azure Container Apps Environment

```bash
# Install the extension first
az extension add --name containerapp --upgrade

# Create the environment
az containerapp env create \
  --name orchvate-audit-env \
  --resource-group orchvate-rg \
  --location eastus
```

---

## Step 4 — Deploy the Backend Container

```bash
az containerapp create \
  --name orchvate-audit-api \
  --resource-group orchvate-rg \
  --environment orchvate-audit-env \
  --image orchvateregistry.azurecr.io/orchvate-audit-api:latest \
  --registry-server orchvateregistry.azurecr.io \
  --target-port 80 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars \
    PGHOST=generative-ai.postgres.database.azure.com \
    PGDATABASE=nd_audit \
    PGUSER=orchvate_admin \
    PGPASSWORD=secretref:pgpassword \
    PGPORT=5432 \
    ACS_CONNECTION_STRING=secretref:acsconnstring \
    ACS_SENDER_ADDRESS=founders@orchvate.in \
    "ACS_SENDER_NAME=Geethanjali & Panchali" \
    FUNCTIONS_WORKER_RUNTIME=python \
    AzureWebJobsStorage=UseDevelopmentStorage=true
```

> **⚠️ Note:** `--ingress internal` means the backend is NOT public — only the frontend can call it. This is secure.

---

## Step 5 — Deploy the Frontend Container

```bash
az containerapp create \
  --name orchvate-audit-ui \
  --resource-group orchvate-rg \
  --environment orchvate-audit-env \
  --image orchvateregistry.azurecr.io/orchvate-audit-ui:latest \
  --registry-server orchvateregistry.azurecr.io \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3
```

> **Note:** `--ingress external` means the frontend IS publicly accessible via a URL like `https://orchvate-audit-ui.azurecontainerapps.io`

---

## Step 6 — Get your live URL

```bash
az containerapp show \
  --name orchvate-audit-ui \
  --resource-group orchvate-rg \
  --query "properties.configuration.ingress.fqdn" \
  --output tsv
```

Your app will be live at that URL! 🎉

---

## Step 7 — Test Locally with Docker Compose

Before pushing to Azure, always test locally first:

```bash
# From the project root
docker compose up --build

# Frontend:  http://localhost:3000
# Backend:   http://localhost:7071/api/...
```

---

## Re-deploying After Code Changes

Every time you make code changes, just repeat Step 2 and then update the container app:

```bash
# Rebuild and push
docker build -t orchvateregistry.azurecr.io/orchvate-audit-api:latest .
docker push orchvateregistry.azurecr.io/orchvate-audit-api:latest

# Tell Azure to pull the new image
az containerapp update \
  --name orchvate-audit-api \
  --resource-group orchvate-rg \
  --image orchvateregistry.azurecr.io/orchvate-audit-api:latest
```

---

## Estimated Monthly Cost

| Service | Tier | Est. Cost |
|---|---|---|
| Azure Container Apps (API) | Consumption | ~$5–15/mo |
| Azure Container Apps (UI) | Consumption | ~$3–8/mo |
| Azure Container Registry | Basic | ~$5/mo |
| Azure PostgreSQL | Already exists | $0 extra |
| **Total** | | **~$13–28/mo** |

> Scales to zero when nobody is using it — you only pay for actual usage!

---

## App Name Ideas 🎨

| Name | Why it works |
|---|---|
| **`orchvate-audit`** | Clean, matches your brand, Azure-safe |
| **`nd-audit-portal`** | Descriptive, professional |
| **`inclusion-lens`** | Creative, memorable |
| **`ndbridge`** | Short, snappy |

**Recommended:** `orchvate-audit` — it ties directly to your brand.
