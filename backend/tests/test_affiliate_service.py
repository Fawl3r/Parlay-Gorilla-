"""
Tests for the Affiliate Service.

Tests the affiliate program functionality:
- Affiliate registration
- Click tracking
- Referral attribution
- Commission calculation
- Tier upgrades
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.services.affiliate_service import AffiliateService
from app.models.affiliate import Affiliate
from app.models.affiliate_click import AffiliateClick
from app.models.affiliate_referral import AffiliateReferral
from app.models.affiliate_commission import CommissionSaleType
from app.models.user import User
from app.core.billing_config import AffiliateTier, AFFILIATE_TIERS, calculate_tier_for_revenue


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_affiliate():
    """Create a mock affiliate."""
    affiliate = MagicMock(spec=Affiliate)
    affiliate.id = uuid.uuid4()
    affiliate.user_id = uuid.uuid4()
    affiliate.referral_code = "GORILLA123"
    affiliate.tier = AffiliateTier.ROOKIE.value
    affiliate.commission_rate_sub_first = Decimal("0.20")
    affiliate.commission_rate_sub_recurring = Decimal("0.00")
    affiliate.commission_rate_credits = Decimal("0.20")
    affiliate.total_referred_revenue = Decimal("0.00")
    affiliate.total_commission_earned = Decimal("0.00")
    affiliate.total_commission_paid = Decimal("0.00")
    affiliate.total_clicks = 0
    affiliate.total_referrals = 0
    affiliate.is_active = True
    affiliate.is_approved = True
    affiliate.payout_email = None
    affiliate.payout_method = None
    affiliate.created_at = datetime.now(timezone.utc)
    
    def increment_click():
        affiliate.total_clicks += 1
    
    def increment_referral():
        affiliate.total_referrals += 1
    
    def add_revenue(amount, commission):
        affiliate.total_referred_revenue += amount
        affiliate.total_commission_earned += commission
    
    def recalculate_tier():
        return False
    
    affiliate.increment_click = increment_click
    affiliate.increment_referral = increment_referral
    affiliate.add_revenue = add_revenue
    affiliate.recalculate_tier = recalculate_tier
    
    return affiliate


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.referred_by_affiliate_id = None
    return user


@pytest.fixture
def mock_referred_user(mock_affiliate):
    """Create a mock user who was referred by an affiliate."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "referred@example.com"
    user.referred_by_affiliate_id = mock_affiliate.id
    return user


class TestAffiliateTierCalculation:
    """Tests for tier calculation logic."""
    
    def test_rookie_tier_for_zero_revenue(self):
        """Test that $0 revenue results in Rookie tier."""
        tier = calculate_tier_for_revenue(Decimal("0"))
        assert tier.tier == AffiliateTier.ROOKIE
    
    def test_rookie_tier_for_low_revenue(self):
        """Test that < $500 revenue results in Rookie tier."""
        tier = calculate_tier_for_revenue(Decimal("150"))
        assert tier.tier == AffiliateTier.ROOKIE
    
    def test_pro_tier_threshold(self):
        """Test that $500+ revenue results in Pro tier."""
        tier = calculate_tier_for_revenue(Decimal("500"))
        assert tier.tier == AffiliateTier.PRO
    
    def test_all_star_tier_threshold(self):
        """Test that $2500+ revenue results in All-Star tier."""
        tier = calculate_tier_for_revenue(Decimal("2500"))
        assert tier.tier == AffiliateTier.ALL_STAR
    
    def test_hall_of_fame_tier_threshold(self):
        """Test that $5000+ revenue results in Hall of Fame tier."""
        tier = calculate_tier_for_revenue(Decimal("5000"))
        assert tier.tier == AffiliateTier.HALL_OF_FAME
    
    def test_commission_rates_by_tier(self):
        """Test that commission rates increase with tier."""
        rookie = AFFILIATE_TIERS[AffiliateTier.ROOKIE.value]
        pro = AFFILIATE_TIERS[AffiliateTier.PRO.value]
        hall_of_fame = AFFILIATE_TIERS[AffiliateTier.HALL_OF_FAME.value]
        
        # First subscription payment rate (top tier gets a higher first-sub rate)
        assert rookie.commission_rate_sub_first == Decimal("0.20")
        assert pro.commission_rate_sub_first == Decimal("0.25")
        assert hall_of_fame.commission_rate_sub_first == Decimal("0.40")
        
        # Recurring starts at 0, and unlocks at higher tiers
        assert rookie.commission_rate_sub_recurring == Decimal("0.00")
        assert pro.commission_rate_sub_recurring == Decimal("0.00")
        
        # Credit rate increases with tier
        assert rookie.commission_rate_credits == Decimal("0.20")
        assert hall_of_fame.commission_rate_credits == Decimal("0.40")


class TestAffiliateTierUpgrade:
    """Tests for tier upgrades updating stored commission rates."""

    def test_recalculate_tier_updates_rates_for_hall_of_fame(self):
        affiliate = Affiliate(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            referral_code="GORILLA40",
            tier=AffiliateTier.ALL_STAR.value,
            commission_rate_sub_first=Decimal("0.30"),
            commission_rate_sub_recurring=Decimal("0.10"),
            commission_rate_credits=Decimal("0.30"),
            total_referred_revenue=Decimal("5000.00"),
            total_commission_earned=Decimal("0.00"),
            total_commission_paid=Decimal("0.00"),
            total_clicks=0,
            total_referrals=0,
            is_active=True,
            is_approved=True,
        )

        upgraded = affiliate.recalculate_tier()

        assert upgraded is True
        assert affiliate.tier == AffiliateTier.HALL_OF_FAME.value
        assert affiliate.commission_rate_sub_first == Decimal("0.40")
        assert affiliate.commission_rate_sub_recurring == Decimal("0.10")
        assert affiliate.commission_rate_credits == Decimal("0.40")


class TestAffiliateService:
    """Tests for AffiliateService."""
    
    @pytest.mark.asyncio
    async def test_get_affiliate_by_code(self, mock_db, mock_affiliate):
        """Test getting affiliate by referral code."""
        service = AffiliateService(mock_db)
        
        # Setup mock response
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_affiliate
        mock_db.execute.return_value = mock_result
        
        affiliate = await service.get_affiliate_by_code("GORILLA123")
        
        assert affiliate is not None
        assert affiliate.referral_code == "GORILLA123"
    
    @pytest.mark.asyncio
    async def test_record_click(self, mock_db, mock_affiliate):
        """Test recording a referral click."""
        service = AffiliateService(mock_db)
        
        with patch.object(service, 'get_affiliate_by_code', return_value=mock_affiliate):
            click = await service.record_click(
                referral_code="GORILLA123",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                referer_url="https://twitter.com",
            )
        
        # Verify click was added
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        
        # Verify affiliate click count was incremented
        assert mock_affiliate.total_clicks == 1
    
    @pytest.mark.asyncio
    async def test_record_click_inactive_affiliate(self, mock_db, mock_affiliate):
        """Test that clicks for inactive affiliates are not recorded."""
        mock_affiliate.is_active = False
        
        service = AffiliateService(mock_db)
        
        with patch.object(service, 'get_affiliate_by_code', return_value=mock_affiliate):
            click = await service.record_click(
                referral_code="GORILLA123",
                ip_address="192.168.1.1",
            )
        
        assert click is None
    
    @pytest.mark.asyncio
    async def test_calculate_commission_subscription_first(self, mock_db, mock_affiliate, mock_referred_user):
        """Test commission calculation for first subscription payment."""
        service = AffiliateService(mock_db)
        
        # Setup mocks
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = mock_referred_user
        
        mock_result_affiliate = MagicMock()
        mock_result_affiliate.scalar_one_or_none.return_value = mock_affiliate

        # When webhook flags a "first subscription", the service verifies it's truly the
        # first-ever paid subscription for this user (avoids double-paying first-sub rate).
        mock_result_prior_subscription = MagicMock()
        mock_result_prior_subscription.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [
            mock_result_user,
            mock_result_affiliate,
            mock_result_prior_subscription,
        ]
        
        commission = await service.calculate_and_create_commission(
            user_id=str(mock_referred_user.id),
            sale_type=CommissionSaleType.SUBSCRIPTION.value,
            sale_amount=Decimal("39.99"),
            sale_id="sub_123",
            is_first_subscription=True,
            subscription_plan="elite_monthly",
        )
        
        # Verify commission was created
        assert commission is not None
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        
        assert commission.is_first_subscription_payment is True
        assert commission.commission_rate == Decimal("0.20")
        assert commission.amount == Decimal("7.998")  # 20% of $39.99

        # Verify affiliate revenue was added
        assert mock_affiliate.total_referred_revenue > 0

    @pytest.mark.asyncio
    async def test_calculate_commission_subscription_first_hof_40_percent(
        self, mock_db, mock_affiliate, mock_referred_user
    ):
        """Hall of Fame should earn 40% on a referred user's first-ever subscription payment."""
        service = AffiliateService(mock_db)

        # Make affiliate Hall of Fame rates explicit on the stored affiliate object
        mock_affiliate.tier = AffiliateTier.HALL_OF_FAME.value
        mock_affiliate.commission_rate_sub_first = Decimal("0.40")
        mock_affiliate.commission_rate_sub_recurring = Decimal("0.10")
        mock_affiliate.commission_rate_credits = Decimal("0.40")

        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = mock_referred_user

        mock_result_affiliate = MagicMock()
        mock_result_affiliate.scalar_one_or_none.return_value = mock_affiliate

        mock_result_prior_subscription = MagicMock()
        mock_result_prior_subscription.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [
            mock_result_user,
            mock_result_affiliate,
            mock_result_prior_subscription,
        ]

        commission = await service.calculate_and_create_commission(
            user_id=str(mock_referred_user.id),
            sale_type=CommissionSaleType.SUBSCRIPTION.value,
            sale_amount=Decimal("39.99"),
            sale_id="sub_456",
            is_first_subscription=True,
            subscription_plan="elite_monthly",
        )

        assert commission is not None
        assert commission.is_first_subscription_payment is True
        assert commission.commission_rate == Decimal("0.40")
        assert commission.amount == Decimal("15.996")  # 40% of $39.99

    @pytest.mark.asyncio
    async def test_first_subscription_flag_does_not_double_pay_first_sub_rate(
        self, mock_db, mock_affiliate, mock_referred_user
    ):
        """If a user already has a prior subscription commission, we must not re-apply first-sub rate."""
        service = AffiliateService(mock_db)

        mock_affiliate.tier = AffiliateTier.HALL_OF_FAME.value
        mock_affiliate.commission_rate_sub_first = Decimal("0.40")
        mock_affiliate.commission_rate_sub_recurring = Decimal("0.10")

        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = mock_referred_user

        mock_result_affiliate = MagicMock()
        mock_result_affiliate.scalar_one_or_none.return_value = mock_affiliate

        # Simulate an existing subscription commission already on record
        mock_result_prior_subscription = MagicMock()
        mock_result_prior_subscription.scalar_one_or_none.return_value = uuid.uuid4()

        mock_db.execute.side_effect = [
            mock_result_user,
            mock_result_affiliate,
            mock_result_prior_subscription,
        ]

        commission = await service.calculate_and_create_commission(
            user_id=str(mock_referred_user.id),
            sale_type=CommissionSaleType.SUBSCRIPTION.value,
            sale_amount=Decimal("39.99"),
            sale_id="sub_789",
            is_first_subscription=True,  # webhook says "first", but service enforces first-ever
            subscription_plan="elite_monthly",
        )

        assert commission is not None
        assert commission.is_first_subscription_payment is False
        assert commission.commission_rate == Decimal("0.10")
        assert commission.amount == Decimal("3.999")  # 10% of $39.99
    
    @pytest.mark.asyncio
    async def test_no_commission_for_unreferred_user(self, mock_db, mock_user):
        """Test that no commission is created for users without a referrer."""
        mock_user.referred_by_affiliate_id = None
        
        service = AffiliateService(mock_db)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        commission = await service.calculate_and_create_commission(
            user_id=str(mock_user.id),
            sale_type=CommissionSaleType.SUBSCRIPTION.value,
            sale_amount=Decimal("39.99"),
            sale_id="sub_123",
            is_first_subscription=True,
        )
        
        assert commission is None


    @pytest.mark.asyncio
    async def test_attribute_user_to_affiliate(self, mock_db, mock_affiliate, mock_user):
        """User attribution should set referred_by_affiliate_id and create referral."""
        # Mock affiliate lookup by code
        mock_result_aff = MagicMock()
        mock_result_aff.scalar_one_or_none.return_value = mock_affiliate
        # Mock user lookup
        from types import SimpleNamespace
        user_obj = SimpleNamespace(
            id=mock_user.id,
            email=mock_user.email,
            referred_by_affiliate_id=None,
        )
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = user_obj
        mock_db.execute.side_effect = [mock_result_aff, mock_result_user]

        service = AffiliateService(mock_db)
        # Avoid hitting deeper DB paths in create_referral
        from unittest.mock import AsyncMock
        service.create_referral = AsyncMock(return_value="referral")
        success = await service.attribute_user_to_affiliate(
            user_id=str(user_obj.id),
            referral_code=mock_affiliate.referral_code,
            click_id=None,
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_create_affiliate_generates_unique_code(self, mock_db, mock_user):
        """Ensure create_affiliate assigns a unique referral code and commits."""
        service = AffiliateService(mock_db)
        # get_affiliate_by_user_id returns None to allow creation
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=None)

        affiliate = await service.create_affiliate(str(mock_user.id))

        assert affiliate is not None
        assert affiliate.referral_code
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_calculate_commission_for_credit_pack(self, mock_db, mock_affiliate, mock_referred_user):
        """Commission should be created for credit pack purchases."""
        service = AffiliateService(mock_db)

        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = mock_referred_user

        mock_result_affiliate = MagicMock()
        mock_result_affiliate.scalar_one_or_none.return_value = mock_affiliate

        mock_db.execute.side_effect = [mock_result_user, mock_result_affiliate]

        commission = await service.calculate_and_create_commission(
            user_id=str(mock_referred_user.id),
            sale_type=CommissionSaleType.CREDIT_PACK.value,
            sale_amount=Decimal("25.00"),
            sale_id="credit_123",
            is_first_subscription=False,
            subscription_plan=None,
        )

        assert commission is not None
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

