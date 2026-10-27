# Azure AD Setup Guide for NIWI

## Problem
Authentication is failing with error: "Could not load sign-in configuration from the server."

This happens because the Azure AD (Microsoft Entra ID) credentials are not configured.

## Root Cause
The `.env` file contains placeholder values:
```
ENTRA_CLIENT_ID=your-azure-ad-application-client-id
ENTRA_TENANT_ID=your-azure-ad-tenant-id
```

## Solution

### Step 1: Create Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations** → **New registration**
3. Fill in the details:
   - **Name**: NIWI Admin Portal
   - **Supported account types**: Accounts in this organizational directory only (Single tenant)
   - **Redirect URI**: 
     - Type: Web
     - URI: `https://niwi.orchvate.in/portal`
4. Click **Register**

### Step 2: Configure Authentication

1. After registration, note down:
   - **Application (client) ID** (e.g., `12345678-1234-1234-1234-123456789abc`)
   - **Directory (tenant) ID** (e.g., `87654321-4321-4321-4321-cba987654321`)

2. Go to **Authentication** section:
   - Click **Add a platform** → **Web**
   - Add redirect URI: `https://niwi.orchvate.in`
   - Under **Implicit grant and hybrid flows**, check:
     - ✅ ID tokens (used for implicit and hybrid flows)
   - Click **Save**

3. Go to **API permissions** (optional but recommended):
   - Verify these permissions are present:
     - Microsoft Graph → User.Read (Delegated)
     - Microsoft Graph → openid (Delegated)
     - Microsoft Graph → profile (Delegated)
     - Microsoft Graph → email (Delegated)

### Step 3: Update Environment Variables on VM

SSH into your VM and update the `.env` file:

```bash
ssh your-username@niwi.orchvate.in

# Navigate to NIWI directory
cd /path/to/niwi

# Edit .env file
nano .env
```

Update these lines with your actual values:
```bash
ENTRA_CLIENT_ID=12345678-1234-1234-1234-123456789abc
ENTRA_TENANT_ID=87654321-4321-4321-4321-cba987654321
```

Also ensure other required values are set:
```bash
# Database credentials
PGHOST=your-database-host.postgres.database.azure.com
PGUSER=your-database-username
PGPASSWORD=your-database-password

# Azure Communication Services
ACS_CONNECTION_STRING=endpoint=https://...
ACS_SENDER_ADDRESS=noreply@orchvate.in

# JWT Secret (generate a secure random string)
JWT_SECRET=your-secure-jwt-secret-here

# CORS Origins
CORS_ORIGINS=https://niwi.orchvate.in
FRONTEND_URL=https://niwi.orchvate.in
```

Save and exit (Ctrl+X, then Y, then Enter).

### Step 4: Redeploy the Application

```bash
# Make deploy script executable if needed
chmod +x deploy.sh

# Deploy
./deploy.sh
```

### Step 5: Configure Admin Users

Add authorized admin users to the database:

```bash
# Connect to your PostgreSQL database
psql -h your-database-host.postgres.database.azure.com -U your-username -d nd_audit

# Insert admin user (replace with actual email)
INSERT INTO admin_users (email, role) VALUES ('admin@orchvate.in', 'admin');

# Exit
\q
```

### Step 6: Test Authentication

1. Navigate to `https://niwi.orchvate.in/portal`
2. Click "Sign in with Microsoft"
3. You should be redirected to Microsoft login
4. After successful login, you should be redirected back to the NIWI dashboard

## Troubleshooting

### Error: "Could not load sign-in configuration from the server"
- Check that ENTRA_CLIENT_ID and ENTRA_TENANT_ID are set in `.env`
- Verify the container is using the updated `.env` file: `sudo docker logs niwi | grep ENTRA`

### Error: "AADSTS50011: The redirect URI specified in the request does not match"
- Add `https://niwi.orchvate.in` and `https://niwi.orchvate.in/portal` to Azure AD redirect URIs

### Error: "Sign-in verification failed"
- Ensure your email is added to the `admin_users` table in the database
- Check API logs: `sudo docker logs -f niwi`

### Still not working?
1. Check container logs: `sudo docker logs -f niwi`
2. Verify environment variables are loaded: `sudo docker exec niwi env | grep ENTRA`
3. Test the config endpoint: `curl https://niwi.orchvate.in/api/auth/config`
   - Should return: `{"clientId": "your-client-id", "tenantId": "your-tenant-id"}`

## Security Notes

- Never commit the actual `.env` file to Git (it's already in `.gitignore`)
- Use strong, unique values for JWT_SECRET
- Regularly rotate database passwords and API keys
- Only add trusted users to the `admin_users` table
