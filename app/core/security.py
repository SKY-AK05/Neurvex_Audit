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
        logger.info(f"Expected parameters in security.py: TENANT_ID={TENANT_ID}, CLIENT_ID={CLIENT_ID}")
    except Exception as ex:
        logger.error(f"Failed to decode unverified token: {ex}")

    VALID_ISSUERS = [
        f"https://sts.windows.net/{TENANT_ID}/",
        f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
    ]
    try:
        # Decode without issuer check first (PyJWT 2.x does not support list issuers)
        decode_opts = {"verify_iss": False, "verify_aud": False}
        payload = jwt.decode(
            token,
            jwt.algorithms.RSAAlgorithm.from_jwk(rsa_key),
            algorithms=["RS256"],
            options=decode_opts,
        )
        token_aud = payload.get("aud")
        valid_audiences = {CLIENT_ID}
        if isinstance(token_aud, list):
            if not valid_audiences.intersection(token_aud):
                raise jwt.InvalidTokenError(f"Invalid audience: {token_aud}")
        elif token_aud not in valid_audiences:
            raise jwt.InvalidTokenError(f"Invalid audience: {token_aud}")
        # Manually validate issuer against both v1 and v2 endpoints
        token_iss = payload.get("iss", "")
        if token_iss not in VALID_ISSUERS:
            logger.error(f"JWT issuer rejected: got={token_iss}, accepted={VALID_ISSUERS}")
            raise HTTPException(status_code=401, detail=f"Invalid issuer: {token_iss}")
        logger.info(f"JWT validated successfully for iss={token_iss}")
        return payload
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT Decode failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

async def jwks_middleware(request: Request, call_next):
    # Only protect admin endpoints
    protected_paths = ["/api/manage", "/api/settings", "/api/submissions"]
    
    # Exceptions that are public
    if request.url.path in (
        "/api/submit",
        "/api/auth/verify",
        "/api/auth/config",
        "/api/health",
        "/api/support",
        "/api/book-call",
    ) or request.url.path.startswith("/api/org/") or request.url.path.startswith("/api/drafts"):
        return await call_next(request)

    # Form builder modifications (POST, PUT, DELETE) must require admin auth
    is_form_mutation = request.url.path.startswith("/api/form") and request.method not in ("GET", "HEAD", "OPTIONS")
    is_protected = any(request.url.path.startswith(p) for p in protected_paths) or is_form_mutation
    
    if is_protected:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization header"})
        
        token = auth_header.split(" ")[1]
        try:
            # Check for local developer login bypass — ONLY when explicitly enabled in dev/test environment
            app_env = os.environ.get("APP_ENV", os.environ.get("ENVIRONMENT", "production")).lower()
            is_dev_env = app_env in ("development", "dev", "test", "testing") or os.environ.get("TESTING") == "true"
            enable_dev_bypass = os.environ.get("ENABLE_DEV_BYPASS", "").lower() in ("true", "1")

            if is_dev_env and enable_dev_bypass and token.startswith("local_bypass:"):
                email = token.split("local_bypass:")[1].lower()
                from app.core.database import get_conn
                conn = get_conn()
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT role FROM admin_users WHERE LOWER(email) = %s", (email,))
                        row = cur.fetchone()
                    if not row:
                        return JSONResponse(status_code=401, content={"detail": "Unauthorized developer email"})
                    request.state.admin_email = email
                    request.state.admin_role = row[0] if row else "admin"
                finally:
                    conn.close()
            else:
                # Microsoft Entra ID verification
                payload = verify_jwt(token)
                admin_email = (
                    payload.get("preferred_username")
                    or payload.get("unique_name")
                    or payload.get("email")
                    or "unknown"
                ).lower()
                
                # Verify that the Entra ID user is an authorized admin in admin_users
                from app.core.database import get_conn
                try:
                    conn = get_conn()
                    with conn.cursor() as cur:
                        cur.execute("SELECT role FROM admin_users WHERE LOWER(email) = %s", (admin_email,))
                        row = cur.fetchone()
                    conn.close()
                    if not row:
                        # User authenticated with Entra ID but not authorized in the app
                        return JSONResponse(
                            status_code=403,
                            content={"detail": "Forbidden: You are not an authorized administrator"}
                        )
                    request.state.admin_role = row[0]
                except Exception as db_err:
                    logger.warning("Could not verify admin role in DB: %s", db_err)
                    request.state.admin_role = "admin"

                request.state.admin_email = admin_email

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
