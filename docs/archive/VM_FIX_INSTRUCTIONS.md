# VM Fix Instructions for niwi.orchvate.in

## 🔍 Problem Identified

Your VM `.env` file has the **wrong domain**:

```bash
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://neuromark.orchvate.in
FRONTEND_URL=https://neuromark.orchvate.in
```

But your deployment is at: **niwi.orchvate.in**

This causes:
- Authentication redirects to fail
- CORS errors when frontend tries to access API
- "Could not load sign-in configuration from the server" error

---

## ✅ Your VM Already Has (Good!)

- ✅ Azure PostgreSQL credentials
- ✅ Azure Communication Services credentials
- ✅ Azure AD (ENTRA) credentials
- ✅ Database and email services configured

---

## 🔧 What Needs to Be Fixed

### 1. Update CORS_ORIGINS and FRONTEND_URL

**Current (WRONG):**
```bash
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://neuromark.orchvate.in
FRONTEND_URL=https://neuromark.orchvate.in
```

**Should be:**
```bash
CORS_ORIGINS=https://niwi.orchvate.in
FRONTEND_URL=https://niwi.orchvate.in
```

### 2. Update JWT_SECRET (Security)

**Current:**
```bash
JWT_SECRET=default_jwt_secret_key_change_me
```

**Should be:** A secure random string

---

## 🚀 Quick Fix (Choose One Method)

### Method A: Automated Script (Recommended)

1. **Copy fix script to VM:**
   ```bash
   scp fix-vm-env.sh your-user@niwi.orchvate.in:/path/to/niwi/
   ```

2. **SSH to VM and run:**
   ```bash
   ssh your-user@niwi.orchvate.in
   cd /path/to/niwi
   chmod +x fix-vm-env.sh
   ./fix-vm-env.sh
   ```

### Method B: Manual Fix

1. **SSH to VM:**
   ```bash
   ssh your-user@niwi.orchvate.in
   cd /path/to/niwi
   ```

2. **Backup current .env:**
   ```bash
   cp .env .env.backup
   ```

3. **Edit .env:**
   ```bash
   nano .env
   ```

4. **Change these lines:**
   ```bash
   # CHANGE FROM:
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://neuromark.orchvate.in
   FRONTEND_URL=https://neuromark.orchvate.in
   
   # TO:
   CORS_ORIGINS=https://niwi.orchvate.in
   FRONTEND_URL=https://niwi.orchvate.in
   ```

5. **Optionally, generate and update JWT_SECRET:**
   ```bash
   openssl rand -hex 32
   # Copy the output and replace JWT_SECRET value
   ```

6. **Save and exit:** `Ctrl+X` → `Y` → `Enter`

7. **Redeploy:**
   ```bash
   ./deploy.sh
   ```

---

## 🔍 Verify Azure AD Redirect URIs

Make sure your Azure AD app registration has the correct redirect URIs:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to: **Azure Active Directory** → **App registrations**
3. Find your app (Client ID: `2f900af5-c166-4fdb-90f1-1eaee09eeff2`)
4. Go to **Authentication**
5. Ensure these redirect URIs are listed:
   - ✅ `https://niwi.orchvate.in`
   - ✅ `https://niwi.orchvate.in/portal`
   - ❌ Remove: `https://neuromark.orchvate.in` (if present)

---

## ✅ After Deployment - Test

### 1. Test Auth Config Endpoint

```bash
curl http://localhost:8080/api/auth/config
```

**Expected response:**
```json
{
  "clientId": "2f900af5-c166-4fdb-90f1-1eaee09eeff2",
  "tenantId": "ea77fe37-fd2c-4294-87c3-8746bce6625a"
}
```

**NOT:**
```json
{
  "clientId": null,
  "tenantId": null
}
```

### 2. Test Health Endpoint

```bash
curl http://localhost:8080/api/health
```

Should return database connection status.

### 3. Test Frontend

1. Open: `https://niwi.orchvate.in/portal`
2. Should see login page (not error message)
3. Click **"Sign in with Microsoft"**
4. Should redirect to Microsoft login page
5. After login, should redirect back to dashboard

---

## 🔐 Add Admin Users

If login verification fails, ensure your email is in the database:

```bash
# Connect to database
psql -h generative-ai.postgres.database.azure.com -U orchvate_admin -d nd_audit

# Add your admin email
INSERT INTO admin_users (email, role) 
VALUES ('your-email@orchvate.in', 'admin');

# Verify
SELECT * FROM admin_users;

# Exit
\q
```

---

## 📊 Full Diagnostic

Run this on your VM to see all current settings:

```bash
echo "=== Container Status ==="
sudo docker ps | grep niwi

echo -e "\n=== Auth Config Endpoint ==="
curl -s http://localhost:8080/api/auth/config | python3 -m json.tool

echo -e "\n=== Environment Variables in Container ==="
sudo docker exec niwi env | grep -E "ENTRA|CORS|FRONTEND" | grep -v PASSWORD

echo -e "\n=== Recent Logs ==="
sudo docker logs --tail 30 niwi
```

---

## 🐛 Common Issues and Solutions

### Issue: "AADSTS50011: The redirect URI does not match"

**Solution:** Update Azure AD redirect URIs to include `https://niwi.orchvate.in` and `https://niwi.orchvate.in/portal`

### Issue: "Sign-in verification failed (403)"

**Solution:** Add your email to `admin_users` table in database

### Issue: CORS errors in browser console

**Solution:** Ensure `CORS_ORIGINS=https://niwi.orchvate.in` in .env

### Issue: Still showing neuromark domain

**Solution:** 
1. Verify .env is updated: `cat .env | grep FRONTEND_URL`
2. Redeploy: `./deploy.sh`
3. Check container picked up changes: `sudo docker exec niwi env | grep FRONTEND`

---

## 📝 Complete Correct .env for VM

```bash
# --- Azure PostgreSQL (cloud) ---
PGHOST=your-database-host.postgres.database.azure.com
PGPORT=5432
PGDATABASE=nd_audit
PGUSER=your_admin_username
PGPASSWORD=your_secure_password

# --- Azure Communication Services ---
ACS_CONNECTION_STRING=endpoint=https://your-acs-resource.communication.azure.com/;accesskey=your_access_key_here
ACS_SENDER_ADDRESS=noreply@orchvate.in
ACS_SENDER_NAME="Your Sender Name"

# --- App Environment ---
APP_ENV=production

# --- App Settings ---
JWT_SECRET=<generate-with-openssl-rand-hex-32>
CORS_ORIGINS=https://niwi.orchvate.in
FRONTEND_URL=https://niwi.orchvate.in
DELETE_ALL_PASSWORD=your_admin_password

# --- Microsoft Entra ID (admin portal) ---
ENTRA_CLIENT_ID=your-client-id-here
ENTRA_TENANT_ID=your-tenant-id-here
```

---

## ⏱️ Expected Timeline

- Fix .env: 2 minutes
- Redeploy: 3-5 minutes
- Test: 1 minute
- **Total: ~10 minutes**

---

## 📞 If Still Not Working

1. Check container logs: `sudo docker logs -f niwi`
2. Check browser console for specific errors (F12)
3. Verify DNS: `nslookup niwi.orchvate.in`
4. Test from outside: `curl https://niwi.orchvate.in/api/health`
5. Check nginx/reverse proxy configuration
