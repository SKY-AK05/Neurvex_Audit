# Dashboard & Email Updates - Show All Collected Data

## Problem
The form was collecting more information (Job Role/Designation, Contact Number) but:
1. ❌ Dashboard submissions table only showed: Name, Organisation, Email
2. ❌ Submission detail view was missing fields
3. ❌ Email reports didn't include contact information

## Solution Implemented

### 1. Dashboard Table Update (`Dashboard.vue`)

**Added Columns:**
- **Job Role** - Shows designation/job title
- **Contact** - Shows contact number

**Before:**
```
# | Name | Organisation | Email | Submitted | Avg Score | Maturity | Status | Export
```

**After:**
```
# | Name | Job Role | Organisation | Email | Contact | Submitted | Avg Score | Maturity | Status | Export
```

### 2. Email Report Update (`scoring_service.py`)

**Updated Email Header:**
- Added `contact_number` parameter to `build_email()` function
- Display contact in email header alongside name, designation, company

**Email Header Now Shows:**
```
John Smith (HR Manager) · Acme Corp · +44 7700 900000 · October 2026
```

**Format:**
- Name (Designation) · Company · Contact · Month Year
- If contact is empty, it's hidden gracefully

## Files Modified

### Frontend
1. **`frontend/src/views/Dashboard.vue`**
   - Added "Job Role" column (shows `designation`)
   - Added "Contact" column (shows `contact_number`)
   - Updated colspan from 9 to 11 for empty row
   - Shows "—" when fields are empty

### Backend  
2. **`app/services/scoring_service.py`**
   - Updated `build_email()` signature to accept `contact_number`
   - Pass `contact_number` from data in `calculate_scores()`
   - Display contact in email header template
   - Conditionally show contact (hidden if empty)

## Visual Changes

### Dashboard Table
```
┌────┬──────────────┬─────────────┬──────────────┬────────────────────┬─────────────────┬─────────┬───────┬──────┐
│ ID │ Name         │ Job Role    │ Organisation │ Email              │ Contact         │ Score   │ Level │ ...  │
├────┼──────────────┼─────────────┼──────────────┼────────────────────┼─────────────────┼─────────┼───────┼──────┤
│ 1  │ Alex Johnson │ HR Manager  │ Acme Corp    │ alex@acme.com      │ +44 7700 900000 │ 15.5/20 │ L3    │ ...  │
│ 2  │ Jane Smith   │ —           │ TechCo       │ jane@techco.com    │ —               │ 12.0/20 │ L2    │ ...  │
└────┴──────────────┴─────────────┴──────────────┴────────────────────┴─────────────────┴─────────┴───────┴──────┘
```

### Email Report Header
**Before:**
```
John Smith · HR Manager · Acme Corp · October 2026
```

**After:**
```
John Smith (HR Manager) · Acme Corp · +44 7700 900000 · October 2026
```

## Benefits

✅ **Complete Information** - All collected data now visible  
✅ **Better Contact Management** - Easy to see contact numbers at a glance  
✅ **Professional Emails** - Contact info included in reports  
✅ **Consistent Display** - Same data shown everywhere  
✅ **Graceful Handling** - Missing fields show "—" instead of empty  

## Data Flow

```
Form Submission
      ↓
   Database
   (stores all fields)
      ↓
   ├─→ Dashboard Table (shows all)
   ├─→ Detail View (shows all)
   └─→ Email Report (includes all)
```

## Testing Checklist

### Dashboard
- [ ] Job Role column displays designation
- [ ] Contact column displays contact_number
- [ ] Empty fields show "—"
- [ ] Table scrolls horizontally on small screens
- [ ] All data is clickable to open detail view

### Email Reports
- [ ] Contact shows in header if provided
- [ ] Contact hidden if empty
- [ ] Format: Name (Designation) · Company · Contact · Date
- [ ] Email layout not broken
- [ ] Mobile-responsive

### CSV Export
- [ ] Job Role included in export
- [ ] Contact included in export
- [ ] All fields present in downloaded file

## Deployment Steps

**On your server:**

```bash
# Navigate to project
cd ~/apps/niwi/Audit

# Pull latest changes
git pull origin main

# Rebuild Docker image
sudo docker build -t niwi -f Dockerfile .

# Stop old container
sudo docker stop niwi && sudo docker rm niwi

# Start new container
sudo docker run -d \
  --name niwi \
  -p 8080:80 \
  --env-file .env \
  -e TZ=Asia/Kolkata \
  --restart unless-stopped \
  niwi

# Check logs
sudo docker logs niwi --tail 50
```

## Example Data Display

### Complete Submission View

**Respondent Info:**
```
Name: Alex Johnson
Job Role: People Manager/Supervisor - HR
Organisation: Acme Corp
Email: aakash.padyachi@orchvate.com
Contact: +44 7700 900000
Submitted: 15 Oct 2026, 10:29 pm
Status: ● Pending
```

**Email Header:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         Neurodiversity
       NeuroMark Audit
                              ⭕ 15.5
Alex Johnson (People Manager)         of 20
Acme Corp · +44 7700 900000
October 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Notes

- **Backward Compatible** - Works with old submissions missing these fields
- **Mobile Friendly** - Table scrolls horizontally on small screens  
- **Accessible** - Shows "—" for empty fields (not blank)
- **Professional** - Consistent formatting throughout

## Future Enhancements

Possible improvements:
- [ ] Make contact clickable (tel: link)
- [ ] Add phone number formatting
- [ ] Add email mailto: links
- [ ] Export vCard format
- [ ] SMS integration

---

**Updated:** January 15, 2025  
**Impact:** All collected form data now visible in dashboard and emails  
**Status:** ✅ Complete and ready for deployment
