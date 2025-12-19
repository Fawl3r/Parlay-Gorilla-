"""
Coinbase subscription fulfillment.

Coinbase Commerce charges are one-time payments. For "monthly" and "annual" crypto
plans, users must manually renew by paying again before their access end date.

This service:
- Creates a Subscription record for each confirmed charge (idempotent by charge_id).
- Sets current_period_end for time-based plans (monthly/annual).
- Leaves current_period_end unset for lifetime plans.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription, SubscriptionStatus
from app.models.subscription_plan import BillingCycle, SubscriptionPlan
from app.models.user import SubscriptionStatusEnum, User
from app.utils.datetime_utils import coerce_utc, now_utc

logger = logging.getLogger(__name__)


@dataclass
class CoinbaseSubscriptionFulfillmentService:
    db: AsyncSession

    async def fulfill_from_confirmed_charge(
        self,
        *,
        user_id: str,
        plan_code: str,
        charge_id: str,
        charge_data: dict,
    ) -> Subscription | None:
        """
        Create a subscription record from a confirmed Coinbase charge.

        Returns:
            Subscription if created, None if already processed for this charge_id.
        """
        user_uuid = uuid.UUID(user_id)
        plan_code = (plan_code or "").strip()
        charge_id = (charge_id or "").strip()
        if not plan_code or not charge_id:
            raise ValueError("plan_code and charge_id are required")

        # Idempotency by provider charge id.
        existing = await self.db.execute(
            select(Subscription.id).where(
                and_(
                    Subscription.provider == "coinbase",
                    Subscription.provider_subscription_id == charge_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            logger.info("Coinbase subscription already processed for charge_id=%s", charge_id)
            return None

        billing_cycle = await self._resolve_billing_cycle(plan_code)
        is_lifetime = billing_cycle == BillingCycle.lifetime.value

        now = now_utc()
        period_end = None
        period_start = now

        if not is_lifetime:
            duration_days = self._duration_days_for_cycle(billing_cycle)
            period_start = await self._compute_stacked_start(user_uuid=user_uuid, plan_code=plan_code, now=now)
            period_end = period_start + timedelta(days=duration_days)

        subscription = Subscription(
            id=uuid.uuid4(),
            user_id=user_uuid,
            plan=plan_code,
            provider="coinbase",
            provider_subscription_id=charge_id,
            status=SubscriptionStatus.active.value,
            current_period_start=period_start,
            current_period_end=period_end,
            is_lifetime=is_lifetime,
            provider_metadata=charge_data,
        )
        self.db.add(subscription)

        # Update user subscription fields for account details.
        user = (await self.db.execute(select(User).where(User.id == user_uuid))).scalar_one_or_none()
        if user:
            user.plan = self._user_plan_for_subscription(plan_code, is_lifetime=is_lifetime)
            user.subscription_plan = plan_code
            user.subscription_status = SubscriptionStatusEnum.active.value
            user.subscription_renewal_date = period_end  # None for lifetime
            user.subscription_last_billed_at = now
            user.daily_parlays_used = 0

        return subscription

    async def _resolve_billing_cycle(self, plan_code: str) -> str:
        # Prefer DB plan definition when present.
        result = await self.db.execute(select(SubscriptionPlan.billing_cycle).where(SubscriptionPlan.code == plan_code))
        billing_cycle = result.scalar_one_or_none()
        if billing_cycle:
            return str(billing_cycle)

        # Fallback inference.
        lc = plan_code.lower()
        if "lifetime" in lc:
            return BillingCycle.lifetime.value
        if "annual" in lc or "year" in lc:
            return BillingCycle.annual.value
        return BillingCycle.monthly.value

    def _duration_days_for_cycle(self, billing_cycle: str) -> int:
        if billing_cycle == BillingCycle.annual.value:
            return 365
        # default to 30-day months
        return 30

    async def _compute_stacked_start(self, *, user_uuid: uuid.UUID, plan_code: str, now) -> object:
        """
        Compute start for the new period.

        If the user renews early (existing period end in the future), we stack from
        that end; otherwise from now.
        """
        result = await self.db.execute(
            select(Subscription.current_period_end)
            .where(
                and_(
                    Subscription.user_id == user_uuid,
                    Subscription.provider == "coinbase",
                    Subscription.plan == plan_code,
                    Subscription.current_period_end.is_not(None),
                )
            )
            .order_by(Subscription.current_period_end.desc())
            .limit(1)
        )
        last_end = result.scalar_one_or_none()
        if not last_end:
            return now
        try:
            last_end_utc = coerce_utc(last_end)
        except Exception:
            return now
        return last_end_utc if last_end_utc > now else now

    def _user_plan_for_subscription(self, plan_code: str, *, is_lifetime: bool) -> str:
        if is_lifetime:
            return "elite"
        if "elite" in (plan_code or "").lower():
            return "elite"
        return "standard"


