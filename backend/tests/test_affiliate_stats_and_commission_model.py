"""
Tests for affiliate stats + commission model utilities.

This is split out from `test_affiliate_service.py` to keep files under 500 lines.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import uuid

from app.models.affiliate_commission import (
    AffiliateCommission,
    CommissionSaleType,
    CommissionSettlementProvider,
    CommissionStatus,
)
from app.services.affiliate_stats_service import AffiliateStats, SettlementTotals


class TestAffiliateStats:
    """Tests for AffiliateStats data class."""

    def test_stats_to_dict(self):
        """Test that AffiliateStats converts to dict properly."""
        stats = AffiliateStats(
            total_clicks=100,
            total_referrals=25,
            total_revenue=Decimal("500.00"),
            total_commission_earned=Decimal("100.00"),
            total_commission_paid=Decimal("50.00"),
            pending_commission=Decimal("50.00"),
            conversion_rate=25.0,
            clicks_last_30_days=30,
            referrals_last_30_days=8,
            revenue_last_30_days=Decimal("150.00"),
            settlement_breakdown={
                CommissionSettlementProvider.INTERNAL.value: SettlementTotals(
                    earned=Decimal("60.00"), paid=Decimal("20.00"), pending=Decimal("40.00")
                ),
                CommissionSettlementProvider.LEMONSQUEEZY.value: SettlementTotals(
                    earned=Decimal("40.00"), paid=Decimal("30.00"), pending=Decimal("10.00")
                ),
            },
        )

        d = stats.to_dict()

        assert d["total_clicks"] == 100
        assert d["total_referrals"] == 25
        assert d["total_revenue"] == 500.0
        assert d["conversion_rate"] == 25.0
        assert d["last_30_days"]["clicks"] == 30
        assert d["last_30_days"]["revenue"] == 150.0
        assert "settlement_breakdown" in d
        assert d["settlement_breakdown"]["internal"]["earned"] == 60.0
        assert d["settlement_breakdown"]["lemonsqueezy"]["earned"] == 40.0


class TestCommissionLifecycle:
    """Tests for commission status lifecycle."""

    def test_commission_starts_pending(self):
        """Test that new commissions start as pending."""
        commission = AffiliateCommission.create_commission(
            affiliate_id=uuid.uuid4(),
            referred_user_id=uuid.uuid4(),
            sale_id="sale_123",
            sale_type=CommissionSaleType.SUBSCRIPTION.value,
            base_amount=Decimal("39.99"),
            commission_rate=Decimal("0.20"),
            is_first_subscription_payment=True,
        )

        assert commission.status == CommissionStatus.PENDING.value
        assert commission.settlement_provider == CommissionSettlementProvider.INTERNAL.value

    def test_commission_ready_at_calculation(self):
        """Test that ready_at is 30 days after creation."""
        commission = AffiliateCommission.create_commission(
            affiliate_id=uuid.uuid4(),
            referred_user_id=uuid.uuid4(),
            sale_id="sale_123",
            sale_type=CommissionSaleType.CREDIT_PACK.value,
            base_amount=Decimal("19.99"),
            commission_rate=Decimal("0.25"),
        )

        # ready_at should be ~30 days from now
        days_until_ready = (commission.ready_at - datetime.now(timezone.utc)).days
        assert 29 <= days_until_ready <= 30

    def test_commission_amount_calculation(self):
        """Test that commission amount is calculated correctly."""
        commission = AffiliateCommission.create_commission(
            affiliate_id=uuid.uuid4(),
            referred_user_id=uuid.uuid4(),
            sale_id="sale_123",
            sale_type=CommissionSaleType.SUBSCRIPTION.value,
            base_amount=Decimal("39.99"),
            commission_rate=Decimal("0.20"),  # 20%
            is_first_subscription_payment=True,
        )

        # 20% of $39.99 = $7.998
        assert commission.amount == Decimal("7.998")

    def test_mark_commission_ready(self):
        """Test marking a commission as ready."""
        commission = AffiliateCommission.create_commission(
            affiliate_id=uuid.uuid4(),
            referred_user_id=uuid.uuid4(),
            sale_id="sale_123",
            sale_type=CommissionSaleType.CREDIT_PACK.value,
            base_amount=Decimal("19.99"),
            commission_rate=Decimal("0.25"),
        )

        commission.mark_ready()

        assert commission.status == CommissionStatus.READY.value

    def test_mark_commission_paid(self):
        """Test marking a commission as paid."""
        commission = AffiliateCommission.create_commission(
            affiliate_id=uuid.uuid4(),
            referred_user_id=uuid.uuid4(),
            sale_id="sale_123",
            sale_type=CommissionSaleType.CREDIT_PACK.value,
            base_amount=Decimal("19.99"),
            commission_rate=Decimal("0.25"),
        )

        commission.mark_ready()
        commission.mark_paid(payout_id="payout_123", notes="Paid via PayPal")

        assert commission.status == CommissionStatus.PAID.value
        assert commission.payout_id == "payout_123"
        assert commission.paid_at is not None


