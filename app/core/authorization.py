"""
authorization.py — Authorization and access control for NIWI
Implements two administrator roles: Normal Admin ('admin') and Super Admin ('super').
Both roles have global organization and submission visibility.
Super Admin retains exclusive privileges for user management and destructive actions.
"""

import logging
import os
from typing import List, Optional
from fastapi import Request, HTTPException, Depends
import jwt
import psycopg2.extras
from app.core.database import get_conn

logger = logging.getLogger(__name__)


def get_user_from_request(request: Request) -> dict:
    """
    Extract user information from request state (populated by middleware) or Authorization header.
    Returns dict with 'email' and 'role' fields.
    Raises HTTPException(401) if authentication is missing or invalid.
    Raises HTTPException(403) if user is not in admin_users.
    """
    # 1. Fast path: populated by jwks_middleware
    admin_email = getattr(request.state, "admin_email", None) if hasattr(request, "state") else None
    admin_role = getattr(request.state, "admin_role", None) if hasattr(request, "state") else None
    if isinstance(admin_email, str) and isinstance(admin_role, str) and admin_email and admin_role:
        return {"email": admin_email, "role": admin_role}

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(" ")[1]
    
    # Check for dev bypass
    app_env = os.environ.get("APP_ENV", os.environ.get("ENVIRONMENT", "production")).lower()
    is_dev_env = app_env in ("development", "dev", "test", "testing") or os.environ.get("TESTING") == "true"
    enable_dev_bypass = os.environ.get("ENABLE_DEV_BYPASS", "").lower() in ("true", "1")
    
    if enable_dev_bypass and not is_dev_env:
        enable_dev_bypass = False
    
    # Handle dev bypass
    if is_dev_env and enable_dev_bypass and token.startswith("local_bypass:"):
        email = token.split("local_bypass:")[1].lower()
        
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT email, role FROM admin_users WHERE LOWER(email) = LOWER(%s)",
                    (email,)
                )
                row = cur.fetchone()
            
            if not row:
                raise HTTPException(status_code=403, detail=f"User {email} not authorized")
            
            return {"email": row["email"], "role": row["role"]}
        finally:
            conn.close()
    
    # Production / standard JWT decode
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        email = (
            payload.get("preferred_username")
            or payload.get("email")
            or payload.get("upn")
            or payload.get("unique_name")
        )
        
        if not email:
            logger.error(f"JWT token missing email claims: {list(payload.keys())}")
            raise HTTPException(status_code=401, detail="Token missing email claim")
        
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT email, role FROM admin_users WHERE LOWER(email) = LOWER(%s)",
                    (email.lower(),)
                )
                row = cur.fetchone()
            
            if not row:
                raise HTTPException(status_code=403, detail=f"User {email} not authorized")
            
            return {"email": row["email"], "role": row["role"]}
        finally:
            conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extract user from token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def require_admin(request: Request) -> dict:
    """
    Dependency that requires an authenticated administrator (Normal Admin or Super Admin).
    Raises HTTP 401 if unauthenticated, HTTP 403 if role is not authorized.
    """
    user = get_user_from_request(request)
    role = user.get("role", "").lower()
    if role not in ("admin", "super"):
        raise HTTPException(status_code=403, detail="Administrator privileges required")
    return user


def require_super_admin(request: Request) -> dict:
    """
    Dependency that strictly requires a Super Admin role.
    Normal Admins receive HTTP 403 Forbidden.
    Unauthenticated users receive HTTP 401 Unauthorized.
    """
    user = get_user_from_request(request)
    role = user.get("role", "").lower()
    if role != "super":
        raise HTTPException(status_code=403, detail="Super administrator privileges required")
    return user


def get_admin_organizations(admin_email: str, admin_role: str, conn=None) -> Optional[List[str]]:
    """
    In the agreed permission model, both Normal Admin ('admin') and Super Admin ('super')
    have global access to all organizations.
    Returns None (representing unrestricted, global access).
    """
    return None


def filter_submissions_by_org_access(
    query: str,
    params: tuple,
    admin_email: str,
    admin_role: str,
    conn=None
) -> tuple:
    """
    Both Normal Admin and Super Admin have global access across all submissions.
    Returns query and params unchanged.
    """
    return (query, params)


def check_submission_access(
    submission_id: str,
    admin_email: str,
    admin_role: str,
    conn=None
) -> bool:
    """
    Both Normal Admin and Super Admin have access to all submissions.
    """
    return True
