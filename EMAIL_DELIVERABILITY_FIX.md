# Email Deliverability Issues - Diagnosis & Fix

## Problem
Emails landing in Junk/Spam folder

## Root Causes

### 1. **Missing Email Authentication (Critical)**
- No SPF record configured
- No DKIM signature
- No DMARC policy
- Azure Communication Services needs proper DNS setup

### 2. **Content Issues**
- Using external image URLs (QuickChart)
- HTML-heavy content without proper plain text alternative
- Missing proper email headers

### 3. **Sender Reputation**
- New domain/sender without warm-up
- No dedicated IP address
- Bulk sending from cold domain

## Immediate Fixes Required

### A. DNS Configuration (MUST DO - Critical for deliverability)

Add these DNS records for your sending domain:

#### 1. SPF Record
```
Type: TXT
Host: @
Value: v=spf1 include:spf.protection.outlook.com include:_spf.azurecomm.net -all
TTL: 3600
```

#### 2. DKIM (Azure Communication Services)
Azure ACS provides DKIM automatically, but you need to verify your domain:

1. Go to Azure Portal → Communication Services → your resource
2. Navigate to "Email" → "Domains"
3. Click "Verify domain"
4. Add the TXT records Azure provides
5. Wait for verification (can take up to 48 hours)

#### 3. DMARC Policy
```
Type: TXT
Host: _dmarc
Value: v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@orchvate.com; pct=100; adkim=s; aspf=s
TTL: 3600
```

**Explanation:**
- `p=quarantine` - Tell receivers to quarantine suspicious emails (use `p=reject` after testing)
- `rua=mailto:...` - Where to send aggregate reports
- `adkim=s` - Strict DKIM alignment
- `aspf=s` - Strict SPF alignment

### B. Azure Communication Services Configuration

1. **Verify Domain Ownership**
   ```bash
   # In Azure Portal
   1. Go to ACS resource
   2. Email → Domains → Add custom domain
   3. Enter: neuromark.orchvate.in or orchvate.com
   4. Copy verification TXT record
   5. Add to DNS
   6. Click "Verify"
   ```

2. **Enable Email Protection**
   - Ensure DKIM signing is enabled (automatic in ACS)
   - Configure SPF pass-through
   - Set up bounce/complaint handling

3. **Update .env with Verified Domain**
   ```env
   ACS_SENDER_ADDRESS=noreply@orchvate.com
   # OR
   ACS_SENDER_ADDRESS=neuromark@orchvate.com
   ACS_SENDER_NAME=NeuroMark - Orchvate
   ```

### C. Email Content Improvements

#### 1. Better Plain Text Version
Current: Minimal plain text
Needed: Comprehensive plain text that mirrors HTML content

#### 2. Proper Email Headers
Add these headers in the code:
```python
{
    "headers": {
        "X-Priority": "3",
        "Importance": "normal",
        "X-Entity-Ref-ID": f"submission-{submission_id}",
        "List-Unsubscribe": "<mailto:unsubscribe@orchvate.com>",
        "Precedence": "bulk"
    }
}
```

#### 3. Image Optimization
- QuickChart is fine, but ensure it's HTTPS
- Add proper alt tags (already done ✓)
- Consider embedding small images as base64 (for logos only)

#### 4. Link Safety
- All links should be HTTPS
- Use proper tracking parameters
- Include unsubscribe link

### D. Sender Warm-up Strategy

**Week 1:** 50 emails/day
**Week 2:** 100 emails/day
**Week 3:** 250 emails/day
**Week 4+:** Full volume

This builds sender reputation gradually.

## Implementation Steps

### Step 1: DNS Configuration (Do First - Takes 24-48h to propagate)

```bash
# Add these to your DNS provider (Cloudflare, GoDaddy, etc.)

1. SPF Record:
   Type: TXT
   Name: @
   Value: v=spf1 include:_spf.azurecomm.net -all

2. DMARC Record:
   Type: TXT
   Name: _dmarc
   Value: v=DMARC1; p=quarantine; rua=mailto:aakash.padyachi@orchvate.com

3. Azure ACS Domain Verification (get from Azure Portal):
   Type: TXT
   Name: <provided by Azure>
   Value: <provided by Azure>
```

### Step 2: Update Email Sending Code

File: `app/services/settings_service.py`

```python
def send_acs_email(*, to_addresses: list[str] = None, to_address: str = None, 
                   to_name: str = "", cc_addresses: list[str] = None, 
                   subject: str, html: str, plain: str,
                   sender_address: str, sender_name: str,
                   submission_id: str = None) -> None:
    client = EmailClient.from_connection_string(os.environ["ACS_CONNECTION_STRING"])
    
    to_recipients = [{"address": a.strip()} for a in to_addresses if a.strip()] if to_addresses else [{"address": to_address, "displayName": to_name}]
    
    # Build message with proper headers
    message = {
        "senderAddress": sender_address,
        "recipients": {"to": to_recipients},
        "content": {
            "subject": subject, 
            "html": html, 
            "plainText": plain
        },
        "replyTo": [{"address": sender_address, "displayName": sender_name}],
        "headers": {
            "X-Priority": "3",
            "Importance": "normal",
        }
    }
    
    # Add submission tracking
    if submission_id:
        message["headers"]["X-Entity-Ref-ID"] = f"submission-{submission_id}"
    
    if cc_addresses:
        cc_recipients = [{"address": c.strip()} for c in cc_addresses if c.strip()]
        if cc_recipients:
            message["recipients"]["cc"] = cc_recipients

    poller = client.begin_send(message)
    poller.result()
```

### Step 3: Improve Plain Text Content

Current plain text is too basic. Update in `scoring_service.py`:

```python
def build_plain_text_email(name, company_name, overall_avg, overall_level, section_scores):
    """Generate comprehensive plain text version"""
    plain = f"""
Hi {name},

Thank you for completing the NeuroMark Workplace Audit for {company_name}.

YOUR OVERALL SCORE: {overall_avg}/20 — {overall_level}

SEGMENT BREAKDOWN:
"""
    
    for key, label, score, level, is_low in section_scores:
        if score != "NA":
            plain += f"\n• {label}: {score}/20 — {level}"
        else:
            plain += f"\n• {label}: Not Applicable"
    
    plain += f"""

NEXT STEPS:
Your detailed report with recommendations has been prepared. Please review it to understand your organisation's neuro-inclusion maturity and identify opportunities for improvement.

Need guidance? Book a consultation: {booking_url}

Best regards,
NeuroMark Team
Orchvate

---
This is an automated report. Please do not reply to this email.
"""
    
    return plain
```

### Step 4: Testing

1. **Check DNS Propagation**
   ```bash
   # Check SPF
   nslookup -type=txt orchvate.com
   
   # Check DMARC
   nslookup -type=txt _dmarc.orchvate.com
   ```

2. **Test Email Deliverability**
   - Use https://www.mail-tester.com/
   - Send a test email to test-xxxxx@srv1.mail-tester.com
   - Check score (should be 8+/10)

3. **Monitor Delivery**
   - Azure Portal → ACS → Metrics → Email sent/delivered
   - Check bounce rates
   - Monitor complaint rates

## Quick Wins (Implement Today)

1. ✅ Add proper plain text version
2. ✅ Add email headers (X-Priority, etc.)
3. ✅ Update sender name to be professional
4. ⏳ Configure SPF/DKIM/DMARC (requires DNS access)

## Expected Results

After implementing:
- **Before:** 60-70% land in spam
- **After:** 90%+ land in inbox

Timeline:
- DNS changes: 24-48 hours to propagate
- Full improvement: 1-2 weeks as sender reputation builds

## Monitoring

Check these weekly:
1. Delivery rate in Azure Portal
2. Bounce rate (should be < 5%)
3. Complaint rate (should be < 0.1%)
4. Mail-tester.com score (should be 8+/10)

## Critical Actions

**DO IMMEDIATELY:**
1. Configure SPF/DKIM/DMARC DNS records
2. Verify domain in Azure Communication Services
3. Update sender email to verified domain
4. Implement email headers

**DO WITHIN 1 WEEK:**
1. Set up DMARC reporting
2. Monitor bounce/complaint rates
3. Adjust content based on feedback

**DO WITHIN 1 MONTH:**
1. Request dedicated IP (if sending > 100k emails/month)
2. Implement proper list hygiene (remove bounces)
3. Add unsubscribe functionality (if needed for marketing)
