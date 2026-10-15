# Admin Notification System - Debugging Guide

## Current Status
✅ Code is in place and functional
❓ User reports not receiving notifications

## How It Works

### 1. Notification Flow
```
User submits form 
  ↓
Backend creates submission in database
  ↓
notify_admin_new_submission() function called
  ↓
Checks if notifications are enabled
  ↓
Gets admin email from settings
  ↓
Sends email via Azure Communication Services
```

### 2. Settings Configuration

From the screenshot, your settings show:
- **Support inbox email**: aakash.padyachi@orchvate.com
- **Notification email(s)**: panchali.banerjee@orchvate.com  
- **CC email(s)**: aakash.padyachi@orchvate.com
- **Status**: ✅ Alerts ON — emailed for new submissions

## Diagnostic Steps

### Step 1: Check if Notifications are Enabled in Database

```sql
-- Connect to your PostgreSQL database and run:
SELECT notifications_enabled, notification_email, notification_cc_email 
FROM settings 
LIMIT 1;
```

**Expected Result:**
- `notifications_enabled`: `true`
- `notification_email`: should have at least one email address
- `notification_cc_email`: optional

**If FALSE**: Toggle notifications ON in the Settings page.

### Step 2: Check Recent Submissions

```sql
-- Check if submissions are being created:
SELECT id, company_name, name, email, submitted_at, status
FROM submissions
ORDER BY submitted_at DESC
LIMIT 5;
```

This confirms that submissions are making it to the database.

### Step 3: Check Application Logs

On your server, check Docker logs for notification-related messages:

```bash
# View last 100 lines of logs
sudo docker logs niwi --tail 100

# Or follow logs in real-time
sudo docker logs niwi -f

# Look for these specific log messages:
# - "Admin notification sent for submission {id}"
# - "Admin notification not sent"
# - "Notifications enabled but notification_email is empty"
# - "No sender address configured for admin notification"
# - "Background admin notification failed"
```

### Step 4: Test Email Sending Manually

Create a test endpoint to verify Azure Communication Services is working:

```python
# Add this temporary route in app/api/routes.py for testing:

@router.post("/test-notification")
async def test_notification():
    """Test endpoint to verify notification system"""
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                from app.services.settings_service import send_acs_email, get_sender_for_send, get_settings
                
                settings = get_settings(cur)
                sender_address, sender_name = get_sender_for_send(cur)
                
                if not sender_address:
                    return {"success": False, "error": "Sender address not configured"}
                
                if not settings["notifications_enabled"]:
                    return {"success": False, "error": "Notifications are disabled"}
                
                admin_emails = [e.strip() for e in (settings["notification_email"] or "").split(",") if e.strip()]
                if not admin_emails:
                    return {"success": False, "error": "No admin emails configured"}
                
                # Send test email
                send_acs_email(
                    to_addresses=admin_emails,
                    subject="Test Notification from NeuroMark",
                    html="<p>This is a <strong>test notification</strong> from the NeuroMark system.</p><p>If you received this, notifications are working correctly!</p>",
                    plain="This is a test notification from the NeuroMark system.\n\nIf you received this, notifications are working correctly!",
                    sender_address=sender_address,
                    sender_name=sender_name,
                )
                
                return {"success": True, "message": f"Test email sent to {', '.join(admin_emails)}"}
        conn.close()
    except Exception as e:
        logger.error(f"Test notification failed: {e}")
        return {"success": False, "error": str(e)}
```

Then test it:
```bash
curl -X POST http://localhost:8080/api/test-notification
# OR
curl -X POST https://niwi.orchvate.in/api/test-notification
```

### Step 5: Common Issues and Solutions

#### Issue 1: Emails Going to Spam/Junk
**Solution**: See `EMAIL_DELIVERABILITY_FIX.md` - configure SPF, DKIM, DMARC

**Quick check:**
- Check spam/junk folder
- Add sender to safe senders list
- Check if domain is verified in Azure Communication Services

#### Issue 2: Azure Communication Services Not Configured
**Symptoms**: 
- Logs show "No sender address configured"
- HTTP 500 errors when sending

**Solution**:
```bash
# Check .env file has these set:
ACS_CONNECTION_STRING=endpoint=https://...
ACS_SENDER_ADDRESS=noreply@orchvate.com
ACS_SENDER_NAME=NeuroMark
```

#### Issue 3: Notifications Disabled
**Symptoms**: Logs show "Admin notification not sent - notifications may be disabled"

**Solution**:
1. Go to Settings page in admin dashboard
2. Look for the notification status indicator
3. If it says "Alerts OFF", click the bell icon to enable
4. OR update database directly:
   ```sql
   UPDATE settings SET notifications_enabled = true;
   ```

#### Issue 4: Invalid Email Addresses
**Symptoms**: Azure returns authentication or delivery errors

**Solution**:
- Verify email addresses in Settings don't have typos
- Remove spaces or special characters
- Test with a simple email like `test@orchvate.com`

#### Issue 5: Background Thread Failing Silently
**Symptoms**: No errors in logs, but email not received

**Solution**: The notification runs in a background thread. Add more logging:

```python
def bg_send():
    try:
        logger.info(f"Starting background notification send to {admin_emails}")
        send_acs_email(
            to_addresses=admin_emails,
            cc_addresses=cc_emails,
            subject=subject,
            html=html,
            plain=plain,
            sender_address=sender_address,
            sender_name=sender_name,
        )
        logger.info("Background notification sent successfully")
    except Exception as e:
        logger.error("Background admin notification failed: %s", e)
        # Log full traceback for debugging
        import traceback
        logger.error(traceback.format_exc())
```

## Testing Checklist

Use this checklist to verify the notification system:

- [ ] **Database Check**: Notifications enabled in settings table
- [ ] **Settings UI**: Shows "Alerts ON" in Settings page
- [ ] **Email Configured**: Notification email(s) field has valid addresses
- [ ] **Sender Configured**: ACS_SENDER_ADDRESS set in .env
- [ ] **Azure ACS**: Connection string valid and domain verified
- [ ] **Test Submission**: Submit a test form and check logs immediately
- [ ] **Email Received**: Check both inbox and spam folder
- [ ] **Logs Clean**: No error messages in docker logs

## Quick Fix Commands

If notifications are not working, try these in order:

### 1. Enable Notifications via Database
```sql
UPDATE settings SET notifications_enabled = true;
```

### 2. Set Notification Email
```sql
UPDATE settings SET notification_email = 'panchali.banerjee@orchvate.com';
```

### 3. Check Current Settings
```sql
SELECT * FROM settings;
```

### 4. Restart Docker Container
```bash
cd ~/apps/niwi/Audit
sudo docker restart niwi
sudo docker logs niwi --tail 50
```

## Expected Behavior

When working correctly:

1. **User submits form** → Sees success message
2. **Backend logs** → Shows "Admin notification sent for submission X"
3. **Admin receives email** within 1-2 minutes with:
   - Subject: "New audit to review — [Company Name]"
   - Body: Company name, respondent name, submission ID
   - Link to review submission in admin panel
4. **CC recipients** (if configured) also receive the email

## Monitoring

Add this to your monitoring routine:

```bash
# Daily check: Count submissions vs notifications
SELECT 
  COUNT(*) as total_submissions,
  (SELECT notifications_enabled FROM settings LIMIT 1) as alerts_enabled
FROM submissions 
WHERE submitted_at > NOW() - INTERVAL '24 hours';
```

## Support Escalation

If notifications still don't work after following this guide:

1. **Collect logs:**
   ```bash
   sudo docker logs niwi --tail 200 > /tmp/niwi-logs.txt
   ```

2. **Check Azure ACS metrics:**
   - Go to Azure Portal
   - Navigate to your Communication Services resource  
   - Check "Metrics" → "Email sent", "Email delivered"
   - Look for delivery failures

3. **Verify DNS:**
   ```bash
   nslookup -type=txt orchvate.com
   nslookup -type=txt _dmarc.orchvate.com
   ```

4. **Test with different recipient:**
   - Try sending to personal Gmail or Outlook account
   - Check if organization email filters are blocking

## Recent Changes

In this session, we added:
- Better logging for notification success/failure
- Email headers for better deliverability
- Submission ID tracking in email headers

These changes are in the code but need deployment to take effect.
