"""
config.py — Application configuration
Reads environment variables for DB, ACS, and app settings.
"""
import os

PGHOST       = os.environ.get("PGHOST", "localhost")
PGPORT       = os.environ.get("PGPORT", "5432")
PGDATABASE   = os.environ.get("PGDATABASE", "nd_audit")
PGUSER       = os.environ.get("PGUSER", "postgres")
PGPASSWORD   = os.environ.get("PGPASSWORD", "")

ACS_CONNECTION_STRING = os.environ.get("ACS_CONNECTION_STRING", "")
ACS_SENDER_ADDRESS    = os.environ.get("ACS_SENDER_ADDRESS", "")

APP_ENV = os.environ.get("APP_ENV", os.environ.get("ENVIRONMENT", "production")).lower()
IS_DEV_OR_TEST = APP_ENV in ("development", "dev", "test", "testing") or os.environ.get("TESTING") == "true"

raw_jwt_secret = os.environ.get("JWT_SECRET", "").strip()

# Prohibited weak / placeholder secrets
PROHIBITED_SECRETS = {
    "",
    "default_jwt_secret_key_change_me",
    "your-jwt-secret-signing-key",
    "change_me",
    "secret",
}

if not raw_jwt_secret or raw_jwt_secret in PROHIBITED_SECRETS:
    if IS_DEV_OR_TEST:
        # Development / test fallback only when explicitly declared
        JWT_SECRET = "dev-insecure-only-local-testing-secret-key-32chars-min!!"
    else:
        raise RuntimeError(
            "FATAL: Missing or insecure JWT_SECRET configuration. "
            "A strong secret key of at least 32 characters must be configured in environment variables. "
            "Insecure default fallbacks are strictly prohibited."
        )
elif len(raw_jwt_secret) < 32 and not IS_DEV_OR_TEST:
    raise RuntimeError(
        "FATAL: JWT_SECRET is too short for production use. "
        "A strong secret key of at least 32 characters is required."
    )
else:
    JWT_SECRET = raw_jwt_secret

CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,https://niwi.orchvate.in"
).split(",")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://niwi.orchvate.in").rstrip("/")

# Microsoft Entra ID (public — exposed via GET /api/auth/config for browser MSAL)
ENTRA_CLIENT_ID = os.environ.get("ENTRA_CLIENT_ID", "")
ENTRA_TENANT_ID = os.environ.get("ENTRA_TENANT_ID", "")

