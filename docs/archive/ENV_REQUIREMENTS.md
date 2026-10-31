# .env File Requirements

## Current Status of Your .env File

| Variable | Status | Priority | Where to Get It |
|----------|--------|----------|-----------------|
| **ENTRA_CLIENT_ID** | ❌ Placeholder | 🔴 CRITICAL | Azure AD App Registration |
| **ENTRA_TENANT_ID** | ❌ Placeholder | 🔴 CRITICAL | Azure AD App Registration |
| **PGHOST** | ❌ Placeholder | 🔴 CRITICAL | Azure PostgreSQL Flexible Server |
| **PGUSER** | ❌ Placeholder | 🔴 CRITICAL | Azure PostgreSQL Admin User |
| **PGPASSWORD** | ❌ Placeholder | 🔴 CRITICAL | Azure PostgreSQL Password |
| **ACS_CONNECTION_STRING** | ❌ Placeholder | 🟡 HIGH | Azure Communication Services |
| **ACS_SENDER_ADDRESS** | ⚠️ Set to orchvate.in | 🟡 HIGH | Azure Communication Services |
| **JWT_SECRET** | ❌ Placeholder | 🟡 HIGH | Generate: `openssl rand -hex 32` |
| CORS_ORIGINS | ✅ Correct | ✅ OK | Already set |
| FRONTEND_URL | ✅ Correct | ✅ OK | Already set |
| DELETE_ALL_PASSWORD | ✅ Set | ✅ OK | Already set |

---

## 🔴 CRITICAL (App won't work without these)

### 1. ENTRA_CLIENT_ID & ENTRA_TENANT_ID

**Why it's critical:** Authentication completely broken without these

**Current value:**
```
ENTRA_CLIENT_ID=your-azure-ad-application-client-id
ENTRA_TENANT_ID=your-azure-ad-tenant-id
```

**How to get:**
1. Azure Portal → Azure Active Directory → App registrations → New registration
2. Name: NIWI Admin Portal
3. Redirect URI: https://niwi.orchvate.in/portal
4. Copy the two IDs and paste them in .env

**Example:**
```bash
ENTRA_CLIENT_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
ENTRA_TENANT_ID=9876fedc-ba09-8765-4321-0fedcba98765
```

---

### 2. PostgreSQL Database Credentials

**Why it's critical:** All data storage depends on this

**Current values:**
```
PGHOST=your-database-host.postgres.database.azure.com
PGUSER=your-database-username
PGPASSWORD=your-database-password
```

**How to get:**
1. Azure Portal → Create Azure Database for PostgreSQL Flexible Server
2. Or use existing PostgreSQL instance
3. Get connection details from Overview page

**Example:**
```bash
PGHOST=niwi-db-server.postgres.database.azure.com
PGPORT=5432
PGDATABASE=nd_audit
PGUSER=niwiadmin
PGPASSWORD=YourSecurePassword123!
```

**After setting up, initialize schema:**
```bash
psql -h niwi-db-server.postgres.database.azure.com -U niwiadmin -d nd_audit -f create_table.sql
```

---

## 🟡 HIGH (Important features won't work without these)

### 3. Azure Communication Services (Email)

**Why it's important:** Audit reports can't be emailed to users

**Current values:**
```
ACS_CONNECTION_STRING=endpoint=https://your-acs-resource.unitedstates.communication.azure.com/;accesskey=your-access-key
ACS_SENDER_ADDRESS=noreply@orchvate.in
```

**How to get:**
1. Azure Portal → Create Communication Services resource
2. Go to Keys → Copy connection string
3. Set up Email service → Get sender address

**Example:**
```bash
ACS_CONNECTION_STRING=endpoint=https://niwi-comms.unitedstates.communication.azure.com/;accesskey=xxxxxxxxxxxxxxxxxxx
ACS_SENDER_ADDRESS=DoNotReply@a1b2c3d4-e5f6-7890.azurecomm.net
ACS_SENDER_NAME=NIWI Audit Team
```

---

### 4. JWT Secret

**Why it's important:** Session security and token signing

**Current value:**
```
JWT_SECRET=your-jwt-secret-signing-key-CHANGE-THIS-TO-SECURE-RANDOM-STRING
```

**How to generate:**
```bash
openssl rand -hex 32
```

**Example:**
```bash
JWT_SECRET=a1b2c3d4e5f67890abcdef1234567890fedcba9876543210abcdef1234567890
```

---

## ✅ Already Configured Correctly

These are already set in your .env:

```bash
# Environment
APP_ENV=production

# URLs and CORS
CORS_ORIGINS=https://niwi.orchvate.in
FRONTEND_URL=https://niwi.orchvate.in

# Admin password for delete-all function
DELETE_ALL_PASSWORD=ORCHVATE@1234

# Database settings
PGPORT=5432
PGDATABASE=nd_audit

# Display name for emails
ACS_SENDER_NAME=NIWI Audit Team
```

---

## 📋 Complete .env Template (Fill in the blanks)

```bash
# ==========================================
# AZURE POSTGRESQL DATABASE
# ==========================================
PGHOST=_________________.postgres.database.azure.com
PGPORT=5432
PGDATABASE=nd_audit
PGUSER=_________________
PGPASSWORD=_________________

# ==========================================
# AZURE COMMUNICATION SERVICES (Email)
# ==========================================
ACS_CONNECTION_STRING=endpoint=https://_________________.communication.azure.com/;accesskey=_________________
ACS_SENDER_ADDRESS=_________________@_________________.azurecomm.net
ACS_SENDER_NAME=NIWI Audit Team

# ==========================================
# APP CONFIGURATION
# ==========================================
APP_ENV=production
JWT_SECRET=_________________ (generate with: openssl rand -hex 32)
CORS_ORIGINS=https://niwi.orchvate.in
FRONTEND_URL=https://niwi.orchvate.in
DELETE_ALL_PASSWORD=ORCHVATE@1234

# ==========================================
# MICROSOFT ENTRA ID (Azure AD)
# ==========================================
ENTRA_CLIENT_ID=_________________
ENTRA_TENANT_ID=_________________
```

---

## 🚀 After Filling All Values

1. **Copy to VM:**
   ```bash
   scp .env user@niwi.orchvate.in:/path/to/niwi/
   ```

2. **Deploy:**
   ```bash
   ssh user@niwi.orchvate.in
   cd /path/to/niwi
   ./deploy.sh
   ```

3. **Add admin users to database:**
   ```bash
   psql -h your-db-host.postgres.database.azure.com -U your_user -d nd_audit
   ```
   ```sql
   INSERT INTO admin_users (email, role) VALUES ('your-email@orchvate.in', 'admin');
   ```

4. **Test:**
   ```bash
   curl http://localhost:8080/api/auth/config
   curl http://localhost:8080/api/health
   ```

5. **Access:** https://niwi.orchvate.in/portal

---

## 🔒 Security Reminders

- ✅ Never commit .env to Git (already in .gitignore)
- ✅ Use strong passwords (12+ characters, mixed case, numbers, symbols)
- ✅ Keep JWT_SECRET random and secret
- ✅ Rotate credentials periodically
- ✅ Restrict database firewall to your VM's IP only
- ✅ Enable SSL/TLS for PostgreSQL connections
