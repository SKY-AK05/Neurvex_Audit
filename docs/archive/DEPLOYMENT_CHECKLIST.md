# NIWI Deployment Checklist

## ⚠️ Critical: Why Authentication is Failing

Your auth error "Could not load sign-in configuration from the server" is caused by missing Azure AD configuration. Follow this checklist to fix it.

---

## 📋 What You Need to Configure (In Order)

### ✅ 1. Azure AD App Registration (REQUIRED - This fixes auth!)

**Status:** ❌ NOT CONFIGURED - This is blocking authentication

**Steps:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to: **Azure Active Directory** → **App registrations** → **New registration**
3. Configure:
   ```
   Name: NIWI Admin Portal
   Supported account types: Single tenant
   Redirect URI (Web): https://niwi.orchvate.in/portal
   ```
4. Click **Register**
5. **Copy these values** (you'll need them in .env):
   - Application (client) ID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - Directory (tenant) ID: `yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy`

6. Go to **Authentication** tab:
   - Add another redirect URI: `https://niwi.orchvate.in`
   - Under "Implicit grant and hybrid flows", enable:
     - ✅ ID tokens
   - Click **Save**

7. **Update .env file** on your VM:
   ```bash
   ENTRA_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ENTRA_TENANT_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
   ```

📖 **Detailed Guide:** See `AZURE_AD_SETUP.md`

---

### ✅ 2. Azure PostgreSQL Database (REQUIRED)

**Status:** ❌ NOT CONFIGURED - Placeholders in .env

**What you need:**
- Azure PostgreSQL Flexible Server instance
- Database name: `nd_audit`
- Admin username and password

**Steps:**
1. Go to Azure Portal → **Create a resource** → **Azure Database for PostgreSQL**
2. Choose **Flexible server**
3. Configure:
   ```
   Server name: niwi-db (or your choice)
   Region: Same as your VM
   PostgreSQL version: 16
   Authentication: PostgreSQL authentication
   ```
4. After creation, get connection details from **Overview** page
5. **Update .env file:**
   ```bash
   PGHOST=niwi-db.postgres.database.azure.com
   PGPORT=5432
   PGDATABASE=nd_audit
   PGUSER=your_admin_username
   PGPASSWORD=your_secure_password
   ```

6. **Initialize database schema:**
   ```bash
   psql -h niwi-db.postgres.database.azure.com -U your_admin_username -d nd_audit -f create_table.sql
   ```

---

### ✅ 3. Azure Communication Services (REQUIRED for emails)

**Status:** ❌ NOT CONFIGURED - Needed for sending audit reports

**What you need:**
- Azure Communication Services resource
- Email communication service with verified domain

**Steps:**
1. Go to Azure Portal → **Create a resource** → **Communication Services**
2. Create the resource
3. Go to **Keys** tab → Copy **Connection string**
4. Set up Email service:
   - Go to **Email** → **Domains**
   - Either use Azure subdomain (free) or connect custom domain
   - Get sender address (e.g., `DoNotReply@xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.azurecomm.net`)

5. **Update .env file:**
   ```bash
   ACS_CONNECTION_STRING=endpoint=https://your-resource.communication.azure.com/;accesskey=xxxxx
   ACS_SENDER_ADDRESS=DoNotReply@xxxxxx.azurecomm.net
   ACS_SENDER_NAME=NIWI Audit Team
   ```

---

### ✅ 4. JWT Secret (REQUIRED for security)

**Status:** ⚠️ Using placeholder - Must change for production

**Steps:**
1. Generate a secure random string:
   ```bash
   openssl rand -hex 32
   ```
2. **Update .env file:**
   ```bash
   JWT_SECRET=<paste-the-generated-string-here>
   ```

---

### ✅ 5. Add Admin Users to Database (REQUIRED)

**Status:** ❌ Probably empty - You won't be able to login without this

**Steps:**
1. Connect to your PostgreSQL database:
   ```bash
   psql -h your-db-host.postgres.database.azure.com -U your_username -d nd_audit
   ```

2. Add admin users (replace with actual emails):
   ```sql
   INSERT INTO admin_users (email, role) 
   VALUES ('your-email@orchvate.in', 'admin');
   
   -- Add more admins if needed
   INSERT INTO admin_users (email, role) 
   VALUES ('another-admin@orchvate.in', 'admin');
   ```

3. Verify:
   ```sql
   SELECT * FROM admin_users;
   ```

4. Exit:
   ```
   \q
   ```

**Important:** Only emails in this table can login to the admin portal!

---

### ✅ 6. Domain and SSL (Already configured ✅)

Your domain `niwi.orchvate.in` appears to be already set up. Verify:
- DNS points to your VM IP
- SSL certificate is valid
- Nginx/reverse proxy routes traffic to port 8080

---

## 🚀 Deployment Steps (After Configuration)

### On your VM:

1. **Copy the updated .env file to VM:**
   ```bash
   scp .env your-username@niwi.orchvate.in:/path/to/niwi/
   ```

2. **SSH into VM:**
   ```bash
   ssh your-username@niwi.orchvate.in
   cd /path/to/niwi
   ```

3. **Verify .env is updated:**
   ```bash
   cat .env | grep ENTRA_CLIENT_ID
   cat .env | grep PGHOST
   ```

4. **Deploy:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

5. **Check if it's working:**
   ```bash
   # Test the auth config endpoint
   curl http://localhost:8080/api/auth/config
   
   # Should return something like:
   # {"clientId":"xxx-xxx-xxx","tenantId":"yyy-yyy-yyy"}
   # NOT: {"clientId":null,"tenantId":null}
   ```

6. **Check logs:**
   ```bash
   sudo docker logs -f niwi
   ```

---

## 🧪 Testing Authentication

1. Open browser: `https://niwi.orchvate.in/portal`
2. Click **"Sign in with Microsoft"**
3. You should see Microsoft login page (not an error)
4. Login with an email that's in the `admin_users` table
5. You should be redirected to the dashboard

---

## ❌ Troubleshooting

### Error: "Could not load sign-in configuration from the server"
- ✅ ENTRA_CLIENT_ID and ENTRA_TENANT_ID must be set in .env
- ✅ Container must be restarted after .env changes
- Test: `curl http://localhost:8080/api/auth/config`

### Error: "AADSTS50011: The redirect URI does not match"
- ✅ Add `https://niwi.orchvate.in` AND `https://niwi.orchvate.in/portal` to Azure AD redirect URIs

### Error: "Sign-in verification failed" or "Forbidden"
- ✅ Your email must be in the `admin_users` table
- ✅ Check: `psql` → `SELECT * FROM admin_users;`

### Database connection errors
- ✅ Check Azure PostgreSQL firewall rules allow your VM's IP
- ✅ Verify PGHOST, PGUSER, PGPASSWORD in .env

---

## 📝 Quick Diagnostic Commands

Run on your VM:

```bash
# Check container status
sudo docker ps | grep niwi

# Check environment variables in container
sudo docker exec niwi env | grep ENTRA

# Test auth config endpoint
curl http://localhost:8080/api/auth/config

# Check logs for errors
sudo docker logs --tail 50 niwi

# Or run the diagnostic script
chmod +x check-auth-config.sh
./check-auth-config.sh
```

---

## 📚 Related Documentation

- `AZURE_AD_SETUP.md` - Detailed Azure AD setup guide
- `check-auth-config.sh` - Automated diagnostic script
- `DEPLOY-NIWI.md` - Deployment instructions
- `docs/SETUP.md` - Full setup documentation

---

## ✅ Completion Checklist

Before going live, verify:

- [ ] Azure AD App Registration created
- [ ] ENTRA_CLIENT_ID and ENTRA_TENANT_ID in .env
- [ ] Azure PostgreSQL database configured
- [ ] Database schema initialized (create_table.sql)
- [ ] Admin users added to database
- [ ] Azure Communication Services configured (for emails)
- [ ] JWT_SECRET changed from placeholder
- [ ] Application deployed: `./deploy.sh`
- [ ] Auth config endpoint returns valid IDs: `curl .../api/auth/config`
- [ ] Can login at `https://niwi.orchvate.in/portal`
- [ ] Can see dashboard after login
- [ ] Email delivery works (test by submitting an audit)

---

## 🔐 Security Notes

- ✅ Never commit .env to Git (already in .gitignore)
- ✅ Use strong passwords for database
- ✅ Rotate JWT_SECRET periodically
- ✅ Only add trusted emails to admin_users table
- ✅ Keep Azure AD credentials secure
- ✅ Enable Azure PostgreSQL SSL/TLS
