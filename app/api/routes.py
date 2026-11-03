"""
routes.py — FastAPI route definitions
Ported from Azure Functions (function_app.py).
All routes are prefixed with /api via the router prefix in main.py.
"""

import hashlib
import json
import logging
import math
import os
import re
import threading
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
import uuid as uuid_pkg

from cachetools import TTLCache
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import jwt
import psycopg2
import psycopg2.extras

from app.api.drafts import router as drafts_router
from app.api.org import router as org_router
from app.api.orgs import router as orgs_router
from app.api.public import router as public_router
from app.core.authorization import (
    get_user_from_request,
    filter_submissions_by_org_access,
    check_submission_access,
    get_admin_organizations,
    require_admin,
    require_super_admin,
)
from app.core.config import JWT_SECRET
from app.core.database import get_conn, get_db_connection, get_db_transaction
from app.core.limiter import limiter
from app.core.security import audit_log
from app.models.audit import AuditSubmission
from app.services.crm_service import sync_to_hubspot
from app.services.filter_service import (
    build_filter_query,
    ALLOWED_FILTER_FIELDS,
    ALLOWED_SORT_FIELDS,
)
from app.services.scoring_service import calculate_scores, calculate_scores_pure, get_form_sections_metadata, build_email
from app.services.settings_service import (
    get_settings,
    get_sender_for_send,
    notify_admin_new_submission,
    send_acs_email,
    send_support_request,
    update_settings,
)
from app.services.user_service import add_user, get_users, remove_user, verify_user
from app.utils.helpers import to_iso_utc

logger = logging.getLogger(__name__)

router = APIRouter()
router.include_router(drafts_router)
router.include_router(org_router)
router.include_router(orgs_router)
router.include_router(public_router)

# Organization-aware dashboard cache: keys are (admin_email, org_filter_hash)
# TTL of 60 seconds to balance performance and data freshness
dashboard_cache = TTLCache(maxsize=500, ttl=60)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def serialize(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return to_iso_utc(obj)
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


def _bg_notify_admin(submission_id: str, name: str, company_name: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                notify_admin_new_submission(cur, submission_id, name, company_name)
    except Exception as e:
        logger.error(f"Failed to send admin notification for submission {submission_id}: {e}")


# ---------------------------------------------------------------------------
# POST /api/submit
# ---------------------------------------------------------------------------

@router.post("/submit", status_code=201)
@limiter.limit("100/hour")  # Per IP - allows shared office IPs
@limiter.limit("1000/day")  # Daily safety limit per IP
def submit(request: Request, payload: AuditSubmission, background_tasks: BackgroundTasks):
    data = payload.dict()
    idempotency_key = data.get("idempotency_key")
    if idempotency_key:
        idempotency_key = str(idempotency_key).strip() or None

    # Step 1: Pre-compute pure scores BEFORE borrowing any database connection (CALC-001 through CALC-006)
    sections, threshold = get_form_sections_metadata(None)
    scores = calculate_scores_pure(data, sections=sections, threshold=threshold)

    # Step 2: Open single pooled connection for atomic short transaction
    with get_db_connection() as conn:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Idempotency fast-path: check if already committed
                if idempotency_key:
                    cur.execute(
                        "SELECT id FROM submissions WHERE idempotency_key = %s LIMIT 1",
                        (idempotency_key,)
                    )
                    existing = cur.fetchone()
                    if existing:
                        logger.info("Idempotent replay detected for key %s, returning submission %s", idempotency_key, existing["id"])
                        return {"success": True, "submission_id": str(existing["id"])}

                # Email-based duplicate detection (5-minute window)
                email = data.get("email")
                if email:
                    try:
                        cur.execute("""
                            SELECT id FROM submissions 
                            WHERE LOWER(TRIM(email)) = LOWER(TRIM(%s))
                            AND submitted_at > NOW() - INTERVAL '5 minutes'
                            LIMIT 1
                        """, (email,))
                        recent = cur.fetchone()
                        if recent:
                            raise HTTPException(
                                status_code=429,
                                detail="A submission from this email was received recently. Please wait a few minutes before submitting again."
                            )
                    except HTTPException:
                        raise
                    except Exception as e:
                        logger.warning(f"Duplicate check failed: {e}")

                organization_id = None
                invitation_id = None
                submission_source = "DIRECT"
                resolved_company_name = (data.get("company_name") or "").strip()

                # 1. Check for Invitation Token (Method B)
                raw_inv_token = (data.get("invitation_token") or "").strip()
                if raw_inv_token:
                    token_hash = hashlib.sha256(raw_inv_token.encode("utf-8")).hexdigest()
                    try:
                        cur.execute("""
                            SELECT oi.id, oi.organization_id, oi.is_active, oi.expires_at, oi.max_submissions,
                                   oi.submission_count, oi.revoked_at,
                                   o.name AS org_name, o.is_active AS org_active, o.is_deleted AS org_deleted
                            FROM organization_invitations oi
                            JOIN organizations o ON o.id = oi.organization_id
                            WHERE oi.token_hash = %s
                        """, (token_hash,))
                        inv_record = cur.fetchone()
                    except Exception as e:
                        logger.error("Failed to query invitation record: %s", e)
                        raise HTTPException(status_code=500, detail="Database error verifying invitation")

                    if not inv_record:
                        raise HTTPException(status_code=400, detail="Invalid invitation link.")
                    if inv_record["org_deleted"] or not inv_record["org_active"]:
                        raise HTTPException(status_code=400, detail="The organization associated with this invitation is inactive.")

                    if not inv_record["is_active"] or inv_record["revoked_at"] is not None:
                        raise HTTPException(status_code=400, detail="This invitation link has been revoked or deactivated.")
                    now = datetime.now(timezone.utc)
                    if inv_record["expires_at"] and inv_record["expires_at"] < now:
                        raise HTTPException(status_code=400, detail="This invitation link has expired.")
                    if inv_record["max_submissions"] is not None and inv_record["submission_count"] >= inv_record["max_submissions"]:
                        raise HTTPException(status_code=400, detail="This invitation has reached its submission limit.")

                    # Derive organization strictly on server
                    organization_id = str(inv_record["organization_id"])
                    invitation_id = str(inv_record["id"])
                    resolved_company_name = inv_record["org_name"]
                    submission_source = "INVITATION"

                else:
                    # 2. Normal Website Access (Method A)
                    req_org_id = data.get("organization_id")
                    auth_header = request.headers.get("Authorization")
                    if not req_org_id and auth_header and auth_header.startswith("Bearer "):
                        token = auth_header.split(" ")[1]
                        try:
                            token_payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                            if token_payload.get("role") == "org_member":
                                req_org_id = token_payload.get("org_id")
                        except Exception:
                            pass

                    if req_org_id:
                        try:
                            cur.execute("""
                                SELECT id, name, is_active, is_deleted
                                FROM organizations
                                WHERE id = %s AND is_deleted = FALSE AND is_active = TRUE
                            """, (str(req_org_id),))
                            org_row = cur.fetchone()
                        except Exception as e:
                            logger.error("Failed to query organisation: %s", e)
                            raise HTTPException(status_code=500, detail="Database error verifying organisation")

                        if not org_row:
                            raise HTTPException(status_code=400, detail="Selected organisation is invalid or inactive.")

                        organization_id = str(org_row["id"])
                        resolved_company_name = org_row["name"]
                        submission_source = "DIRECT"
                    elif resolved_company_name:
                        clean_name = " ".join(resolved_company_name.split())
                        
                        # Narrow advisory lock Option A: taken ONLY right here for org lookup/create
                        try:
                            cur.execute(
                                "SELECT pg_advisory_xact_lock(hashtext(lower(trim(%s))))",
                                (clean_name,)
                            )
                            cur.execute("""
                                SELECT id, name
                                FROM organizations
                                WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s)) AND is_deleted = FALSE
                            """, (clean_name,))
                            org_row = cur.fetchone()

                            if org_row:
                                organization_id = str(org_row["id"])
                                resolved_company_name = org_row["name"]
                                submission_source = "DIRECT"
                            else:
                                cur.execute("""
                                    INSERT INTO organizations (name, is_active, is_deleted, approval_status)
                                    VALUES (%s, TRUE, FALSE, 'approved')
                                    RETURNING id, name
                                """, (clean_name,))
                                new_org = cur.fetchone()
                                organization_id = str(new_org["id"])
                                resolved_company_name = new_org["name"]
                                submission_source = "DIRECT"
                                logger.info(f"Auto-created organisation: {resolved_company_name} (ID: {organization_id})")
                        except Exception as e:
                            logger.error("Failed to lookup or create organisation: %s", e)
                            raise HTTPException(status_code=500, detail="Failed to resolve organisation")
                    else:
                        raise HTTPException(status_code=400, detail="Organisation name is required.")

                dimension_scores_json = json.dumps(scores.get("dimension_scores", {}))

                insert_sql = """
                    INSERT INTO submissions (
                        name, designation, company_name, email, contact_number,
                        has_physical_workspace, has_suppliers,
                        q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,
                        q15,q16,q17,q18,q19,q20,q21,q22,q23,q24,
                        q25,q26,q27,q28,q29,q30,q31,q32,q33,q34,
                        q35,q36,q37,q38,q39,q40,q41,q42,q43,q44,
                        lc_score, lc_level, ro_score, ro_level,
                        we_score, we_level, be_score, be_level,
                        tm_score, tm_level, ca_score, ca_level,
                        pc_score, pc_level, sp_score, sp_level,
                        overall_avg, overall_level, email_body, status,
                        consent_given, consent_timestamp, organization_id,
                        submission_source, invitation_id, dimension_scores, answers,
                        idempotency_key
                    ) VALUES (
                        %(name)s, %(designation)s, %(company_name)s, %(email)s, %(contact_number)s,
                        %(has_physical_workspace)s, %(has_suppliers)s,
                        %(q5)s,%(q6)s,%(q7)s,%(q8)s,%(q9)s,%(q10)s,%(q11)s,%(q12)s,%(q13)s,%(q14)s,
                        %(q15)s,%(q16)s,%(q17)s,%(q18)s,%(q19)s,%(q20)s,%(q21)s,%(q22)s,%(q23)s,%(q24)s,
                        %(q25)s,%(q26)s,%(q27)s,%(q28)s,%(q29)s,%(q30)s,%(q31)s,%(q32)s,%(q33)s,%(q34)s,
                        %(q35)s,%(q36)s,%(q37)s,%(q38)s,%(q39)s,%(q40)s,%(q41)s,%(q42)s,%(q43)s,%(q44)s,
                        %(lc_score)s, %(lc_level)s, %(ro_score)s, %(ro_level)s,
                        %(we_score)s, %(we_level)s, %(be_score)s, %(be_level)s,
                        %(tm_score)s, %(tm_level)s, %(ca_score)s, %(ca_level)s,
                        %(pc_score)s, %(pc_level)s, %(sp_score)s, %(sp_level)s,
                        %(overall_avg)s, %(overall_level)s, %(email_body)s, 'pending',
                        %(consent_given)s, %(consent_timestamp)s, %(organization_id)s,
                        %(submission_source)s, %(invitation_id)s, %(dimension_scores)s, %(answers)s,
                        %(idempotency_key)s
                    )
                    ON CONFLICT (idempotency_key) WHERE idempotency_key IS NOT NULL DO NOTHING
                    RETURNING id
                """

                sanitized_scores = {k: (None if v == "NA" else v) for k, v in scores.items()}

                excluded_fields = {
                    "name", "designation", "company_name", "email", "contact_number",
                    "has_physical_workspace", "has_suppliers", "consent_given", "draft_id",
                    "organization_id", "invitation_token", "submission_source", "invitation_id", "idempotency_key"
                }
                dynamic_answers = {k: v for k, v in data.items() if k not in excluded_fields}

                params = {
                    **sanitized_scores,
                    "name": data.get("name") or "",
                    "designation": data.get("designation") or data.get("role") or "",
                    "company_name": resolved_company_name,
                    "email": data.get("email"),
                    "contact_number": data.get("contact_number", None),
                    "has_physical_workspace": data.get("has_physical_workspace") or None,
                    "has_suppliers": data.get("has_suppliers") or None,
                    "consent_given": data.get("consent_given", False),
                    "consent_timestamp": data.get("consent_timestamp", datetime.now(timezone.utc)),
                    "organization_id": organization_id,
                    "submission_source": submission_source,
                    "invitation_id": invitation_id,
                    "email_body": None,  # Offloaded to background worker
                    "idempotency_key": idempotency_key,
                    **{f"q{i}": data.get(f"q{i}") for i in range(5, 45)},
                    "dimension_scores": dimension_scores_json,
                    "answers": json.dumps(dynamic_answers),
                }

                try:
                    cur.execute(insert_sql, params)
                    sub_row = cur.fetchone()
                except Exception as ins_err:
                    logger.error("DB insert failed: %s", ins_err)
                    raise HTTPException(status_code=500, detail="Database error")

                if not sub_row:
                    if idempotency_key:
                        cur.execute("SELECT id FROM submissions WHERE idempotency_key = %s LIMIT 1", (idempotency_key,))
                        conflict_row = cur.fetchone()
                        if conflict_row:
                            conf_id = conflict_row["id"] if isinstance(conflict_row, dict) else conflict_row[0]
                            logger.info("Concurrent idempotency conflict resolved cleanly for key %s -> submission %s", idempotency_key, conf_id)
                            return {"success": True, "submission_id": str(conf_id)}
                    logger.error("Insert returned no ID and idempotency key resolution failed")
                    raise HTTPException(status_code=500, detail="Database error")

                submission_id = sub_row["id"] if isinstance(sub_row, dict) else sub_row[0]

                # If invitation submission, atomically increment counter
                if invitation_id:
                    cur.execute("""
                        UPDATE organization_invitations
                        SET submission_count = submission_count + 1
                        WHERE id = %s
                    """, (str(invitation_id),))

                # Enqueue non-blocking admin notification
                background_tasks.add_task(_bg_notify_admin, str(submission_id), data.get("name", ""), resolved_company_name)

                # Update draft as submitted if draft_id is provided
                draft_id = data.get("draft_id")
                if draft_id and str(draft_id).strip() not in ("", "null", "undefined"):
                    try:
                        uuid_pkg.UUID(str(draft_id))
                        cur.execute("UPDATE draft_submissions SET submitted = TRUE WHERE id = %s", (str(draft_id),))
                    except ValueError:
                        logger.warning("Invalid draft_id UUID: %s", draft_id)

                # Link to org_submission_links
                if organization_id:
                    try:
                        cur.execute("""
                            INSERT INTO org_submission_links (org_id, submission_id, weight, linked_by)
                            VALUES (%s, %s, 1.0, NULL)
                            ON CONFLICT (org_id, submission_id) DO NOTHING
                        """, (str(organization_id), str(submission_id)))
                    except Exception as link_err:
                        logger.warning("org_submission_links insert skipped: %s", link_err)

                # Check if CRM is enabled in settings
                cur.execute("SELECT crm_sync_enabled FROM app_settings WHERE id = 1")
                row = cur.fetchone()
                crm_enabled = bool((row.get("crm_sync_enabled") if isinstance(row, dict) else row[0]) if row else False)

                # Enqueue post-submit jobs for email & crm
                email_job_payload = json.dumps({
                    "email": data.get("email"),
                    "name": data.get("name", ""),
                    "company_name": resolved_company_name,
                    "designation": data.get("designation") or data.get("role") or "",
                    "contact_number": data.get("contact_number")
                })
                cur.execute("""
                    INSERT INTO post_submit_jobs (submission_id, job_type, payload)
                    VALUES (%s, 'email', %s)
                    ON CONFLICT (submission_id, job_type) DO NOTHING
                """, (str(submission_id), email_job_payload))

                if crm_enabled:
                    crm_job_payload = json.dumps({
                        "data": data,
                        "score_data": scores
                    })
                    cur.execute("""
                        INSERT INTO post_submit_jobs (submission_id, job_type, payload)
                        VALUES (%s, 'crm', %s)
                        ON CONFLICT (submission_id, job_type) DO NOTHING
                    """, (str(submission_id), crm_job_payload))

    dashboard_cache.clear()

    return {"success": True, "submission_id": str(submission_id)}


# ---------------------------------------------------------------------------
# GET /api/submissions
# ---------------------------------------------------------------------------

@router.get("/submissions")
def get_submissions(request: Request):
    user = require_admin(request)
    admin_email = user["email"]
    admin_role = user["role"]

    cache_key_data = f"{admin_email}:{admin_role}"
    cache_key = hashlib.md5(cache_key_data.encode()).hexdigest()

    if cache_key in dashboard_cache:
        return dashboard_cache[cache_key]

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT id, name, designation, company_name, email, contact_number, submitted_at,
                           overall_avg, overall_level, status, answers, organization_id,
                           submission_source, invitation_id,
                           lc_score, lc_level, ro_score, ro_level,
                           we_score, we_level, be_score, be_level,
                           tm_score, tm_level, ca_score, ca_level,
                           pc_score, pc_level, sp_score, sp_level
                    FROM submissions
                    ORDER BY submitted_at DESC
                """
                cur.execute(query)
                rows = cur.fetchall()
    except Exception as e:
        logger.error("DB query failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    result = []
    for row in rows:
        r = dict(row)
        if r.get("submitted_at"):
            r["submitted_at"] = to_iso_utc(r["submitted_at"])
        if r.get("id"):
            r["id"] = str(r["id"])
        if r.get("organization_id"):
            r["organization_id"] = str(r["organization_id"])
        if r.get("invitation_id"):
            r["invitation_id"] = str(r["invitation_id"])
        if r.get("submission_source") is None:
            r["submission_source"] = "DIRECT"

        if r.get("overall_avg") is not None:
            r["overall_avg"] = float(r["overall_avg"])
        for score_key in ("lc_score", "ro_score", "we_score", "be_score", "tm_score", "ca_score", "pc_score", "sp_score"):
            if r.get(score_key) is not None:
                r[score_key] = float(r[score_key])

        if r.get("answers"):
            answers = r["answers"]
            if isinstance(answers, str):
                try:
                    answers = json.loads(answers)
                    r["answers"] = answers
                except Exception:
                    answers = {}
            demographic_fields = [
                "function", "function_other", "country", "state_ut",
                "role", "gender", "gender_other",
                "is_pwd", "is_neurodivergent", "is_marginalized"
            ]
            for field in demographic_fields:
                if isinstance(answers, dict) and field in answers and field not in r:
                    r[field] = answers[field]

        result.append(r)

    dashboard_cache[cache_key] = result
    return result


# ---------------------------------------------------------------------------
# POST /api/submissions/filter — ServiceNow-Style Advanced Filter Execution
# ---------------------------------------------------------------------------

@router.post("/submissions/filter")
async def filter_submissions(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    filter_groups = body.get("filter_groups", [])
    sort_by = body.get("sort_by", [])
    page = body.get("page", 1)
    per_page = body.get("per_page", 10)

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

    if not organization_id:
        require_admin(request)

    try:
        data_sql, count_sql, params, summary = build_filter_query(
            filter_groups=filter_groups,
            sort_by=sort_by,
            page=page,
            per_page=per_page,
            organization_id=organization_id,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(count_sql, params)
                count_row = cur.fetchone()
                total = count_row["count"] if count_row else 0

                cur.execute(data_sql, params)
                rows = cur.fetchall()
    except Exception as e:
        logger.error("Filter query failed: %s", e)
        raise HTTPException(status_code=500, detail="Database query error")

    items = []
    for row in rows:
        r = dict(row)
        if r.get("submitted_at"):
            r["submitted_at"] = to_iso_utc(r["submitted_at"])
        if r.get("id"):
            r["id"] = str(r["id"])
        if r.get("organization_id"):
            r["organization_id"] = str(r["organization_id"])
        if r.get("invitation_id"):
            r["invitation_id"] = str(r["invitation_id"])
        if r.get("submission_source") is None:
            r["submission_source"] = "DIRECT"
        if r.get("overall_avg") is not None:
            r["overall_avg"] = float(r["overall_avg"])
        for score_key in ("lc_score", "ro_score", "we_score", "be_score", "tm_score", "ca_score", "pc_score", "sp_score"):
            if r.get(score_key) is not None:
                r[score_key] = float(r[score_key])

        if r.get("answers"):
            answers = r["answers"]
            demographic_fields = ["function", "country", "role", "gender", "is_neurodivergent"]
            for field in demographic_fields:
                if field in answers and field not in r:
                    r[field] = answers[field]

        items.append(r)

    limit = max(1, min(100, int(per_page)))
    total_pages = max(1, math.ceil(total / limit))

    return {
        "items": items,
        "total": total,
        "page": int(page),
        "per_page": limit,
        "total_pages": total_pages,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Saved Filters API: CRUD for reusable ServiceNow-style filters
# ---------------------------------------------------------------------------

DEFAULT_SYSTEM_SAVED_FILTERS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "All Submissions",
        "description": "Default view showing all submissions ordered by date",
        "filter_config": {"filter_groups": [], "sort_by": [{"field": "submitted_at", "direction": "desc"}]},
        "created_by": "system",
        "is_shared": True,
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Pending Review",
        "description": "Submissions pending email review and delivery",
        "filter_config": {"filter_groups": [{"logical_operator": "AND", "conditions": [{"field": "status", "operator": "is", "value": "pending"}]}], "sort_by": [{"field": "submitted_at", "direction": "desc"}]},
        "created_by": "system",
        "is_shared": True,
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "name": "Delivered Reports",
        "description": "Submissions with delivered audit reports",
        "filter_config": {"filter_groups": [{"logical_operator": "AND", "conditions": [{"field": "status", "operator": "is", "value": "sent"}]}], "sort_by": [{"field": "submitted_at", "direction": "desc"}]},
        "created_by": "system",
        "is_shared": True,
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "name": "High Maturity (Developing)",
        "description": "Organisations achieving developing maturity stage (score >= 15)",
        "filter_config": {"filter_groups": [{"logical_operator": "AND", "conditions": [{"field": "overall_avg", "operator": "greater_than_or_equal", "value": "15"}]}], "sort_by": [{"field": "overall_avg", "direction": "desc"}]},
        "created_by": "system",
        "is_shared": True,
    },
    {
        "id": "55555555-5555-5555-5555-555555555555",
        "name": "Foundational Priority",
        "description": "Organisations in foundational stage needing support (score <= 6)",
        "filter_config": {"filter_groups": [{"logical_operator": "AND", "conditions": [{"field": "overall_avg", "operator": "less_than_or_equal", "value": "6"}]}], "sort_by": [{"field": "overall_avg", "direction": "asc"}]},
        "created_by": "system",
        "is_shared": True,
    },
]

@router.get("/submissions/saved-filters")
async def list_saved_filters(request: Request):
    require_admin(request)
    admin_email = getattr(request.state, "admin_email", "system")
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables WHERE table_name = 'saved_filters'
                    )
                """)
                table_exists = cur.fetchone()["exists"]
                if not table_exists:
                    return DEFAULT_SYSTEM_SAVED_FILTERS

                cur.execute("""
                    SELECT id, name, description, filter_config, created_by, is_shared, created_at, updated_at
                    FROM saved_filters
                    WHERE is_shared = TRUE OR LOWER(created_by) = LOWER(%s)
                    ORDER BY (created_by = 'system') DESC, name ASC
                """, (admin_email,))
                rows = cur.fetchall()

        result = []
        for r in rows:
            item = dict(r)
            if item.get("id"):
                item["id"] = str(item["id"])
            if item.get("created_at"):
                item["created_at"] = to_iso_utc(item["created_at"])
            if item.get("updated_at"):
                item["updated_at"] = to_iso_utc(item["updated_at"])
            result.append(item)
        return result if result else DEFAULT_SYSTEM_SAVED_FILTERS
    except Exception as e:
        logger.warning("Could not fetch saved filters from DB (%s); returning presets", e)
        return DEFAULT_SYSTEM_SAVED_FILTERS


@router.post("/submissions/saved-filters")
async def create_saved_filter(request: Request):
    require_admin(request)
    admin_email = getattr(request.state, "admin_email", "admin")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Filter name is required")

    filter_config = body.get("filter_config") or {}
    description = (body.get("description") or "").strip()
    is_shared = bool(body.get("is_shared", True))
    filter_config_json = json.dumps(filter_config)

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS saved_filters (
                            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            name          VARCHAR(255) NOT NULL,
                            description   TEXT,
                            filter_config JSONB NOT NULL,
                            created_by    VARCHAR(255) NOT NULL DEFAULT 'admin',
                            is_shared     BOOLEAN NOT NULL DEFAULT TRUE,
                            created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """)
                    cur.execute("""
                        INSERT INTO saved_filters (name, description, filter_config, created_by, is_shared)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id, name, description, filter_config, created_by, is_shared, created_at
                    """, (name, description, filter_config_json, admin_email, is_shared))
                    new_row = dict(cur.fetchone())

        if new_row.get("id"):
            new_row["id"] = str(new_row["id"])
        if new_row.get("created_at"):
            new_row["created_at"] = to_iso_utc(new_row["created_at"])
        return new_row
    except Exception as e:
        logger.error("Failed to save filter: %s", e)
        raise HTTPException(status_code=500, detail="Database error saving filter")


@router.delete("/submissions/saved-filters/{filter_id}")
async def delete_saved_filter(request: Request, filter_id: str):
    require_admin(request)
    admin_email = getattr(request.state, "admin_email", "admin")
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM saved_filters
                        WHERE id = %s AND (created_by = %s OR created_by != 'system')
                    """, (filter_id, admin_email))
                    deleted = cur.rowcount > 0
        if not deleted:
            raise HTTPException(status_code=404, detail="Saved filter not found or cannot be deleted")
        return {"success": True, "message": "Saved filter deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete saved filter: %s", e)
        raise HTTPException(status_code=500, detail="Database error")


# ---------------------------------------------------------------------------
# GET /api/submissions/{id} — Safely fetch single submission with IDOR validation
# ---------------------------------------------------------------------------

@router.get("/submissions/{submission_id}")
async def get_submission(request: Request, submission_id: str):
    sub_id = str(submission_id).strip()

    try:
        uuid_pkg.UUID(sub_id)
    except (ValueError, AttributeError):
        if not sub_id.isdigit():
            raise HTTPException(status_code=400, detail="Invalid submission ID format. Must be a valid UUID or integer.")

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM submissions WHERE id = %s", (sub_id,))
                row = cur.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Submission not found")

            # Check if caller is org_member (enforce tenant isolation)
            auth_header = request.headers.get("Authorization")
            is_org_member = False
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    token_payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                    if token_payload.get("role") == "org_member":
                        is_org_member = True
                        user_org_id = str(token_payload.get("org_id", ""))
                        sub_org_id = str(row.get("organization_id") or "")
                        if not user_org_id or user_org_id != sub_org_id:
                            raise HTTPException(status_code=403, detail="Forbidden: You do not have permission to view this submission.")
                except jwt.PyJWTError:
                    pass

            # If not org_member, require admin
            if not is_org_member:
                require_admin(request)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("DB query failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    r = dict(row)
    for ts_field in ("submitted_at", "sent_at", "consent_timestamp"):
        if r.get(ts_field):
            r[ts_field] = to_iso_utc(r[ts_field])

    if r.get("id"):
        r["id"] = str(r["id"])
    if r.get("organization_id"):
        r["organization_id"] = str(r["organization_id"])
    if r.get("invitation_id"):
        r["invitation_id"] = str(r["invitation_id"])
    if r.get("submission_source") is None:
        r["submission_source"] = "DIRECT"

    if r.get("answers"):
        answers = r["answers"]
        demographic_fields = ["function", "function_other", "country", "state_ut", "role", 
                              "gender", "gender_other", "is_pwd", "is_neurodivergent", "is_marginalized"]
        for field in demographic_fields:
            if field in answers and field not in r:
                r[field] = answers[field]

    return r


# ---------------------------------------------------------------------------
# PATCH /api/submissions/{id}/respondent - Update respondent information
# ---------------------------------------------------------------------------

@router.patch("/submissions/{submission_id}/respondent")
@audit_log("edit_respondent_info")
async def update_respondent(request: Request, submission_id: str):
    require_admin(request)
    sub_id = str(submission_id).strip()
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    allowed_fields = ["name", "email", "company_name", "contact_number", "designation"]
    updates = {k: v for k, v in body.items() if k in allowed_fields}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    try:
        with get_db_connection() as conn:
            set_clause = ", ".join([f"{k} = %({k})s" for k in updates.keys()])
            sql = f"UPDATE submissions SET {set_clause} WHERE id = %(submission_id)s"
            params = {**updates, "submission_id": sub_id}

            with conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    if cur.rowcount == 0:
                        raise HTTPException(status_code=404, detail="Submission not found")

        dashboard_cache.clear()
        return {"message": "Respondent information updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update respondent: %s", e)
        raise HTTPException(status_code=500, detail="Database error")


# ---------------------------------------------------------------------------
# PATCH /api/submissions/{id}/scores - Update score values
# ---------------------------------------------------------------------------

@router.patch("/submissions/{submission_id}/scores")
@audit_log("edit_submission_scores")
async def update_submission_scores(request: Request, submission_id: str):
    require_admin(request)
    sub_id = str(submission_id).strip()
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    score_keys = ["lc_score", "ro_score", "we_score", "be_score", "tm_score", "ca_score", "pc_score", "sp_score"]
    updates = {}
    valid_scores = []

    for k in score_keys:
        if k in body:
            val = body[k]
            if val is None or val == "NA" or val == "":
                updates[k] = None
            else:
                try:
                    fval = round(float(val), 2)
                    if 0 <= fval <= 20:
                        updates[k] = fval
                        valid_scores.append(fval)
                    else:
                        raise HTTPException(status_code=400, detail=f"Score {k} must be between 0 and 20")
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail=f"Invalid score value for {k}")

    if not updates and "overall_avg" not in body:
        raise HTTPException(status_code=400, detail="No valid score fields provided to update")

    def _calc_level(score):
        r = round(score)
        if r <= 6:
            return "Level 1 — Foundational"
        elif r <= 14:
            return "Level 2 — Early Progress"
        else:
            return "Level 3 — Developing"

    # Compute overall_avg if not explicitly provided
    if "overall_avg" in body and body["overall_avg"] is not None:
        try:
            overall_avg = round(float(body["overall_avg"]), 2)
        except (ValueError, TypeError):
            overall_avg = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0.0
    elif valid_scores:
        overall_avg = round(sum(valid_scores) / len(valid_scores), 2)
    else:
        overall_avg = 0.0

    updates["overall_avg"] = overall_avg
    overall_level = body.get("overall_level") or _calc_level(overall_avg)
    updates["overall_level"] = overall_level

    # Update individual pillar levels
    for k in score_keys:
        if k in updates:
            if updates[k] is not None:
                updates[f"{k[:2]}_level"] = _calc_level(updates[k])
            else:
                updates[f"{k[:2]}_level"] = "Not applicable"

    try:
        with get_db_connection() as conn:
            set_clause = ", ".join([f"{k} = %({k})s" for k in updates.keys()])
            sql = f"UPDATE submissions SET {set_clause} WHERE id = %(submission_id)s"
            params = {**updates, "submission_id": sub_id}

            with conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    if cur.rowcount == 0:
                        raise HTTPException(status_code=404, detail="Submission not found")

        dashboard_cache.clear()
        return {
            "message": "Scores updated successfully",
            "scores": updates
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update scores: %s", e)
        raise HTTPException(status_code=500, detail="Database error")


# ---------------------------------------------------------------------------
# PATCH /api/submissions/{id}/organisation
# ---------------------------------------------------------------------------

@router.patch("/submissions/{submission_id}/organisation")
@audit_log("reassign_submission_organisation")
async def reassign_submission_organisation(request: Request, submission_id: str):
    """
    Reassign a submission to a different organisation.
    Updates both submissions.organization_id AND submissions.company_name.
    Updates org_submission_links table.
    Creates audit trail in submission_reassignments table.
    Both Normal Admin and Super Admin have global access to reassign between any organisations.
    """
    user = require_admin(request)
    admin_email = user["email"]
    admin_user_id = getattr(request.state, "user_id", admin_email) or admin_email

    sub_id = str(submission_id).strip()

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    new_org_id = body.get("organization_id")
    reason = body.get("reason", "").strip()

    if not new_org_id:
        raise HTTPException(status_code=400, detail="Missing organization_id")

    try:
        UUID(sub_id)
        UUID(new_org_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # 1. Verify submission exists and get current org
                    cur.execute(
                        "SELECT id, organization_id, company_name FROM submissions WHERE id = %s",
                        (sub_id,)
                    )
                    submission = cur.fetchone()
                    if not submission:
                        raise HTTPException(status_code=404, detail="Submission not found")

                    old_org_id = str(submission["organization_id"]) if submission["organization_id"] else None

                    if old_org_id == str(new_org_id):
                        raise HTTPException(
                            status_code=400, 
                            detail="Submission already assigned to this organisation"
                        )

                    # 2. Verify target organisation exists and fetch canonical name
                    cur.execute(
                        "SELECT id, name FROM organizations WHERE id = %s AND is_deleted = FALSE",
                        (new_org_id,)
                    )
                    target_org = cur.fetchone()
                    if not target_org:
                        raise HTTPException(status_code=404, detail="Target organisation not found")

                    target_name = target_org["name"]

                    # 3. Update both organization_id and company_name in submissions
                    cur.execute(
                        "UPDATE submissions SET organization_id = %s, company_name = %s WHERE id = %s",
                        (new_org_id, target_name, sub_id)
                    )

                    # 4. Update org_submission_links
                    cur.execute(
                        "DELETE FROM org_submission_links WHERE submission_id = %s",
                        (sub_id,)
                    )
                    cur.execute("""
                        INSERT INTO org_submission_links (org_id, submission_id, weight, linked_by)
                        VALUES (%s, %s, 1.0, %s)
                        ON CONFLICT (org_id, submission_id) DO NOTHING
                    """, (new_org_id, sub_id, admin_user_id))

                    # 5. Create audit trail in submission_reassignments
                    cur.execute("""
                        INSERT INTO submission_reassignments (
                            submission_id, 
                            old_organization_id, 
                            new_organization_id, 
                            reassigned_by, 
                            reason
                        )
                        VALUES (%s, %s, %s, %s, %s)
                    """, (sub_id, old_org_id, new_org_id, admin_user_id, reason or None))

        dashboard_cache.clear()

        logger.info(
            "Submission %s reassigned from org %s to org %s (%s) by user %s",
            sub_id, old_org_id, new_org_id, target_name, admin_email
        )

        return {
            "message": "Submission reassigned successfully",
            "old_organization_id": old_org_id,
            "new_organization_id": new_org_id,
            "company_name": target_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to reassign submission: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during reassignment")


# ---------------------------------------------------------------------------
# PUT /api/submissions/{id}/email
# ---------------------------------------------------------------------------

@router.put("/submissions/{submission_id}/email")
@audit_log("edit_email_draft")
async def update_email(request: Request, submission_id: str):
    require_admin(request)
    sub_id = str(submission_id).strip()
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    email_body = body.get("email_body")
    if email_body is None:
        raise HTTPException(status_code=400, detail="Missing email_body")

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE submissions SET email_body = %s WHERE id = %s",
                        (email_body, sub_id),
                    )
                    if cur.rowcount == 0:
                        raise HTTPException(status_code=404, detail="Not found")
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
async def regenerate_email(request: Request, submission_id: str):
    require_admin(request)
    sub_id = str(submission_id).strip()

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM submissions WHERE id = %s", (sub_id,))
                row = cur.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Not found")

            if row.get("status") == "sent":
                raise HTTPException(status_code=409, detail="Cannot regenerate sent email")

            data = dict(row)
            scores = calculate_scores(data, conn)
            new_email_body = scores.get("email_body")

            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE submissions SET email_body = %s WHERE id = %s",
                        (new_email_body, sub_id),
                    )

        return {"success": True, "email_body": new_email_body}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Regenerate email failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")


# ---------------------------------------------------------------------------
# POST /api/submissions/{id}/send
# ---------------------------------------------------------------------------

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
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE submissions SET status = 'sent', sent_at = %s WHERE id = %s",
                        (sent_at, submission_id),
                    )
        dashboard_cache.clear()
    except Exception as e:
        logger.error(f"Async email failed: {e}")
        try:
            with get_db_connection() as conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO email_dlq (submission_id, payload, attempts, last_error) 
                            VALUES (%s, %s, 3, %s)
                        """, (submission_id, json.dumps(payload), str(e)))
                        cur.execute("UPDATE submissions SET status = 'failed' WHERE id = %s", (submission_id,))
        except Exception as dlq_err:
            logger.critical("Failed to write to email_dlq: %s", dlq_err)


@router.post("/submissions/{submission_id}/send")
@audit_log("send_audit_report")
async def send_email_route(request: Request, submission_id: str, background_tasks: BackgroundTasks):
    require_admin(request)
    sub_id_str = str(submission_id).strip()

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT name, email, company_name, email_body, status FROM submissions WHERE id = %s",
                    (sub_id_str,),
                )
                row = cur.fetchone()

                if not row:
                    raise HTTPException(status_code=404, detail="Not found")

                if not row.get("email_body"):
                    raise HTTPException(status_code=400, detail="Email body is still being prepared by the background worker. Please try again shortly.")

                if row["status"] in ("sent", "sending"):
                    raise HTTPException(status_code=409, detail="Already sent or sending")

                sender_address, sender_name = get_sender_for_send(cur)

            with conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE submissions SET status = 'sending' WHERE id = %s", (sub_id_str,))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("DB query/update failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")

    payload = {
        "to_address": row["email"],
        "to_name": row["name"],
        "subject": f"NeuroMark Audit Results — {row['company_name']}",
        "html": row["email_body"],
        "plain": strip_html(row["email_body"]),
        "sender_address": sender_address,
        "sender_name": sender_name,
        "submission_id": sub_id_str,
    }

    background_tasks.add_task(process_email_dispatch, sub_id_str, payload)
    dashboard_cache.clear()

    return {"success": True, "status": "sending"}


# ---------------------------------------------------------------------------
# GET / PUT /api/settings
# ---------------------------------------------------------------------------

@router.get("/settings")
async def get_settings_route(request: Request):
    require_admin(request)
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                data = get_settings(cur)
        return data
    except Exception as e:
        logger.error("Settings failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")


@router.put("/settings")
@audit_log("update_settings")
async def save_settings_route(request: Request):
    require_admin(request)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not body:
        raise HTTPException(status_code=400, detail="Empty body")

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    data = update_settings(cur, body)
        return data
    except Exception as e:
        logger.error("Settings update failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")


# ---------------------------------------------------------------------------
# POST /api/settings/notifications/toggle
# ---------------------------------------------------------------------------

@router.post("/settings/notifications/toggle")
@audit_log("toggle_notifications")
async def toggle_notifications(request: Request):
    require_admin(request)
    try:
        with get_db_connection() as conn:
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
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Toggle notifications failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")


# ---------------------------------------------------------------------------
# POST /api/book-call
# ---------------------------------------------------------------------------

@router.post("/book-call")
@limiter.limit("10/hour")
async def book_call(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    name           = (body.get("name") or "").strip()
    designation    = (body.get("designation") or "").strip()
    company        = (body.get("company") or "").strip()
    email          = (body.get("email") or "").strip()
    phone          = (body.get("phone") or "").strip()
    preferred_time = (body.get("preferred_time") or "").strip()
    message        = (body.get("message") or "").strip()

    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required")
    if not company:
        raise HTTPException(status_code=400, detail="Organisation is required")

    import html as html_module

    def esc(t):
        return html_module.escape(str(t))

    subject_line = f"[NeuroMark] New call booking request — {company}"
    plain = (
        f"New call booking request from NeuroMark\n\n"
        f"Name: {name}\n"
        f"Job title: {designation or '—'}\n"
        f"Organisation: {company}\n"
        f"Email: {email}\n"
        f"Phone: {phone or '—'}\n"
        f"Preferred time: {preferred_time or 'No preference'}\n\n"
        f"Message:\n{message or '—'}\n"
    )
    html_body = (
        "<p><strong>New call booking request</strong> from NeuroMark</p>"
        f"<table style='border-collapse:collapse;font-family:sans-serif;font-size:14px;'>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#888;'>Name</td><td style='padding:4px 0;'><strong>{esc(name)}</strong></td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#888;'>Job title</td><td style='padding:4px 0;'>{esc(designation) or '—'}</td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#888;'>Organisation</td><td style='padding:4px 0;'>{esc(company)}</td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#888;'>Email</td><td style='padding:4px 0;'><a href='mailto:{esc(email)}'>{esc(email)}</a></td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#888;'>Phone</td><td style='padding:4px 0;'>{esc(phone) or '—'}</td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#888;'>Preferred time</td><td style='padding:4px 0;'>{esc(preferred_time) or 'No preference'}</td></tr>"
        f"</table>"
        + (f"<p><strong>Message:</strong></p><p style='white-space:pre-wrap;line-height:1.6;'>{esc(message)}</p>" if message else "")
    )

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                settings = get_settings(cur)
                sender_address, sender_name = get_sender_for_send(cur)

                to_address = (
                    (settings.get("notification_email") or "").strip()
                    or os.environ.get("SUPPORT_EMAIL", "").strip()
                    or "aakash.padyachi@orchvate.com"
                )

                if not sender_address:
                    raise ValueError("Sender address is not configured")

                def _bg():
                    try:
                        send_acs_email(
                            to_address=to_address,
                            to_name="Orchvate Team",
                            subject=subject_line,
                            html=html_body,
                            plain=plain,
                            sender_address=sender_address,
                            sender_name=sender_name,
                        )
                    except Exception as e:
                        logger.error("Book-call email failed: %s", e)

                threading.Thread(target=_bg).start()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Book-call request failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to send booking request")

    return {"success": True, "message": "Booking request received. We will be in touch soon."}


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
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                send_support_request(cur, name, email, subject, message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Support request failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to send support request")

    return {"success": True, "message": "Support request sent. We will get back to you soon."}


# ---------------------------------------------------------------------------
# GET /api/auth/config  — public MSAL settings for the admin portal
# ---------------------------------------------------------------------------

@router.get("/auth/config")
async def auth_config():
    from app.core.config import ENTRA_CLIENT_ID, ENTRA_TENANT_ID
    return {
        "clientId": ENTRA_CLIENT_ID or None,
        "tenantId": ENTRA_TENANT_ID or None,
    }


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
        with get_db_connection() as conn:
            res = verify_user(conn, email)
        return res
    except Exception as e:
        logger.error("Verify user failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error")


# ---------------------------------------------------------------------------
# RBAC: /api/manage/users — Strictly Super Admin Only
# ---------------------------------------------------------------------------

@router.get("/manage/users")
async def admin_users_list(request: Request):
    require_super_admin(request)
    try:
        with get_db_connection() as conn:
            users = get_users(conn)
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
    require_super_admin(request)
    try:
        body = await request.json()
        email = (body.get("email") or "").strip().lower()
        role = (body.get("role") or "admin").strip().lower()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        with get_db_connection() as conn:
            new_user = add_user(conn, email, role)
        if new_user.get("created_at"):
            new_user["created_at"] = new_user["created_at"].isoformat()
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Admin user add failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/manage/users/{email}")
@audit_log("remove_user")
async def admin_user_remove(request: Request, email: str):
    require_super_admin(request)
    try:
        with get_db_connection() as conn:
            remove_user(conn, email.lower())
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Admin user remove failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /api/settings/delete-all-records — Strictly Super Admin Only
# ---------------------------------------------------------------------------

@router.post("/settings/delete-all-records")
@audit_log("delete_all_records")
async def delete_all_records(request: Request):
    """
    Deletes all submissions from the database.
    Strictly Super Admin only. Requires explicit confirmation text 'DELETE ALL SUBMISSIONS'.
    Normal Admin receives HTTP 403 Forbidden.
    Unauthenticated caller receives HTTP 401 Unauthorized.
    """
    admin_user = require_super_admin(request)
    actor_email = admin_user["email"]

    try:
        body = await request.json()
    except Exception:
        body = {}

    confirmation = (body.get("confirmation") or "").strip()
    password = (body.get("password") or "").strip()
    correct_password = os.environ.get("DELETE_ALL_PASSWORD", "")

    # Require explicit confirmation payload
    if confirmation != "DELETE ALL SUBMISSIONS":
        # Allow password check as secondary fallback for existing tests/scripts
        if not (correct_password and password == correct_password):
            raise HTTPException(
                status_code=400,
                detail='Explicit confirmation string "DELETE ALL SUBMISSIONS" is required to delete all records.'
            )

    try:
        with get_db_transaction() as conn:
            with conn.cursor() as cur:
                # 1. Clean email_dlq first to prevent foreign key NO ACTION violations
                cur.execute("DELETE FROM email_dlq")

                # 2. Delete all submissions (cascades to org_submission_links and submission_reassignments)
                cur.execute("DELETE FROM submissions")
                deleted_count = cur.rowcount

                # 3. Reset invitation counters
                cur.execute("UPDATE organization_invitations SET submission_count = 0")

        dashboard_cache.clear()
        logger.warning(
            "ALL SUBMISSIONS DELETED: %d records removed by Super Admin %s",
            deleted_count, actor_email
        )
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        logger.error("Delete all records failed: %s", e)
        raise HTTPException(status_code=500, detail="Database error during records deletion")


# ---------------------------------------------------------------------------
# GET /api/manage/audit-logs
# ---------------------------------------------------------------------------

@router.get("/manage/audit-logs")
async def get_audit_logs(request: Request):
    require_admin(request)
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100")
                rows = cur.fetchall()

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
