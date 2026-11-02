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

router = APIRouter(prefix="/public", tags=["Public Assessment"])
logger = logging.getLogger(__name__)


class ValidateInvitationRequest(BaseModel):
    token: str = Field(..., min_length=1)


class ValidateOrganisationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


@router.post("/organisations/validate")
@limiter.limit("60/minute")
async def validate_organisation_by_name(request: Request, body: ValidateOrganisationRequest):
    """
    Validates a manually entered organisation name against existing records.
    Returns minimal information without exposing organisation directory.
    Uses case-insensitive, whitespace-normalized matching.
    """
    name = body.name.strip()
    if not name:
        return {
            "valid": False,
            "error": "Organisation name cannot be empty"
        }
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Case-insensitive, whitespace-normalized lookup
                cur.execute("""
                    SELECT id, name
                    FROM organizations
                    WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))
                    AND is_active = TRUE 
                    AND is_deleted = FALSE
                """, (name,))
                org = cur.fetchone()
        
        if org:
            return {
                "valid": True,
                "organization_id": str(org["id"]),
                "organization_name": org["name"]  # Return canonical spelling
            }
        else:
            return {
                "valid": False,
                "error": "We couldn't find this organisation. Please check the spelling or contact your administrator."
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
