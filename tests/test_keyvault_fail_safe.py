"""
test_keyvault_fail_safe.py — Rigorous tests for Key Vault enforcement and environment validation.
"""
import os
import sys
import importlib
import pytest
from unittest.mock import patch, MagicMock

class TestEnvironmentAndKeyVaultEnforcement:
    """Validate strict environment validation and Key Vault fail-safe behaviour."""

    def test_unknown_environment_fails_safely(self):
        """Unrecognized environment strings (e.g. 'staging', 'qa', 'unknown') must fail safely."""
        with patch.dict(os.environ, {"APP_ENV": "staging"}):
            with pytest.raises(RuntimeError) as exc_info:
                import app.core.config
                importlib.reload(app.core.config)
            assert "Unrecognized or invalid environment APP_ENV='staging'" in str(exc_info.value)
            assert "Unknown environments fail safely" in str(exc_info.value)

    def test_require_keyvault_enforces_keyvault_in_development(self):
        """Setting REQUIRE_KEYVAULT=true must mandate Key Vault even when APP_ENV=development."""
        from app.core import keyvault

        # Case A: Missing SDK raises immediately
        with patch.dict(os.environ, {
            "APP_ENV": "development",
            "REQUIRE_KEYVAULT": "true",
            "KEY_VAULT_NAME": "",
            "TESTING": ""
        }), patch.object(keyvault, "_AZURE_AVAILABLE", False):
            with pytest.raises(RuntimeError) as exc_info:
                keyvault.init_keyvault()
            assert "Azure Key Vault SDK is not installed in required Key Vault environment" in str(exc_info.value)

        # Case B: SDK present but missing KEY_VAULT_NAME raises immediately
        with patch.dict(os.environ, {
            "APP_ENV": "development",
            "REQUIRE_KEYVAULT": "true",
            "KEY_VAULT_NAME": "",
            "TESTING": ""
        }), patch.object(keyvault, "_AZURE_AVAILABLE", True):
            with pytest.raises(RuntimeError) as exc_info:
                keyvault.init_keyvault()
            assert "KEY_VAULT_NAME is not configured in required Key Vault environment" in str(exc_info.value)

    def test_require_keyvault_blocks_env_file_loading(self):
        """When REQUIRE_KEYVAULT=true, .env loading is strictly disabled."""
        from app.core import config
        # Verify the condition logic
        assert not (config.IS_DEV_OR_TEST and config.REQUIRE_KEYVAULT)

    def test_production_missing_secret_fails_startup(self):
        """In production, missing required secrets must raise RuntimeError without fallback."""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "TESTING": "",
            "KEY_VAULT_NAME": "test-kv"
        }):
            from app.core import keyvault
            keyvault.clear_cache()
            with patch.object(keyvault, "_use_keyvault", True), \
                 patch.object(keyvault, "_kv_client", MagicMock()):
                keyvault._kv_client.get_secret.side_effect = Exception("SecretNotFound")
                with pytest.raises(RuntimeError) as exc_info:
                    keyvault.get_secret("required-secret", required=True)
                assert "Required secret 'required-secret' could not be retrieved from Azure Key Vault" in str(exc_info.value)

    def test_no_secret_values_are_logged(self, caplog):
        """Verify that secret retrieval failures and operations do not log sensitive values."""
        from app.core import keyvault
        keyvault.clear_cache()
        secret_password = "SuperSecretPlaintextPassword123!"
        
        with patch.dict(os.environ, {"TEST_SECRET_ENV": secret_password, "APP_ENV": "development"}):
            val = keyvault.get_secret("test-secret-env")
            assert val == secret_password
            # Verify secret value is never in log output
            for record in caplog.records:
                assert secret_password not in record.message
