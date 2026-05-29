import os
import logging
import jwt
import psycopg2.extras
from datetime import datetime, timezone, timedelta
from uuid import UUID
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, HTTPException, Request, Depends

from app.core.database import get_conn
from app.services.settings_service import send_acs_email, get_sender_for_send

router = APIRouter(prefix="/org", tags=["Organizations"])
logger = logging.getLogger(__name__)

from app.core.config import JWT_SECRET, FRONTEND_URL

class RegisterPayload(BaseModel):
    email: EmailStr
    company_name: str

def create_magic_link_token(email: str, company_name: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    return jwt.encode({"email": email.lower(), "company_name": company_name, "exp": exp, "type": "magic_link"}, JWT_SECRET, algorithm="HS256")

@router.post("/register")
async def register_or_login_org(payload: RegisterPayload):
    email = payload.email.lower()
    company_name = payload.company_name
    
    # 1. Send magic link email
    token = create_magic_link_token(email, company_name)
    login_url = f"{FRONTEND_URL}/org/verify?token={token}"
    
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                sender_address, sender_name = get_sender_for_send(cur)
        conn.close()
    except Exception:
        sender_address = os.environ.get("ACS_SENDER_ADDRESS", "founders@orchvate.in")
        sender_name = os.environ.get("ACS_SENDER_NAME", "Orchvate")

    email_html = f"""
    <p>Hello,</p>
    <p>Please click the link below to access your NeuroMark Org Dashboard:</p>
    <p><a href="{login_url}" style="font-weight:bold;color:#7F77DD;">Access my Dashboard</a></p>
    <p>This link is valid for 15 minutes.</p>
    """
    
    try:
        send_acs_email(
            to_address=email,
            to_name=company_name,
            subject="Access your NeuroMark Org Dashboard",
            html=email_html,
            plain=f"Click here to log in: {login_url}",
            sender_address=sender_address,
            sender_name=sender_name
        )
    except Exception as e:
        logger.error(f"Failed to send magic link: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification email.")
        
    return {"success": True, "message": "Magic link sent to your email."}

@router.get("/verify")
async def verify_magic_link(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "magic_link":
            raise HTTPException(status_code=400, detail="Invalid token type.")
        email = payload.get("email").lower()
        company_name = payload.get("company_name")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Verification link has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid link token.")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                # Get or Create Organization
                cur.execute("SELECT id FROM organizations WHERE name = %s", (company_name,))
                org_row = cur.fetchone()
                if org_row:
                    org_id = org_row[0]
                else:
                    cur.execute("INSERT INTO organizations (name) VALUES (%s) RETURNING id", (company_name,))
                    org_id = cur.fetchone()[0]

                # Get or Create Org User
                cur.execute("SELECT id FROM organization_users WHERE email = %s", (email,))
                user_row = cur.fetchone()
                if not user_row:
                    cur.execute("INSERT INTO organization_users (organization_id, email) VALUES (%s, %s) RETURNING id", (org_id, email))
                    user_row = cur.fetchone()
                
                # Claim older submissions that matched this email but had no organization_id
                cur.execute("""
                    UPDATE submissions 
                    SET organization_id = %s 
                    WHERE email = %s AND organization_id IS NULL
                """, (org_id, email))
                
        conn.close()
    except Exception as e:
        logger.error(f"Error in verification database steps: {e}")
        raise HTTPException(status_code=500, detail="Database registration failed.")

    # Create 30-day session token
    exp = datetime.now(timezone.utc) + timedelta(days=30)
    session_token = jwt.encode({
        "email": email,
        "org_id": str(org_id),
        "exp": exp,
        "role": "org_member"
    }, JWT_SECRET, algorithm="HS256")
    
    return {
        "success": True,
        "token": session_token,
        "organization": {"id": str(org_id), "name": company_name},
        "email": email
    }

async def get_current_org_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "org_member":
            raise HTTPException(status_code=403, detail="Forbidden")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

@router.get("/dashboard")
async def get_org_dashboard(current_user: dict = Depends(get_current_org_user)):
    org_id = current_user.get("org_id")
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, designation, company_name, email, submitted_at,
                           overall_avg, overall_level, status,
                           lc_score, ro_score, we_score, be_score,
                           tm_score, ca_score, pc_score, sp_score
                    FROM submissions
                    WHERE organization_id = %s
                    ORDER BY submitted_at ASC
                """, (org_id,))
                submissions = cur.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Dashboard query failed: {e}")
        raise HTTPException(status_code=500, detail="Database query failed.")

    # Process and build history graph
    history = []
    current_level = "Foundational"
    last_audit_date = None
    
    for sub in submissions:
        submitted_at_iso = sub["submitted_at"].isoformat() if sub.get("submitted_at") else None
        history.append({
            "date": submitted_at_iso,
            "score": float(sub["overall_avg"]) if sub.get("overall_avg") else 0.0
        })
        current_level = sub["overall_level"]
        last_audit_date = submitted_at_iso

    return {
        "submissions": [dict(s) for s in submissions],
        "history": history,
        "current_level": current_level,
        "last_audit_date": last_audit_date
    }
