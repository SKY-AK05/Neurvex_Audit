"""
token_service.py — Secure Assessment Access Token Service
Generates cryptographically random 256-bit access tokens, stores SHA-256 hashes,
and resolves assessment links securely without exposing organisation identifiers in URLs.
Provides backward compatibility for existing organization invitations.
"""

import base64
import hashlib
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import psycopg2.extras
from cryptography.fernet import Fernet

from app.core.config import JWT_SECRET
from app.core.database import get_db_connection

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(JWT_SECRET.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_org_token(org_id: str | UUID, org_name: str) -> str:
    """Creates a URL-safe encrypted assessment token."""
    f = _get_fernet()
    data = json.dumps({"org_id": str(org_id), "org_name": org_name}).encode("utf-8")
    enc = f.encrypt(data).decode("utf-8")
    return f"enc_{enc}"


def decrypt_org_token(token_str: str) -> Optional[dict[str, Any]]:
    """Decrypts an encrypted assessment token. Returns None if invalid or corrupted."""
    if not token_str or not isinstance(token_str, str):
        return None
    raw = token_str.strip()
    if raw.startswith("enc_"):
        raw = raw[4:]
    try:
        f = _get_fernet()
        dec = f.decrypt(raw.encode("utf-8")).decode("utf-8")
        return json.loads(dec)
    except Exception:
        return None


def generate_secure_token() -> str:
    """Generates a cryptographically random, URL-safe 256-bit access token."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hash of a raw token. Only hashes are stored or queried in the database."""
    if not raw_token or not isinstance(raw_token, str):
        return ""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def create_assessment_token(
    org_id: str | UUID,
    campaign_id: Optional[str | UUID] = None,
    name: Optional[str] = None,
    created_by: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    is_default: bool = False,
) -> dict[str, Any]:
    """
    Creates a new secure access token for an organisation and optional campaign.
    Persists only the SHA-256 hash and preserved token. Returns the raw token once for link delivery.
    """
    raw_token = generate_secure_token()
    token_hash = hash_token(raw_token)
    oid = str(org_id)
    cid = str(campaign_id) if campaign_id else None

    with get_db_connection() as conn:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Verify organisation exists and is active
                cur.execute("""
                    SELECT id, name, is_active, is_deleted, approval_status
                    FROM organizations
                    WHERE id = %s AND is_deleted = FALSE
                """, (oid,))
                org = cur.fetchone()
                if not org:
                    raise ValueError("Organisation not found or has been deleted.")
                if not org["is_active"]:
                    raise ValueError("Cannot create assessment link for an inactive organisation.")

                link_name = (name or "").strip() or f"{org['name']} Assessment Link"

                cur.execute("""
                    INSERT INTO assessment_access_tokens (
                        organisation_id, token_hash, token, campaign_id, name, is_default, created_by, expires_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, organisation_id, campaign_id, name, is_default, created_by, created_at, expires_at
                """, (oid, token_hash, raw_token, cid, link_name, is_default, created_by, expires_at))
                row = cur.fetchone()

    return {
        "id": str(row["id"]),
        "organisation_id": str(row["organisation_id"]),
        "campaign_id": str(row["campaign_id"]) if row["campaign_id"] else None,
        "name": row["name"],
        "is_default": bool(row.get("is_default", False)),
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
        "raw_token": raw_token,
        "assessment_url": f"/audit?t={raw_token}",
    }


def get_or_create_default_token(
    org_id: str | UUID,
    created_by: Optional[str] = None,
) -> dict[str, Any]:
    """
    Retrieves the active default assessment token for an organisation, or creates one if none exists.
    Guarantees that an organisation (including historical organisations like SKY11) has an opaque,
    secure assessment link (/audit?t=SECURE_TOKEN) ready for instant copying.
    """
    oid = str(org_id)
    now = datetime.now(timezone.utc)

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # 1. Check for existing active token with raw_token preserved
                    cur.execute("""
                        SELECT id, organisation_id, campaign_id, name, token, is_default, created_by, created_at, expires_at
                        FROM assessment_access_tokens
                        WHERE organisation_id = %s
                          AND revoked_at IS NULL
                          AND (expires_at IS NULL OR expires_at > %s)
                          AND token IS NOT NULL
                        ORDER BY is_default DESC, created_at DESC
                        LIMIT 1
                    """, (oid, now))
                    row = cur.fetchone()

                    if row and row.get("token"):
                        raw_token = row["token"]
                        return {
                            "id": str(row["id"]),
                            "organisation_id": str(row["organisation_id"]),
                            "campaign_id": str(row["campaign_id"]) if row["campaign_id"] else None,
                            "name": row["name"],
                            "is_default": bool(row.get("is_default", False)),
                            "created_by": row["created_by"],
                            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                            "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
                            "raw_token": raw_token,
                            "assessment_url": f"/audit?t={raw_token}",
                        }
    except Exception as e:
        logger.warning("Failed to lookup existing default token for %s: %s", oid, e)

    # If no active token with preserved raw_token, create a new default one
    return create_assessment_token(
        org_id=oid,
        name="Corporate Assessment Link",
        created_by=created_by or "system",
        is_default=True,
    )


def resolve_assessment_token(raw_token: str) -> dict[str, Any]:
    """
    Resolves a raw access token to its secure assessment context.
    Checks assessment_access_tokens first, then falls back to organization_invitations
    for backward compatibility.
    Validates token revocation, expiration, and organisation active/approved status.
    """
    if not raw_token or not isinstance(raw_token, str) or not raw_token.strip():
        return {
            "valid": False,
            "error": "Access token is required.",
        }

    token_hash = hash_token(raw_token)

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # 1. Check assessment_access_tokens
                cur.execute("""
                    SELECT 
                        aat.id AS token_id,
                        aat.organisation_id,
                        aat.campaign_id,
                        aat.name AS link_name,
                        aat.expires_at,
                        aat.revoked_at,
                        o.name AS organization_name,
                        o.is_active AS org_active,
                        o.is_deleted AS org_deleted,
                        o.approval_status AS org_approval
                    FROM assessment_access_tokens aat
                    JOIN organizations o ON o.id = aat.organisation_id
                    WHERE aat.token_hash = %s
                """, (token_hash,))
                record = cur.fetchone()

                # 2. Backward compatibility fallback: check organization_invitations
                is_legacy_invitation = False
                if not record:
                    cur.execute("""
                        SELECT 
                            oi.id AS token_id,
                            oi.organization_id AS organisation_id,
                            NULL::uuid AS campaign_id,
                            oi.invitation_name AS link_name,
                            oi.expires_at,
                            oi.revoked_at,
                            oi.is_active AS inv_active,
                            oi.max_submissions,
                            oi.submission_count,
                            o.name AS organization_name,
                            o.is_active AS org_active,
                            o.is_deleted AS org_deleted,
                            o.approval_status AS org_approval
                        FROM organization_invitations oi
                        JOIN organizations o ON o.id = oi.organization_id
                        WHERE oi.token_hash = %s
                    """, (token_hash,))
                    record = cur.fetchone()
                    is_legacy_invitation = True

        if not record:
            decrypted = decrypt_org_token(raw_token)
            if decrypted and decrypted.get("org_id"):
                from app.services.org_cache_service import get_organisation_by_id, is_org_eligible
                org, _ = get_organisation_by_id(decrypted["org_id"])
                if org:
                    eligible, err = is_org_eligible(org)
                    if not eligible:
                        return {
                            "valid": False,
                            "error": err or "The organisation associated with this link is inactive.",
                        }
                    return {
                        "valid": True,
                        "token_id": "encrypted",
                        "organization_name": org["name"],
                        "organization_id": str(org["id"]),
                        "campaign_id": None,
                        "link_name": f"{org['name']} Corporate Assessment",
                        "expires_at": None,
                        "is_legacy_invitation": False,
                    }

            return {
                "valid": False,
                "error": "This assessment link is invalid or does not exist.",
            }

        # Check organisation health
        is_deleted = bool(record.get("org_deleted", False))
        is_active = bool(record.get("org_active", True))
        if is_deleted or not is_active:
            return {
                "valid": False,
                "error": "The organisation associated with this assessment link is inactive.",
            }

        if record.get("org_approval") and record["org_approval"] != "approved":
            return {
                "valid": False,
                "error": "The organisation associated with this assessment link is pending administrative approval.",
            }

        # Check revocation
        if record.get("revoked_at") is not None:
            return {
                "valid": False,
                "error": "This assessment link has been revoked.",
            }

        if is_legacy_invitation and not record.get("inv_active", True):
            return {
                "valid": False,
                "error": "This assessment link has been deactivated.",
            }

        # Check expiration
        now = datetime.now(timezone.utc)
        if record["expires_at"] and record["expires_at"] < now:
            return {
                "valid": False,
                "error": "This assessment link has expired.",
            }

        # Check submission count limit for legacy invitations
        if is_legacy_invitation and record.get("max_submissions") is not None:
            if record.get("submission_count", 0) >= record["max_submissions"]:
                return {
                    "valid": False,
                    "error": "This assessment link has reached its maximum allowed submission limit.",
                }

        token_id = str(record.get("token_id") or record.get("id") or "")
        org_id = str(record.get("organisation_id") or record.get("organization_id") or "")
        org_name = record.get("organization_name") or record.get("org_name") or ""
        link_name = record.get("link_name") or record.get("invitation_name") or "Corporate Assessment"
        campaign_id = str(record["campaign_id"]) if record.get("campaign_id") else None
        expires_at_iso = record["expires_at"].isoformat() if record.get("expires_at") else None

        return {
            "valid": True,
            "token_id": token_id,
            "organization_name": org_name,
            "organization_id": org_id,
            "campaign_id": campaign_id,
            "link_name": link_name,
            "expires_at": expires_at_iso,
            "is_legacy_invitation": is_legacy_invitation,
        }

    except Exception as e:
        logger.error("Failed to resolve assessment token: %s", e)
        raise


def revoke_assessment_token(token_id: str | UUID, revoked_by: str) -> bool:
    """Revokes an assessment access token immediately."""
    tid = str(token_id)
    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE assessment_access_tokens
                    SET revoked_at = NOW(), revoked_by = %s
                    WHERE id = %s AND revoked_at IS NULL
                """, (revoked_by, tid))
                return cur.rowcount > 0
