"""
public.py — Public endpoints for NIWI Assessment Dual Entry.
- POST /api/public/organisations/validate: Validate organisation name for direct assessment
- POST /api/public/invitations/validate: Validate invitation token for invitation-based assessment
"""

import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel, Field
import psycopg2.extras

from app.core.database import get_db_connection
from app.core.limiter import limiter
from app.services.org_cache_service import get_organisation_by_name, is_org_eligible
from app.services.email_policy_service import check_corporate_email_eligibility
from app.services.token_service import resolve_assessment_token, get_or_create_default_token

router = APIRouter(prefix="/public", tags=["Public Assessment"])
logger = logging.getLogger(__name__)


class ValidateInvitationRequest(BaseModel):
    token: str = Field(..., min_length=1)


class ValidateOrganisationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ValidateEmailRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)


class ResolveLinkRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=512)


class ResolveLegacyOrgRequest(BaseModel):
    org: str = Field(..., min_length=1, max_length=255)


@router.post("/assessment/resolve-link")
@limiter.limit("120/minute")
async def resolve_assessment_link_endpoint(request: Request, body: ResolveLinkRequest):
    """
    Resolves a secure assessment token to its organisation and campaign context.
    Eliminates exposure of organisation names and codes in URLs.
    """
    raw_token = body.token.strip()
    if not raw_token:
        raise HTTPException(status_code=400, detail="Token is required")
    
    try:
        result = resolve_assessment_token(raw_token)
        return result
    except Exception as e:
        logger.error("resolve_assessment_link failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to resolve assessment link")


@router.post("/assessment/resolve-legacy-org")
@limiter.limit("120/minute")
async def resolve_legacy_org(request: Request, body: ResolveLegacyOrgRequest):
    """
    Backward compatibility endpoint for legacy links (?org=SKY11).
    Resolves the organisation securely from cache, ensures a secure opaque token exists,
    and returns the secure token and masked assessment URL so the frontend can
    instantly replace the URL in the address bar without exposing the organisation name.
    """
    org_name = body.org.strip()
    if not org_name:
        raise HTTPException(status_code=400, detail="Organisation name is required")

    org, _ = get_organisation_by_name(org_name)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    eligible, err = is_org_eligible(org)
    if not eligible:
        raise HTTPException(status_code=400, detail=err or "Organisation is inactive")

    try:
        token_info = get_or_create_default_token(org["id"])
        return {
            "valid": True,
            "token": token_info["raw_token"],
            "organization_id": str(org["id"]),
            "organization_name": org["name"],
            "assessment_url": f"/audit?t={token_info['raw_token']}",
        }
    except Exception as e:
        logger.error("resolve_legacy_org failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to resolve organisation link")


@router.post("/email/validate")
@limiter.limit("120/minute")
async def validate_corporate_email(request: Request, body: ValidateEmailRequest):
    """
    Checks corporate email eligibility without requiring OTP or mailbox authentication.
    Accepts any corporate domain and rejects known personal/free email providers.
    """
    return check_corporate_email_eligibility(body.email)


@router.post("/organisations/validate")
@limiter.limit("120/minute")
async def validate_organisation_by_name(request: Request, body: ValidateOrganisationRequest):
    """
    Validates a manually entered organisation name against existing records.
    Returns minimal information without exposing organisation directory.
    Uses high-performance in-memory organisation registry cache with sub-10ms latency.
    """
    name = body.name.strip()
    if not name:
        return {
            "valid": False,
            "error": "Organisation name cannot be empty"
        }
    
    try:
        org, source = get_organisation_by_name(name)
        if not org:
            return {
                "valid": False,
                "error": "We couldn't find this organisation. Please check the spelling or contact your administrator."
            }
        
        eligible, err = is_org_eligible(org)
        if not eligible:
            return {
                "valid": False,
                "error": err
            }
        
        return {
            "valid": True,
            "organization_id": str(org["id"]),
            "organization_name": org["name"]  # Return canonical spelling
        }
    except Exception as e:
        logger.error("validate_organisation_by_name failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to validate organisation")


@router.post("/invitations/validate")
@limiter.limit("30/minute")
async def validate_invitation(request: Request, body: ValidateInvitationRequest):
    """
    Validates an invitation token without leaking sensitive org internals.
    Derives whether the token is valid, active, non-expired, and within limits.
    """
    raw_token = body.token.strip()
    if not raw_token:
        raise HTTPException(status_code=400, detail="Token is required")

    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        oi.id AS invitation_id,
                        oi.organization_id,
                        oi.invitation_name,
                        oi.expires_at,
                        oi.is_active AS invitation_active,
                        oi.max_submissions,
                        oi.submission_count,
                        oi.revoked_at,
                        o.name AS organization_name,
                        o.is_active AS org_active,
                        o.is_deleted AS org_deleted
                    FROM organization_invitations oi
                    JOIN organizations o ON o.id = oi.organization_id
                    WHERE oi.token_hash = %s
                """, (token_hash,))
                inv = cur.fetchone()

        if not inv:
            return {
                "valid": False,
                "error": "This invitation link is invalid or does not exist."
            }

        # Check organization status
        if inv["org_deleted"] or not inv["org_active"]:
            return {
                "valid": False,
                "error": "The organization associated with this invitation is inactive."
            }

        # Check invitation status
        if not inv["invitation_active"] or inv["revoked_at"] is not None:
            return {
                "valid": False,
                "error": "This invitation link has been revoked or deactivated."
            }

        # Check expiration
        now = datetime.now(timezone.utc)
        if inv["expires_at"] and inv["expires_at"] < now:
            return {
                "valid": False,
                "error": "This invitation link has expired."
            }

        # Check maximum submissions limit
        if inv["max_submissions"] is not None and inv["submission_count"] >= inv["max_submissions"]:
            return {
                "valid": False,
                "error": "This invitation link has reached its maximum allowed submissions."
            }

        return {
            "valid": True,
            "organization_name": inv["organization_name"],
            "invitation_name": inv["invitation_name"] or "Assessment Invitation",
            "expires_at": inv["expires_at"].isoformat() if inv["expires_at"] else None,
            "submission_count": inv["submission_count"],
            "max_submissions": inv["max_submissions"],
        }
    except Exception as e:
        logger.error("validate_invitation failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to validate invitation")
