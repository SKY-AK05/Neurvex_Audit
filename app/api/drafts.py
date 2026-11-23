import os
import json
import logging
import html as html_module
from datetime import datetime, timezone, timedelta
from uuid import UUID
import jwt
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

from app.core.database import get_db_connection
from app.services.settings_service import get_sender_for_send, send_acs_email

router = APIRouter(prefix="/drafts", tags=["Drafts"])
logger = logging.getLogger(__name__)

from app.core.config import JWT_SECRET, FRONTEND_URL

class SaveDraftPayload(BaseModel):
    draft_id: Optional[UUID] = None
    email: EmailStr
    company_name: str
    form_state: Dict[str, Any]
    current_step: int
    send_email: bool = False

def _e(val: Any) -> str:
    return html_module.escape(str(val or ""))

def render_draft_email(
    *,
    is_reminder: bool,
    name: str,
    company_name: str,
    resume_url: str
) -> tuple[str, str, str]:
    """
    Renders an accessible, brand-aligned email matching Orchvate's design tokens:
    Navy #120050, Deep Purple #1E1A4A, Soft Purple #AFA9EC, Teal #009070, Lime #C8F31D.
    Returns (subject, html_content, plain_text).
    """
    safe_name = _e(name or "there")
    safe_company = _e(company_name or "your organisation")
    safe_url = _e(resume_url)
    display_company = str(company_name or "Your Organisation").strip()

    if is_reminder:
        subject = f"Reminder: Continue your NIWI Self-Assessment — {display_company}"
        eyebrow = "ORCHVATE · NEURO-INCLUSIVE WORKPLACE INDEX"
        heading = "Continue Your NIWI Assessment"
        intro_lead = f"You recently started the Neuro-Inclusive Workplace Index (NIWI) self-assessment for <strong>{safe_company}</strong>."
        intro_body = "We've safely saved all of your responses so you can pick up exactly where you left off without having to start over."
        cta_text = "Resume Assessment &rarr;"
        preheader = f"Continue your saved NIWI assessment for {safe_company}. Progress is preserved for 30 days."
    else:
        subject = f"Resume your NIWI Self-Assessment — {display_company}"
        eyebrow = "ORCHVATE · NEURO-INCLUSIVE WORKPLACE INDEX"
        heading = "Assessment Progress Saved"
        intro_lead = f"Your progress on the Neuro-Inclusive Workplace Index (NIWI) self-assessment for <strong>{safe_company}</strong> has been saved."
        intro_body = "You can return to your assessment anytime within the next 30 days using your secure resumption link."
        cta_text = "Resume Assessment &rarr;"
        preheader = f"Your NIWI assessment progress for {safe_company} has been saved."

    plain_text = (
        f"Hi {name or 'there'},\n\n"
        f"{intro_lead.replace('<strong>', '').replace('</strong>', '')}\n"
        f"{intro_body}\n\n"
        f"When you're ready to continue, click the secure link below to pick up right where you left off:\n"
        f"{resume_url}\n\n"
        f"Key Details:\n"
        f"• Saved for 30 days from your last edit.\n"
        f"• Your answers reload automatically upon opening the link.\n"
        f"• Takes just 5–10 minutes to complete.\n\n"
        f"Best regards,\n"
        f"The Orchvate Team\n"
        f"https://www.orchvate.com\n"
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_e(subject)}</title>
  <!--[if mso]>
  <noscript>
  <xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml>
  </noscript>
  <![endif]-->
  <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap');
    body {{ margin: 0; padding: 0; background-color: #F5F2EB; font-family: 'DM Sans', Arial, -apple-system, BlinkMacSystemFont, sans-serif; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
    table {{ border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
    img {{ border: 0; outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; display: block; }}
    a {{ color: #009070; text-decoration: none; }}
    @media only screen and (max-width: 620px) {{
      .email-wrapper {{ width: 100% !important; }}
      .header-cell {{ padding: 28px 24px 24px !important; }}
      .body-cell {{ padding: 24px 20px 20px !important; }}
      .footer-cell {{ padding: 20px 20px !important; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background-color:#F5F2EB;">
  <div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">
    {_e(preheader)} &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;
  </div>
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#F5F2EB;">
    <tr>
      <td align="center" style="padding: 32px 16px 48px;">
        <table class="email-wrapper" width="600" cellpadding="0" cellspacing="0" role="presentation" style="max-width:600px;width:100%;">
          
          <!-- Top Branded Header -->
          <tr>
            <td class="header-cell" style="background:#120050;border-radius:16px 16px 0 0;padding:34px 40px 30px;">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td>
                    <p style="margin:0 0 10px;font-family:'DM Sans',Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:2px;color:#AFA9EC;text-transform:uppercase;">
                      {eyebrow}
                    </p>
                    <h1 style="margin:0 0 6px;font-family:'DM Serif Display',Georgia,serif;font-size:26px;font-weight:400;color:#FFFFFF;line-height:1.2;">
                      {heading}
                    </h1>
                    <p style="margin:0;font-family:'DM Sans',Arial,sans-serif;font-size:13px;color:#AFA9EC;">
                      {safe_company} &nbsp;·&nbsp; 30-Day Saved Progress
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Body Card -->
          <tr>
            <td class="body-cell" style="background:#FFFFFF;border-left:1px solid #E2DDD4;border-right:1px solid #E2DDD4;padding:32px 40px 28px;">
              <p style="margin:0 0 16px;font-family:'DM Sans',Arial,sans-serif;font-size:15px;color:#1E1A4A;line-height:1.6;">
                Dear <strong>{safe_name}</strong>,
              </p>
              <p style="margin:0 0 16px;font-family:'DM Sans',Arial,sans-serif;font-size:14px;color:#475569;line-height:1.65;">
                {intro_lead}
              </p>
              <p style="margin:0 0 24px;font-family:'DM Sans',Arial,sans-serif;font-size:14px;color:#475569;line-height:1.65;">
                {intro_body}
              </p>

              <!-- Progress Status Card -->
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#F9F8FF;border:1px solid #E2DDD4;border-left:4px solid #009070;border-radius:10px;margin-bottom:28px;">
                <tr>
                  <td style="padding:16px 20px;">
                    <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                      <tr>
                        <td>
                          <p style="margin:0 0 4px;font-family:'DM Sans',Arial,sans-serif;font-size:11px;font-weight:700;color:#120050;text-transform:uppercase;letter-spacing:0.06em;">
                            Assessment Progress
                          </p>
                          <p style="margin:0;font-family:'DM Sans',Arial,sans-serif;font-size:13px;color:#334155;line-height:1.5;">
                            All completed answers are safely preserved and will automatically reload.
                          </p>
                        </td>
                        <td width="115" align="right" valign="top">
                          <span style="display:inline-block;background:#EEEDFE;color:#120050;font-family:'DM Sans',Arial,sans-serif;font-size:11px;font-weight:700;padding:5px 10px;border-radius:99px;white-space:nowrap;">
                            Valid for 30 Days
                          </span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Action CTA Button -->
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="margin:20px 0 28px;">
                <tr>
                  <td align="center">
                    <a href="{safe_url}" target="_blank" style="display:inline-block;background-color:#009070;color:#FFFFFF !important;text-decoration:none;padding:14px 34px;border-radius:99px;font-family:'DM Sans',Arial,sans-serif;font-size:15px;font-weight:700;letter-spacing:0.02em;box-shadow:0 4px 14px rgba(0,144,112,0.25);">
                      {cta_text}
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Direct URL Fallback -->
              <p style="margin:0 0 6px;font-family:'DM Sans',Arial,sans-serif;font-size:12px;color:#94A3B8;text-align:center;">
                Or copy and paste this secure link into your browser:
              </p>
              <p style="margin:0 0 24px;font-family:'DM Sans',Arial,sans-serif;font-size:12px;text-align:center;word-break:break-all;">
                <a href="{safe_url}" style="color:#009070;text-decoration:underline;">{safe_url}</a>
              </p>

              <!-- Confidentiality & Guidance Note -->
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#F4F2F0;border-radius:8px;">
                <tr>
                  <td style="padding:12px 16px;">
                    <p style="margin:0;font-family:'DM Sans',Arial,sans-serif;font-size:12px;color:#555;line-height:1.55;">
                      <strong style="color:#120050;">Quick &amp; Confidential:</strong> Completing the assessment takes approximately 5–10 minutes. Upon completion, an instant multi-pillar inclusion reflection is generated for your organization.
                    </p>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td class="footer-cell" style="background:#FFFFFF;border-radius:0 0 16px 16px;border-left:1px solid #E2DDD4;border-right:1px solid #E2DDD4;border-bottom:1px solid #E2DDD4;padding:26px 40px;text-align:center;">
              <p style="margin:0 0 6px;font-family:'DM Sans',Arial,sans-serif;font-size:12px;color:#64748B;">
                Powered by <strong>Orchvate</strong> · Neuro-Inclusive Workplace Index
              </p>
              <p style="margin:0;font-family:'DM Sans',Arial,sans-serif;font-size:11px;color:#94A3B8;line-height:1.5;">
                If you already submitted this assessment or received this email by error, you can safely disregard this message.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    return subject, html_content, plain_text

def send_resume_email(email: str, name: str, company_name: str, resume_url: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                sender_address, sender_name = get_sender_for_send(cur)
    except Exception as e:
        logger.error(f"Failed to load email settings for resume draft email: {e}")
        sender_address = os.environ.get("ACS_SENDER_ADDRESS", "")
        sender_name = os.environ.get("ACS_SENDER_NAME", "Orchvate")

    if not sender_address:
        logger.error("No sender address configured for resume draft email")
        return

    subject, html, plain = render_draft_email(
        is_reminder=False,
        name=name,
        company_name=company_name,
        resume_url=resume_url
    )

    try:
        send_acs_email(
            to_address=email,
            to_name=name,
            subject=subject,
            html=html,
            plain=plain,
            sender_address=sender_address,
            sender_name=sender_name,
        )
        logger.info(f"Resume email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send resume email to {email}: {e}")

def send_reminder_email(email: str, name: str, company_name: str, resume_url: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                sender_address, sender_name = get_sender_for_send(cur)
    except Exception as e:
        logger.error(f"Failed to load email settings for reminder email: {e}")
        sender_address = os.environ.get("ACS_SENDER_ADDRESS", "")
        sender_name = os.environ.get("ACS_SENDER_NAME", "Orchvate")

    if not sender_address:
        logger.error("No sender address configured for reminder email")
        return

    subject, html, plain = render_draft_email(
        is_reminder=True,
        name=name,
        company_name=company_name,
        resume_url=resume_url
    )

    try:
        send_acs_email(
            to_address=email,
            to_name=name,
            subject=subject,
            html=html,
            plain=plain,
            sender_address=sender_address,
            sender_name=sender_name,
        )
        logger.info(f"Reminder email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send reminder email to {email}: {e}")

@router.post("/save")
async def save_draft(payload: SaveDraftPayload, request: Request, background_tasks: BackgroundTasks):
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    # Clean up expired drafts (older than 30 days)
                    cur.execute("""
                        DELETE FROM draft_submissions
                        WHERE (submitted = FALSE AND updated_at < NOW() - INTERVAL '30 days')
                           OR (submitted = TRUE AND updated_at < NOW() - INTERVAL '7 days')
                    """)

                    if payload.draft_id:
                        cur.execute("SELECT submitted, email FROM draft_submissions WHERE id = %s", (str(payload.draft_id),))
                        row = cur.fetchone()
                        if not row:
                            raise HTTPException(status_code=404, detail="Draft not found.")
                        if row[0]:
                            raise HTTPException(status_code=400, detail="This draft has already been submitted.")
                        
                        existing_owner_email = row[1]
                        if existing_owner_email and existing_owner_email.lower().strip() != payload.email.lower().strip():
                            raise HTTPException(
                                status_code=403,
                                detail="Forbidden: You do not have permission to modify this draft."
                            )

                        cur.execute("""
                            UPDATE draft_submissions
                            SET email = %s, company_name = %s, form_state = %s, current_step = %s, updated_at = NOW()
                            WHERE id = %s
                            RETURNING id
                        """, (payload.email, payload.company_name, json.dumps(payload.form_state), payload.current_step, str(payload.draft_id)))
                        draft_id = cur.fetchone()[0]
                    else:
                        cur.execute("""
                            INSERT INTO draft_submissions (email, company_name, form_state, current_step)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id
                        """, (payload.email, payload.company_name, json.dumps(payload.form_state), payload.current_step))
                        draft_id = cur.fetchone()[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving draft: {e}")
        raise HTTPException(status_code=500, detail="Database save failed.")

    # Enforce 30-day resume token limit
    exp = datetime.now(timezone.utc) + timedelta(days=30)
    token = jwt.encode({"draft_id": str(draft_id), "exp": exp}, JWT_SECRET, algorithm="HS256")
    
    resume_url = f"{FRONTEND_URL}/resume?token={token}"
    
    # Send email only when explicitly requested (e.g. manual click or button trigger)
    # This prevents inbox spam during background auto-saves.
    if payload.send_email:
        background_tasks.add_task(
            send_resume_email,
            payload.email,
            payload.form_state.get("name", "there"),
            payload.company_name,
            resume_url
        )
    
    return {
        "success": True,
        "draft_id": str(draft_id),
        "resume_url": resume_url
    }

@router.get("/resume")
async def resume_draft(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        draft_id = payload.get("draft_id")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid resume token.")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT email, company_name, form_state, current_step, submitted, updated_at 
                    FROM draft_submissions WHERE id = %s
                """, (draft_id,))
                row = cur.fetchone()
    except Exception as e:
        logger.error(f"Database error while loading draft: {e}")
        raise HTTPException(status_code=500, detail="Database query failed.")

    if not row:
        raise HTTPException(status_code=404, detail="Draft not found.")
    
    email, company_name, form_state, current_step, submitted, updated_at = row
    if submitted:
        raise HTTPException(status_code=400, detail="This draft has already been submitted.")

    # Strictly enforce 30-day limit on the stored draft record
    if updated_at:
        now = datetime.now(timezone.utc)
        u_utc = updated_at.replace(tzinfo=timezone.utc) if updated_at.tzinfo is None else updated_at
        if now - u_utc > timedelta(days=30):
            raise HTTPException(status_code=401, detail="This draft has expired (30-day limit).")

    return {
        "email": email,
        "company_name": company_name,
        "form_state": form_state,
        "current_step": current_step,
        "draft_id": draft_id
    }

def process_draft_reminders(limit: int = 50, hours_threshold: Optional[int] = None) -> int:
    """
    Finds incomplete drafts (submitted = FALSE) older than hours_threshold (default 48 hours)
    that haven't received a reminder.
    Dispatches a branded Orchvate reminder email with a 30-day resume link and marks reminder_sent_at.
    """
    if hours_threshold is None:
        try:
            hours_threshold = int(os.environ.get("DRAFT_REMINDER_HOURS", "48"))
        except (ValueError, TypeError):
            hours_threshold = 48

    sent_count = 0
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    # 1. Reconcile with submissions: if user completed the audit elsewhere, mark submitted
                    cur.execute("""
                        UPDATE draft_submissions d
                        SET submitted = TRUE
                        WHERE d.submitted = FALSE
                          AND EXISTS (
                              SELECT 1 FROM submissions s
                              WHERE LOWER(TRIM(s.email)) = LOWER(TRIM(d.email))
                                AND s.created_at >= d.created_at
                          )
                    """)

                    # 2. Select eligible drafts needing reminders
                    cur.execute("""
                        SELECT id, email, company_name, form_state
                        FROM draft_submissions
                        WHERE submitted = FALSE
                          AND email IS NOT NULL
                          AND TRIM(email) != ''
                          AND updated_at <= NOW() - (%s || ' hours')::interval
                          AND updated_at >= NOW() - INTERVAL '30 days'
                          AND reminder_sent_at IS NULL
                        ORDER BY updated_at ASC
                        LIMIT %s
                        FOR UPDATE SKIP LOCKED
                    """, (hours_threshold, limit))
                    candidates = cur.fetchall()
                    for row in candidates:
                        draft_id, email, company_name, form_state = row
                        if isinstance(form_state, str):
                            try:
                                form_state = json.loads(form_state)
                            except Exception:
                                form_state = {}
                        name = form_state.get("name", "there") if isinstance(form_state, dict) else "there"
                        exp = datetime.now(timezone.utc) + timedelta(days=30)
                        token = jwt.encode({"draft_id": str(draft_id), "exp": exp}, JWT_SECRET, algorithm="HS256")
                        resume_url = f"{FRONTEND_URL}/resume?token={token}"
                        
                        send_reminder_email(email, name, company_name, resume_url)
                        
                        cur.execute("""
                            UPDATE draft_submissions
                            SET reminder_sent_at = NOW(),
                                reminder_count = reminder_count + 1
                            WHERE id = %s
                        """, (str(draft_id),))
                        sent_count += 1
                        logger.info("Sent draft reminder email to %s (company: %s, draft: %s)", email, company_name, draft_id)
    except Exception as e:
        logger.error(f"Error processing draft reminders: {e}")
    return sent_count

@router.post("/reminders/process")
async def trigger_draft_reminders():
    count = process_draft_reminders()
    return {"status": "ok", "reminders_sent": count}
