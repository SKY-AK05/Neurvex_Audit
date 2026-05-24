import os
import json
import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
import jwt
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

from app.core.database import get_conn
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

def send_resume_email(email: str, name: str, company_name: str, resume_url: str):
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                sender_address, sender_name = get_sender_for_send(cur)
        conn.close()
    except Exception as e:
        logger.error(f"Failed to load email settings for resume draft email: {e}")
        sender_address = os.environ.get("ACS_SENDER_ADDRESS", "")
        sender_name = os.environ.get("ACS_SENDER_NAME", "Orchvate")

    if not sender_address:
        logger.error("No sender address configured for resume draft email")
        return

    subject = f"Resume your Neurvex Inclusion Audit — {company_name}"
    plain = (
        f"Hi {name},\n\n"
        f"Your progress on the Neurvex Inclusion Audit for {company_name} has been saved.\n\n"
        f"You can resume your audit anytime within the next 7 days by clicking the link below:\n"
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
    <h2>Audit Progress Saved</h2>
    <p>Hi {name or 'there'},</p>
    <p>Your progress on the Neurvex Inclusion Audit for <strong>{company_name}</strong> has been saved.</p>
    <p>You can resume your audit anytime within the next 7 days by clicking the button below:</p>
    <p style="text-align: center;">
      <a href="{resume_url}" class="btn">Resume Audit &rarr;</a>
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

@router.post("/save")
async def save_draft(payload: SaveDraftPayload, request: Request, background_tasks: BackgroundTasks):
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                if payload.draft_id:
                    # Check if already submitted
                    cur.execute("SELECT submitted FROM draft_submissions WHERE id = %s", (str(payload.draft_id),))
                    row = cur.fetchone()
                    if row and row[0]:
                        raise HTTPException(status_code=400, detail="This draft has already been submitted.")
                    
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
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving draft: {e}")
        raise HTTPException(status_code=500, detail="Database save failed.")

    # Generate token expiring in 7 days
    exp = datetime.now(timezone.utc) + timedelta(days=7)
    token = jwt.encode({"draft_id": str(draft_id), "exp": exp}, JWT_SECRET, algorithm="HS256")
    
    resume_url = f"{FRONTEND_URL}/#/resume?token={token}"
    
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
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT email, company_name, form_state, current_step, submitted 
                    FROM draft_submissions WHERE id = %s
                """, (draft_id,))
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error(f"Database error while loading draft: {e}")
        raise HTTPException(status_code=500, detail="Database query failed.")

    if not row:
        raise HTTPException(status_code=404, detail="Draft not found.")
    
    email, company_name, form_state, current_step, submitted = row
    if submitted:
        raise HTTPException(status_code=400, detail="This draft has already been submitted.")

    return {
        "email": email,
        "company_name": company_name,
        "form_state": form_state,
        "current_step": current_step,
        "draft_id": draft_id
    }
