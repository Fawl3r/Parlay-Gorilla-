"""Promo code creation and redemption service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.promo_code import PromoCode, PromoRewardType
from app.models.promo_redemption import PromoRedemption
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import SubscriptionStatusEnum, User, UserPlan
from app.services.promo_codes.promo_code_generator import PromoCodeGenerator


@dataclass(frozen=True)
class PromoRedeemResult:
    reward_type: PromoRewardType
    message: str
    credits_added: int = 0
    new_credit_balance: Optional[int] = None
    premium_until: Optional[datetime] = None


class PromoCodeService:
    """
    Service for managing promo codes.

    Redemption is enforced atomically:
    - Row-lock PromoCode
    - Check eligibility + per-user uniqueness
    - Apply reward
    - Insert PromoRedemption
    - Increment redeemed_count
    """

    _PREMIUM_DAYS = 30
    _CREDITS_AMOUNT = 3
    _DEFAULT_PREMIUM_PLAN_CODE = "PG_PREMIUM_MONTHLY"

    def __init__(self, db: AsyncSession):
        self._db = db
        self._generator = PromoCodeGenerator()

    async def create_code(
        self,
        *,
        reward_type: PromoRewardType,
        expires_at: datetime,
        max_uses_total: int = 1,
        created_by_user_id: Optional[str] = None,
        code: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> PromoCode:
        expires_at = self._require_tz(expires_at)
        if expires_at <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")

        normalized_code = PromoCodeGenerator.normalize(code) if code else None

        for _attempt in range(10):
            chosen_code = normalized_code or self._generator.generate(reward_type)
            promo = PromoCode(
                code=chosen_code,
                reward_type=reward_type.value,
                expires_at=expires_at,
                max_uses_total=max_uses_total,
                redeemed_count=0,
                is_active=True,
                created_by_user_id=created_by_user_id,
                notes=notes,
            )
            self._db.add(promo)
            try:
                await self._db.commit()
                await self._db.refresh(promo)
                return promo
            except IntegrityError:
                await self._db.rollback()
                if normalized_code:
                    raise ValueError("code already exists")
                continue

        raise RuntimeError("Failed to generate a unique promo code after multiple attempts")

    async def bulk_create_codes(
        self,
        *,
        reward_type: PromoRewardType,
        expires_at: datetime,
        count: int = 10,
        max_uses_total: int = 1,
        created_by_user_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> list[PromoCode]:
        expires_at = self._require_tz(expires_at)
        if expires_at <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")

        if count < 1 or count > 500:
            raise ValueError("count must be between 1 and 500")

        for _attempt in range(3):
            try:
                codes = set()
                promos: list[PromoCode] = []
                for _ in range(count):
                    generated = self._generator.generate(reward_type)
                    while generated in codes:
                        generated = self._generator.generate(reward_type)
                    codes.add(generated)
                    promos.append(
                        PromoCode(
                            code=generated,
                            reward_type=reward_type.value,
                            expires_at=expires_at,
                            max_uses_total=max_uses_total,
                            redeemed_count=0,
                            is_active=True,
                            created_by_user_id=created_by_user_id,
                            notes=notes,
                        )
                    )

                self._db.add_all(promos)
                await self._db.commit()
                for promo in promos:
                    await self._db.refresh(promo)
                return promos
            except IntegrityError:
                await self._db.rollback()
                continue

        raise RuntimeError("Failed to bulk-create promo codes (unique constraint collisions)")

    async def list_codes(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        reward_type: Optional[PromoRewardType] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[PromoCode], int]:
        page = max(1, int(page))
        page_size = min(100, max(1, int(page_size)))
        offset = (page - 1) * page_size

        query = select(PromoCode)
        count_query = select(func.count(PromoCode.id))

        conditions = []
        if search:
            conditions.append(PromoCode.code.ilike(f"%{search.strip()}%"))
        if reward_type:
            conditions.append(PromoCode.reward_type == reward_type.value)
        if is_active is not None:
            conditions.append(PromoCode.is_active == is_active)
        if conditions:
            from sqlalchemy import and_

            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total = int((await self._db.execute(count_query)).scalar_one() or 0)
        result = await self._db.execute(
            query.order_by(PromoCode.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def deactivate(self, *, promo_code_id: str) -> PromoCode:
        from uuid import UUID

        promo = (
            await self._db.execute(select(PromoCode).where(PromoCode.id == UUID(promo_code_id)))
        ).scalar_one_or_none()
        if not promo:
            raise ValueError("promo code not found")

        promo.is_active = False
        promo.deactivated_at = datetime.now(timezone.utc)
        await self._db.commit()
        await self._db.refresh(promo)
        return promo

    async def redeem(
        self,
        *,
        user: User,
        code: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> PromoRedeemResult:
        normalized = PromoCodeGenerator.normalize(code)
        if not normalized:
            raise ValueError("Invalid code")

        now = datetime.now(timezone.utc)

        promo = (
            await self._db.execute(
                select(PromoCode)
                .where(PromoCode.code == normalized)
                .with_for_update()
            )
        ).scalar_one_or_none()

        if not promo:
            raise ValueError("Code not found")
        if not promo.is_active:
            raise ValueError("Code is not active")
        expires_at = self._to_utc(promo.expires_at)
        if expires_at <= now:
            raise ValueError("Code is expired")
        if promo.redeemed_count >= promo.max_uses_total:
            raise ValueError("Code has no remaining uses")

        # One-time per account (enforced also by UNIQUE constraint)
        already = (
            await self._db.execute(
                select(PromoRedemption.id).where(
                    PromoRedemption.promo_code_id == promo.id,
                    PromoRedemption.user_id == user.id,
                )
            )
        ).scalar_one_or_none()
        if already:
            raise ValueError("Code already redeemed for this account")

        reward_type = PromoRewardType(promo.reward_type)

        credits_added = 0
        new_credit_balance: Optional[int] = None
        premium_until: Optional[datetime] = None

        if reward_type == PromoRewardType.credits_3:
            credits_added = self._CREDITS_AMOUNT
            user.credit_balance += credits_added
            new_credit_balance = int(user.credit_balance)

        elif reward_type == PromoRewardType.premium_month:
            premium_until = await self._grant_premium_month(user=user, now=now)

        else:
            raise ValueError("Unsupported promo reward")

        self._db.add(
            PromoRedemption(
                promo_code_id=promo.id,
                user_id=user.id,
                reward_type=reward_type.value,
                user_agent=user_agent,
                ip_address=ip_address,
            )
        )
        promo.redeemed_count += 1

        await self._db.commit()

        message = (
            "Promo code redeemed."
            if reward_type == PromoRewardType.credits_3
            else "Premium unlocked for 30 days."
        )
        return PromoRedeemResult(
            reward_type=reward_type,
            message=message,
            credits_added=credits_added,
            new_credit_balance=new_credit_balance,
            premium_until=premium_until,
        )

    async def _grant_premium_month(self, *, user: User, now: datetime) -> datetime:
        """
        Grant a premium month by creating a new Subscription period.

        - If user has an existing non-lifetime subscription with a future period_end,
          stack the promo month after it.
        - If user is lifetime (or has no end date), reject to avoid wasting the code.
        """
        existing = (
            await self._db.execute(
                select(Subscription)
                .where(Subscription.user_id == user.id)
                # SQLite does not support NULLS LAST, so emulate ordering:
                # - Non-null period_end first
                # - Latest period_end first
                # - Newest record as tie-breaker
                .order_by(
                    Subscription.current_period_end.is_(None),
                    Subscription.current_period_end.desc(),
                    Subscription.created_at.desc(),
                )
                .limit(1)
                .with_for_update()
            )
        ).scalar_one_or_none()

        if existing and (getattr(existing, "is_lifetime", False) or existing.current_period_end is None):
            raise ValueError("You already have lifetime premium access")

        base_end = now
        if existing and existing.current_period_end:
            existing_end = self._to_utc(existing.current_period_end)
            if existing_end > now:
                base_end = existing_end

        period_start = base_end if base_end > now else now
        period_end = base_end + timedelta(days=self._PREMIUM_DAYS)

        plan_code = (
            (existing.plan if existing and (existing.plan or "").strip() else None)
            or (user.subscription_plan or "").strip()
            or self._DEFAULT_PREMIUM_PLAN_CODE
        )

        self._db.add(
            Subscription(
                user_id=user.id,
                plan=plan_code,
                provider="promo",
                provider_subscription_id=None,
                provider_customer_id=None,
                status=SubscriptionStatus.active.value,
                current_period_start=period_start,
                current_period_end=period_end,
                cancel_at_period_end=True,
                is_lifetime=False,
                provider_metadata={"source": "promo_code"},
            )
        )

        # Keep legacy/user-facing subscription fields in sync (used by billing access-status).
        user.subscription_plan = plan_code
        user.subscription_status = SubscriptionStatusEnum.active.value
        user.subscription_renewal_date = period_end
        user.subscription_last_billed_at = now
        user.daily_parlays_used = 0

        # Align user.plan with plan_code naming (consistent with webhooks).
        # PG_PREMIUM_MONTHLY maps to elite tier
        if plan_code == "PG_PREMIUM_MONTHLY" or "premium" in (plan_code or "").lower():
            user.plan = UserPlan.elite.value
        else:
            user.plan = UserPlan.standard.value

        return period_end

    @staticmethod
    def _require_tz(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            raise ValueError("datetime must include timezone")
        return dt

    @staticmethod
    def _to_utc(dt: datetime) -> datetime:
        """
        Normalize datetimes to UTC-aware.

        SQLite commonly returns naive datetimes even when `timezone=True`.
        We treat naive values as UTC to keep comparisons safe in tests/CI.
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


