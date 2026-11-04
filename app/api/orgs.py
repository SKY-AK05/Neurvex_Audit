"""
orgs.py — Admin endpoints for multi-respondent org scoring, organisation management, and invitation links.

All routes are under /manage/orgs and protected for Normal Admin and Super Admin.
"""

from collections import defaultdict
import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import psycopg2.extras
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from pydantic import BaseModel, Field

from app.core.database import get_db_connection
from app.core.authorization import require_admin
from app.services.org_scoring_service import calc_weighted_org_score, build_org_summary_email
from app.services.settings_service import send_acs_email, get_sender_for_send
from app.services.org_cache_service import invalidate_org_cache
from app.services.token_service import (
    create_assessment_token,
    revoke_assessment_token,
    get_or_create_default_token,
)

router = APIRouter(
    prefix="/manage/orgs",
    tags=["Org Scoring & Management"],
    dependencies=[Depends(require_admin)]
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CreateOrgRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class UpdateOrgRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class OrgStatusRequest(BaseModel):
    is_active: bool


class CreateInvitationRequest(BaseModel):
    invitation_name: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = None
    max_submissions: Optional[int] = Field(None, ge=1)


class UpdateInvitationRequest(BaseModel):
    invitation_name: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = None
    max_submissions: Optional[int] = Field(None, ge=1)


class CreateAssessmentLinkRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    campaign_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_row(row: dict) -> dict:
    """Convert non-JSON-serialisable types in a DB row."""
    from decimal import Decimal
    from datetime import datetime
    import json
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
    if isinstance(out.get("answers"), str):
        try:
            out["answers"] = json.loads(out["answers"])
        except Exception:
            pass
    return out


def _fetch_org_links(conn, org_id: str) -> list[dict]:
    """Return all linked submissions for an org, enriched with weight and submission method."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT
                s.*,
                osl.weight, osl.linked_by, osl.linked_at,
                s.submission_source,
                s.invitation_id,
                oi.invitation_name
            FROM org_submission_links osl
            JOIN submissions s ON s.id = osl.submission_id
            LEFT JOIN organization_invitations oi ON oi.id = s.invitation_id
            WHERE osl.org_id = %s
            ORDER BY s.submitted_at ASC
        """, (org_id,))
        return [_serialize_row(dict(r)) for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# GET /api/manage/orgs
# List all orgs with weighted avg summary, active status, invitation counts,
# PLUS virtual groups for unlinked submissions.
# Optimized: Batch queries to eliminate N+1 loops.
# ---------------------------------------------------------------------------

@router.get("")
def list_orgs(include_deleted: bool = Query(False)):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # 1. Real org accounts
                where_clause = "" if include_deleted else "WHERE o.is_deleted = FALSE"
                cur.execute(f"""
                    SELECT o.id, o.name, o.is_active, o.is_deleted, o.created_at, o.updated_at,
                           (
                               COUNT(DISTINCT osl.submission_id) +
                               COALESCE((
                                   SELECT COUNT(*) FROM raw_submissions r 
                                   WHERE (r.organization_id = o.id OR LOWER(TRIM(r.payload->>'company_name')) = LOWER(TRIM(o.name)))
                                     AND r.status IN ('RECEIVED', 'PROCESSING', 'DEAD_LETTERED', 'FAILED', 'RETRYING')
                                     AND NOT EXISTS (
                                         SELECT 1 FROM submissions s WHERE s.id = r.submission_id OR s.raw_submission_id = r.submission_id
                                     )
                               ), 0)
                           ) AS respondent_count,
                           COUNT(DISTINCT oi.id) FILTER (
                               WHERE oi.is_active = TRUE AND (oi.expires_at IS NULL OR oi.expires_at > NOW())
                           ) AS active_invitations_count
                    FROM organizations o
                    LEFT JOIN org_submission_links osl ON osl.org_id = o.id
                    LEFT JOIN organization_invitations oi ON oi.organization_id = o.id
                    {where_clause}
                    GROUP BY o.id, o.name, o.is_active, o.is_deleted, o.created_at, o.updated_at
                    ORDER BY o.name ASC
                """)
                orgs = [_serialize_row(dict(r)) for r in cur.fetchall()]

                # 2. Batch fetch all linked submissions to eliminate N+1 query loop
                cur.execute("""
                    SELECT
                        s.*,
                        osl.org_id,
                        osl.weight, osl.linked_by, osl.linked_at,
                        s.submission_source,
                        s.invitation_id,
                        oi.invitation_name
                    FROM org_submission_links osl
                    JOIN submissions s ON s.id = osl.submission_id
                    LEFT JOIN organization_invitations oi ON oi.id = s.invitation_id
                    ORDER BY s.submitted_at ASC
                """)
                all_links = cur.fetchall()
                links_by_org = defaultdict(list)
                for r in all_links:
                    d = _serialize_row(dict(r))
                    links_by_org[str(d["org_id"])].append(d)

                # 3. Unlinked submissions grouped by company_name (virtual groups)
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

            # Compute weighted avg for real orgs from batched links
            result = []
            for org in orgs:
                org_links = links_by_org.get(str(org["id"]), [])
                scores = calc_weighted_org_score(org_links) if org_links else None
                result.append({
                    **org,
                    "org_avg":                  scores["org_avg"]   if scores else None,
                    "org_level":                scores["org_level"] if scores else None,
                    "is_virtual":               False,
                    "active_invitations_count": int(org.get("active_invitations_count") or 0),
                })

            # Add virtual groups (unlinked, grouped by company_name)
            for g in unlinked_groups:
                name_key = g["name_key"] or ""
                real_names = {o["name"].lower().strip() for o in orgs}
                if name_key in real_names:
                    continue
                fake_id = "virtual-" + hashlib.md5(name_key.encode()).hexdigest()[:12]
                avg = float(g["org_avg"]) if g["org_avg"] else None
                result.append({
                    "id":                       fake_id,
                    "name":                     g["display_name"],
                    "is_active":                True,
                    "is_deleted":               False,
                    "created_at":               None,
                    "updated_at":               None,
                    "respondent_count":         int(g["respondent_count"]),
                    "active_invitations_count": 0,
                    "org_avg":                  round(avg, 2) if avg else None,
                    "org_level":                None,
                    "is_virtual":               True,
                })

        return result
    except Exception as e:
        logger.error("list_orgs failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /api/manage/orgs
# Create a new formal organisation
# ---------------------------------------------------------------------------

@router.post("")
async def create_org(request: Request, body: CreateOrgRequest):
    company_name = " ".join(body.name.strip().split())
    if not company_name:
        raise HTTPException(status_code=400, detail="Organization name is required")

    admin_email = getattr(request.state, "admin_email", "unknown")

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Check for existing non-deleted org (case and whitespace normalized)
                    cur.execute("""
                        SELECT id FROM organizations
                        WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s)) AND is_deleted = FALSE
                    """, (company_name,))
                    if cur.fetchone():
                        raise HTTPException(status_code=400, detail="An organization with this name already exists")

                    cur.execute("""
                        INSERT INTO organizations (name, is_active, is_deleted, approval_status, updated_by)
                        VALUES (%s, TRUE, FALSE, 'approved', %s)
                        RETURNING id, name, is_active, is_deleted, created_at
                    """, (company_name, admin_email))
                    row = cur.fetchone()
                    org_id = str(row["id"])

                    # Link all unlinked submissions matching this company_name
                    cur.execute("""
                        SELECT id FROM submissions s
                        WHERE LOWER(TRIM(s.company_name)) = LOWER(TRIM(%s))
                        AND NOT EXISTS (
                            SELECT 1 FROM org_submission_links osl WHERE osl.submission_id = s.id
                        )
                    """, (company_name,))
                    sub_ids = [str(r["id"]) for r in cur.fetchall()]

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

        try:
            invalidate_org_cache()
        except Exception as err:
            logger.warning("Cache invalidation failed on create_org: %s", err)

        return {
            "success": True,
            "org": _serialize_row(dict(row)),
            "linked_count": len(sub_ids)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_org failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# Legacy alias: POST /api/manage/orgs/create
@router.post("/create")
async def create_org_legacy(request: Request):
    try:
        body = await request.json()
        name = (body.get("company_name") or body.get("name") or "").strip()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    return await create_org(request, CreateOrgRequest(name=name))


# ---------------------------------------------------------------------------
# GET /api/manage/orgs/unlinked
# Submissions with no org link — optionally filtered by company_name
# ---------------------------------------------------------------------------

@router.get("/unlinked")
async def list_unlinked(company_name: str = None):
    try:
        with get_db_connection() as conn:
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
        return rows
    except Exception as e:
        logger.error("list_unlinked failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /api/manage/orgs/{org_id}
# Org detail with all linked submissions + live weighted scores
# ---------------------------------------------------------------------------

@router.get("/{org_id}")
async def get_org(org_id: UUID):
    oid = str(org_id)
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, is_active, is_deleted, created_at, updated_at
                    FROM organizations
                    WHERE id = %s
                """, (oid,))
                org_row = cur.fetchone()
            if not org_row:
                raise HTTPException(status_code=404, detail="Organisation not found")

            links = _fetch_org_links(conn, oid)
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
# PUT /api/manage/orgs/{org_id}
# Update organization name / metadata
# ---------------------------------------------------------------------------

@router.put("/{org_id}")
async def update_org(org_id: UUID, body: UpdateOrgRequest, request: Request):
    oid = str(org_id)
    name = " ".join(body.name.strip().split())
    if not name:
        raise HTTPException(status_code=400, detail="Organization name is required")

    admin_email = getattr(request.state, "admin_email", "unknown")

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Check for duplicate name
                    cur.execute("""
                        SELECT id FROM organizations
                        WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s)) AND id != %s AND is_deleted = FALSE
                    """, (name, oid))
                    if cur.fetchone():
                        raise HTTPException(status_code=400, detail="Another organization with this name already exists")

                    cur.execute("""
                        UPDATE organizations
                        SET name = %s, updated_at = NOW(), updated_by = %s
                        WHERE id = %s AND is_deleted = FALSE
                        RETURNING id, name, is_active, is_deleted, updated_at
                    """, (name, admin_email, oid))
                    row = cur.fetchone()
                    if not row:
                        raise HTTPException(status_code=404, detail="Organisation not found or has been deleted")

        try:
            invalidate_org_cache()
        except Exception as err:
            logger.warning("Cache invalidation failed on update_org: %s", err)

        return {"success": True, "org": _serialize_row(dict(row))}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_org failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# PATCH /api/manage/orgs/{org_id}/status
# Toggle active / inactive status
# ---------------------------------------------------------------------------

@router.patch("/{org_id}/status")
async def toggle_org_status(org_id: UUID, body: OrgStatusRequest, request: Request):
    oid = str(org_id)
    admin_email = getattr(request.state, "admin_email", "unknown")

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        UPDATE organizations
                        SET is_active = %s, updated_at = NOW(), updated_by = %s
                        WHERE id = %s AND is_deleted = FALSE
                        RETURNING id, name, is_active, is_deleted, updated_at
                    """, (body.is_active, admin_email, oid))
                    row = cur.fetchone()
                    if not row:
                        raise HTTPException(status_code=404, detail="Organisation not found or has been deleted")

        try:
            invalidate_org_cache()
        except Exception as err:
            logger.warning("Cache invalidation failed on toggle_org_status: %s", err)

        return {"success": True, "org": _serialize_row(dict(row))}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("toggle_org_status failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# DELETE /api/manage/orgs/{org_id}
# Soft delete an organisation, revoking its active invitations while preserving
# all historical submissions and scoring data.
# ---------------------------------------------------------------------------

@router.delete("/{org_id}")
async def delete_org(org_id: UUID, request: Request):
    oid = str(org_id)
    admin_email = getattr(request.state, "admin_email", "unknown")

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE organizations
                        SET is_deleted = TRUE, is_active = FALSE, deleted_at = NOW(), deleted_by = %s
                        WHERE id = %s AND is_deleted = FALSE
                        RETURNING id
                    """, (admin_email, oid))
                    if cur.rowcount == 0:
                        raise HTTPException(status_code=404, detail="Organisation not found or already deleted")

                    # Deactivate all active invitations for this organisation
                    cur.execute("""
                        UPDATE organization_invitations
                        SET is_active = FALSE, revoked_at = NOW(), revoked_by = %s
                        WHERE organization_id = %s AND is_active = TRUE
                    """, (admin_email, oid))

        try:
            invalidate_org_cache()
        except Exception as err:
            logger.warning("Cache invalidation failed on delete_org: %s", err)

        return {"success": True, "message": "Organisation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_org failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /api/manage/orgs/{org_id}/restore
# Restore a soft-deleted organisation, reactivating it while preserving
# all historical submissions, answers, scores, and links.
# ---------------------------------------------------------------------------

@router.post("/{org_id}/restore")
async def restore_org(org_id: UUID, request: Request):
    require_admin(request)
    oid = str(org_id)

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE organizations
                        SET is_deleted = FALSE, is_active = TRUE, deleted_at = NULL, deleted_by = NULL
                        WHERE id = %s AND is_deleted = TRUE
                        RETURNING id
                    """, (oid,))
                    if cur.rowcount == 0:
                        raise HTTPException(status_code=404, detail="Organisation not found or not deleted")

        try:
            invalidate_org_cache()
        except Exception as err:
            logger.warning("Cache invalidation failed on restore_org: %s", err)

        return {"success": True, "message": "Organisation restored successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("restore_org failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# SECURE ASSESSMENT LINKS MANAGEMENT
# ---------------------------------------------------------------------------

@router.post("/{org_id}/assessment-links")
async def create_org_assessment_link(org_id: UUID, body: CreateAssessmentLinkRequest, request: Request):
    """
    Generate an opaque secure assessment link (/audit?t=SECURE_TOKEN).
    Eliminates exposure of organisation names or codes in URLs.
    Stores only the SHA-256 hash. Returns the raw token once.
    """
    admin_email = getattr(request.state, "admin_email", "unknown")
    try:
        res = create_assessment_token(
            org_id=org_id,
            campaign_id=body.campaign_id,
            name=body.name,
            created_by=admin_email,
            expires_at=body.expires_at,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("create_org_assessment_link failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create assessment link")


@router.post("/{org_id}/assessment-links/default")
async def get_or_create_org_default_link(org_id: UUID, request: Request):
    """
    Returns or creates the active default secure assessment link for an organisation.
    Ensures that whenever an admin copies an audit link (for old orgs like SKY11 or new ones),
    an opaque secure token link (/audit?t=SECURE_TOKEN) is always delivered,
    preventing any exposure of organisation identifiers in URLs.
    """
    admin_email = getattr(request.state, "admin_email", "admin")
    oid = str(org_id)
    try:
        res = get_or_create_default_token(oid, created_by=admin_email)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("get_or_create_org_default_link failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve default assessment link")


@router.get("/{org_id}/assessment-links")
async def list_org_assessment_links(org_id: UUID):
    """List all secure assessment links for an organisation."""
    oid = str(org_id)
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, organisation_id, campaign_id, name, token, is_default, created_by, created_at,
                           expires_at, revoked_at, revoked_by
                    FROM assessment_access_tokens
                    WHERE organisation_id = %s
                    ORDER BY created_at DESC
                """, (oid,))
                raw_rows = cur.fetchall()
                rows = []
                for r in raw_rows:
                    row_dict = _serialize_row(dict(r))
                    if row_dict.get("token"):
                        row_dict["assessment_url"] = f"/audit?t={row_dict['token']}"
                    rows.append(row_dict)
        return rows
    except Exception as e:
        logger.error("list_org_assessment_links failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list assessment links")


@router.delete("/{org_id}/assessment-links/{token_id}")
async def revoke_org_assessment_link(org_id: UUID, token_id: UUID, request: Request):
    """Revoke an assessment link immediately."""
    admin_email = getattr(request.state, "admin_email", "unknown")
    try:
        success = revoke_assessment_token(token_id=token_id, revoked_by=admin_email)
        if not success:
            raise HTTPException(status_code=404, detail="Assessment link not found or already revoked")
        return {"success": True, "message": "Assessment link revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("revoke_org_assessment_link failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to revoke assessment link")


# ---------------------------------------------------------------------------
# INVITATIONS MANAGEMENT
# ---------------------------------------------------------------------------

@router.post("/{org_id}/invitations")
async def create_invitation(org_id: UUID, body: CreateInvitationRequest, request: Request):
    """
    Generate a reusable invitation link with a cryptographically secure token (32+ bytes).
    Store only the SHA-256 hash. Return raw token only once.
    """
    oid = str(org_id)
    admin_email = getattr(request.state, "admin_email", "unknown")

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, name, is_active, is_deleted
                        FROM organizations
                        WHERE id = %s AND is_deleted = FALSE
                    """, (oid,))
                    org = cur.fetchone()
                    if not org:
                        raise HTTPException(status_code=404, detail="Organisation not found or is deleted")
                    if not org["is_active"]:
                        raise HTTPException(status_code=400, detail="Cannot create invitation for an inactive organisation")

                    inv_name = (body.invitation_name or "").strip() or f"{org['name']} Assessment Link"

                    cur.execute("""
                        INSERT INTO organization_invitations (
                            organization_id, token_hash, invitation_name, created_by,
                            expires_at, max_submissions, is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                        RETURNING id, organization_id, invitation_name, created_by, created_at,
                                  expires_at, is_active, max_submissions, submission_count
                    """, (oid, token_hash, inv_name, admin_email, body.expires_at, body.max_submissions))
                    row = cur.fetchone()

        res = _serialize_row(dict(row))
        res["raw_token"] = raw_token
        res["invite_url"] = f"/invite/{raw_token}"
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_invitation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{org_id}/invitations")
async def list_invitations(org_id: UUID):
    """List all invitations for an organisation."""
    oid = str(org_id)
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, organization_id, invitation_name, created_by, created_at,
                           expires_at, is_active, max_submissions, submission_count,
                           revoked_at, revoked_by
                    FROM organization_invitations
                    WHERE organization_id = %s
                    ORDER BY created_at DESC
                """, (oid,))
                rows = [_serialize_row(dict(r)) for r in cur.fetchall()]
        return rows
    except Exception as e:
        logger.error("list_invitations failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/invitations/{invitation_id}")
async def update_invitation(invitation_id: UUID, body: UpdateInvitationRequest):
    """Update invitation label, expiration, or maximum submissions limit."""
    inv_id = str(invitation_id)
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        UPDATE organization_invitations
                        SET invitation_name = COALESCE(%s, invitation_name),
                            expires_at = %s,
                            max_submissions = %s
                        WHERE id = %s
                        RETURNING id, organization_id, invitation_name, created_by, created_at,
                                  expires_at, is_active, max_submissions, submission_count,
                                  revoked_at, revoked_by
                    """, (
                        body.invitation_name.strip() if body.invitation_name else None,
                        body.expires_at,
                        body.max_submissions,
                        inv_id
                    ))
                    row = cur.fetchone()
                    if not row:
                        raise HTTPException(status_code=404, detail="Invitation not found")

        return _serialize_row(dict(row))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_invitation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invitations/{invitation_id}/revoke")
async def revoke_invitation(invitation_id: UUID, request: Request):
    """Revoke an active invitation link immediately."""
    inv_id = str(invitation_id)
    admin_email = getattr(request.state, "admin_email", "unknown")

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE organization_invitations
                        SET is_active = FALSE, revoked_at = NOW(), revoked_by = %s
                        WHERE id = %s
                        RETURNING id
                    """, (admin_email, inv_id))
                    if cur.rowcount == 0:
                        raise HTTPException(status_code=404, detail="Invitation not found")

        return {"success": True, "message": "Invitation revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("revoke_invitation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invitations/{invitation_id}/regenerate")
async def regenerate_invitation(invitation_id: UUID, request: Request):
    """
    Revoke the existing invitation and generate a fresh token with identical settings.
    Returns the new raw token and link.
    """
    inv_id = str(invitation_id)
    admin_email = getattr(request.state, "admin_email", "unknown")

    new_raw_token = secrets.token_urlsafe(32)
    new_token_hash = hashlib.sha256(new_raw_token.encode("utf-8")).hexdigest()

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        UPDATE organization_invitations
                        SET is_active = FALSE, revoked_at = NOW(), revoked_by = %s
                        WHERE id = %s
                        RETURNING organization_id, invitation_name, expires_at, max_submissions
                    """, (admin_email, inv_id))
                    old_inv = cur.fetchone()
                    if not old_inv:
                        raise HTTPException(status_code=404, detail="Invitation not found")

                    cur.execute("""
                        INSERT INTO organization_invitations (
                            organization_id, token_hash, invitation_name, created_by,
                            expires_at, max_submissions, is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                        RETURNING id, organization_id, invitation_name, created_by, created_at,
                                  expires_at, is_active, max_submissions, submission_count
                    """, (
                        old_inv["organization_id"],
                        new_token_hash,
                        old_inv["invitation_name"],
                        admin_email,
                        old_inv["expires_at"],
                        old_inv["max_submissions"]
                    ))
                    new_row = cur.fetchone()

        res = _serialize_row(dict(new_row))
        res["raw_token"] = new_raw_token
        res["invite_url"] = f"/invite/{new_raw_token}"
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error("regenerate_invitation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


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
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE org_submission_links
                        SET weight = %s
                        WHERE org_id = %s AND submission_id = %s
                    """, (weight, oid, sid))
                    if cur.rowcount == 0:
                        raise HTTPException(status_code=404, detail="Link not found")

            links = _fetch_org_links(conn, oid)
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
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM submissions WHERE id = %s", (submission_id,))
                    if not cur.fetchone():
                        raise HTTPException(status_code=404, detail="Submission not found")

                    cur.execute("SELECT id FROM organizations WHERE id = %s", (oid,))
                    if not cur.fetchone():
                        raise HTTPException(status_code=404, detail="Organisation not found")

                    cur.execute("""
                        INSERT INTO org_submission_links (org_id, submission_id, weight, linked_by)
                        VALUES (%s, %s, 1.0, %s)
                        ON CONFLICT (org_id, submission_id) DO NOTHING
                    """, (oid, submission_id, admin_email))

                    cur.execute("""
                        UPDATE submissions SET organization_id = %s
                        WHERE id = %s AND organization_id IS NULL
                    """, (oid, submission_id))

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("link_submission failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /api/manage/orgs/{org_id}/report-preview
# ---------------------------------------------------------------------------

@router.get("/{org_id}/report-preview")
async def org_report_preview(org_id: UUID):
    oid = str(org_id)
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id, name FROM organizations WHERE id = %s", (oid,))
                org_row = cur.fetchone()
            if not org_row:
                raise HTTPException(status_code=404, detail="Organisation not found")
            links = _fetch_org_links(conn, oid)
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


# ---------------------------------------------------------------------------
# POST /api/manage/orgs/{org_id}/message
# ---------------------------------------------------------------------------

@router.post("/{org_id}/message")
async def send_org_message(org_id: UUID, request: Request):
    try:
        body = await request.json()
        subject    = (body.get("subject") or "").strip()
        message    = (body.get("body") or "").strip()
        recipients = body.get("recipients", [])
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
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    sender_address, sender_name = get_sender_for_send(cur)

                    if is_org_report:
                        links = _fetch_org_links(conn, oid)
                        scores = calc_weighted_org_score(links)
                        if not scores:
                            raise HTTPException(status_code=400, detail="No linked submissions to report on")
                        cur.execute("SELECT name FROM organizations WHERE id = %s", (oid,))
                        org_row = cur.fetchone()
                        org_name = org_row["name"] if org_row else "Your Organisation"
                        email_html = build_org_summary_email(org_name, scores, scores["respondents"])
                        email_plain = f"Organisation Audit Summary for {org_name}\n\nOverall Score: {scores['org_avg']}/20 — {scores['org_level']}"
                    else:
                        email_html  = f"<p>{message.replace(chr(10), '<br>')}</p>"
                        email_plain = message

                    import json
                    cur.execute("""
                        INSERT INTO admin_messages (org_id, sent_by, subject, body, recipients)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (oid, admin_email, subject, message or "(org report)", json.dumps(recipients)))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("send_org_message failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

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
                with get_db_connection() as conn:
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
                
                from app.api.routes import dashboard_cache
                dashboard_cache.clear()
            except Exception as update_err:
                logger.error("Failed to update submission status after sending org report: %s", update_err)

    if errors:
        return {"success": False, "failed_recipients": errors}
    return {"success": True, "sent_count": len(recipients)}
