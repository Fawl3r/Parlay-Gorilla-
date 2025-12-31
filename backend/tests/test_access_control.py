"""
Tests for the Access Control Service.

Tests the hybrid access model:
- Free parlay allocation
- Subscription-based access
- Credit-based access
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.services.access_control_service import AccessControlService, AccessCheckResult, AccessStatus
from app.models.user import User, SubscriptionStatusEnum
from app.core.billing_config import ParlayType


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def free_user():
    """Create a mock user with free parlays remaining."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.free_parlays_total = 2
    user.free_parlays_used = 0
    user.free_parlays_remaining = 2
    user.has_free_parlays_remaining = True
    user.subscription_status = SubscriptionStatusEnum.none.value
    user.subscription_plan = None
    user.has_active_subscription = False
    user.is_within_daily_subscription_limit = False
    user.subscription_parlays_remaining_today = 0
    user.credit_balance = 0
    user.daily_parlays_used = 0
    user.daily_parlays_usage_date = None
    return user


@pytest.fixture
def subscribed_user():
    """Create a mock user with an active subscription."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.free_parlays_total = 2
    user.free_parlays_used = 2
    user.free_parlays_remaining = 0
    user.has_free_parlays_remaining = False
    user.subscription_status = SubscriptionStatusEnum.active.value
    user.subscription_plan = "elite_monthly"
    user.has_active_subscription = True
    user.is_within_daily_subscription_limit = True
    user.subscription_parlays_remaining_today = 15
    user.credit_balance = 0
    user.daily_parlays_used = 0
    user.daily_parlays_usage_date = date.today()
    
    def get_subscription_daily_limit():
        return 15
    
    user.get_subscription_daily_limit = get_subscription_daily_limit
    return user


@pytest.fixture
def credits_user():
    """Create a mock user with credits but no subscription."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.free_parlays_total = 2
    user.free_parlays_used = 2
    user.free_parlays_remaining = 0
    user.has_free_parlays_remaining = False
    user.subscription_status = SubscriptionStatusEnum.none.value
    user.subscription_plan = None
    user.has_active_subscription = False
    user.is_within_daily_subscription_limit = False
    user.subscription_parlays_remaining_today = 0
    user.credit_balance = 10
    user.daily_parlays_used = 0
    user.daily_parlays_usage_date = None
    
    def has_credits(amount):
        return user.credit_balance >= amount
    
    user.has_credits = has_credits
    return user


@pytest.fixture
def no_access_user():
    """Create a mock user with no access methods available."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.free_parlays_total = 2
    user.free_parlays_used = 2
    user.free_parlays_remaining = 0
    user.has_free_parlays_remaining = False
    user.subscription_status = SubscriptionStatusEnum.none.value
    user.subscription_plan = None
    user.has_active_subscription = False
    user.is_within_daily_subscription_limit = False
    user.subscription_parlays_remaining_today = 0
    user.credit_balance = 0
    user.daily_parlays_used = 0
    user.daily_parlays_usage_date = None
    
    def has_credits(amount):
        return user.credit_balance >= amount
    
    user.has_credits = has_credits
    return user


class TestAccessControlService:
    """Tests for AccessControlService."""
    
    @pytest.mark.asyncio
    async def test_free_user_can_generate(self, mock_db, free_user):
        """Test that a user with free parlays remaining can generate."""
        service = AccessControlService(mock_db)
        
        with patch.object(service, 'get_user', return_value=free_user):
            with patch.object(service, '_reset_daily_counter_if_needed', return_value=False):
                result = await service.can_generate_parlay(str(free_user.id))
        
        assert result.allowed is True
        assert result.access_type == "free"
        assert result.free_remaining == 2
    
    @pytest.mark.asyncio
    async def test_subscribed_user_can_generate(self, mock_db, subscribed_user):
        """Test that a subscribed user can generate within daily limits."""
        service = AccessControlService(mock_db)
        
        with patch.object(service, 'get_user', return_value=subscribed_user):
            with patch.object(service, '_reset_daily_counter_if_needed', return_value=False):
                result = await service.can_generate_parlay(str(subscribed_user.id))
        
        assert result.allowed is True
        assert result.access_type == "subscription"
        assert result.subscription_remaining == 15
    
    @pytest.mark.asyncio
    async def test_credits_user_can_generate(self, mock_db, credits_user):
        """Test that a user with credits can generate."""
        service = AccessControlService(mock_db)
        
        with patch.object(service, 'get_user', return_value=credits_user):
            with patch.object(service, '_reset_daily_counter_if_needed', return_value=False):
                result = await service.can_generate_parlay(str(credits_user.id))
        
        assert result.allowed is True
        assert result.access_type == "credits"
        assert result.credits_available == 10
    
    @pytest.mark.asyncio
    async def test_no_access_user_denied(self, mock_db, no_access_user):
        """Test that a user with no access is denied."""
        service = AccessControlService(mock_db)
        
        with patch.object(service, 'get_user', return_value=no_access_user):
            with patch.object(service, '_reset_daily_counter_if_needed', return_value=False):
                result = await service.can_generate_parlay(str(no_access_user.id))
        
        assert result.allowed is False
        assert result.reason is not None
        assert "subscribe" in result.reason.lower() or "credits" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_elite_parlay_requires_3_credits(self, mock_db, credits_user):
        """Test that elite parlays require 3 credits (per usage)."""
        # Give user fewer than required credits
        credits_user.credit_balance = 2
        
        def has_credits(amount):
            return credits_user.credit_balance >= amount
        
        credits_user.has_credits = has_credits
        
        service = AccessControlService(mock_db)
        
        with patch.object(service, 'get_user', return_value=credits_user):
            with patch.object(service, '_reset_daily_counter_if_needed', return_value=False):
                result = await service.can_generate_parlay(
                    str(credits_user.id),
                    parlay_type=ParlayType.ELITE.value
                )
        
        # Should be denied because elite costs 3 credits (same as standard)
        assert result.allowed is False
        assert result.credits_required == 3
    
    @pytest.mark.asyncio
    async def test_user_not_found(self, mock_db):
        """Test handling of non-existent user."""
        service = AccessControlService(mock_db)
        
        with patch.object(service, 'get_user', return_value=None):
            result = await service.can_generate_parlay("nonexistent-id")
        
        assert result.allowed is False
        assert "not found" in result.reason.lower()


class TestAccessStatus:
    """Tests for AccessStatus data class."""
    
    def test_access_status_to_dict(self):
        """Test that AccessStatus converts to dict properly."""
        status = AccessStatus(
            free_total=2,
            free_used=1,
            free_remaining=1,
            has_subscription=True,
            subscription_plan="elite_monthly",
            subscription_daily_limit=15,
            subscription_used_today=3,
            subscription_remaining_today=12,
            credit_balance=25,
            custom_builder_used=0,
            custom_builder_limit=0,
            custom_builder_remaining=0,
            custom_builder_period_start=None,
            inscriptions_used=0,
            inscriptions_limit=0,
            inscriptions_remaining=0,
            inscriptions_period_start=None,
            can_generate_standard=True,
            can_generate_elite=True,
        )
        
        d = status.to_dict()
        
        assert d["free"]["total"] == 2
        assert d["free"]["remaining"] == 1
        assert d["subscription"]["active"] is True
        assert d["subscription"]["plan"] == "elite_monthly"
        assert d["credits"]["balance"] == 25
        assert d["can_generate"]["standard"] is True


class TestAccessCheckResult:
    """Tests for AccessCheckResult data class."""
    
    def test_allowed_result(self):
        """Test allowed access result."""
        result = AccessCheckResult(
            allowed=True,
            access_type="subscription",
            free_remaining=0,
            subscription_remaining=10,
            credits_available=5,
        )
        
        d = result.to_dict()
        
        assert d["allowed"] is True
        assert d["access_type"] == "subscription"
    
    def test_denied_result(self):
        """Test denied access result."""
        result = AccessCheckResult(
            allowed=False,
            reason="No access available. Subscribe or buy credits.",
            credits_required=1,
            credits_available=0,
        )
        
        d = result.to_dict()
        
        assert d["allowed"] is False
        assert d["reason"] is not None
        assert d["credits_required"] == 1




