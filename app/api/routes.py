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
from fastapi import APIRouter, HTTPException, Request, Response, BackgroundTasks, Depends, status
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
from app.services.org_cache_service import (
    get_organisation_by_name,
    get_organisation_by_id,
    is_org_eligible,
    invalidate_org_cache,
)
from app.services.email_policy_service import check_corporate_email_eligibility
from app.services.token_service import resolve_assessment_token
from app.services.rate_limit_service import (
    enforce_submission_rate_limits,
    get_effective_submit_hourly_limit,
    get_effective_submit_daily_limit,
    get_client_ip,
    get_rate_limit_config_response,
    update_rate_limit_settings,
    reset_rate_limit_settings,
)

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

@router.post("/submit", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(get_effective_submit_hourly_limit, key_func=get_client_ip)
@limiter.limit(get_effective_submit_daily_limit, key_func=get_client_ip)
def submit(request: Request, payload: AuditSubmission, response: Response, background_tasks: BackgroundTasks):
    t_req_start = time.perf_counter()
    data = payload.dict()
    idempotency_key = (data.get("idempotency_key") or request.headers.get("Idempotency-Key") or "").strip()
    if not idempotency_key:
        idempotency_key = str(uuid_pkg.uuid4())

    # Step 0: Dynamic per-traffic classification and session attempt rate limiting
    enforce_submission_rate_limits(request, data)

    # Step 1: Validate Corporate Email Eligibility
    user_email = (data.get("email") or "").strip()
    if user_email:
        email_check = check_corporate_email_eligibility(user_email)
        if not email_check["eligible"]:
            raise HTTPException(status_code=400, detail=email_check.get("error", "Corporate email is required."))

    # Step 2: Organization / Token / Invitation resolution
    organization_id = None
    invitation_id = None
    access_token_id = None
    campaign_id = None
    submission_source = "DIRECT"
    resolved_company_name = (data.get("company_name") or "").strip()

    raw_token = (data.get("t") or data.get("token") or data.get("access_token") or data.get("invitation_token") or "").strip()
    if raw_token:
        token_res = resolve_assessment_token(raw_token)
        if not token_res.get("valid"):
            raise HTTPException(status_code=400, detail=token_res.get("error", "Invalid assessment link."))

        organization_id = str(token_res["organization_id"])
        resolved_company_name = token_res["organization_name"]
        campaign_id = token_res.get("campaign_id")
        if token_res.get("is_legacy_invitation"):
            invitation_id = str(token_res["token_id"])
            submission_source = "INVITATION"
        else:
            access_token_id = str(token_res["token_id"])
            submission_source = "SECURE_LINK"
    else:
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
            org, _ = get_organisation_by_id(req_org_id)
            if not org:
                raise HTTPException(status_code=400, detail="Invalid organisation ID.")
            eligible, err = is_org_eligible(org)
            if not eligible:
                raise HTTPException(status_code=400, detail=err or "Organisation is inactive.")
            organization_id = str(org["id"])
            resolved_company_name = org["name"]
            submission_source = "DIRECT"
        elif resolved_company_name:
            clean_name = " ".join(resolved_company_name.split())
            org, _ = get_organisation_by_name(clean_name)
            if org:
                eligible, err = is_org_eligible(org)
                if not eligible:
                    raise HTTPException(status_code=400, detail=err or "Organisation is inactive.")
                organization_id = str(org["id"])
                resolved_company_name = org["name"]
            else:
                with get_db_connection() as org_conn:
                    with org_conn:
                        with org_conn.cursor() as org_cur:
                            org_cur.execute(
                                "SELECT pg_advisory_xact_lock(hashtext(lower(trim(%s))))",
                                (clean_name,)
                            )
                            org_cur.execute("""
                                SELECT id, name FROM organizations 
                                WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s)) AND is_deleted = FALSE
                            """, (clean_name,))
                            org_row = org_cur.fetchone()
                            if org_row:
                                organization_id = str(org_row[0])
                                resolved_company_name = org_row[1]
                            else:
                                org_cur.execute("""
                                    INSERT INTO organizations (name, is_active, is_deleted, approval_status)
                                    VALUES (%s, TRUE, FALSE, 'approved')
                                    RETURNING id, name
                                """, (clean_name,))
                                new_org = org_cur.fetchone()
                                organization_id = str(new_org[0])
                                resolved_company_name = new_org[1]
                                try:
                                    invalidate_org_cache()
                                except Exception:
                                    pass
            submission_source = "DIRECT"
        else:
            raise HTTPException(status_code=400, detail="Organisation name or ID is required.")

    # Attach resolved properties for the background worker
    data["_resolved_org_id"] = organization_id
    data["_resolved_company_name"] = resolved_company_name
    data["_resolved_source"] = submission_source
    data["_invitation_id"] = invitation_id
    data["_access_token_id"] = access_token_id
    data["_campaign_id"] = campaign_id

    draft_uuid = None
    draft_id = data.get("draft_id")
    if draft_id and str(draft_id).strip() not in ("", "null", "undefined"):
        try:
            draft_uuid = str(uuid_pkg.UUID(str(draft_id)))
        except ValueError:
            logger.warning("Invalid draft_id UUID: %s", draft_id)

    new_sub_id = str(uuid_pkg.uuid4())

    # Step 3: Single atomic transaction - write raw submission & outbox
    cte_sql = """
        WITH existing_raw AS (
            SELECT submission_id, payload, status FROM raw_submissions
            WHERE idempotency_key = %(idempotency_key)s
            LIMIT 1
        ),
        new_raw AS (
            INSERT INTO raw_submissions (
                submission_id, idempotency_key, organization_id, user_id,
                payload, schema_version, status, scoring_status, report_status,
                email_status, crm_status
            )
            SELECT
                %(submission_id)s::uuid,
                %(idempotency_key)s,
                %(organization_id)s::uuid,
                %(user_id)s,
                %(payload)s::jsonb,
                1,
                'RECEIVED',
                'PENDING',
                'PENDING',
                'PENDING',
                'PENDING'
            WHERE NOT EXISTS (SELECT 1 FROM existing_raw)
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING submission_id
        ),
        new_outbox AS (
            INSERT INTO service_bus_outbox (
                event_type, aggregate_id, message_id, payload, status
            )
            SELECT
                'SUBMISSION_CREATED',
                submission_id,
                submission_id::text,
                json_build_object(
                    'submission_id', submission_id::text,
                    'organization_id', %(organization_id)s::text,
                    'idempotency_key', %(idempotency_key)s
                )::jsonb,
                'PENDING'
            FROM new_raw
        ),
        update_invitation AS (
            UPDATE organization_invitations
            SET submission_count = submission_count + 1
            WHERE %(invitation_id)s IS NOT NULL AND id = %(invitation_id)s::uuid
              AND EXISTS (SELECT 1 FROM new_raw)
        ),
        update_draft AS (
            UPDATE draft_submissions
            SET submitted = TRUE
            WHERE %(draft_uuid)s IS NOT NULL AND id = %(draft_uuid)s::uuid
              AND EXISTS (SELECT 1 FROM new_raw)
        )
        SELECT 
            (SELECT submission_id FROM new_raw) AS created_id,
            (SELECT submission_id FROM existing_raw) AS existing_id,
            (SELECT status FROM existing_raw) AS existing_status,
            (SELECT payload FROM existing_raw) AS existing_payload;
    """

    params = {
        "submission_id": new_sub_id,
        "idempotency_key": idempotency_key,
        "organization_id": organization_id,
        "user_id": data.get("user_id") or data.get("email"),
        "payload": json.dumps(data),
        "invitation_id": invitation_id,
        "draft_uuid": draft_uuid
    }

    t_checkout_start = time.perf_counter()
    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(cte_sql, params)
                res = cur.fetchone()

    t_tx_end = time.perf_counter()
    created_id, existing_id, existing_status, existing_payload = res

    if existing_id:
        if existing_payload and isinstance(existing_payload, dict):
            existing_email = (existing_payload.get("email") or "").strip().lower()
            incoming_email = (data.get("email") or "").strip().lower()
            if existing_email and incoming_email and existing_email != incoming_email:
                logger.warning("Idempotency key %s reused with conflicting email: %s vs %s",
                               idempotency_key, incoming_email, existing_email)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key has already been used with a different payload."
                )
        logger.info("Idempotent replay detected for key %s, returning submission %s (status=%s)",
                    idempotency_key, existing_id, existing_status)
        response.status_code = status.HTTP_200_OK if existing_status == "COMPLETED" else status.HTTP_202_ACCEPTED
        return {
            "success": True,
            "submission_id": str(existing_id),
            "status": existing_status or "RECEIVED",
            "message": "Your submission has been received and is being processed."
        }

    if not created_id:
        # Fallback query for millisecond concurrency collision
        with get_db_connection() as fb_conn:
            with fb_conn.cursor() as fb_cur:
                fb_cur.execute(
                    "SELECT submission_id, status FROM raw_submissions WHERE idempotency_key = %s LIMIT 1",
                    (idempotency_key,)
                )
                fb_row = fb_cur.fetchone()
                if fb_row:
                    logger.info("Recovered parallel idempotency conflict for key %s -> %s", idempotency_key, fb_row[0])
                    response.status_code = status.HTTP_202_ACCEPTED
                    return {
                        "success": True,
                        "submission_id": str(fb_row[0]),
                        "status": fb_row[1] or "RECEIVED",
                        "message": "Your submission has been received and is being processed."
                    }

        logger.error("Failed to persist raw submission for key %s", idempotency_key)
        raise HTTPException(status_code=500, detail="Database error persisting submission")

    submission_id = str(created_id)
    dashboard_cache.clear()

    t_req_end = time.perf_counter()
    logger.info(
        "INGESTION_METRICS: id=%s total_ms=%.2f tx_ms=%.2f",
        submission_id,
        (t_req_end - t_req_start) * 1000.0,
        (t_tx_end - t_checkout_start) * 1000.0
    )

    response.status_code = status.HTTP_202_ACCEPTED
    return {
        "success": True,
        "submission_id": submission_id,
        "status": "RECEIVED",
        "message": "Your submission has been received and is being processed."
    }


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
                    UNION ALL
                    SELECT r.submission_id AS id,
                           COALESCE(r.payload->>'name', '') AS name,
                           COALESCE(r.payload->>'designation', r.payload->>'role', '') AS designation,
                           COALESCE(r.payload->>'company_name', o.name, '') AS company_name,
                           r.payload->>'email' AS email,
                           r.payload->>'contact_number' AS contact_number,
                           r.created_at AS submitted_at,
                           NULL AS overall_avg,
                           NULL AS overall_level,
                           r.status AS status,
                           r.payload AS answers,
                           r.organization_id,
                           COALESCE(r.payload->>'submission_source', 'DIRECT') AS submission_source,
                           NULL AS invitation_id,
                           NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
                    FROM raw_submissions r
                    LEFT JOIN organizations o ON o.id = r.organization_id
                    WHERE r.status IN ('RECEIVED', 'PROCESSING', 'DEAD_LETTERED', 'FAILED', 'RETRYING')
                      AND NOT EXISTS (
                          SELECT 1 FROM submissions s WHERE s.id = r.submission_id OR s.raw_submission_id = r.submission_id
                      )
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
# GET /api/submissions/{id}/status — Query asynchronous processing status
# ---------------------------------------------------------------------------

@router.get("/submissions/{submission_id}/status")
async def get_submission_status(request: Request, submission_id: str):
    sub_id = str(submission_id).strip()

    try:
        uuid_pkg.UUID(sub_id)
    except (ValueError, AttributeError):
        if not sub_id.isdigit():
            raise HTTPException(status_code=400, detail="Invalid submission ID format. Must be a valid UUID or integer.")

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT 
                        r.submission_id,
                        r.organization_id,
                        r.status AS raw_status,
                        r.scoring_status,
                        r.report_status AS raw_report_status,
                        r.email_status AS raw_email_status,
                        r.crm_status AS raw_crm_status,
                        r.retry_count,
                        r.last_error,
                        r.created_at AS raw_created_at,
                        r.processing_completed_at AS raw_completed_at,
                        s.id AS sub_id,
                        s.async_status AS sub_async_status,
                        s.email_status AS sub_email_status,
                        s.crm_status AS sub_crm_status,
                        s.report_status AS sub_report_status,
                        s.admin_notify_status,
                        s.hubspot_deal_id,
                        s.submitted_at AS sub_submitted_at,
                        s.async_completed_at AS sub_completed_at,
                        s.email_body
                    FROM raw_submissions r
                    LEFT JOIN submissions s ON (s.id = r.submission_id OR s.raw_submission_id = r.submission_id)
                    WHERE r.submission_id = %s
                    """,
                    (sub_id,)
                )
                row = cur.fetchone()

                if not row:
                    # Fallback to direct legacy lookup in submissions table
                    cur.execute(
                        """
                        SELECT id, organization_id, async_status, email_status, crm_status,
                               report_status, admin_notify_status, hubspot_deal_id,
                               submitted_at, async_completed_at, email_body
                        FROM submissions
                        WHERE id = %s
                        """,
                        (sub_id,)
                    )
                    leg_row = cur.fetchone()
                    if leg_row:
                        row = {
                            "submission_id": leg_row["id"],
                            "organization_id": leg_row.get("organization_id"),
                            "raw_status": leg_row.get("async_status") or "COMPLETED",
                            "scoring_status": "COMPLETED",
                            "raw_report_status": leg_row.get("report_status"),
                            "raw_email_status": leg_row.get("email_status"),
                            "raw_crm_status": leg_row.get("crm_status"),
                            "raw_created_at": leg_row.get("submitted_at"),
                            "raw_completed_at": leg_row.get("async_completed_at"),
                            "sub_id": leg_row["id"],
                            "admin_notify_status": leg_row.get("admin_notify_status"),
                            "hubspot_deal_id": leg_row.get("hubspot_deal_id"),
                            "email_body": leg_row.get("email_body")
                        }

        if not row:
            raise HTTPException(status_code=404, detail="Submission not found")

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                token_payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                if token_payload.get("role") == "org_member":
                    user_org_id = str(token_payload.get("org_id", ""))
                    sub_org_id = str(row.get("organization_id") or "")
                    if user_org_id and user_org_id != sub_org_id:
                        raise HTTPException(status_code=403, detail="Forbidden: You do not have permission to view this submission status.")
            except jwt.PyJWTError:
                pass

        eff_status = row.get("raw_status") or row.get("sub_async_status") or "RECEIVED"
        rep_status = row.get("sub_report_status") or row.get("raw_report_status") or ("GENERATED" if row.get("email_body") else "PENDING")

        return {
            "submission_id": str(row.get("submission_id") or row.get("sub_id")),
            "status": eff_status,
            "scoring_status": row.get("scoring_status") or ("COMPLETED" if row.get("sub_id") else "PENDING"),
            "email_status": row.get("sub_email_status") or row.get("raw_email_status") or "PENDING",
            "crm_status": row.get("sub_crm_status") or row.get("raw_crm_status") or "PENDING",
            "report_status": rep_status,
            "admin_notify_status": row.get("admin_notify_status") or "PENDING",
            "hubspot_deal_id": row.get("hubspot_deal_id"),
            "retry_count": row.get("retry_count") or 0,
            "last_error": row.get("last_error"),
            "submitted_at": to_iso_utc(row.get("raw_created_at") or row.get("sub_submitted_at")),
            "completed_at": to_iso_utc(row.get("raw_completed_at") or row.get("sub_completed_at"))
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("DB query failed checking submission status: %s", e)
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
                        "UPDATE submissions SET status = 'sent', email_status = 'SENT', sent_at = %s WHERE id = %s",
                        (sent_at, submission_id),
                    )
                    cur.execute(
                        """
                        INSERT INTO submission_operation_states (
                            submission_id, operation_type, idempotency_key, status, completed_at, updated_at
                        )
                        VALUES (%s, 'EMAIL_DELIVERY', %s, 'SENT', NOW(), NOW())
                        ON CONFLICT (submission_id, operation_type) DO UPDATE
                        SET status = 'SENT', completed_at = NOW(), updated_at = NOW()
                        """,
                        (str(submission_id), f"{submission_id}:EMAIL_DELIVERY")
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
                        cur.execute("UPDATE submissions SET status = 'failed', email_status = 'FAILED' WHERE id = %s", (submission_id,))
                        cur.execute(
                            """
                            INSERT INTO submission_operation_states (
                                submission_id, operation_type, idempotency_key, status, last_error, updated_at
                            )
                            VALUES (%s, 'EMAIL_DELIVERY', %s, 'FAILED', %s, NOW())
                            ON CONFLICT (submission_id, operation_type) DO UPDATE
                            SET status = 'FAILED', last_error = %s, updated_at = NOW()
                            """,
                            (str(submission_id), f"{submission_id}:EMAIL_DELIVERY", str(e)[:1000], str(e)[:1000])
                        )
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
# Rate Limit Settings Management
# GET /api/manage/settings/rate-limits  (and /api/settings/rate-limits)
# PUT /api/manage/settings/rate-limits  (and /api/settings/rate-limits)
# POST /api/manage/settings/rate-limits/reset (and /api/settings/rate-limits/reset)
# ---------------------------------------------------------------------------

@router.get("/manage/settings/rate-limits")
@router.get("/settings/rate-limits")
async def get_rate_limits_route(request: Request):
    require_admin(request)
    try:
        return get_rate_limit_config_response()
    except Exception as e:
        logger.error("Failed to fetch rate limits: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve rate limit settings")


@router.put("/manage/settings/rate-limits")
@router.put("/settings/rate-limits")
async def update_rate_limits_route(request: Request):
    user = require_admin(request)
    admin_email = user.get("email") or getattr(request.state, "admin_email", "admin")
    client_ip = get_client_ip(request)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    try:
        updated = update_rate_limit_settings(body, admin_email=admin_email, client_ip=client_ip)
        return updated
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("Failed to update rate limits: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update rate limit settings")


@router.post("/manage/settings/rate-limits/reset")
@router.post("/settings/rate-limits/reset")
async def reset_rate_limits_route(request: Request):
    user = require_admin(request)
    admin_email = user.get("email") or getattr(request.state, "admin_email", "admin")
    client_ip = get_client_ip(request)

    try:
        reset_res = reset_rate_limit_settings(admin_email=admin_email, client_ip=client_ip)
        return reset_res
    except Exception as e:
        logger.error("Failed to reset rate limits: %s", e)
        raise HTTPException(status_code=500, detail="Failed to reset rate limit settings")


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


# ---------------------------------------------------------------------------
# GET /api/admin/submissions/dead-lettered
# ---------------------------------------------------------------------------

@router.get("/admin/submissions/dead-lettered")
def get_dead_lettered_submissions(request: Request):
    require_admin(request)
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    r.submission_id,
                    r.idempotency_key,
                    r.organization_id,
                    o.name AS organization_name,
                    r.payload->>'name' AS user_name,
                    r.payload->>'email' AS user_email,
                    r.status,
                    r.scoring_status,
                    r.report_status,
                    r.retry_count,
                    r.last_error,
                    r.created_at,
                    r.updated_at
                FROM raw_submissions r
                LEFT JOIN organizations o ON o.id = r.organization_id
                WHERE r.status IN ('DEAD_LETTERED', 'FAILED')
                ORDER BY r.updated_at DESC
            """)
            rows = cur.fetchall()

    result = []
    for row in rows:
        r = dict(row)
        r["submission_id"] = str(r["submission_id"])
        if r.get("organization_id"):
            r["organization_id"] = str(r["organization_id"])
        if r.get("created_at"):
            r["created_at"] = to_iso_utc(r["created_at"])
        if r.get("updated_at"):
            r["updated_at"] = to_iso_utc(r["updated_at"])
        result.append(r)
    return {"dead_lettered_submissions": result, "count": len(result)}


# ---------------------------------------------------------------------------
# POST /api/admin/submissions/{submission_id}/replay
# ---------------------------------------------------------------------------

@router.post("/admin/submissions/{submission_id}/replay")
def replay_submission(request: Request, submission_id: str):
    require_admin(request)
    sub_uuid = str(submission_id).strip()
    try:
        uuid_pkg.UUID(sub_uuid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid submission ID format.")

    with get_db_connection() as conn:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT submission_id, idempotency_key, organization_id, payload, status
                    FROM raw_submissions
                    WHERE submission_id = %s
                    FOR UPDATE
                    """,
                    (sub_uuid,)
                )
                raw = cur.fetchone()
                if not raw:
                    raise HTTPException(status_code=404, detail="Submission not found in raw_submissions.")

                cur.execute(
                    """
                    UPDATE raw_submissions
                    SET status = 'PENDING',
                        retry_count = 0,
                        last_error = NULL,
                        updated_at = NOW()
                    WHERE submission_id = %s
                    """,
                    (sub_uuid,)
                )

                cur.execute(
                    """
                    INSERT INTO service_bus_outbox (
                        event_type, aggregate_id, message_id, payload, status, next_retry_at
                    )
                    VALUES (
                        'SUBMISSION_CREATED',
                        %s::uuid,
                        %s,
                        json_build_object(
                            'submission_id', %s::text,
                            'replay', true,
                            'replayed_at', NOW()
                        )::jsonb,
                        'PENDING',
                        NOW()
                    )
                    """,
                    (sub_uuid, sub_uuid, sub_uuid)
                )

    dashboard_cache.clear()
    logger.info("Submission %s re-armed for replay by admin", sub_uuid)
    return {
        "success": True,
        "submission_id": sub_uuid,
        "status": "PENDING",
        "message": f"Submission {sub_uuid} has been queued for replay."
    }
