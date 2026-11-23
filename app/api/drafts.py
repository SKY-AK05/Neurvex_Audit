import os
import json
import logging
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

    subject = f"Resume your NIWI Self-Assessment — {company_name}"
    plain = (
        f"Hi {name},\n\n"
        f"Your progress on the Neuro-Inclusive Workplace Index (NIWI) self-assessment for {company_name} has been saved.\n\n"
        f"You can resume your assessment anytime within the next 30 days by clicking the link below:\n"
        f"{resume_url}\n\n"
        f"Best regards,\n"
        f"The Orchvate Team\n"
    )
    
    html = f"""<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: 'Inter', sans-serif; background-color: #F5F2EB; color: #120050; padding: 2rem; margin: 0; }}
    .card {{ background-color: #FFFFFF; border: 2px solid #120050; border-radius: 12px; padding: 2.5rem; max-width: 500px; margin: 0 auto; box-shadow: 4px 4px 0 #009070; }}
    h2 {{ font-family: 'Playfair Display', serif; font-size: 1.6rem; color: #120050; margin-top: 0; margin-bottom: 1rem; }}
    p {{ font-size: 0.95rem; line-height: 1.6; color: #555; margin-bottom: 1.5rem; }}
    .btn {{ display: inline-block; background-color: #120050; color: #FFFFFF !important; text-decoration: none; padding: 0.8rem 1.8rem; border-radius: 99px; font-weight: bold; border: 2px solid #120050; font-family: 'Playfair Display', serif; box-shadow: 3px 3px 0 #C8F31D; margin-top: 0.5rem; }}
    .btn:hover {{ background-color: #009070; border-color: #009070; box-shadow: 3px 3px 0 #120050; }}
    .footer {{ font-size: 0.8rem; color: #aaa; margin-top: 2rem; text-align: center; border-top: 1px solid #E2DDD4; padding-top: 1rem; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>Assessment Progress Saved</h2>
    <p>Hi {name or 'there'},</p>
    <p>Your progress on the Neuro-Inclusive Workplace Index (NIWI) for <strong>{company_name}</strong> has been saved.</p>
    <p>You can resume your assessment anytime within the next 30 days by clicking the button below:</p>
    <p style="text-align: center;">
      <a href="{resume_url}" class="btn">Resume Assessment &rarr;</a>
    </p>
    <p>Or copy and paste this link into your browser:<br>
    <a href="{resume_url}" style="color: #009070;">{resume_url}</a></p>
    <div class="footer">
      <p>Powered by Orchvate</p>
    </div>
  </div>
</body>
</html>"""

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

    subject = f"Reminder: Continue your NIWI Self-Assessment — {company_name}"
    plain = (
        f"Hi {name},\n\n"
        f"You recently started the Neuro-Inclusive Workplace Index (NIWI) self-assessment for {company_name}.\n\n"
        f"Your progress has been saved. When you're ready, click the link below to pick up right where you left off:\n"
        f"{resume_url}\n\n"
        f"Your saved responses will remain accessible for 30 days.\n\n"
        f"Best regards,\n"
        f"The Orchvate Team\n"
    )
    
    html = f"""<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: 'Inter', sans-serif; background-color: #F5F2EB; color: #120050; padding: 2rem; margin: 0; }}
    .card {{ background-color: #FFFFFF; border: 2px solid #120050; border-radius: 12px; padding: 2.5rem; max-width: 500px; margin: 0 auto; box-shadow: 4px 4px 0 #009070; }}
    h2 {{ font-family: 'Playfair Display', serif; font-size: 1.6rem; color: #120050; margin-top: 0; margin-bottom: 1rem; }}
    p {{ font-size: 0.95rem; line-height: 1.6; color: #555; margin-bottom: 1.5rem; }}
    .btn {{ display: inline-block; background-color: #120050; color: #FFFFFF !important; text-decoration: none; padding: 0.8rem 1.8rem; border-radius: 99px; font-weight: bold; border: 2px solid #120050; font-family: 'Playfair Display', serif; box-shadow: 3px 3px 0 #C8F31D; margin-top: 0.5rem; }}
    .btn:hover {{ background-color: #009070; border-color: #009070; box-shadow: 3px 3px 0 #120050; }}
    .footer {{ font-size: 0.8rem; color: #aaa; margin-top: 2rem; text-align: center; border-top: 1px solid #E2DDD4; padding-top: 1rem; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>Continue Your NIWI Assessment</h2>
    <p>Hi {name or 'there'},</p>
    <p>You recently started the Neuro-Inclusive Workplace Index (NIWI) self-assessment for <strong>{company_name}</strong>.</p>
    <p>Your progress is saved! You can pick up right where you left off anytime within the next 30 days by clicking below:</p>
    <p style="text-align: center;">
      <a href="{resume_url}" class="btn">Resume Assessment &rarr;</a>
    </p>
    <p>Or paste this link into your browser:<br>
    <a href="{resume_url}" style="color: #009070;">{resume_url}</a></p>
    <div class="footer">
      <p>Powered by Orchvate</p>
    </div>
  </div>
</body>
</html>"""

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

def process_draft_reminders(limit: int = 20) -> int:
    """
    Finds incomplete drafts (submitted = FALSE) older than 48 hours that haven't received a reminder.
    Dispatches a reminder email with a 30-day resume link and marks reminder_sent_at.
    """
    sent_count = 0
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, email, company_name, form_state
                        FROM draft_submissions
                        WHERE submitted = FALSE
                          AND email IS NOT NULL
                          AND email != ''
                          AND updated_at <= NOW() - INTERVAL '48 hours'
                          AND updated_at >= NOW() - INTERVAL '30 days'
                          AND reminder_sent_at IS NULL
                        LIMIT %s
                        FOR UPDATE SKIP LOCKED
                    """, (limit,))
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
                        logger.info("Sent draft reminder email to %s (draft: %s)", email, draft_id)
    except Exception as e:
        logger.error(f"Error processing draft reminders: {e}")
    return sent_count

@router.post("/reminders/process")
async def trigger_draft_reminders():
    count = process_draft_reminders()
    return {"status": "ok", "reminders_sent": count}
