"""
function_app.py — Azure Functions for Neurvex Audit Tool
Routes:
  POST   /api/submit
  GET    /api/submissions
  PUT    /api/submissions/{id}/email
  POST   /api/submissions/{id}/send
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from decimal import Decimal

import azure.functions as func
import psycopg2
import psycopg2.extras
from app.services.scoring_service import calculate_scores
from app.services.settings_service import (
    get_settings,
    update_settings,
    get_sender_for_send,
    notify_admin_new_submission,
    send_acs_email,
    send_support_request,
)
from app.services.user_service import (
    verify_user,
    get_users,
    add_user,
    remove_user,
)

def strip_html(html: str) -> str:
    """Convert basic HTML to plain text for email sending."""
    text = re.sub(r'<br\s*/?>', '\n', html)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'</li>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# ---------------------------------------------------------------------------
# DB helpers
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


def json_response(body, status: int = 200) -> func.HttpResponse:
    def serializer(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    return func.HttpResponse(
        json.dumps(body, default=serializer),
        status_code=status,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


def options_response() -> func.HttpResponse:
    """Handle CORS preflight."""
    return func.HttpResponse(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )


# ---------------------------------------------------------------------------
# POST /api/submit
# ---------------------------------------------------------------------------

@app.route(route="submit", methods=["POST", "OPTIONS"])
def submit(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    try:
        data = req.get_json()
    except ValueError:
        return json_response({"error": "Invalid JSON"}, 400)

    # Validate required respondent fields
    for field in ("name", "designation", "company_name", "email"):
        if not data.get(field):
            return json_response({"error": f"Missing required field: {field}"}, 400)

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
                notify_admin_new_submission(
                    cur,
                    submission_id,
                    data.get("name", ""),
                    data.get("company_name", ""),
                )
        conn.close()
    except Exception as e:
        logging.error("DB insert failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    return json_response({"success": True, "submission_id": submission_id}, 201)


# ---------------------------------------------------------------------------
# GET /api/submissions
# ---------------------------------------------------------------------------

@app.route(route="submissions", methods=["GET", "OPTIONS"])
def get_submissions(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

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
        logging.error("DB query failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    # Convert datetime to ISO string for JSON serialisation
    result = []
    for row in rows:
        r = dict(row)
        if r.get("submitted_at"):
            r["submitted_at"] = r["submitted_at"].isoformat()
        result.append(r)

    return json_response(result)


# ---------------------------------------------------------------------------
# GET /api/submissions/{id}  — full detail for dashboard detail view
# ---------------------------------------------------------------------------

@app.route(route="submissions/{id}", methods=["GET", "OPTIONS"])
def get_submission(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    submission_id = req.route_params.get("id")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM submissions WHERE id = %s", (submission_id,))
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logging.error("DB query failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    if not row:
        return json_response({"error": "Not found"}, 404)

    r = dict(row)
    for ts_field in ("submitted_at", "sent_at"):
        if r.get(ts_field):
            r[ts_field] = r[ts_field].isoformat()

    return json_response(r)


# ---------------------------------------------------------------------------
# PUT /api/submissions/{id}/email
# ---------------------------------------------------------------------------

@app.route(route="submissions/{id}/email", methods=["PUT", "OPTIONS"])
def update_email(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    submission_id = req.route_params.get("id")

    try:
        body = req.get_json()
    except ValueError:
        return json_response({"error": "Invalid JSON"}, 400)

    email_body = body.get("email_body")
    if email_body is None:
        return json_response({"error": "Missing email_body"}, 400)

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
                    return json_response({"error": "Not found"}, 404)
        conn.close()
    except Exception as e:
        logging.error("DB update failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    return json_response({"success": True})


# ---------------------------------------------------------------------------
# POST /api/submissions/{id}/regenerate-email
# ---------------------------------------------------------------------------

@app.route(route="submissions/{id}/regenerate-email", methods=["POST", "OPTIONS"])
def regenerate_email(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    submission_id = req.route_params.get("id")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM submissions WHERE id = %s", (submission_id,))
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logging.error("DB query failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    if not row:
        return json_response({"error": "Not found"}, 404)

    if row.get("status") == "sent":
        return json_response({"error": "Cannot regenerate sent email"}, 409)

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
        logging.error("DB update failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    return json_response({"success": True, "email_body": new_email_body})


# ---------------------------------------------------------------------------
# POST /api/submissions/{id}/send
# ---------------------------------------------------------------------------

@app.route(route="submissions/{id}/send", methods=["POST", "OPTIONS"])
def send_email(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    submission_id = req.route_params.get("id")

    # Fetch submission
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
        logging.error("DB query failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    if not row:
        return json_response({"error": "Not found"}, 404)

    if row["status"] == "sent":
        return json_response({"error": "Already sent"}, 409)

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                sender_address, sender_name = get_sender_for_send(cur)
        conn.close()
    except Exception as e:
        logging.error("Settings load failed: %s", e)
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
        logging.error("ACS send failed: %s", e)
        return json_response({"error": "Email send failed"}, 500)

    # Update status
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
        logging.error("DB status update failed: %s", e)
        return json_response({"error": "Email sent but DB update failed"}, 500)

    return json_response({"success": True, "sent_at": sent_at.isoformat()})


# ---------------------------------------------------------------------------
# GET / PUT /api/settings
# ---------------------------------------------------------------------------

@app.route(route="settings", methods=["GET", "PUT", "OPTIONS"])
def settings(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                if req.method == "GET":
                    data = get_settings(cur)
                else:
                    try:
                        body = req.get_json()
                    except ValueError:
                        return json_response({"error": "Invalid JSON"}, 400)
                    if not body:
                        return json_response({"error": "Empty body"}, 400)
                    data = update_settings(cur, body)
        conn.close()
    except Exception as e:
        logging.error("Settings failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    return json_response(data)


# ---------------------------------------------------------------------------
# POST /api/settings/notifications/toggle
# ---------------------------------------------------------------------------

@app.route(route="settings/notifications/toggle", methods=["POST", "OPTIONS"])
def toggle_notifications(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                current = get_settings(cur)
                enabling = not current["notifications_enabled"]
                if enabling and not (current["notification_email"] or "").strip():
                    return json_response(
                        {
                            "error": "Set a notification email in Settings before enabling alerts.",
                        },
                        400,
                    )
                data = update_settings(
                    cur, {"notifications_enabled": enabling}
                )
        conn.close()
    except Exception as e:
        logging.error("Toggle notifications failed: %s", e)
        return json_response({"error": "Database error"}, 500)

    return json_response(data)


# ---------------------------------------------------------------------------
# POST /api/support
# ---------------------------------------------------------------------------

@app.route(route="support", methods=["POST", "OPTIONS"])
def support_request(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    try:
        body = req.get_json()
    except ValueError:
        return json_response({"error": "Invalid JSON"}, 400)

    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()
    subject = (body.get("subject") or "").strip()
    message = (body.get("message") or "").strip()

    if not name:
        return json_response({"error": "Name is required"}, 400)
    if not email or "@" not in email:
        return json_response({"error": "A valid email is required"}, 400)
    if not subject:
        return json_response({"error": "Subject is required"}, 400)
    if not message:
        return json_response({"error": "Message is required"}, 400)

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                send_support_request(cur, name, email, subject, message)
        conn.close()
    except ValueError as e:
        return json_response({"error": str(e)}, 400)
    except Exception as e:
        logging.error("Support request failed: %s", e)
        return json_response({"error": "Failed to send support request"}, 500)

    return json_response({
        "success": True,
        "message": "Support request sent. We will get back to you soon.",
    })

# ---------------------------------------------------------------------------
# POST /api/auth/verify
# ---------------------------------------------------------------------------
@app.route(route="auth/verify", methods=["POST", "OPTIONS"])
def auth_verify(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    try:
        body = req.get_json()
        email = (body.get("email") or "").strip().lower()
    except Exception:
        return json_response({"error": "Invalid request"}, 400)

    if not email:
        return json_response({"error": "Email is required"}, 400)

    try:
        conn = get_conn()
        res = verify_user(conn, email)
        conn.close()
        return json_response(res)
    except Exception as e:
        logging.error("Verify user failed: %s", e)
        return json_response({"error": "Database error"}, 500)

# ---------------------------------------------------------------------------
# RBAC: /api/admin/users
# ---------------------------------------------------------------------------
@app.route(route="manage/users", methods=["GET", "POST", "OPTIONS"])
def admin_users_list(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    try:
        conn = get_conn()
        
        if req.method == "GET":
            users = get_users(conn)
            conn.close()
            return json_response(users)

        if req.method == "POST":
            body = req.get_json()
            email = (body.get("email") or "").strip().lower()
            role = (body.get("role") or "admin").strip().lower()
            
            if not email:
                return json_response({"error": "Email is required"}, 400)
            
            new_user = add_user(conn, email, role)
            conn.close()
            return json_response(new_user)
            
    except Exception as e:
        logging.error("Admin users list failed: %s", e)
        return json_response({"error": str(e)}, 500)

@app.route(route="manage/users/{email}", methods=["DELETE", "OPTIONS"])
def admin_user_delete(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return options_response()

    email = req.route_params.get("email", "").strip().lower()
    if not email:
        return json_response({"error": "Email is required"}, 400)

    try:
        conn = get_conn()
        deleted = remove_user(conn, email)
        conn.close()
        return json_response({"success": deleted})
    except Exception as e:
        logging.error("Admin user delete failed: %s", e)
        return json_response({"error": str(e)}, 500)
