# Quick Fix for Authentication Issue

## The Problem
Error: **"Could not load sign-in configuration from the server."**

## The Cause
Missing Azure AD (Microsoft Entra) credentials in `.env` file.

---

## 🔧 Quick Fix (3 Steps)

### Step 1: Create Azure AD App (5 minutes)

1. Go to: https://portal.azure.com
2. Navigate: **Azure Active Directory** → **App registrations** → **New registration**
3. Fill in:
   - Name: `NIWI Admin Portal`
   - Account types: `Single tenant`
   - Redirect URI: `https://niwi.orchvate.in/portal`
4. Click **Register**
5. **COPY THESE TWO VALUES:**
   ```
   Application (client) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   Directory (tenant) ID:   yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
   ```
6. Click **Authentication** → Add redirect URI: `https://niwi.orchvate.in`
7. Enable **ID tokens** → Save

### Step 2: Update .env File

SSH to your VM and edit the .env file:

```bash
ssh your-vm
cd /path/to/niwi
nano .env
```

Update these TWO lines (paste the values from Step 1):
```bash
ENTRA_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
ENTRA_TENANT_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
```

**Also check these are configured:**
```bash
# Database (get from Azure PostgreSQL)
PGHOST=your-db.postgres.database.azure.com
PGUSER=your_username
PGPASSWORD=your_password

# Generate secure JWT secret: openssl rand -hex 32
JWT_SECRET=your-long-random-string-here

# Email service (get from Azure Communication Services)
ACS_CONNECTION_STRING=endpoint=https://...
ACS_SENDER_ADDRESS=noreply@orchvate.in
```

Save and exit: `Ctrl+X` → `Y` → `Enter`

### Step 3: Redeploy

```bash
./deploy.sh
```

**Verify it worked:**
```bash
curl http://localhost:8080/api/auth/config
```

Should return:
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
}
```

NOT:
```json
{
  "clientId": null,
  "tenantId": null
}
```

---

## ✅ Test Login

1. Go to: `https://niwi.orchvate.in/portal`
2. Click **"Sign in with Microsoft"**
3. Should redirect to Microsoft login ✅

---

## ⚠️ If Login Still Fails

Add your email to the database:

```bash
psql -h your-db.postgres.database.azure.com -U your_username -d nd_audit
```

```sql
INSERT INTO admin_users (email, role) VALUES ('your-email@orchvate.in', 'admin');
SELECT * FROM admin_users;
\q
```

---

## 📚 Need More Details?

- Full guide: `DEPLOYMENT_CHECKLIST.md`
- Azure AD setup: `AZURE_AD_SETUP.md`
- Diagnostics: Run `./check-auth-config.sh` on VM
