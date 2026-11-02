"""
keyvault.py — Azure Key Vault integration with Managed Identity
Retrieves secrets from Azure Key Vault for production deployment.
Falls back to environment variables for local development or when Key Vault is unavailable.
"""
import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Safe import of Azure Identity & Key Vault packages
_AZURE_AVAILABLE = False
try:
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
    from azure.keyvault.secrets import SecretClient
    from azure.core.exceptions import AzureError
    _AZURE_AVAILABLE = True
except ImportError as err:
    logger.info("Azure Key Vault SDK not available in current environment; using environment variables fallback (%s)", err)

# Global secret cache
_secret_cache: Dict[str, str] = {}
_kv_client: Optional[object] = None
_use_keyvault: bool = False


def init_keyvault():
    """
    Initialize Azure Key Vault client with Managed Identity.
    Should be called once at application startup.
    
    In production:
    - Azure SDK must be installed.
    - KEY_VAULT_NAME must be set.
    - Managed Identity authentication and Key Vault probe must succeed.
    - Startup fails immediately with RuntimeError if Key Vault is unavailable.
    
    In development/testing:
    - Gracefully falls back to environment variables.
    """
    global _kv_client, _use_keyvault
    
    app_env = os.environ.get("APP_ENV", os.environ.get("APP-ENV", "development")).lower()
    key_vault_name = os.environ.get("KEY_VAULT_NAME", "").strip()
    require_kv = os.environ.get("REQUIRE_KEYVAULT", "").lower() in ("true", "1")
    is_prod = app_env in ("production", "prod") and os.environ.get("TESTING") != "true"
    must_use_kv = require_kv or is_prod
    
    if not must_use_kv:
        logger.info("APP_ENV=%s: Operating with environment configuration (Key Vault not required).", app_env)
        _use_keyvault = False
        return

    if not _AZURE_AVAILABLE:
        raise RuntimeError("FATAL: Azure Key Vault SDK is not installed in required Key Vault environment.")
    
    if not key_vault_name:
        raise RuntimeError("FATAL: KEY_VAULT_NAME is not configured in required Key Vault environment.")
    
    try:
        credential = DefaultAzureCredential()
        vault_url = f"https://{key_vault_name}.vault.azure.net/"
        _kv_client = SecretClient(vault_url=vault_url, credential=credential)
        
        # Test connection by attempting to retrieve a test secret
        try:
            _ = _kv_client.get_secret("pgpassword")
            logger.info("Key Vault initialized successfully: %s", vault_url)
            _use_keyvault = True
        except AzureError as e:
            _use_keyvault = False
            _kv_client = None
            raise RuntimeError(
                f"FATAL: Managed Identity authentication failed or Azure Key Vault probe failed at '{vault_url}': {type(e).__name__}"
            )
            
    except RuntimeError:
        raise
    except Exception as e:
        _use_keyvault = False
        _kv_client = None
        raise RuntimeError(
            f"FATAL: Azure Key Vault client setup failed for '{key_vault_name}': {type(e).__name__}"
        )


def get_secret(secret_name: str, env_var_name: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get a secret from Azure Key Vault or environment variables.
    Never logs secret values.
    """
    global _secret_cache, _kv_client, _use_keyvault
    
    app_env = os.environ.get("APP_ENV", os.environ.get("APP-ENV", "development")).lower()
    require_kv = os.environ.get("REQUIRE_KEYVAULT", "").lower() in ("true", "1")
    is_prod = app_env in ("production", "prod") and os.environ.get("TESTING") != "true"
    must_use_kv = require_kv or is_prod
    
    if env_var_name is None:
        env_var_name = secret_name.upper().replace("-", "_")
    
    # 1. In-memory cache
    if secret_name in _secret_cache:
        return _secret_cache[secret_name]
    
    # 2. Key Vault (if active)
    if _use_keyvault and _kv_client is not None:
        try:
            secret = _kv_client.get_secret(secret_name)
            value = secret.value
            if value:
                _secret_cache[secret_name] = value
                return value
        except Exception as e:
            if must_use_kv and required:
                raise RuntimeError(f"FATAL: Required secret '{secret_name}' could not be retrieved from Azure Key Vault: {type(e).__name__}")
            logger.warning("Failed to retrieve secret '%s' from Key Vault: %s", secret_name, type(e).__name__)
    
    # In strict production or require_keyvault mode, do not silently fall back to environment variables
    if must_use_kv:
        if required:
            raise RuntimeError(f"FATAL: Required secret '{secret_name}' is missing in Azure Key Vault in required mode.")
        return None
    
    # 3. Environment variable fallback (development/test mode only)
    value = os.environ.get(env_var_name) or os.environ.get(env_var_name.replace("_", "-"))
    if value:
        _secret_cache[secret_name] = value
    
    return value


def get_database_config() -> Dict[str, str]:
    return {
        "host": get_secret("pghost", "PGHOST", required=True) or "localhost",
        "port": get_secret("pgport", "PGPORT") or "5432",
        "database": get_secret("pgdatabase", "PGDATABASE", required=True) or "nd_audit",
        "user": get_secret("pguser", "PGUSER", required=True) or "postgres",
        "password": get_secret("pgpassword", "PGPASSWORD", required=True) or "",
    }


def get_acs_config() -> Dict[str, str]:
    return {
        "connection_string": get_secret("acs-connection-string", "ACS_CONNECTION_STRING") or "",
        "sender_address": get_secret("acs-sender-address", "ACS_SENDER_ADDRESS") or "",
        "sender_name": get_secret("acs-sender-name", "ACS_SENDER_NAME") or "NIWI Team",
    }


def get_jwt_secret() -> str:
    return get_secret("jwt-secret", "JWT_SECRET", required=True) or "insecure-dev-secret"


def get_entra_config() -> Dict[str, str]:
    return {
        "client_id": get_secret("entra-client-id", "ENTRA_CLIENT_ID") or "",
        "tenant_id": get_secret("entra-tenant-id", "ENTRA_TENANT_ID") or "",
    }


def clear_cache():
    global _secret_cache
    _secret_cache.clear()


def is_using_keyvault() -> bool:
    return _use_keyvault
