"""
routes.py — FastAPI route definitions
Ported from Azure Functions (function_app.py).
All routes are prefixed with /api via the router prefix in main.py.
"""

import logging
import os
import re
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from cachetools import TTLCache

from app.services.scoring_service import calculate_scores
from app.services.settings_service import (
    get_settings,
    get_sender_for_send,
    notify_admin_new_submission,
    send_acs_email,
    send_support_request,
    update_settings,
)
from app.services.user_service import add_user, get_users, remove_user, verify_user
from app.models.audit import AuditSubmission
from app.core.limiter import limiter
from app.core.security import audit_log

import jwt
from app.api.drafts import router as drafts_router
from app.api.org import router as org_router
from app.services.crm_service import sync_to_hubspot

router = APIRouter()
router.include_router(drafts_router)
router.include_router(org_router)

from app.core.config import JWT_SECRET

logger = logging.getLogger(__name__)

dashboard_cache = TTLCache(maxsize=100, ttl=60)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ.get("PGDATABASE", "nd_audit"),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", "5432"),
        sslmode="require",
    )


def serialize(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def strip_html(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</p>", "\n", text)
    text = re.sub(r"</li>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# POST /api/submit
# ---------------------------------------------------------------------------

@router.post("/submit", status_code=201)
@limiter.limit("5/hour")
async def submit(request: Request, payload: AuditSubmission, background_tasks: BackgroundTasks):
    data = payload.dict()

    scores = calculate_scores(data)

    # 1. Extract optional org token
    organization_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            token_payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            if token_payload.get("role") == "org_member":
                organization_id = token_payload.get("org_id")
        except Exception:
            pass

    import json
    dimension_scores_json = json.dumps(scores.get("dimension_scores", {}))

    insert_sql = """
        INSERT INTO submissions (
            name, designation, company_name, email, contact_number,
            q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,
            q15,q16,q17,q18,q19,q20,q21,q22,q23,q24,
            q25,q26,q27,q28,q29,q30,q31,q32,q33,q34,
            q35,q36,q37,q38,q39,q40,q41,q42,q43,q44,
            lc_score, lc_level, ro_score, ro_level,
            we_score, we_level, be_score, be_level,
            tm_score, tm_level, ca_score, ca_level,
            pc_score, pc_level, sp_score, sp_level,
            overall_avg, overall_level, email_body, status,
            consent_given, consent_timestamp, organization_id, dimension_scores
        ) VALUES (
            %(name)s, %(designation)s, %(company_name)s, %(email)s, %(contact_number)s,
            %(q5)s,%(q6)s,%(q7)s,%(q8)s,%(q9)s,%(q10)s,%(q11)s,%(q12)s,%(q13)s,%(q14)s,
            %(q15)s,%(q16)s,%(q17)s,%(q18)s,%(q19)s,%(q20)s,%(q21)s,%(q22)s,%(q23)s,%(q24)s,
            %(q25)s,%(q26)s,%(q27)s,%(q28)s,%(q29)s,%(q30)s,%(q31)s,%(q32)s,%(q33)s,%(q34)s,
            %(q35)s,%(q36)s,%(q37)s,%(q38)s,%(q39)s,%(q40)s,%(q41)s,%(q42)s,%(q43)s,%(q44)s,
            %(lc_score)s, %(lc_level)s, %(ro_score)s, %(ro_level)s,
            %(we_score)s, %(we_level)s, %(be_score)s, %(be_level)s,
            %(tm_score)s, %(tm_level)s, %(ca_score)s, %(ca_level)s,
            %(pc_score)s, %(pc_level)s, %(sp_score)s, %(sp_level)s,
            %(overall_avg)s, %(overall_level)s, %(email_body)s, 'pending',
            %(consent_given)s, %(consent_timestamp)s, %(organization_id)s, %(dimension_scores)s
        ) RETURNING id
    """

    params = {
        **scores,
        "name": data.get("name"),
        "designation": data.get("designation"),
        "company_name": data.get("company_name"),
        "email": data.get("email"),
        "contact_number": data.get("contact_number", None),
        "consent_given": data.get("consent_given", False),
        "consent_timestamp": data.get("consent_timestamp", datetime.now(timezone.utc)),
        "organization_id": organization_id,
        **{f"q{i}": data.get(f"q{i}") for i in range(5, 45)},
        "dimension_scores": dimension_scores_json,
    }

    crm_enabled = False
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(insert_sql, params)
                submission_id = cur.fetchone()[0]
                notify_admin_new_submission(cur, submission_id, data.get("name", ""), data.get("company_name", ""))
                
                # Update draft as submitted if draft_id is provided and is a valid UUID
                draft_id = data.get("draft_id")
                if draft_id and str(draft_id).strip() not in ("", "null", "undefined"):
                    try:
                        import uuid
                        uuid.UUID(str(draft_id))
                        cur.execute("UPDATE draft_submissions SET submitted = TRUE WHERE id = %s", (str(draft_id),))
                    except ValueError:
                        logger.warning("Invalid draft_id UUID: %s", draft_id)
                    
                # Check if CRM is enabled in settings
                cur.execute("SELECT crm_sync_enabled FROM app_settings WHERE id = 1")
                row = cur.fetchone()
                crm_enabled = bool(row[0]) if row else False
        conn.close()
    except Exception as e:
        logger.error("DB insert failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")
    
    if crm_enabled:
        background_tasks.add_task(sync_to_hubspot, data, scores, str(submission_id))
    
    if "dashboard" in dashboard_cache:
        del dashboard_cache["dashboard"]

    return {"success": True, "submission_id": str(submission_id)}


# ---------------------------------------------------------------------------
# GET /api/submissions
# ---------------------------------------------------------------------------

@router.get("/submissions")
async def get_submissions():
    if "dashboard" in dashboard_cache:
        return dashboard_cache["dashboard"]
        
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, designation, company_name, email, submitted_at,
                           overall_avg, overall_level, status
                    FROM submissions
                    ORDER BY submitted_at DESC
                """)
                rows = cur.fetchall()
        conn.close()
    except Exception as e:
        logger.error("DB query failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    result = []
    for row in rows:
        r = dict(row)
        if r.get("submitted_at"):
            r["submitted_at"] = r["submitted_at"].isoformat()
        if r.get("id"):
            r["id"] = str(r["id"])
        result.append(r)
        
    dashboard_cache["dashboard"] = result

    return result


# ---------------------------------------------------------------------------
# GET /api/submissions/{id}
# ---------------------------------------------------------------------------

@router.get("/submissions/{submission_id}")
async def get_submission(submission_id: UUID):
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM submissions WHERE id = %s", (str(submission_id),))
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("DB query failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    r = dict(row)
    for ts_field in ("submitted_at", "sent_at", "consent_timestamp"):
        if r.get(ts_field):
            r[ts_field] = r[ts_field].isoformat()
            
    if r.get("id"):
        r["id"] = str(r["id"])

    return r


# ---------------------------------------------------------------------------
# PUT /api/submissions/{id}/email
# ---------------------------------------------------------------------------

@router.put("/submissions/{submission_id}/email")
@audit_log("edit_email_draft")
async def update_email(request: Request, submission_id: UUID):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    email_body = body.get("email_body")
    if email_body is None:
        raise HTTPException(status_code=400, detail="Missing email_body")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE submissions SET email_body = %s WHERE id = %s",
                    (email_body, str(submission_id)),
                )
                if cur.rowcount == 0:
                    conn.close()
                    raise HTTPException(status_code=404, detail="Not found")
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("DB update failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    return {"success": True}


# ---------------------------------------------------------------------------
# POST /api/submissions/{id}/regenerate-email
# ---------------------------------------------------------------------------

@router.post("/submissions/{submission_id}/regenerate-email")
@audit_log("regenerate_email_draft")
async def regenerate_email(request: Request, submission_id: UUID):
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM submissions WHERE id = %s", (str(submission_id),))
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("DB query failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    if row.get("status") == "sent":
        raise HTTPException(status_code=409, detail="Cannot regenerate sent email")

    data = dict(row)
    scores = calculate_scores(data)
    new_email_body = scores.get("email_body")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE submissions SET email_body = %s WHERE id = %s",
                    (new_email_body, str(submission_id)),
                )
        conn.close()
    except Exception as e:
        logger.error("DB update failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    return {"success": True, "email_body": new_email_body}


# ---------------------------------------------------------------------------
# POST /api/submissions/{id}/send
# ---------------------------------------------------------------------------
import time

def send_acs_email_with_retry(payload: dict, max_attempts=3):
    delays = [1, 4, 16]
    for attempt in range(max_attempts):
        try:
            send_acs_email(**payload)
            return True
        except Exception as e:
            logger.error(f"ACS email failed attempt {attempt+1}: {e}")
            if attempt < max_attempts - 1:
                time.sleep(delays[attempt])
            else:
                logger.error(f"Permanent email failure after {max_attempts} attempts.")
                raise e

def process_email_dispatch(submission_id: str, payload: dict):
    try:
        send_acs_email_with_retry(payload)
        sent_at = datetime.now(timezone.utc)
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE submissions SET status = 'sent', sent_at = %s WHERE id = %s",
                    (sent_at, submission_id),
                )
        conn.close()
        
        if "dashboard" in dashboard_cache:
            del dashboard_cache["dashboard"]
            
    except Exception as e:
        logger.error(f"Async email failed: {e}")
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                import json
                cur.execute("""
                    INSERT INTO email_dlq (submission_id, payload, attempts, last_error) 
                    VALUES (%s, %s, 3, %s)
                """, (submission_id, json.dumps(payload), str(e)))
                cur.execute("UPDATE submissions SET status = 'failed' WHERE id = %s", (submission_id,))
        conn.close()

@router.post("/submissions/{submission_id}/send")
@audit_log("send_audit_report")
async def send_email_route(request: Request, submission_id: UUID, background_tasks: BackgroundTasks):
    sub_id_str = str(submission_id)
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT name, email, company_name, email_body, status FROM submissions WHERE id = %s",
                    (sub_id_str,),
                )
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("DB query failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    if row["status"] in ("sent", "sending"):
        raise HTTPException(status_code=409, detail="Already sent or sending")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                sender_address, sender_name = get_sender_for_send(cur)
        conn.close()
    except Exception as e:
        logger.error("Settings load failed: %s", e)
        sender_address = os.environ.get("ACS_SENDER_ADDRESS", "")
        sender_name = os.environ.get("ACS_SENDER_NAME", "Orchvate")

    payload = {
        "to_address": row["email"],
        "to_name": row["name"],
        "subject": f"Neurvex Audit Results — {row['company_name']}",
        "html": row["email_body"],
        "plain": strip_html(row["email_body"]),
        "sender_address": sender_address,
        "sender_name": sender_name,
    }

    # Transition to 'sending' immediately
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE submissions SET status = 'sending' WHERE id = %s", (sub_id_str,))
        conn.close()
    except Exception as e:
        logger.error("Failed to update status to sending: %s", e)

    background_tasks.add_task(process_email_dispatch, sub_id_str, payload)
    
    if "dashboard" in dashboard_cache:
        del dashboard_cache["dashboard"]

    return {"success": True, "status": "sending"}


# ---------------------------------------------------------------------------
# GET / PUT /api/settings
# ---------------------------------------------------------------------------

@router.get("/settings")
async def get_settings_route():
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                data = get_settings(cur)
        conn.close()
    except Exception as e:
        logger.error("Settings failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")
    return data


@router.put("/settings")
@audit_log("update_settings")
async def save_settings_route(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not body:
        raise HTTPException(status_code=400, detail="Empty body")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                data = update_settings(cur, body)
        conn.close()
    except Exception as e:
        logger.error("Settings update failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")
    return data


# ---------------------------------------------------------------------------
# POST /api/settings/notifications/toggle
# ---------------------------------------------------------------------------

@router.post("/settings/notifications/toggle")
@audit_log("toggle_notifications")
async def toggle_notifications(request: Request):
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                current = get_settings(cur)
                enabling = not current["notifications_enabled"]
                if enabling and not (current.get("notification_email") or "").strip():
                    raise HTTPException(
                        status_code=400,
                        detail="Set a notification email in Settings before enabling alerts.",
                    )
                data = update_settings(cur, {"notifications_enabled": enabling})
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Toggle notifications failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")
    return data


# ---------------------------------------------------------------------------
# POST /api/support
# ---------------------------------------------------------------------------

@router.post("/support")
@limiter.limit("5/hour")
async def support_request(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()
    subject = (body.get("subject") or "").strip()
    message = (body.get("message") or "").strip()

    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required")
    if not subject:
        raise HTTPException(status_code=400, detail="Subject is required")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                send_support_request(cur, name, email, subject, message)
        conn.close()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Support request failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to send support request")

    return {"success": True, "message": "Support request sent. We will get back to you soon."}


# ---------------------------------------------------------------------------
# POST /api/auth/verify
# ---------------------------------------------------------------------------

@router.post("/auth/verify")
async def auth_verify(request: Request):
    try:
        body = await request.json()
        email = (body.get("email") or "").strip().lower()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        conn = get_conn()
        res = verify_user(conn, email)
        conn.close()
        return res
    except Exception as e:
        logger.error("Verify user failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")


# ---------------------------------------------------------------------------
# RBAC: /api/manage/users
# ---------------------------------------------------------------------------

@router.get("/manage/users")
async def admin_users_list():
    try:
        conn = get_conn()
        users = get_users(conn)
        conn.close()
        for u in users:
            if u.get("created_at"):
                u["created_at"] = u["created_at"].isoformat()
        return users
    except Exception as e:
        logger.error("Admin users list failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manage/users")
@audit_log("add_user")
async def admin_user_add(request: Request):
    try:
        body = await request.json()
        email = (body.get("email") or "").strip().lower()
        role = (body.get("role") or "admin").strip().lower()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        conn = get_conn()
        new_user = add_user(conn, email, role)
        conn.close()
        if new_user.get("created_at"):
            new_user["created_at"] = new_user["created_at"].isoformat()
        return new_user
    except Exception as e:
        logger.error("Admin user add failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/manage/users/{email}")
@audit_log("delete_user")
async def admin_user_delete(request: Request, email: str):
    email = email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        conn = get_conn()
        deleted = remove_user(conn, email)
        conn.close()
        return {"success": deleted}
    except Exception as e:
        logger.error("Admin user delete failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /api/manage/audit-logs
# ---------------------------------------------------------------------------
@router.get("/manage/audit-logs")
async def get_audit_logs():
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100")
                rows = cur.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            r = dict(row)
            if r.get("timestamp"):
                r["timestamp"] = r["timestamp"].isoformat()
            if r.get("target_resource_id"):
                r["target_resource_id"] = str(r["target_resource_id"])
            result.append(r)
        return result
    except Exception as e:
        logger.error("Failed to fetch audit logs: %s", e)
        raise HTTPException(status_code=500, detail="Database error")
