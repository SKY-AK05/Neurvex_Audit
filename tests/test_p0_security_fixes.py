"""
Test P0 Security Fixes
Tests for critical security improvements:
1. Development bypass cannot be enabled in production
2. Weak database passwords are rejected
3. Authentication bypass protection
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from fastapi import Request
from fastapi.responses import JSONResponse


class TestDevelopmentBypassProtection:
    """Test that development authentication bypass cannot be enabled in production"""
    
    def test_dev_bypass_blocked_in_production(self):
        """Development bypass should be forcibly disabled when APP_ENV=production"""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "ENABLE_DEV_BYPASS": "true"  # Attacker tries to enable bypass
        }):
            # Import after setting environment
            import importlib
            import app.core.security
            importlib.reload(app.core.security)
            
            from app.core.security import jwks_middleware
            
            # Create mock request with bypass token
            request = MagicMock(spec=Request)
            request.url.path = "/api/submissions"
            request.method = "GET"
            request.headers.get.return_value = "Bearer local_bypass:attacker@evil.com"
            
            async def call_next(req):
                return JSONResponse(content={"data": "protected"})
            
            # In production, bypass token should be rejected
            # (Will fail JWT validation since it's not a valid JWT)
            import asyncio
            response = asyncio.run(jwks_middleware(request, call_next))
            
            # Should return 401 unauthorized, not bypass auth
            assert response.status_code == 401
    
    def test_dev_bypass_works_in_development(self):
        """Development bypass should work when APP_ENV=development AND explicitly enabled"""
        with patch.dict(os.environ, {
            "APP_ENV": "development",
            "ENABLE_DEV_BYPASS": "true",
            "PGHOST": "localhost",
            "PGDATABASE": "test_db",
            "PGUSER": "test_user",
            "PGPASSWORD": "test_password",
            "JWT_SECRET": "dev-test-secret-key-minimum-32chars!!"
        }):
            # Mock database connection - import from correct module
            with patch("app.core.database.get_conn") as mock_conn:
                mock_cursor = MagicMock()
                mock_cursor.fetchone.return_value = ("admin",)
                mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
                mock_conn.return_value.close = MagicMock()
                
                import importlib
                import app.core.security
                importlib.reload(app.core.security)
                
                from app.core.security import jwks_middleware
                
                request = MagicMock(spec=Request)
                request.url.path = "/api/submissions"
                request.method = "GET"
                request.headers.get.return_value = "Bearer local_bypass:dev@example.com"
                request.state = MagicMock()
                
                async def call_next(req):
                    return JSONResponse(content={"data": "protected"})
                
                import asyncio
                response = asyncio.run(jwks_middleware(request, call_next))
                
                # In development with explicit bypass enabled, should work
                assert response.status_code == 200


class TestDatabaseCredentialValidation:
    """Test that weak or compromised database passwords are rejected in production"""
    
    def test_weak_password_rejected_in_production(self):
        """Known weak password Coffee!92 should be rejected"""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "PGPASSWORD": "Coffee!92"  # The compromised password
        }):
            # Importing config should fail with sys.exit(1)
            with pytest.raises(SystemExit) as exc_info:
                import importlib
                import app.core.config
                importlib.reload(app.core.config)
            
            assert exc_info.value.code == 1
    
    def test_short_password_rejected_in_production(self):
        """Password shorter than 16 characters should be rejected"""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "PGPASSWORD": "short123"  # Only 8 characters
        }):
            with pytest.raises(SystemExit) as exc_info:
                import importlib
                import app.core.config
                importlib.reload(app.core.config)
            
            assert exc_info.value.code == 1
    
    def test_empty_password_rejected_in_production(self):
        """Empty password should be rejected"""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "PGPASSWORD": ""
        }):
            with pytest.raises(SystemExit) as exc_info:
                import importlib
                import app.core.config
                importlib.reload(app.core.config)
            
            assert exc_info.value.code == 1
    
    def test_strong_password_accepted_in_production(self):
        """Strong 32-character password should be accepted"""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "TESTING": "true",
            "PGPASSWORD": "aB3$xK9!pL2@mN7&qR5#wT8*uV1^yZ4%",  # 32 chars, strong
            "JWT_SECRET": "production-jwt-secret-minimum-32-characters-required-here!!"
        }):
            # Should not raise SystemExit
            import importlib
            import app.core.config
            importlib.reload(app.core.config)
            
            assert app.core.config.PGPASSWORD == "aB3$xK9!pL2@mN7&qR5#wT8*uV1^yZ4%"
    
    def test_weak_password_allowed_in_development(self):
        """Weak passwords should be allowed in development for convenience"""
        with patch.dict(os.environ, {
            "APP_ENV": "development",
            "PGPASSWORD": "test"  # Weak, but OK for dev
        }):
            import importlib
            import app.core.config
            importlib.reload(app.core.config)
            
            assert app.core.config.PGPASSWORD == "test"


class TestUserIdInAuditTrail:
    """Test that user_id is properly extracted from JWT for audit trails"""
    
    def test_user_id_extracted_from_jwt(self):
        """user_id should be extracted from JWT 'oid' or 'sub' claims"""
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "ENTRA_CLIENT_ID": "test-client-id",
            "ENTRA_TENANT_ID": "test-tenant-id",
            "PGPASSWORD": "test-production-password-32chars-minimum!!",
            "JWT_SECRET": "test-jwt-secret-production-32chars-minimum-required!!"
        }):
            import importlib
            import app.core.security
            importlib.reload(app.core.security)
            
            with patch("app.core.security.verify_jwt") as mock_verify:
                with patch("app.core.database.get_conn") as mock_conn:
                    # Mock JWT payload with user ID
                    mock_verify.return_value = {
                        "oid": "12345-67890-abcdef",  # Azure AD user object ID
                        "email": "admin@example.com",
                        "preferred_username": "admin@example.com"
                    }
                    
                    # Mock database query
                    mock_cursor = MagicMock()
                    mock_cursor.fetchone.return_value = ("admin",)
                    mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
                    mock_conn.return_value.close = MagicMock()
                    
                    from app.core.security import jwks_middleware
                    
                    request = MagicMock(spec=Request)
                    request.url.path = "/api/submissions"
                    request.method = "GET"
                    request.headers.get.return_value = "Bearer valid.jwt.token"
                    request.state = MagicMock()
                    
                    async def call_next(req):
                        return JSONResponse(content={"data": "protected"})
                    
                    import asyncio
                    asyncio.run(jwks_middleware(request, call_next))
                    
                    # Verify user_id was set from 'oid' claim
                    assert hasattr(request.state, 'user_id')
                    assert request.state.user_id == "12345-67890-abcdef"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
