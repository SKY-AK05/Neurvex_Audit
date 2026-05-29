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

JWT_SECRET   = os.environ.get("JWT_SECRET", "default_jwt_secret_key_change_me")
CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,https://neuromark.orchvate.in"
).split(",")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://neuromark.orchvate.in").rstrip("/")

# Microsoft Entra ID (public — exposed via GET /api/auth/config for browser MSAL)
ENTRA_CLIENT_ID = os.environ.get("ENTRA_CLIENT_ID", "")
ENTRA_TENANT_ID = os.environ.get("ENTRA_TENANT_ID", "")
