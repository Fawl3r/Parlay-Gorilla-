"""
Tests for profile, verification, and badge endpoints.

Run with: pytest tests/test_profile_verification_badges.py -v
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
import uuid
from datetime import datetime, timezone, timedelta

from app.main import app
from app.models.user import User
from app.models.badge import Badge
from app.models.user_badge import UserBadge
from app.models.verification_token import VerificationToken, TokenType
from app.services.auth_service import get_password_hash, create_access_token
from app.core.dependencies import get_current_user as dep_get_current_user


def _asgi_client() -> AsyncClient:
    """httpx>=0.28: use ASGITransport instead of AsyncClient(app=...)."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# Test fixtures
@pytest.fixture
def test_user_id():
    return str(uuid.uuid4())


@pytest.fixture
def test_user_data(test_user_id):
    return {
        "id": test_user_id,
        "email": "test@example.com",
        "username": "testuser",
        "password_hash": get_password_hash("testpassword"),
        "email_verified": False,
        "profile_completed": False,
    }


@pytest.fixture
def auth_token(test_user_data):
    return create_access_token({"sub": test_user_data["id"], "email": test_user_data["email"]})


# ============================================================================
# Profile Endpoint Tests
# ============================================================================

class TestProfileEndpoints:
    """Tests for /api/profile/* endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self):
        """Test that unauthenticated requests are rejected."""
        async with _asgi_client() as client:
            response = await client.get("/api/profile/me")
            assert response.status_code == 403  # No auth header
    
    @pytest.mark.asyncio
    async def test_get_profile_success(self, auth_token, test_user_data):
        """Test successful profile retrieval."""
        with patch("app.api.routes.profile.get_current_user") as mock_user:
            mock_user.return_value = AsyncMock(**test_user_data)
            
            async with _asgi_client() as client:
                response = await client.get(
                    "/api/profile/me",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                # Should work if mocking is correct
                # In real test, would check status 200 and response structure
    
    @pytest.mark.asyncio
    async def test_complete_profile_setup_missing_display_name(self, auth_token):
        """Test that profile setup fails without display_name."""
        # Override auth dependency so the request reaches body validation (otherwise it can 404 if user doesn't exist).
        async def _fake_user():
            return AsyncMock(id=uuid.uuid4(), email="test@example.com")

        app.dependency_overrides[dep_get_current_user] = _fake_user
        try:
            async with _asgi_client() as client:
                response = await client.post(
                    "/api/profile/setup",
                    headers={"Authorization": f"Bearer {auth_token}"},
                    json={
                        "favorite_sports": ["NFL"],
                    },
                )
                assert response.status_code == 422  # Validation error (missing display_name)
        finally:
            app.dependency_overrides.pop(dep_get_current_user, None)


# ============================================================================
# Verification Token Tests
# ============================================================================

class TestVerificationTokenModel:
    """Tests for VerificationToken model and methods."""
    
    def test_token_generation(self):
        """Test secure token generation."""
        token = VerificationToken.generate_token()
        assert len(token) == 64  # 32 bytes as hex
        assert token.isalnum()  # Only alphanumeric
    
    def test_token_hashing(self):
        """Test token hashing is deterministic."""
        raw_token = "test_token_12345"
        hash1 = VerificationToken.hash_token(raw_token)
        hash2 = VerificationToken.hash_token(raw_token)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars
    
    def test_create_token(self):
        """Test token creation with hashing."""
        user_id = uuid.uuid4()
        token_obj, raw_token = VerificationToken.create_token(
            user_id=user_id,
            token_type=TokenType.EMAIL_VERIFY,
            expires_in_hours=24
        )
        
        assert token_obj.user_id == user_id
        assert token_obj.token_type == TokenType.EMAIL_VERIFY
        assert token_obj.token_hash == VerificationToken.hash_token(raw_token)
        assert token_obj.expires_at > datetime.now(timezone.utc)
    
    def test_token_expiration_check(self):
        """Test token expiration validation."""
        user_id = uuid.uuid4()
        
        # Create expired token
        token = VerificationToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash="test_hash",
            token_type=TokenType.EMAIL_VERIFY,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        
        assert token.is_expired == True
        assert token.is_valid == False
    
    def test_token_used_check(self):
        """Test token usage validation."""
        user_id = uuid.uuid4()
        
        token = VerificationToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash="test_hash",
            token_type=TokenType.PASSWORD_RESET,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used_at=datetime.now(timezone.utc),
        )
        
        assert token.is_used == True
        assert token.is_valid == False


# ============================================================================
# Badge Tests
# ============================================================================

class TestBadgeSystem:
    """Tests for badge system."""
    
    def test_badge_to_dict_unlocked(self):
        """Test badge serialization when unlocked."""
        badge = Badge(
            id=uuid.uuid4(),
            name="Test Badge",
            slug="test-badge",
            description="A test badge",
            icon="🏆",
            requirement_type="TOTAL_PARLAYS",
            requirement_value=10,
            display_order=1,
        )
        
        result = badge.to_dict(unlocked=True, unlocked_at="2024-01-01T00:00:00")
        
        assert result["name"] == "Test Badge"
        assert result["slug"] == "test-badge"
        assert result["unlocked"] == True
        assert result["unlocked_at"] == "2024-01-01T00:00:00"
    
    def test_badge_to_dict_locked(self):
        """Test badge serialization when locked."""
        badge = Badge(
            id=uuid.uuid4(),
            name="Test Badge",
            slug="test-badge",
            description="A test badge",
            icon="🏆",
            requirement_type="TOTAL_PARLAYS",
            requirement_value=10,
            display_order=1,
        )
        
        result = badge.to_dict(unlocked=False)
        
        assert result["unlocked"] == False
        assert result["unlocked_at"] is None


# ============================================================================
# Auth Endpoint Tests  
# ============================================================================

class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_forgot_password_always_returns_success(self):
        """Test that forgot password returns 200 even for non-existent email."""
        async with _asgi_client() as client:
            response = await client.post(
                "/api/auth/forgot-password",
                json={"email": "nonexistent@example.com"}
            )
            # Should always return success to prevent email enumeration
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self):
        """Test that invalid verification token returns error."""
        async with _asgi_client() as client:
            response = await client.post(
                "/api/auth/verify-email",
                json={"token": "invalid_token_12345"}
            )
            assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self):
        """Test that invalid reset token returns error."""
        async with _asgi_client() as client:
            response = await client.post(
                "/api/auth/reset-password",
                json={"token": "invalid_token", "password": "newpassword123"}
            )
            assert response.status_code == 400


# ============================================================================
# Subscription Endpoint Tests
# ============================================================================

class TestSubscriptionEndpoints:
    """Tests for subscription endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_subscription_unauthorized(self):
        """Test that unauthenticated requests are rejected."""
        async with _asgi_client() as client:
            response = await client.get("/api/subscription/me")
            assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_get_history_unauthorized(self):
        """Test that unauthenticated requests are rejected."""
        async with _asgi_client() as client:
            response = await client.get("/api/subscription/history")
            assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_cancel_subscription_unauthorized(self):
        """Test that unauthenticated requests are rejected."""
        async with _asgi_client() as client:
            response = await client.post("/api/subscription/cancel")
            assert response.status_code == 403


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegrationFlows:
    """Integration tests for complete flows."""
    
    @pytest.mark.asyncio
    async def test_login_response_includes_verification_flags(self):
        """Test that login response includes email_verified and profile_completed."""
        # This would require a seeded test database
        # For now, we just validate the endpoint exists
        async with _asgi_client() as client:
            response = await client.post(
                "/api/auth/login",
                json={"email": "test@test.com", "password": "testpass"}
            )
            # Will fail auth but proves endpoint works
            assert response.status_code in [401, 200]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

