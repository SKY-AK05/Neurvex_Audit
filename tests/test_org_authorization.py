"""
Test suite for Phase 2: Organization-Level Authorization
Tests organization-based access control for submissions endpoints.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from app.core.authorization import (
    get_user_from_request,
    get_admin_organizations,
    filter_submissions_by_org_access,
    check_submission_access
)


class TestGetUserFromRequest:
    """Test user extraction from request authentication"""
    
    def test_missing_auth_header_raises_401(self):
        """Should raise 401 when Authorization header is missing"""
        request = Mock()
        request.headers.get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            get_user_from_request(request)
        
        assert exc_info.value.status_code == 401
        assert "Missing or invalid" in str(exc_info.value.detail)
    
    def test_invalid_auth_header_format_raises_401(self):
        """Should raise 401 when Authorization header doesn't start with Bearer"""
        request = Mock()
        request.headers.get.return_value = "Basic some_token"
        
        with pytest.raises(HTTPException) as exc_info:
            get_user_from_request(request)
        
        assert exc_info.value.status_code == 401
    
    @patch('app.core.authorization.get_conn')
    @patch('app.core.authorization.os.environ.get')
    def test_dev_bypass_extracts_email_and_role(self, mock_env_get, mock_get_conn):
        """Should extract email and role when dev bypass is enabled"""
        # Setup dev environment
        def env_side_effect(key, default=""):
            if key == "APP_ENV":
                return "development"
            elif key == "ENABLE_DEV_BYPASS":
                return "true"
            return default
        
        mock_env_get.side_effect = env_side_effect
        
        # Mock database response
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "email": "test@example.com",
            "role": "admin"
        }
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        # Mock request
        request = Mock()
        request.headers.get.return_value = "Bearer local_bypass:test@example.com"
        
        result = get_user_from_request(request)
        
        assert result["email"] == "test@example.com"
        assert result["role"] == "admin"
    
    @patch('app.core.authorization.get_conn')
    @patch('app.core.authorization.os.environ.get')
    def test_dev_bypass_blocked_in_production(self, mock_env_get, mock_get_conn):
        """Should NOT allow dev bypass when APP_ENV=production"""
        # Setup production environment
        def env_side_effect(key, default=""):
            if key == "APP_ENV":
                return "production"
            elif key == "ENABLE_DEV_BYPASS":
                return "true"  # Trying to enable bypass
            return default
        
        mock_env_get.side_effect = env_side_effect
        
        # Mock request with bypass token
        request = Mock()
        request.headers.get.return_value = "Bearer local_bypass:test@example.com"
        
        # Should raise 401 because bypass is blocked in production
        with pytest.raises(HTTPException) as exc_info:
            get_user_from_request(request)
        
        assert exc_info.value.status_code in (401, 403)


class TestGetAdminOrganizations:
    """Test fetching admin's authorized organizations under the Two-Role Global Model"""
    
    def test_super_admin_returns_none(self):
        """Super admins should return None (global access to all orgs)"""
        result = get_admin_organizations("super@example.com", "super", None)
        assert result is None  # None means "no filtering - global access"
    
    def test_regular_admin_returns_none(self):
        """Regular admins should return None (global access to all orgs)"""
        result = get_admin_organizations("admin@example.com", "admin", None)
        assert result is None  # Global access per Section 1.3


class TestFilterSubmissionsByOrgAccess:
    """Test SQL query filtering under the Two-Role Global Model"""
    
    def test_super_admin_no_filtering(self):
        """Super admin queries should not be modified"""
        query = "SELECT * FROM submissions ORDER BY submitted_at DESC"
        params = ()
        
        result_query, result_params = filter_submissions_by_org_access(
            query, params, "super@example.com", "super", None
        )
        
        assert result_query == query
        assert result_params == params
    
    def test_regular_admin_no_filtering(self):
        """Normal admin queries should also not be modified (global access)"""
        query = "SELECT * FROM submissions ORDER BY submitted_at DESC"
        params = ()
        
        result_query, result_params = filter_submissions_by_org_access(
            query, params, "admin@example.com", "admin", None
        )
        
        assert result_query == query
        assert result_params == params


class TestCheckSubmissionAccess:
    """Test individual submission access verification under Two-Role Global Model"""
    
    def test_super_admin_always_has_access(self):
        """Super admin should always have access"""
        result = check_submission_access(
            "submission-123", "super@example.com", "super", None
        )
        assert result is True
    
    def test_regular_admin_has_global_access(self):
        """Normal admin should also have global access to any submission"""
        result = check_submission_access(
            "submission-123", "admin@example.com", "admin", None
        )
        assert result is True


class TestEndToEndScenarios:
    """End-to-end authorization scenarios under Two-Role Global Model"""
    
    def test_scenario_super_admin_sees_all_submissions(self):
        """Super admin should see all submissions without filtering"""
        query = "SELECT * FROM submissions ORDER BY submitted_at DESC"
        params = ()
        
        result_query, result_params = filter_submissions_by_org_access(
            query, params, "super@example.com", "super", None
        )
        
        assert result_query == query
        assert len(result_params) == 0
    
    def test_scenario_regular_admin_sees_all_submissions(self):
        """Regular admin should see all submissions globally"""
        query = "SELECT * FROM submissions ORDER BY submitted_at DESC"
        params = ()
        
        result_query, result_params = filter_submissions_by_org_access(
            query, params, "admin@company.com", "admin", None
        )
        
        assert result_query == query
        assert len(result_params) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
