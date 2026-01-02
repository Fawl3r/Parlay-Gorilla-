"""
Shared webhook handlers used by multiple payment providers.

NOTE: These functions preserve existing behavior from the legacy monolithic
`webhooks.py` route module. They are intentionally kept small and focused so
provider route modules can remain <500 LOC.
"""

from decimal import Decimal
import logging
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.billing_config import get_credit_pack
from app.core.config import settings
from app.models.affiliate_commission import CommissionSaleType, CommissionSettlementProvider
from app.models.parlay_purchase import ParlayPurchase, PurchaseStatus
from app.models.user import User
from app.services.affiliate_service import AffiliateService
from app.services.parlay_purchase_service import ParlayPurchaseService

logger = logging.getLogger(__name__)


async def _handle_parlay_purchase_confirmed(
    db: AsyncSession,
    user_id: str,
    parlay_type: str,
    provider: str,
    payload: dict,
):
    """
    Handle confirmed payment for one-time parlay purchase.

    Finds the pending purchase record and marks it as available.
    If no pending purchase exists, creates a new one (for direct purchases).
    """
    if not user_id:
        logger.warning("Parlay purchase confirmed but no user_id in payload")
        return

    if not parlay_type:
        parlay_type = "single"  # Default to single if not specified

    purchase_service = ParlayPurchaseService(db)

    # Try to find pending purchase for this user
    result = await db.execute(
        select(ParlayPurchase)
        .where(
            and_(
                ParlayPurchase.user_id == uuid.UUID(user_id),
                ParlayPurchase.parlay_type == parlay_type,
                ParlayPurchase.status == PurchaseStatus.pending.value,
                ParlayPurchase.provider == provider,
            )
        )
        .order_by(ParlayPurchase.created_at.desc())
        .limit(1)
    )
    purchase = result.scalar_one_or_none()

    if purchase:
        # Confirm existing purchase
        purchase.mark_as_available(settings.parlay_purchase_expiry_hours)
        logger.info(f"Confirmed parlay purchase {purchase.id} for user {user_id}")
    else:
        # Create new purchase (for cases where checkout was created externally)
        purchase = await purchase_service.create_parlay_purchase(
            user_id=user_id,
            parlay_type=parlay_type,
            provider=provider,
        )
        purchase.mark_as_available(settings.parlay_purchase_expiry_hours)
        logger.info(f"Created and confirmed parlay purchase {purchase.id} for user {user_id}")

    await db.commit()


async def _handle_credit_pack_purchase(
    db: AsyncSession,
    user_id: str,
    credit_pack_id: str,
    sale_id: str,
    provider: str,
):
    """
    Handle confirmed credit pack purchase.

    Adds credits to user's balance and calculates affiliate commission.
    """
    if not user_id:
        logger.warning("Credit pack purchase confirmed but no user_id")
        return

    # Get credit pack configuration
    credit_pack = get_credit_pack(credit_pack_id)
    if not credit_pack:
        logger.error(f"Unknown credit pack ID: {credit_pack_id}")
        return

    # Fulfill idempotently (purchase-level idempotency)
    from app.services.credit_pack_fulfillment_service import CreditPackFulfillmentService

    fulfillment_service = CreditPackFulfillmentService(db)
    result = await fulfillment_service.fulfill_credit_pack_purchase(
        provider=provider,
        provider_order_id=sale_id,
        user_id=user_id,
        credit_pack_id=credit_pack_id,
    )

    if not result.applied:
        logger.info(
            f"Skipping credit pack fulfillment (already fulfilled): provider={provider} "
            f"order_id={sale_id} user_id={user_id} pack_id={credit_pack_id}"
        )
        return

    # Handle affiliate commission (only once, when credits were actually awarded)
    await _handle_affiliate_commission(
        db=db,
        user_id=user_id,
        sale_type=CommissionSaleType.CREDIT_PACK.value,
        sale_amount=credit_pack.price,
        sale_id=sale_id,
        credit_pack_id=credit_pack_id,
        settlement_provider=(
            CommissionSettlementProvider.STRIPE.value
            if provider == "stripe"
            else (CommissionSettlementProvider.LEMONSQUEEZY.value if provider == "lemonsqueezy" else CommissionSettlementProvider.INTERNAL.value)
        ),
    )

    logger.info(
        f"Added {result.credits_added} credits to user {user_id}. New balance: {result.new_balance} "
        f"(provider={provider}, order_id={sale_id}, pack_id={credit_pack_id})"
    )


async def _handle_affiliate_commission(
    db: AsyncSession,
    user_id: str,
    sale_type: str,
    sale_amount: Decimal,
    sale_id: str,
    settlement_provider: str = CommissionSettlementProvider.INTERNAL.value,
    is_first_subscription: bool = False,
    subscription_plan: str = None,
    credit_pack_id: str = None,
):
    """
    Calculate and create affiliate commission for a referred user's purchase.

    This is called from all payment handlers when a payment is confirmed.
    Does nothing if user has no affiliate referral.
    """
    try:
        affiliate_service = AffiliateService(db)

        commission = await affiliate_service.calculate_and_create_commission(
            user_id=user_id,
            sale_type=sale_type,
            sale_amount=sale_amount,
            sale_id=sale_id,
            settlement_provider=settlement_provider,
            is_first_subscription=is_first_subscription,
            subscription_plan=subscription_plan,
            credit_pack_id=credit_pack_id,
        )

        if commission:
            logger.info(
                f"Created affiliate commission for user {user_id}: "
                f"${commission.amount} ({commission.commission_rate * 100}% of ${sale_amount})"
            )
    except Exception as e:
        # Don't fail the payment webhook because of commission issues
        logger.error(f"Error creating affiliate commission for user {user_id}: {e}")


