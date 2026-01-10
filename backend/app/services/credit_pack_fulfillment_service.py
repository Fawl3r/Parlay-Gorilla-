"""
Credit pack fulfillment service.

Single responsibility:
- Guarantee purchase-level idempotency for credit pack awards
- Atomically increment a user's credit balance exactly once per provider order/charge
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.billing_config import get_credit_pack
from app.models.credit_pack_purchase import CreditPackPurchase, CreditPackPurchaseStatus
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreditPackFulfillmentResult:
    applied: bool
    credits_added: int
    new_balance: int
    purchase_id: str | None
    reason: str | None = None


class CreditPackFulfillmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fulfill_credit_pack_purchase(
        self,
        *,
        provider: str,
        provider_order_id: str,
        user_id: str,
        credit_pack_id: str,
    ) -> CreditPackFulfillmentResult:
        """
        Fulfill (award) a credit pack purchase.

        Important:
        - This method does NOT commit the session. The caller should commit.
        - Idempotency is enforced by `CreditPackPurchase(provider, provider_order_id)` uniqueness.
        """
        provider = (provider or "").strip().lower()
        provider_order_id = (provider_order_id or "").strip()

        if not provider:
            raise ValueError("provider is required")
        if not provider_order_id:
            raise ValueError("provider_order_id is required")

        user_uuid = self._coerce_user_id(user_id)

        credit_pack = get_credit_pack(credit_pack_id)
        if not credit_pack:
            raise ValueError(f"Unknown credit pack id: {credit_pack_id}")

        existing = await self._get_existing_purchase(provider, provider_order_id)
        if existing:
            balance = await self._get_user_credit_balance(user_uuid)
            return CreditPackFulfillmentResult(
                applied=False,
                credits_added=0,
                new_balance=balance,
                purchase_id=str(existing.id),
                reason="already_fulfilled",
            )

        credits_to_add = int(credit_pack.total_credits)
        now = datetime.now(timezone.utc)

        try:
            async with self.db.begin_nested():
                user = await self._get_user_for_update(user_uuid)
                if not user:
                    raise ValueError(f"User not found: {user_id}")

                purchase = CreditPackPurchase(
                    id=uuid.uuid4(),
                    user_id=user_uuid,
                    provider=provider,
                    provider_order_id=provider_order_id,
                    credit_pack_id=credit_pack_id,
                    credits_awarded=credits_to_add,
                    amount=credit_pack.price,
                    currency=credit_pack.currency,
                    status=CreditPackPurchaseStatus.fulfilled.value,
                    fulfilled_at=now,
                )
                self.db.add(purchase)
                await self.db.flush()  # insert purchase (may raise on unique constraint)

                user.credit_balance += credits_to_add
                await self.db.flush()

                return CreditPackFulfillmentResult(
                    applied=True,
                    credits_added=credits_to_add,
                    new_balance=int(user.credit_balance),
                    purchase_id=str(purchase.id),
                    reason=None,
                )
        except IntegrityError:
            # Race condition: another worker fulfilled first.
            existing = await self._get_existing_purchase(provider, provider_order_id)
            balance = await self._get_user_credit_balance(user_uuid)
            return CreditPackFulfillmentResult(
                applied=False,
                credits_added=0,
                new_balance=balance,
                purchase_id=str(existing.id) if existing else None,
                reason="already_fulfilled",
            )

    def _coerce_user_id(self, user_id: str) -> uuid.UUID:
        try:
            return uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except Exception as exc:
            raise ValueError(f"Invalid user_id: {user_id}") from exc

    async def _get_existing_purchase(self, provider: str, provider_order_id: str) -> CreditPackPurchase | None:
        result = await self.db.execute(
            select(CreditPackPurchase).where(
                (CreditPackPurchase.provider == provider)
                & (CreditPackPurchase.provider_order_id == provider_order_id)
            )
        )
        return result.scalar_one_or_none()

    async def _get_user_for_update(self, user_id: uuid.UUID) -> User | None:
        # Use noload() to prevent eager loading of relationships when using FOR UPDATE
        # This avoids PostgreSQL error: "FOR UPDATE cannot be applied to the nullable side of an outer join"
        from sqlalchemy.orm import noload
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(noload(User.affiliate_account), noload(User.referred_by_affiliate), noload(User.referral_record))
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def _get_user_credit_balance(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(select(User.credit_balance).where(User.id == user_id))
        balance = result.scalar_one_or_none()
        return int(balance or 0)


