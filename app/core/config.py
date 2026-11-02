"""
config.py — Application configuration with Key Vault support
Retrieves secrets from Azure Key Vault in production, environment variables in development.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Explicit environment validation
ALLOWED_DEV_TEST_ENVS = {"development", "dev", "test", "testing", "local"}
ALLOWED_PROD_ENVS = {"production", "prod"}
ALL_VALID_ENVS = ALLOWED_DEV_TEST_ENVS | ALLOWED_PROD_ENVS

raw_app_env = os.environ.get("APP_ENV", os.environ.get("APP-ENV", os.environ.get("ENVIRONMENT", "development")))
APP_ENV = raw_app_env.strip().lower() if raw_app_env else "development"

# Unknown environments must fail safely
if APP_ENV not in ALL_VALID_ENVS:
    raise RuntimeError(
        f"FATAL: Unrecognized or invalid environment APP_ENV='{raw_app_env}'. "
        f"Allowed values are: {sorted(ALL_VALID_ENVS)}. Unknown environments fail safely."
    )

IS_PRODUCTION = APP_ENV in ALLOWED_PROD_ENVS
IS_DEV_OR_TEST = APP_ENV in ALLOWED_DEV_TEST_ENVS
REQUIRE_KEYVAULT = os.environ.get("REQUIRE_KEYVAULT", "").lower() in ("true", "1")

# Load .env file ONLY for explicit local development or testing, and NEVER when REQUIRE_KEYVAULT is set
if IS_DEV_OR_TEST and not REQUIRE_KEYVAULT:
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

# Import keyvault after environment is set
from app.core import keyvault

try:
    keyvault.init_keyvault()
    KEYVAULT_AVAILABLE = keyvault.is_using_keyvault()
except Exception as kv_err:
    if (IS_PRODUCTION or REQUIRE_KEYVAULT) and os.environ.get("TESTING") != "true":
        raise RuntimeError(f"FATAL: Key Vault initialization failed in required environment: {kv_err}")
    KEYVAULT_AVAILABLE = False

# ============================================================================
# Database Configuration
# ============================================================================

if KEYVAULT_AVAILABLE:
    db_config = keyvault.get_database_config()
    PGHOST = db_config["host"]
    PGPORT = db_config["port"]
    PGDATABASE = db_config["database"]
    PGUSER = db_config["user"]
    PGPASSWORD = db_config["password"]
else:
    PGHOST = os.environ.get("PGHOST", "localhost")
    PGPORT = os.environ.get("PGPORT", "5432")
    PGDATABASE = os.environ.get("PGDATABASE", "nd_audit")
    PGUSER = os.environ.get("PGUSER", "postgres")
    PGPASSWORD = os.environ.get("PGPASSWORD", "")

PROHIBITED_PASSWORDS = {
    "",
    "Coffee!92",
    "password",
    "postgres",
    "admin",
}

if IS_PRODUCTION:
    if not PGPASSWORD or PGPASSWORD in PROHIBITED_PASSWORDS or len(PGPASSWORD) < 16:
        print("FATAL: Missing, weak, or prohibited database password in production.", file=sys.stderr)
        sys.exit(1)

# ============================================================================
# Azure Communication Services Configuration
# ============================================================================

if KEYVAULT_AVAILABLE:
    acs_config = keyvault.get_acs_config()
    ACS_CONNECTION_STRING = acs_config["connection_string"]
    ACS_SENDER_ADDRESS = acs_config["sender_address"]
    ACS_SENDER_NAME = acs_config["sender_name"]
else:
    ACS_CONNECTION_STRING = os.environ.get("ACS_CONNECTION_STRING", os.environ.get("ACS-CONNECTION-STRING", ""))
    ACS_SENDER_ADDRESS = os.environ.get("ACS_SENDER_ADDRESS", os.environ.get("ACS-SENDER-ADDRESS", ""))
    ACS_SENDER_NAME = os.environ.get("ACS_SENDER_NAME", os.environ.get("ACS-SENDER-NAME", "NIWI Team"))

# ============================================================================
# JWT Configuration
# ============================================================================

if KEYVAULT_AVAILABLE:
    raw_jwt_secret = keyvault.get_jwt_secret()
else:
    raw_jwt_secret = os.environ.get("JWT_SECRET", os.environ.get("JWT-SECRET", "")).strip()

PROHIBITED_SECRETS = {
    "",
    "default_jwt_secret_key_change_me",
    "your-jwt-secret-signing-key",
    "change_me",
    "secret",
    "insecure-dev-secret",
}

if not raw_jwt_secret or raw_jwt_secret in PROHIBITED_SECRETS:
    if IS_DEV_OR_TEST:
        JWT_SECRET = "dev-insecure-only-local-testing-secret-key-32chars-min!!"
    else:
        raise RuntimeError(
            "FATAL: Missing or insecure JWT_SECRET configuration. "
            "A strong secret key of at least 32 characters must be configured in Azure Key Vault. "
            "Insecure default fallbacks are strictly prohibited."
        )
elif len(raw_jwt_secret) < 32 and not IS_DEV_OR_TEST:
    raise RuntimeError(
        "FATAL: JWT_SECRET is too short for production use. "
        "A strong secret key of at least 32 characters is required."
    )
else:
    JWT_SECRET = raw_jwt_secret

# ============================================================================
# Microsoft Entra ID Configuration
# ============================================================================

if KEYVAULT_AVAILABLE:
    entra_config = keyvault.get_entra_config()
    ENTRA_CLIENT_ID = entra_config["client_id"]
    ENTRA_TENANT_ID = entra_config["tenant_id"]
else:
    ENTRA_CLIENT_ID = os.environ.get("ENTRA_CLIENT_ID", os.environ.get("ENTRA-CLIENT-ID", ""))
    ENTRA_TENANT_ID = os.environ.get("ENTRA_TENANT_ID", os.environ.get("ENTRA-TENANT-ID", ""))

# ============================================================================
# Application Configuration
# ============================================================================

ENABLE_DEV_BYPASS = os.environ.get("ENABLE_DEV_BYPASS", os.environ.get("ENABLE-DEV-BYPASS", "false")).lower() in ("true", "1")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", os.environ.get("CORS-ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:8080,https://niwi.orchvate.in")).split(",")
FRONTEND_URL = os.environ.get("FRONTEND_URL", os.environ.get("FRONTEND-URL", "https://niwi.orchvate.in")).rstrip("/")
DELETE_ALL_PASSWORD = os.environ.get("DELETE_ALL_PASSWORD", os.environ.get("DELETE-ALL-PASSWORD", ""))

# JWKS URL for JWT validation
JWKS_URL = f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/discovery/v2.0/keys" if ENTRA_TENANT_ID else ""

# ============================================================================
# Validation Notice
# ============================================================================

if IS_PRODUCTION or REQUIRE_KEYVAULT:
    if KEYVAULT_AVAILABLE:
        print("Production/KeyVault mode: Using Azure Key Vault for secrets", file=sys.stderr)
    elif os.environ.get("TESTING") != "true":
        raise RuntimeError("FATAL: Azure Key Vault is required but is unavailable.")
    
    if ENABLE_DEV_BYPASS:
        print("CRITICAL: ENABLE_DEV_BYPASS=true is not permitted in production or KeyVault-enforced mode.", file=sys.stderr)
        ENABLE_DEV_BYPASS = False
