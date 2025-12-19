"""
Affiliate payout minimum threshold tests.

Ensures the payout pipeline only creates payouts when an affiliate has at least
$25.00 in READY (internal-settled) commissions.
"""

from __future__ import annotations

from decimal import Decimal
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate import Affiliate
from app.models.affiliate_commission import AffiliateCommission, CommissionSettlementProvider
from app.models.user import User
from app.services.payout_service import PayoutService


@pytest.mark.asyncio
async def test_get_ready_commissions_filters_out_under_minimum_by_default(db: AsyncSession):
    user = User(id=uuid.uuid4(), email=f"payout-min-{uuid.uuid4()}@example.com")
    db.add(user)
    await db.commit()

    affiliate = Affiliate.create_with_referral_code(user.id)
    affiliate.payout_email = "affiliate@example.com"
    affiliate.payout_method = "paypal"
    db.add(affiliate)
    await db.commit()

    # 124.95 * 0.20 = 24.99 (below $25 minimum)
    c1 = AffiliateCommission.create_commission(
        affiliate_id=affiliate.id,
        referred_user_id=uuid.uuid4(),
        sale_id=f"sale_{uuid.uuid4()}",
        sale_type="subscription",
        base_amount=Decimal("124.95"),
        commission_rate=Decimal("0.20"),
        settlement_provider=CommissionSettlementProvider.INTERNAL.value,
    )
    c1.mark_ready()
    db.add(c1)
    await db.commit()

    payout_service = PayoutService(db)
    ready = await payout_service.get_ready_commissions_for_affiliate(str(affiliate.id))

    assert ready == []


@pytest.mark.asyncio
async def test_create_payout_requires_minimum_total_amount(db: AsyncSession):
    user = User(id=uuid.uuid4(), email=f"payout-min2-{uuid.uuid4()}@example.com")
    db.add(user)
    await db.commit()

    affiliate = Affiliate.create_with_referral_code(user.id)
    affiliate.payout_email = "affiliate@example.com"
    affiliate.payout_method = "paypal"
    db.add(affiliate)
    await db.commit()

    c1 = AffiliateCommission.create_commission(
        affiliate_id=affiliate.id,
        referred_user_id=uuid.uuid4(),
        sale_id=f"sale_{uuid.uuid4()}",
        sale_type="subscription",
        base_amount=Decimal("62.50"),  # 12.50 commission
        commission_rate=Decimal("0.20"),
        settlement_provider=CommissionSettlementProvider.INTERNAL.value,
    )
    c1.mark_ready()

    c2 = AffiliateCommission.create_commission(
        affiliate_id=affiliate.id,
        referred_user_id=uuid.uuid4(),
        sale_id=f"sale_{uuid.uuid4()}",
        sale_type="subscription",
        base_amount=Decimal("62.50"),  # 12.50 commission
        commission_rate=Decimal("0.20"),
        settlement_provider=CommissionSettlementProvider.INTERNAL.value,
    )
    c2.mark_ready()

    db.add_all([c1, c2])
    await db.commit()

    payout_service = PayoutService(db)

    # Below minimum: $12.50 total
    payout = await payout_service.create_payout(
        affiliate_id=str(affiliate.id),
        commission_ids=[str(c1.id)],
        payout_method="paypal",
        notes="test",
    )
    assert payout is None

    # Meets minimum: $25.00 total
    payout = await payout_service.create_payout(
        affiliate_id=str(affiliate.id),
        commission_ids=[str(c1.id), str(c2.id)],
        payout_method="paypal",
        notes="test",
    )
    assert payout is not None
    assert Decimal(payout.amount) == Decimal("25.00")


