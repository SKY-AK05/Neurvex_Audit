# NIWI Deployment Steps

## What Was Fixed

### 1. Demographic Data Storage & Display
- **Problem**: Form collected demographic fields (function, country, role, gender, pwd status, neurodivergent, marginalized) but they weren't visible in dashboard or detail views
- **Root Cause**: Data was being stored in `answers` JSONB column but not extracted for display
- **Solution**: 
  - Modified backend to extract demographic fields from `answers` JSONB when returning submission data
  - Updated both `/api/submissions` (list) and `/api/submissions/{id}` (detail) endpoints
  - Dashboard now shows: Function, Country, Role, Contact Number
  - Detail view shows all demographic fields in "Demographics & Identity" card

### 2. Edit Respondent Information
- **Problem**: No way to correct respondent information (typos in name, email, etc.)
- **Solution**: 
  - Added new endpoint: `PATCH /api/submissions/{id}/respondent`
  - Added edit button in SubmissionDetail.vue
  - Can now edit: Name, Email, Organisation, Contact Number, Designation
  - Changes saved to database and reflected immediately in UI

## Files Modified

1. **Backend**:
   - `app/api/routes.py`: Extract demographic data from JSONB, add PATCH endpoint for editing

2. **Frontend**:
   - `frontend/src/api.js`: Add `updateRespondent()` function
   - `frontend/src/views/SubmissionDetail.vue`: Add edit mode UI for respondent info

## Deployment Commands

SSH into your server and run these commands:

```bash
# Navigate to project directory
cd ~/apps/niwi/Audit

# Pull latest changes
git pull origin main

# Rebuild Docker image (picks up code changes)
sudo docker build -t niwi -f Dockerfile .

# Stop and remove old container
sudo docker stop niwi
sudo docker rm niwi

# Start new container
sudo docker run -d \
  --name niwi \
  -p 8080:80 \
  --env-file .env \
  -e TZ=Asia/Kolkata \
  --restart unless-stopped \
  niwi

# Verify it's running
sudo docker ps | grep niwi

# Check logs for any errors
sudo docker logs niwi --tail 50
```

## Testing Checklist

After deployment:

1. **Dashboard View** (`/admin/submissions`):
   - [ ] Job Role column shows data
   - [ ] Contact column shows phone numbers
   - [ ] All existing submissions visible

2. **Submission Detail View** (click any submission):
   - [ ] Demographics & Identity card shows:
     - Gender Identity
     - Person with Disability status
     - Neurodivergent status
     - Underrepresented/Marginalized status
   - [ ] Function / Department field populated
   - [ ] Country field populated
   - [ ] Role Level field populated
   - [ ] State/UT field shows for India submissions

3. **Edit Respondent**:
   - [ ] Click "Edit" button in Respondent card
   - [ ] Modify any field (name, email, company, contact, designation)
   - [ ] Click "Save Changes"
   - [ ] Changes reflected immediately
   - [ ] Dashboard updates with new values
   - [ ] No errors in browser console

4. **New Form Submission**:
   - [ ] Submit a new form from `/`
   - [ ] Fill all demographic fields
   - [ ] Check dashboard shows new entry with all data
   - [ ] Open detail view and verify all fields present

## Rollback (if needed)

If deployment fails:

```bash
# Stop the broken container
sudo docker stop niwi

# Revert to previous commit
cd ~/apps/niwi/Audit
git reset --hard c94513b  # Previous working commit

# Rebuild with old code
sudo docker build -t niwi -f Dockerfile .
sudo docker rm niwi
sudo docker run -d --name niwi -p 8080:80 --env-file .env -e TZ=Asia/Kolkata --restart unless-stopped niwi
```

## Git Commit

Current commit: `3d54c33`
Previous commit: `c94513b`

## Notes

- Demographic fields are stored in `answers` JSONB column in database
- Backend now extracts them automatically when serving API responses
- No database migration needed - existing data will work immediately
- Edit functionality only updates direct columns (name, email, company_name, contact_number, designation)
- Demographic data (from answers JSONB) is read-only in current implementation
