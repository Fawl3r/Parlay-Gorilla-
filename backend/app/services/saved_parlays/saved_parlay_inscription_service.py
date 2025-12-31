"""Saved parlay inscription orchestration.

Responsibilities:
- Enforce eligibility (custom-only)
- Enforce premium requirement
- Consume included premium inscription quota when available
- After included quota is exhausted, allow premium users to pay via credits
- Persist per-saved-parlay payment flags so retries don't double-charge
- Enqueue the Redis job for the inscriptions worker
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import AccessErrorCode, PaywallException
from app.core.config import settings
from app.models.saved_parlay import InscriptionStatus, SavedParlay, SavedParlayType
from app.models.user import User
from app.services.premium_usage_service import PremiumUsageService
from app.services.saved_parlays.inscription_queue import InscriptionQueue
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


class SavedParlayInscriptionService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def queue(self, *, saved: SavedParlay, user: User) -> SavedParlay:
        """
        Queue a custom saved parlay for on-chain verification.

        Notes:
        - Idempotent for status queued/confirmed (returns the current record).
        - Retry-safe: quota/credits are charged at most once per saved parlay.
        """
        if str(getattr(saved, "parlay_type", "") or "").strip() != SavedParlayType.custom.value:
            raise ValueError("On-chain verification is available for Custom AI parlays only.")

        status = str(getattr(saved, "inscription_status", InscriptionStatus.none.value) or InscriptionStatus.none.value)
        if status in {InscriptionStatus.confirmed.value, InscriptionStatus.queued.value}:
            return saved

        # Premium-gated (for now). Credits are used only for overage once premium included quota is exhausted.
        subscription_service = SubscriptionService(self._db)
        if not await subscription_service.is_user_premium(str(user.id)):
            raise PaywallException(
                error_code=AccessErrorCode.PREMIUM_REQUIRED,
                message="On-chain inscriptions are a Gorilla Premium feature.",
                feature="inscriptions",
            )

        usage = PremiumUsageService(self._db)

        quota_consumed = bool(getattr(saved, "inscription_quota_consumed", False) or False)
        credits_consumed = bool(getattr(saved, "inscription_credits_consumed", False) or False)
        already_paid = quota_consumed or credits_consumed

        # Resolve whether we should consume included quota or charge credits.
        should_consume_quota = False
        should_charge_credits = False
        credits_required = int(getattr(settings, "credits_cost_inscription", 1) or 1)
        credit_unit = "credit" if credits_required == 1 else "credits"

        snap = None
        if not already_paid:
            snap = await usage.get_inscriptions_snapshot(user)
            if int(snap.remaining) > 0:
                should_consume_quota = True
            else:
                # Premium overage path: credits
                credits_available = int(getattr(user, "credit_balance", 0) or 0)
                if credits_available < credits_required:
                    raise PaywallException(
                        error_code=AccessErrorCode.FREE_LIMIT_REACHED,
                        message=(
                            f"You've used all {snap.limit} included inscriptions in your current "
                            f"{settings.premium_inscriptions_period_days}-day period. "
                            f"Additional inscriptions cost {credits_required} {credit_unit} each."
                        ),
                        remaining_today=0,
                        feature="inscriptions",
                    )
                should_charge_credits = True

        try:
            if should_charge_credits:
                # Atomically spend credits in the DB before enqueue to ensure we never create
                # an unpaid inscription job. If enqueue fails, we refund credits.
                try:
                    user_uuid = uuid.UUID(str(user.id))
                except Exception as exc:
                    raise ValueError("Invalid user id") from exc

                stmt = (
                    update(User)
                    .where(User.id == user_uuid)
                    .where(User.credit_balance >= credits_required)
                    .values(credit_balance=User.credit_balance - credits_required)
                )
                res = await self._db.execute(stmt)
                if getattr(res, "rowcount", 0) != 1:
                    await self._db.rollback()
                    raise PaywallException(
                        error_code=AccessErrorCode.FREE_LIMIT_REACHED,
                        message=(
                            f"Additional inscriptions cost {credits_required} {credit_unit} each. "
                            "Buy credits to continue."
                        ),
                        remaining_today=0,
                        feature="inscriptions",
                    )

                # Mark credits consumed on the saved parlay (retry-safe).
                saved.inscription_credits_consumed = True

            # Set inscription state and persist before enqueue.
            saved.inscription_status = InscriptionStatus.queued.value
            saved.inscription_hash = str(getattr(saved, "content_hash", "") or "")
            saved.inscription_error = None
            saved.inscription_tx = None
            saved.inscribed_at = None
            self._db.add(saved)
            await self._db.commit()
            await self._db.refresh(saved)

            # Enqueue inscription job.
            enqueued = await self._enqueue(saved)

            if not enqueued:
                # If enqueue fails, revert credit charge (best-effort).
                if should_charge_credits:
                    await self._refund_credits_and_revert_flag(saved=saved, user=user, credits=credits_required)
                return saved

            if should_consume_quota:
                new_used = await usage.increment_inscriptions_used(user, count=1)
                logger.info(
                    "Inscription queued (included quota): user=%s saved_parlay=%s cost_usd=%.2f used=%s",
                    getattr(user, "id", "unknown"),
                    str(getattr(saved, "id", "")),
                    float(getattr(settings, "inscription_cost_usd", 0.37) or 0.37),
                    int(new_used),
                )
                saved.inscription_quota_consumed = True
                self._db.add(saved)
                await self._db.commit()
                await self._db.refresh(saved)

            return saved
        except PaywallException:
            # If we reserved the flag but didn't spend, try to revert.
            raise
        except ValueError:
            raise
        except Exception:
            # If something unexpected happens after we spent credits, try to revert.
            if should_charge_credits:
                try:
                    await self._refund_credits_and_revert_flag(saved=saved, user=user, credits=credits_required)
                except Exception:
                    logger.exception("Failed to refund credits after inscription queue failure (saved_parlay=%s)", saved.id)
            raise

    async def _enqueue(self, saved: SavedParlay) -> bool:
        if saved.inscription_status != InscriptionStatus.queued.value:
            return False

        queue = InscriptionQueue()
        try:
            await queue.enqueue_saved_parlay(saved_parlay_id=str(saved.id))
            return True
        except Exception as exc:
            saved.inscription_status = InscriptionStatus.failed.value
            saved.inscription_error = f"Enqueue failed: {exc.__class__.__name__}"
            self._db.add(saved)
            await self._db.commit()
            await self._db.refresh(saved)
            return False

    async def _refund_credits_and_revert_flag(self, *, saved: SavedParlay, user: User, credits: int) -> None:
        try:
            user_uuid = uuid.UUID(str(user.id))
        except Exception as exc:
            raise ValueError("Invalid user id") from exc

        try:
            await self._db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(credit_balance=User.credit_balance + int(credits))
            )
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            logger.exception("Credit refund failed (user=%s saved_parlay=%s)", user.id, saved.id)
        saved.inscription_credits_consumed = False
        self._db.add(saved)
        await self._db.commit()
        await self._db.refresh(saved)


