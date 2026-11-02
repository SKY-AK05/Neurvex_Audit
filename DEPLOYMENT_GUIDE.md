# NIWI Deployment Guide

## Quick Deploy (Standard Process)

### 1. Push to GitHub
```bash
git add .
git commit -m "Add organisation reassignment feature"
git push origin main
```

### 2. Deploy on VM
```bash
# SSH into your VM
ssh your-vm

# Navigate to project
cd /path/to/niwi

# Run deployment script
./deploy.sh
```

### 3. Run Migrations (IMPORTANT!)
```bash
# After container is running, execute migrations
sudo docker exec -it niwi python run_migrations.py
```

**OR** run manually:
```bash
# Connect to running container
sudo docker exec -it niwi bash

# Inside container
python run_migrations.py
exit
```

---

## What Happens During Deployment

### deploy.sh does:
1. ✅ Syncs code from GitHub (force update)
2. ✅ Builds Docker image with new code
3. ✅ Stops and removes old container
4. ✅ Starts new container
5. ❌ **Does NOT run migrations automatically**

### You must manually run:
```bash
sudo docker exec -it niwi python run_migrations.py
```

---

## Migration Safety

### Our migrations are IDEMPOTENT:
- ✅ Safe to run multiple times
- ✅ Won't duplicate tables or columns
- ✅ Won't affect existing data
- ✅ Uses `CREATE TABLE IF NOT EXISTS`
- ✅ Uses `CREATE INDEX IF NOT EXISTS`

### The new migration (06_audit_reassignment.sql):
- Creates `submission_reassignments` audit trail table
- Adds 5 indexes for performance
- **DOES NOT** modify existing tables
- **DOES NOT** touch existing data

---

## Verification Steps

### After deployment, verify:

1. **Container is running:**
```bash
sudo docker ps | grep niwi
```

2. **Application is responding:**
```bash
curl http://localhost:8080/api/health
```

3. **Migration completed:**
```bash
sudo docker exec -it niwi python -c "
from app.api.routes import get_conn
conn = get_conn()
cur = conn.cursor()
cur.execute(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'submission_reassignments')\")
print('✅ Migration applied!' if cur.fetchone()[0] else '❌ Migration not run')
conn.close()
"
```

4. **Check logs:**
```bash
sudo docker logs niwi --tail 50
```

---

## Rollback Plan (If Needed)

### If something goes wrong:

1. **Revert to previous version:**
```bash
# On VM
git reset --hard HEAD~1
./deploy.sh
```

2. **Remove new table (if needed):**
```bash
sudo docker exec -it niwi python -c "
from app.api.routes import get_conn
conn = get_conn()
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS submission_reassignments CASCADE')
conn.commit()
conn.close()
print('✅ Table removed')
"
```

---

## Automatic Migration (Optional Enhancement)

If you want migrations to run automatically on container start, add this to `supervisord.conf`:

```ini
[program:migrations]
command=python run_migrations.py
directory=/app
autostart=true
autorestart=false
startsecs=0
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
priority=10
```

Then rebuild and redeploy. Migrations will run before the API starts.

---

## Troubleshooting

### Problem: Migration fails
**Solution:** Check database connection in `.env`:
```bash
sudo docker exec -it niwi env | grep DATABASE_URL
```

### Problem: Container won't start
**Solution:** Check logs:
```bash
sudo docker logs niwi
```

### Problem: Table already exists error
**Solution:** This is normal if you run migrations twice. The script handles this gracefully.

### Problem: Foreign key constraint error
**Solution:** Ensure parent tables exist (submissions, organizations, users). These should exist from previous migrations.

---

## Database Backup (Before Major Changes)

**Always backup before deploying schema changes:**

```bash
# On VM, backup database
sudo docker exec niwi pg_dump "$DATABASE_URL" > niwi_backup_$(date +%Y%m%d_%H%M%S).sql

# Or from outside container
pg_dump "your_database_url" > backup.sql
```

---

## Files Modified in This Deployment

### New Files:
- `sql/06_audit_reassignment.sql` - New audit trail table
- `run_migrations.py` - Automated migration runner
- `DEPLOYMENT_GUIDE.md` - This guide

### Modified Files:
- `frontend/src/views/AuditForm.vue` - Simplified org input
- `frontend/src/views/SubmissionDetail.vue` - Added reassignment UI
- `frontend/src/api.js` - New API functions
- `app/api/routes.py` - New reassignment endpoint

### No Breaking Changes:
- Existing submissions work normally
- Existing organisations unchanged
- Invitation system unchanged
- Scoring unchanged
- All existing admin features work

---

## Post-Deployment Testing

### Test 1: Simplified Organisation Input
1. Go to public form: http://your-domain:8080/
2. Fill out assessment
3. Enter ANY organisation name (no validation messages should appear)
4. Submit successfully

### Test 2: Admin Reassignment
1. Login to admin: http://your-domain:8080/portal
2. Open any submission
3. Click "🔄 Change Organisation" button
4. Select different organisation
5. Add optional reason
6. Confirm reassignment
7. Verify success message

### Test 3: Audit Trail
```bash
sudo docker exec -it niwi python -c "
from app.api.routes import get_conn
conn = get_conn()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM submission_reassignments')
print(f'Reassignment records: {cur.fetchone()[0]}')
conn.close()
"
```
