import os
import json
import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
import jwt
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request

from app.core.database import get_conn

router = APIRouter(prefix="/drafts", tags=["Drafts"])
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET", "default_jwt_secret_key_change_me")

class SaveDraftPayload(BaseModel):
    draft_id: Optional[UUID] = None
    email: EmailStr
    company_name: str
    form_state: Dict[str, Any]
    current_step: int

@router.post("/save")
async def save_draft(payload: SaveDraftPayload, request: Request):
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
    
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    resume_url = f"{frontend_url}/#/resume?token={token}"
    
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
