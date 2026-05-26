"""
orgs.py — Admin endpoints for multi-respondent org scoring.

All routes are under /manage/orgs and protected by jwks_middleware.
"""

from __future__ import annotations
import logging
from uuid import UUID

import psycopg2.extras
from fastapi import APIRouter, HTTPException, Request

from app.core.database import get_conn
from app.services.org_scoring_service import calc_weighted_org_score, build_org_summary_email
from app.services.settings_service import send_acs_email, get_sender_for_send

router = APIRouter(prefix="/manage/orgs", tags=["Org Scoring"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_row(row: dict) -> dict:
    """Convert non-JSON-serialisable types in a DB row."""
    from decimal import Decimal
    from datetime import datetime
    out = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            out[k] = float(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, UUID):
            out[k] = str(v)
        else:
            out[k] = v
    return out


def _fetch_org_links(conn, org_id: str) -> list[dict]:
    """Return all linked submissions for an org, enriched with weight."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT
                s.*,
                osl.weight, osl.linked_by, osl.linked_at
            FROM org_submission_links osl
            JOIN submissions s ON s.id = osl.submission_id
            WHERE osl.org_id = %s
            ORDER BY s.submitted_at ASC
        """, (org_id,))
        return [_serialize_row(dict(r)) for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# GET /api/manage/orgs
# List all orgs with weighted avg summary, PLUS virtual groups for unlinked
# submissions grouped by company_name so the admin can see and link them.
# ---------------------------------------------------------------------------

@router.get("")
async def list_orgs():
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # 1. Real org accounts
                cur.execute("""
                    SELECT o.id, o.name, o.created_at,
                           COUNT(osl.submission_id) AS respondent_count
                    FROM organizations o
                    LEFT JOIN org_submission_links osl ON osl.org_id = o.id
                    GROUP BY o.id, o.name, o.created_at
                    ORDER BY o.name ASC
                """)
                orgs = [_serialize_row(dict(r)) for r in cur.fetchall()]

                # 2. Unlinked submissions grouped by company_name (virtual groups)
                cur.execute("""
                    SELECT
                        LOWER(TRIM(s.company_name)) AS name_key,
                        MIN(s.company_name)          AS display_name,
                        COUNT(*)                     AS respondent_count,
                        AVG(s.overall_avg)           AS org_avg
                    FROM submissions s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM org_submission_links osl
                        WHERE osl.submission_id = s.id
                    )
                    GROUP BY LOWER(TRIM(s.company_name))
                    ORDER BY display_name ASC
                """)
                unlinked_groups = cur.fetchall()

            # Compute weighted avg for real orgs
            result = []
            for org in orgs:
                links = _fetch_org_links(conn, org["id"])
                scores = calc_weighted_org_score(links) if links else None
                result.append({
                    **org,
                    "org_avg":    scores["org_avg"]   if scores else None,
                    "org_level":  scores["org_level"] if scores else None,
                    "is_virtual": False,
                })

            # Add virtual groups (unlinked, grouped by company_name)
            # Use a stable fake id so the frontend can key on it
            import hashlib
            for g in unlinked_groups:
                name_key = g["name_key"] or ""
                # Skip if a real org already has this name (case-insensitive)
                real_names = {o["name"].lower().strip() for o in orgs}
                if name_key in real_names:
                    continue
                fake_id = "virtual-" + hashlib.md5(name_key.encode()).hexdigest()[:12]
                avg = float(g["org_avg"]) if g["org_avg"] else None
                result.append({
                    "id":              fake_id,
                    "name":            g["display_name"],
                    "created_at":      None,
                    "respondent_count": int(g["respondent_count"]),
                    "org_avg":         round(avg, 2) if avg else None,
                    "org_level":       None,   # no weighted calc without links
                    "is_virtual":      True,   # flag so frontend can show "Link all" CTA
                })

        conn.close()
        return result
    except Exception as e:
        logger.error("list_orgs failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /api/manage/orgs/unlinked
# Submissions with no org link — optionally filtered by company_name
# ---------------------------------------------------------------------------

@router.get("/unlinked")
async def list_unlinked(company_name: str = None):
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if company_name:
                    cur.execute("""
                        SELECT s.*
                        FROM submissions s
                        WHERE NOT EXISTS (
                            SELECT 1 FROM org_submission_links osl
                            WHERE osl.submission_id = s.id
                        )
                        AND LOWER(TRIM(s.company_name)) = LOWER(TRIM(%s))
                        ORDER BY s.submitted_at DESC
                    """, (company_name,))
                else:
                    cur.execute("""
                        SELECT s.*
                        FROM submissions s
                        WHERE NOT EXISTS (
                            SELECT 1 FROM org_submission_links osl
                            WHERE osl.submission_id = s.id
                        )
                        ORDER BY s.submitted_at DESC
                    """)
                rows = [_serialize_row(dict(r)) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        logger.error("list_unlinked failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /api/manage/orgs/create
# Create a new org from a company_name and link all matching unlinked submissions
# ---------------------------------------------------------------------------

@router.post("/create")
async def create_org_from_name(request: Request):
    try:
        body = await request.json()
        company_name = (body.get("company_name") or "").strip()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not company_name:
        raise HTTPException(status_code=400, detail="company_name is required")

    admin_email = getattr(request.state, "admin_email", "unknown")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                # Create org (or get existing one with same name)
                cur.execute("""
                    INSERT INTO organizations (name)
                    VALUES (%s)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """, (company_name,))
                row = cur.fetchone()
                if not row:
                    cur.execute("SELECT id FROM organizations WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))", (company_name,))
                    row = cur.fetchone()
                org_id = str(row[0])

                # Link all unlinked submissions matching this company_name
                cur.execute("""
                    SELECT id FROM submissions s
                    WHERE LOWER(TRIM(s.company_name)) = LOWER(TRIM(%s))
                    AND NOT EXISTS (
                        SELECT 1 FROM org_submission_links osl WHERE osl.submission_id = s.id
                    )
                """, (company_name,))
                sub_ids = [str(r[0]) for r in cur.fetchall()]

                for sid in sub_ids:
                    cur.execute("""
                        INSERT INTO org_submission_links (org_id, submission_id, weight, linked_by)
                        VALUES (%s, %s, 1.0, %s)
                        ON CONFLICT (org_id, submission_id) DO NOTHING
                    """, (org_id, sid, admin_email))
                    cur.execute("""
                        UPDATE submissions SET organization_id = %s
                        WHERE id = %s AND organization_id IS NULL
                    """, (org_id, sid))

        conn.close()
    except Exception as e:
        logger.error("create_org_from_name failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True, "org_id": org_id, "linked_count": len(sub_ids)}


# ---------------------------------------------------------------------------
# GET /api/manage/orgs/{org_id}
# Org detail with all linked submissions + live weighted scores
# ---------------------------------------------------------------------------

@router.get("/{org_id}")
async def get_org(org_id: UUID):
    oid = str(org_id)
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id, name, created_at FROM organizations WHERE id = %s", (oid,))
                org_row = cur.fetchone()
            if not org_row:
                conn.close()
                raise HTTPException(status_code=404, detail="Organisation not found")

            links = _fetch_org_links(conn, oid)
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_org failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    scores = calc_weighted_org_score(links)
    return {
        **_serialize_row(dict(org_row)),
        "scores": scores,
        "respondents": links,
    }


# ---------------------------------------------------------------------------
# PUT /api/manage/orgs/{org_id}/links/{submission_id}
# Update weight for a linked submission
# ---------------------------------------------------------------------------

@router.put("/{org_id}/links/{submission_id}")
async def update_link_weight(org_id: UUID, submission_id: UUID, request: Request):
    try:
        body = await request.json()
        weight = float(body.get("weight", 1.0))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON or weight value")

    if weight <= 0:
        raise HTTPException(status_code=400, detail="Weight must be greater than 0")

    oid = str(org_id)
    sid = str(submission_id)

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE org_submission_links
                    SET weight = %s
                    WHERE org_id = %s AND submission_id = %s
                """, (weight, oid, sid))
                if cur.rowcount == 0:
                    conn.close()
                    raise HTTPException(status_code=404, detail="Link not found")

        # Return updated scores
        links = _fetch_org_links(conn, oid)
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_link_weight failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True, "scores": calc_weighted_org_score(links)}


# ---------------------------------------------------------------------------
# POST /api/manage/orgs/{org_id}/link
# Manually link an unlinked submission to an org
# ---------------------------------------------------------------------------

@router.post("/{org_id}/link")
async def link_submission(org_id: UUID, request: Request):
    try:
        body = await request.json()
        submission_id = str(body.get("submission_id", "")).strip()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not submission_id:
        raise HTTPException(status_code=400, detail="submission_id is required")

    oid = str(org_id)
    admin_email = getattr(request.state, "admin_email", "unknown")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                # Verify submission exists
                cur.execute("SELECT id FROM submissions WHERE id = %s", (submission_id,))
                if not cur.fetchone():
                    conn.close()
                    raise HTTPException(status_code=404, detail="Submission not found")

                # Verify org exists
                cur.execute("SELECT id FROM organizations WHERE id = %s", (oid,))
                if not cur.fetchone():
                    conn.close()
                    raise HTTPException(status_code=404, detail="Organisation not found")

                # Insert link (ignore if already linked to this org)
                cur.execute("""
                    INSERT INTO org_submission_links (org_id, submission_id, weight, linked_by)
                    VALUES (%s, %s, 1.0, %s)
                    ON CONFLICT (org_id, submission_id) DO NOTHING
                """, (oid, submission_id, admin_email))

                # Also update submissions.organization_id if not already set
                cur.execute("""
                    UPDATE submissions SET organization_id = %s
                    WHERE id = %s AND organization_id IS NULL
                """, (oid, submission_id))

        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("link_submission failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True}


# ---------------------------------------------------------------------------
# GET /api/manage/orgs/{org_id}/report-preview
# Returns the rendered HTML for the org summary email (for admin preview)
# ---------------------------------------------------------------------------

@router.get("/{org_id}/report-preview")
async def org_report_preview(org_id: UUID):
    oid = str(org_id)
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id, name FROM organizations WHERE id = %s", (oid,))
                org_row = cur.fetchone()
            if not org_row:
                conn.close()
                raise HTTPException(status_code=404, detail="Organisation not found")
            links = _fetch_org_links(conn, oid)
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("org_report_preview failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    scores = calc_weighted_org_score(links)
    if not scores:
        raise HTTPException(status_code=400, detail="No linked submissions to preview")

    html = build_org_summary_email(
        org_row["name"], scores, scores["respondents"]
    )
    return {"html": html, "org_avg": scores["org_avg"], "org_level": scores["org_level"]}

@router.post("/{org_id}/message")
async def send_org_message(org_id: UUID, request: Request):
    try:
        body = await request.json()
        subject    = (body.get("subject") or "").strip()
        message    = (body.get("body") or "").strip()
        recipients = body.get("recipients", [])   # [{email, name}, ...]
        is_org_report = bool(body.get("is_org_report", False))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not subject:
        raise HTTPException(status_code=400, detail="Subject is required")
    if not message and not is_org_report:
        raise HTTPException(status_code=400, detail="Body is required")
    if not recipients:
        raise HTTPException(status_code=400, detail="At least one recipient is required")

    oid = str(org_id)
    admin_email = getattr(request.state, "admin_email", "unknown")

    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Load sender settings
                sender_address, sender_name = get_sender_for_send(cur)

                # If org report, build the summary email body
                if is_org_report:
                    links = _fetch_org_links(conn, oid)
                    scores = calc_weighted_org_score(links)
                    if not scores:
                        conn.close()
                        raise HTTPException(status_code=400, detail="No linked submissions to report on")
                    cur.execute("SELECT name FROM organizations WHERE id = %s", (oid,))
                    org_row = cur.fetchone()
                    org_name = org_row["name"] if org_row else "Your Organisation"
                    email_html = build_org_summary_email(org_name, scores, scores["respondents"])
                    email_plain = f"Organisation Audit Summary for {org_name}\n\nOverall Score: {scores['org_avg']}/20 — {scores['org_level']}"
                else:
                    email_html  = f"<p>{message.replace(chr(10), '<br>')}</p>"
                    email_plain = message

                # Log the message
                import json
                cur.execute("""
                    INSERT INTO admin_messages (org_id, sent_by, subject, body, recipients)
                    VALUES (%s, %s, %s, %s, %s)
                """, (oid, admin_email, subject, message or "(org report)", json.dumps(recipients)))

        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("send_org_message failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    # Send emails outside the DB transaction
    errors = []
    for r in recipients:
        try:
            send_acs_email(
                to_address=r["email"],
                to_name=r.get("name", ""),
                subject=subject,
                html=email_html,
                plain=email_plain,
                sender_address=sender_address,
                sender_name=sender_name,
            )
        except Exception as e:
            logger.error("Failed to send to %s: %s", r.get("email"), e)
            errors.append(r.get("email"))

    if is_org_report:
        successful_emails = [r["email"] for r in recipients if r["email"] not in errors]
        if successful_emails:
            try:
                conn = get_conn()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE submissions s
                            SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                            FROM org_submission_links osl
                            WHERE s.id = osl.submission_id
                              AND osl.org_id = %s
                              AND s.email = ANY(%s)
                        """, (oid, successful_emails))
                conn.close()
                
                # Clear dashboard cache in routes.py
                from app.api.routes import dashboard_cache
                if "dashboard" in dashboard_cache:
                    del dashboard_cache["dashboard"]
            except Exception as update_err:
                logger.error("Failed to update submission status after sending org report: %s", update_err)

    if errors:
        return {"success": False, "failed_recipients": errors}
    return {"success": True, "sent_count": len(recipients)}
