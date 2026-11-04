# API Keys and External Integrations Reference

> **In plain words:**  
> This document lists every third-party service, secret key, and environment variable that the NIWI platform connects to. It explains what each key does, where it is stored, how to configure it safely, and how to fix common connection problems.
>
> **Last updated:** November 5, 2026  
> **Document Status:** Active Canonical Specification  
> **Target Audience:** System Administrators, DevOps Engineers, Security Reviewers  

---

## Table of Contents
1. [In Plain Words: What is an API Key?](#in-plain-words-what-is-an-api-key)
2. [External Integrations Overview](#external-integrations-overview)
3. [AI Provider & OpenAI Evaluation](#ai-provider--openai-evaluation)
4. [Complete Environment Variables & Secrets Reference](#complete-environment-variables--secrets-reference)
5. [Frontend Exposure & Security Boundaries](#frontend-exposure--security-boundaries)
6. [Beginner's Step-by-Step Setup Guide](#beginners-step-by-step-setup-guide)
7. [Security Practices & Secret Hygiene](#security-practices--secret-hygiene)
8. [Troubleshooting Connection & Integration Errors](#troubleshooting-connection--integration-errors)

---

## 1. In Plain Words: What is an API Key?

An **API Key** is like an electronic hotel keycard. When you check into a hotel, the front desk gives you a plastic card encoded with a special digital signature. When you tap the card on your bedroom door, the lock verifies two things:
1. You are an authorized guest allowed to enter this room.
2. The hotel knows exactly which guest used the room so they can bill the right person for room service.

In software, NIWI uses "keycards" (API keys and connection strings) to talk to outside services:
- It taps a key to **Azure PostgreSQL** to store survey answers.
- It taps a key to **Azure Communication Services** to deliver summary emails.
- It taps a key to **Microsoft Entra ID** to let administrators log in securely with their corporate credentials.

*Why it exists:* Without API keys, outside services would not know who is making requests, and the system would either have to be completely open to hackers or unable to send emails and save data.

---

## 2. External Integrations Overview

The following external services are integrated into the NIWI codebase:

| External Service | Purpose / Capability | Calling Code | Configuration Key / Env Variable | Required / Optional |
|---|---|---|---|:---:|
| **Azure Database for PostgreSQL Flexible Server** | Primary relational database for all submissions, scores, organizations, and audit logs. | `app/core/database.py` (lines 12–70) | `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` | **Required** |
| **Azure Communication Services (ACS)** | Transactional email delivery for executive PDF summaries, draft resume magic links, and 5-minute admin digests. | `app/services/settings_service.py` (lines 130–160), `app/api/drafts.py` (lines 40–80) | `ACS_CONNECTION_STRING`, `ACS_SENDER_ADDRESS`, `ACS_SENDER_NAME` | **Required** in Production (graceful fallback in dev) |
| **Microsoft Entra ID (Azure AD)** | Enterprise Single Sign-On (SSO) and OIDC token validation via JWKS for administrative users. | `app/core/security.py` (lines 50–120), `frontend/src/authConfig.js` | `ENTRA_CLIENT_ID`, `ENTRA_TENANT_ID`, `JWKS_URL` | **Required** in Production (`ENABLE_DEV_BYPASS` in dev) |
| **Azure Key Vault** | Hardware security module (HSM) storing all production secrets retrieved via Managed Identity. | `app/core/keyvault.py` (lines 20–85) | `KEY_VAULT_NAME`, `AZURE_CLIENT_ID` (Managed Identity) | **Required** in Production |
| **Azure Service Bus** | Cloud enterprise message bus for distributed background task execution and worker scaling. | `app/core/service_bus.py`, `app/tasks/service_bus_worker.py` | `SERVICE_BUS_CONNECTION_STRING`, `SERVICE_BUS_FQDN`, `SERVICE_BUS_QUEUE_NAME` | Optional (falls back to PostgreSQL polling worker) |
| **HubSpot CRM** | Optional customer relationship management contact synchronization for leads requesting consultation calls. | `app/services/crm_service.py` (lines 10–50) | `HUBSPOT_ACCESS_TOKEN` | **Optional** (defaults to skipped if unconfigured) |
| **OpenAI / LLM Provider** | Planned AI executive commentary generation. | `app/services/ai_service.py` (line 3) | *None configured in current code* | **Optional (Future Stub)** |

---

## 3. AI Provider & OpenAI Evaluation

### Current Status in Repository
> **Needs confirmation:**  
> The current codebase does not make live network calls to OpenAI, Azure OpenAI, or any other third-party LLM provider.
>
> In the source file `app/services/ai_service.py`, the entire implementation consists of:
> ```python
> """
> ai_service.py — AI-assisted features (future use)
> Placeholder for any LLM-based interpretation or recommendation generation.
> """
> ```
> No `OPENAI_API_KEY` is referenced in `app/core/config.py` or `.env.example`.

### How Scoring & Recommendations Work Today
Instead of using an expensive or non-deterministic AI model, NIWI currently uses a **100% deterministic rules-based scoring engine** located in `app/services/scoring_service.py`:
- All 40 questions are scored on Likert scales (1–5) and normalized onto an exact 0–20 point scale per dimension.
- Maturity levels (Foundational, Early Progress, Developing, Proficient, Leading) are evaluated via static threshold brackets.
- Contextual recommendations in reports are populated through deterministic category lookups.

*Why it exists this way:* In compliance and organizational auditing, deterministic algorithms are legally defensible, verifiable by accountants, 100% immune to LLM hallucinations, and execute in under 1 millisecond at $0.00 compute cost.

### Planned OpenAI Integration Architecture (Roadmap)
When activated in a future release, the planned integration will follow these architectural guidelines:
- **Environment Variable:** `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` (or `OPENAI_API_KEY`).
- **Target Model:** `gpt-4o-mini` (fast, economical commentary) or `gpt-4o`.
- **Calling Module:** `app/services/ai_service.py` inside the background task worker (`app/tasks/service_bus_worker.py`), preventing external LLM API latency from blocking public HTTP survey responses.
- **Cost Controls:** Enforcing `max_tokens=600`, `temperature=0.2` (for factual consistency), and monthly spending hard-caps in the Azure / OpenAI billing console.

---

## 4. Complete Environment Variables & Secrets Reference

Every environment variable read anywhere in the NIWI repository is cataloged below:

| Variable Name | Purpose | Example Placeholder | Where It Is Read | Required / Optional |
|---|---|---|---|:---:|
| `APP_ENV` | Environment classification (`development`, `test`, `production`). | `production` | `app/core/config.py:15` | Required |
| `PGHOST` | PostgreSQL server hostname. | `YOUR_POSTGRES_SERVER.postgres.database.azure.com` | `app/core/config.py:58` | Required |
| `PGPORT` | PostgreSQL TCP port. | `5432` | `app/core/config.py:59` | Required (default 5432) |
| `PGDATABASE` | PostgreSQL database name. | `nd_audit` | `app/core/config.py:60` | Required |
| `PGUSER` | PostgreSQL admin username. | `orchvate_admin` | `app/core/config.py:61` | Required |
| `PGPASSWORD` | PostgreSQL database password (minimum 16 chars in prod, 8 chars if Key Vault managed). | `YOUR_SECURE_DB_PASSWORD` | `app/core/config.py:62` | Required |
| `KEY_VAULT_NAME` | Azure Key Vault resource name for production secrets retrieval. | `kv-niwi-prod` | `app/core/keyvault.py:60` | Required in Prod |
| `REQUIRE_KEYVAULT` | Strict flag requiring Azure Key Vault; fails boot if Key Vault is down. | `true` | `app/core/config.py:27` | Optional (default false) |
| `JWT_SECRET` | Cryptographic secret for signing administrative HS256 tokens (min 32 chars). | `YOUR_32_CHAR_CRYPTOGRAPHIC_KEY_HERE!!` | `app/core/config.py:116` | Required |
| `ENTRA_CLIENT_ID` | Application (Client) ID registered in Microsoft Entra ID. | `00000000-0000-0000-0000-000000000000` | `app/core/config.py:153` | Required in Prod |
| `ENTRA_TENANT_ID` | Directory (Tenant) ID for corporate Microsoft 365 organization. | `00000000-0000-0000-0000-000000000000` | `app/core/config.py:154` | Required in Prod |
| `ENABLE_DEV_BYPASS` | Local development override allowing mock admin login without internet or Entra ID. | `false` | `app/core/config.py:160` | Dev Only (disabled in prod) |
| `ACS_CONNECTION_STRING`| Azure Communication Services primary connection string. | `endpoint=https://YOUR_RESOURCE.communication.azure.com/;accesskey=YOUR_SECRET_KEY` | `app/core/config.py:105` | Required in Prod |
| `ACS_SENDER_ADDRESS` | Verified sending email address configured in Azure Email Communication Services. | `donotreply@yourdomain.com` | `app/core/config.py:106` | Required in Prod |
| `ACS_SENDER_NAME` | Sender display name shown in respondent inboxes. | `NIWI Inclusion Team` | `app/core/config.py:107` | Optional (default "NIWI Team") |
| `SUPPORT_EMAIL` | Fallback recipient for customer support requests. | `support@orchvate.in` | `app/api/routes.py:1830` | Optional |
| `DELETE_ALL_PASSWORD` | Secondary verification secret required to execute destructive database reset. | `YOUR_SUPER_ADMIN_WIPE_PASSWORD` | `app/core/config.py:163` | Required for Wipe API |
| `CORS_ORIGINS` | Comma-separated list of allowed browser origins. | `https://niwi.orchvate.in,http://localhost:5173` | `app/core/config.py:161` | Optional (sensible defaults) |
| `FRONTEND_URL` | Canonical public URL used to build draft magic links and audit invites. | `https://niwi.orchvate.in` | `app/core/config.py:162` | Required in Prod |
| `SERVICE_BUS_CONNECTION_STRING` | Connection string for Azure Service Bus namespace. | `Endpoint=sb://YOUR_BUS.servicebus.windows.net/;SharedAccessKeyName=...;SharedAccessKey=...` | `app/core/config.py:177` | Optional |
| `SERVICE_BUS_FQDN` | Fully qualified domain name for Service Bus using Managed Identity. | `niwi-bus.servicebus.windows.net` | `app/core/config.py:174` | Optional |
| `SERVICE_BUS_QUEUE_NAME` | Name of the primary submission ingestion queue. | `niwi-submission-queue` | `app/core/config.py:175` | Optional (default `niwi-submission-queue`) |
| `SERVICE_BUS_ENABLED` | Toggles Service Bus pipeline active or inactive. | `true` | `app/core/config.py:176` | Optional (default true) |
| `HUBSPOT_ACCESS_TOKEN`| Private app access token for syncing leads to HubSpot CRM. | `pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` | `app/services/crm_service.py:15` | Optional |
| `OUTBOX_POLL_INTERVAL`| Polling interval (seconds) for the PostgreSQL outbox dispatcher. | `1.0` | `app/services/outbox_service.py:15` | Optional (default 1.0) |
| `OUTBOX_BATCH_SIZE` | Maximum records claimed per outbox dispatch cycle. | `10` | `app/services/outbox_service.py:16` | Optional (default 10) |

---

## 5. Frontend Exposure & Security Boundaries

### Strict Zero-Leakage Architecture
- **No private keys, database credentials, or Azure connection strings are ever sent to the browser.**
- All sensitive operations (scoring, database transactions, email sending) execute strictly inside the containerized Python backend.
- The frontend client communicates only with relative paths (`/api/*`).

### Permitted Frontend Configuration (`Vite`)
The only variables bundled into the client build are public parameters prefixed with `VITE_`:
```bash
# Permitted: Tells the browser where the public API gateway lives
VITE_API_BASE=/api

# Permitted: Canonical public site domain
VITE_APP_URL=https://niwi.orchvate.in/

# Permitted: Public Entra ID App Registration ID (Public Client ID only; no secrets)
VITE_MSAL_CLIENT_ID=00000000-0000-0000-0000-000000000000
VITE_MSAL_TENANT_ID=00000000-0000-0000-0000-000000000000
```
*Why it exists:* Microsoft MSAL requires the public Client ID to open the corporate login popup. Because Client IDs are public knowledge, Entra ID enforces identity using cryptographic redirects back to the authorized domain.

---

## 6. Beginner's Step-by-Step Setup Guide

Follow this guide to get NIWI running locally with valid configuration:

### Step 1: Clone and Create Environment File
```bash
# 1. Copy the example template into a local .env file
cp .env.example .env
```

### Step 2: Configure Local Development Mode
Open `.env` in your text editor and ensure development mode is active:
```ini
APP_ENV=development
ENABLE_DEV_BYPASS=true
JWT_SECRET=dev-insecure-only-local-testing-secret-key-32chars-min!!
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Step 3: Configure Database Credentials
Point your `.env` to your local PostgreSQL instance or dev cloud database:
```ini
PGHOST=localhost
PGPORT=5432
PGDATABASE=nd_audit
PGUSER=postgres
PGPASSWORD=YOUR_LOCAL_DB_PASSWORD
```

### Step 4: Verify Configuration
Run the automated test suite to confirm all configurations load properly:
```bash
pytest tests/test_super_admin_dashboard.py
```
If the tests pass, your environment is properly configured.

---

## 7. Security Practices & Secret Hygiene

1. **Never Commit `.env`:** The file `.env` is explicitly listed in `.gitignore`. Never use `git add -f .env`.
2. **Key Rotation Protocol:** 
   - Azure Key Vault secrets (`ACS_CONNECTION_STRING`, `PGPASSWORD`) should be rotated every 90 days.
   - When rotating `JWT_SECRET`, all existing administrator sessions will be invalidated, requiring users to log in again.
3. **Use Managed Identities in Production:** On Azure Container Apps or Azure Virtual Machines, configure Managed Identity so the application accesses Azure PostgreSQL and Key Vault without storing static credentials in files on disk.
4. **Emergency Leak Response:**
   - If a connection string or API token is accidentally committed or exposed:
     1. Revoke the key immediately in the Azure Portal / ACS dashboard.
     2. Generate a new key and update Azure Key Vault.
     3. Restart the container fleet (`./deploy.sh`).
     4. Inspect `audit_logs` table for any unauthorized API activity during the exposure window.

---

## 8. Troubleshooting Connection & Integration Errors

| Error Message | Plain Language Cause | Proven Fix |
|---|---|---|
| `FATAL: KEY_VAULT_NAME is not configured in required Key Vault environment.` | `APP_ENV=production` is active, but Azure Key Vault has not been configured. | Either set `KEY_VAULT_NAME=your-keyvault` and configure Managed Identity, or change `APP_ENV=development` in your local `.env`. |
| `FATAL: Missing or insecure JWT_SECRET configuration.` | `JWT_SECRET` is missing or is less than 32 characters long. | Generate a fresh 32-character key using `openssl rand -hex 32` and place it in `.env`. |
| `psycopg2.OperationalError: connection to server ... failed: Connection refused` | Backend cannot reach PostgreSQL at the specified host and port. | 1. Check if PostgreSQL is running.<br>2. Confirm `PGHOST` and `PGPORT` are correct.<br>3. In Azure, verify that the firewall allows the server IP address. |
| `ACS_CONNECTION_STRING not configured` | Email operations were skipped because no ACS key was provided. | In development, this is normal and safe; the system skips email sending without crashing. In production, configure `ACS_CONNECTION_STRING` in Key Vault. |
| `401 Unauthorized / Token Expired` | An administrator session expired or the MSAL token signature could not be verified against JWKS. | Refresh the browser, log out, and log back in through Microsoft Entra ID. |

