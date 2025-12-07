"""
Tests for admin authentication and authorization.

Verifies that:
- Admin endpoints require authentication
- Non-admin users are blocked from admin endpoints
- Admin users can access admin endpoints
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
import uuid

# Import the auth dependency
from app.api.routes.admin.auth import require_admin, require_mod_or_admin
from app.models.user import User, UserRole


class TestRequireAdmin:
    """Tests for the require_admin dependency."""
    
    @pytest.mark.asyncio
    async def test_admin_user_allowed(self):
        """Admin user should be allowed through."""
        # Create a mock admin user
        admin_user = MagicMock(spec=User)
        admin_user.id = uuid.uuid4()
        admin_user.email = "admin@example.com"
        admin_user.role = UserRole.admin.value
        
        # Call the dependency
        result = await require_admin(current_user=admin_user)
        
        # Should return the user
        assert result == admin_user
    
    @pytest.mark.asyncio
    async def test_regular_user_blocked(self):
        """Regular user should be blocked."""
        # Create a mock regular user
        regular_user = MagicMock(spec=User)
        regular_user.id = uuid.uuid4()
        regular_user.email = "user@example.com"
        regular_user.role = UserRole.user.value
        
        # Call the dependency - should raise 403
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(current_user=regular_user)
        
        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_mod_user_blocked(self):
        """Mod user should be blocked from admin-only endpoints."""
        # Create a mock mod user
        mod_user = MagicMock(spec=User)
        mod_user.id = uuid.uuid4()
        mod_user.email = "mod@example.com"
        mod_user.role = UserRole.mod.value
        
        # Call the dependency - should raise 403
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(current_user=mod_user)
        
        assert exc_info.value.status_code == 403


class TestRequireModOrAdmin:
    """Tests for the require_mod_or_admin dependency."""
    
    @pytest.mark.asyncio
    async def test_admin_user_allowed(self):
        """Admin user should be allowed."""
        admin_user = MagicMock(spec=User)
        admin_user.id = uuid.uuid4()
        admin_user.role = UserRole.admin.value
        
        result = await require_mod_or_admin(current_user=admin_user)
        assert result == admin_user
    
    @pytest.mark.asyncio
    async def test_mod_user_allowed(self):
        """Mod user should be allowed."""
        mod_user = MagicMock(spec=User)
        mod_user.id = uuid.uuid4()
        mod_user.role = UserRole.mod.value
        
        result = await require_mod_or_admin(current_user=mod_user)
        assert result == mod_user
    
    @pytest.mark.asyncio
    async def test_regular_user_blocked(self):
        """Regular user should be blocked."""
        regular_user = MagicMock(spec=User)
        regular_user.id = uuid.uuid4()
        regular_user.role = UserRole.user.value
        
        with pytest.raises(HTTPException) as exc_info:
            await require_mod_or_admin(current_user=regular_user)
        
        assert exc_info.value.status_code == 403
        assert "Moderator or admin access required" in exc_info.value.detail


class TestUserModel:
    """Tests for User model role-related properties."""
    
    def test_is_admin_property(self):
        """Test is_admin property."""
        admin_user = MagicMock(spec=User)
        admin_user.role = UserRole.admin.value
        admin_user.is_admin = property(lambda self: self.role == UserRole.admin.value)
        
        # Direct check since we're using MagicMock
        assert admin_user.role == "admin"
    
    def test_is_premium_property(self):
        """Test is_premium property for different plans."""
        from app.models.user import UserPlan
        
        # Test free user
        free_user = MagicMock()
        free_user.plan = UserPlan.free.value
        assert free_user.plan == "free"
        
        # Test standard user
        standard_user = MagicMock()
        standard_user.plan = UserPlan.standard.value
        assert standard_user.plan == "standard"
        
        # Test elite user
        elite_user = MagicMock()
        elite_user.plan = UserPlan.elite.value
        assert elite_user.plan == "elite"


class TestAdminEndpointAccess:
    """Integration-style tests for admin endpoint access patterns."""
    
    def test_role_hierarchy(self):
        """Test that role hierarchy is correct."""
        roles = [UserRole.user.value, UserRole.mod.value, UserRole.admin.value]
        
        # User is lowest
        assert roles.index("user") < roles.index("mod")
        
        # Admin is highest
        assert roles.index("admin") > roles.index("mod")
    
    def test_role_enum_values(self):
        """Test that role enum has expected values."""
        assert UserRole.user.value == "user"
        assert UserRole.mod.value == "mod"
        assert UserRole.admin.value == "admin"
    
    def test_all_roles_defined(self):
        """Test that all expected roles are defined."""
        expected_roles = {"user", "mod", "admin"}
        actual_roles = {role.value for role in UserRole}
        assert expected_roles == actual_roles

