"""
security.py — Security utilities
Password hashing, token validation, and other security helpers.
"""

import jwt
import requests
import os
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from functools import lru_cache, wraps
import logging

logger = logging.getLogger(__name__)

TENANT_ID = os.environ.get("ENTRA_TENANT_ID", "YOUR_TENANT_ID")
CLIENT_ID = os.environ.get("ENTRA_CLIENT_ID", "YOUR_CLIENT_ID")
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

@lru_cache(maxsize=1)
def get_jwks():
    try:
        response = requests.get(JWKS_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        return {"keys": []}

def verify_jwt(token: str):
    jwks = get_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token header")

    rsa_key = {}
    for key in jwks.get("keys", []):
        if key.get("kid") == unverified_header.get("kid"):
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            break
    
    if not rsa_key:
        raise HTTPException(status_code=401, detail="Invalid token kid")
    
    try:
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        logger.info(f"Unverified token payload: iss={unverified_payload.get('iss')}, aud={unverified_payload.get('aud')}, tid={unverified_payload.get('tid')}")
    except Exception as ex:
        logger.error(f"Failed to decode unverified token: {ex}")

    try:
        payload = jwt.decode(
            token,
            jwt.algorithms.RSAAlgorithm.from_jwk(rsa_key),
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=[
                f"https://sts.windows.net/{TENANT_ID}/",
                f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
            ]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT Decode failed: {e}")
        try:
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            token_iss = unverified_payload.get("iss")
            token_aud = unverified_payload.get("aud")
            msg = f"Invalid token: {e}. Token iss: {token_iss}, Expected one of: https://sts.windows.net/{TENANT_ID}/, https://login.microsoftonline.com/{TENANT_ID}/v2.0. Token aud: {token_aud}, Expected: {CLIENT_ID}"
        except Exception:
            msg = f"Invalid token: {e}"
        raise HTTPException(status_code=401, detail=msg)

async def jwks_middleware(request: Request, call_next):
    # Only protect admin endpoints
    protected_paths = ["/api/manage", "/api/settings", "/api/submissions"]
    
    # Exceptions that are public
    if request.url.path == "/api/submit" or request.url.path == "/api/auth/verify" or request.url.path == "/api/health" or request.url.path == "/api/support":
        return await call_next(request)
        
    is_protected = any(request.url.path.startswith(p) for p in protected_paths)
    if is_protected:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization header"})
        
        token = auth_header.split(" ")[1]
        try:
            # Check for local developer login bypass
            if (TENANT_ID == "YOUR_TENANT_ID" or os.environ.get("ENABLE_DEV_BYPASS") == "true") and token.startswith("local_bypass:"):
                email = token.split("local_bypass:")[1].lower()
                from app.core.database import get_conn
                conn = get_conn()
                with conn.cursor() as cur:
                    cur.execute("SELECT role FROM admin_users WHERE email = %s", (email,))
                    row = cur.fetchone()
                conn.close()
                if not row:
                    return JSONResponse(status_code=401, content={"detail": "Unauthorized developer email"})
                request.state.admin_email = email
            else:
                payload = verify_jwt(token)
                # Store the admin email in the request state for the audit logger
                request.state.admin_email = payload.get("preferred_username") or payload.get("unique_name") or "unknown"
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception as e:
            logger.error("JWKS middleware error: %s", e)
            return JSONResponse(status_code=401, content={"detail": "Token validation failed"})
            
    return await call_next(request)

def audit_log(action_type: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs if possible
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            admin_email = getattr(request.state, "admin_email", "unknown") if request else "unknown"
            ip = request.client.host if request and request.client else "unknown"
            
            # Execute the actual endpoint
            response = await func(*args, **kwargs)
            
            # Log action post-execution
            from app.core.database import get_conn
            try:
                conn = get_conn()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO audit_logs (admin_id, action_type, ip_address)
                            VALUES (%s, %s, %s)
                        """, (admin_email, action_type, ip))
                conn.close()
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
                
            return response
        return wrapper
    return decorator
