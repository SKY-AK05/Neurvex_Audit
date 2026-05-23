"""
routes.py — FastAPI route definitions
Ported from Azure Functions (function_app.py).
All routes are prefixed with /api via the router prefix in main.py.
"""

import logging
import os
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

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

router = APIRouter()

logger = logging.getLogger(__name__)


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
async def submit(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    for field in ("name", "designation", "company_name", "email"):
        if not data.get(field):
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    scores = calculate_scores(data)

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
            overall_avg, overall_level, email_body, status
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
            %(overall_avg)s, %(overall_level)s, %(email_body)s, 'pending'
        ) RETURNING id
    """

    params = {
        "name": data.get("name"),
        "designation": data.get("designation"),
        "company_name": data.get("company_name"),
        "email": data.get("email"),
        "contact_number": data.get("contact_number", None),
        **{f"q{i}": data.get(f"q{i}") for i in range(5, 45)},
        **scores,
    }

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(insert_sql, params)
                submission_id = cur.fetchone()[0]
                notify_admin_new_submission(cur, submission_id, data.get("name", ""), data.get("company_name", ""))
        conn.close()
    except Exception as e:
        logger.error("DB insert failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    return {"success": True, "submission_id": submission_id}


# ---------------------------------------------------------------------------
# GET /api/submissions
# ---------------------------------------------------------------------------

@router.get("/submissions")
async def get_submissions():
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
        result.append(r)

    return result


# ---------------------------------------------------------------------------
# GET /api/submissions/{id}
# ---------------------------------------------------------------------------

@router.get("/submissions/{submission_id}")
async def get_submission(submission_id: int):
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM submissions WHERE id = %s", (submission_id,))
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("DB query failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    r = dict(row)
    for ts_field in ("submitted_at", "sent_at"):
        if r.get(ts_field):
            r[ts_field] = r[ts_field].isoformat()

    return r


# ---------------------------------------------------------------------------
# PUT /api/submissions/{id}/email
# ---------------------------------------------------------------------------

@router.put("/submissions/{submission_id}/email")
async def update_email(submission_id: int, request: Request):
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
                    (email_body, submission_id),
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
async def regenerate_email(submission_id: int):
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM submissions WHERE id = %s", (submission_id,))
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
                    (new_email_body, submission_id),
                )
        conn.close()
    except Exception as e:
        logger.error("DB update failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    return {"success": True, "email_body": new_email_body}


# ---------------------------------------------------------------------------
# POST /api/submissions/{id}/send
# ---------------------------------------------------------------------------

@router.post("/submissions/{submission_id}/send")
async def send_email_route(submission_id: int):
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT name, email, company_name, email_body, status FROM submissions WHERE id = %s",
                    (submission_id,),
                )
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("DB query failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    if row["status"] == "sent":
        raise HTTPException(status_code=409, detail="Already sent")

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

    try:
        send_acs_email(
            to_address=row["email"],
            to_name=row["name"],
            subject=f"Neurvex Audit Results — {row['company_name']}",
            html=row["email_body"],
            plain=strip_html(row["email_body"]),
            sender_address=sender_address,
            sender_name=sender_name,
        )
    except Exception as e:
        logger.error("ACS send failed: %s", e)
        raise HTTPException(status_code=500, detail="Email send failed")

    sent_at = datetime.now(timezone.utc)
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE submissions SET status = 'sent', sent_at = %s WHERE id = %s",
                    (sent_at, submission_id),
                )
        conn.close()
    except Exception as e:
        logger.error("DB status update failed: %s", e)
        raise HTTPException(status_code=500, detail="Email sent but DB update failed")

    return {"success": True, "sent_at": sent_at.isoformat()}


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
async def toggle_notifications():
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
        return users
    except Exception as e:
        logger.error("Admin users list failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manage/users")
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
        return new_user
    except Exception as e:
        logger.error("Admin user add failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/manage/users/{email}")
async def admin_user_delete(email: str):
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
