"""Saved parlay verification record orchestration.

Responsibilities:
- Enforce eligibility (custom-only)
- Enforce premium requirement
- Consume included premium verification quota when available
- After included quota is exhausted, allow premium users to pay via credits
- Persist per-(saved_parlay, data_hash) payment flags so retries don't double-charge
- Enqueue the Redis job for the verification worker
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import AccessErrorCode, PaywallException
from app.core.config import settings
from app.models.saved_parlay import SavedParlay, SavedParlayType
from app.models.user import User
from app.models.verification_record import VerificationRecord, VerificationStatus
from app.services.premium_usage_service import PremiumUsageService
from app.services.subscription_service import SubscriptionService
from app.services.verification_records.verification_queue import VerificationQueue

logger = logging.getLogger(__name__)


class SavedParlayVerificationService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def queue(self, *, saved: SavedParlay, user: User) -> VerificationRecord:
        """
        Queue a saved custom parlay for verification.

        Notes:
        - Idempotent for already queued/confirmed records for the current content hash.
        - Retry-safe: quota/credits are charged at most once per (saved_parlay_id, data_hash).
        """
        if str(getattr(saved, "parlay_type", "") or "").strip() != SavedParlayType.custom.value:
            raise ValueError("Verification records are available for Custom parlays only.")

        data_hash = str(getattr(saved, "content_hash", "") or "").strip()
        if not data_hash:
            raise ValueError("Missing parlay hash")

        # If we already have an active record for this exact hash, return it.
        existing_active = await self._find_active_record(saved_parlay_id=str(saved.id), data_hash=data_hash)
        if existing_active is not None:
            return existing_active

        # Premium-gated (matches existing economics).
        subscription_service = SubscriptionService(self._db)
        if not await subscription_service.is_user_premium(str(user.id)):
            raise PaywallException(
                error_code=AccessErrorCode.PREMIUM_REQUIRED,
                message="Verification records are a Premium feature.",
                feature="inscriptions",  # legacy feature key (frontend paywall mapping)
            )

        usage = PremiumUsageService(self._db)

        already_paid = await self._has_consumed_payment(saved_parlay_id=str(saved.id), data_hash=data_hash)

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
                credits_available = int(getattr(user, "credit_balance", 0) or 0)
                if credits_available < credits_required:
                    raise PaywallException(
                        error_code=AccessErrorCode.FREE_LIMIT_REACHED,
                        message=(
                            f"You've used all {snap.limit} included verifications in your current "
                            f"{settings.premium_inscriptions_period_days}-day period. "
                            f"Additional verifications cost {credits_required} {credit_unit} each."
                        ),
                        remaining_today=0,
                        feature="inscriptions",  # legacy feature key (frontend paywall mapping)
                    )
                should_charge_credits = True

        record = VerificationRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            saved_parlay_id=saved.id,
            data_hash=data_hash,
            status=VerificationStatus.queued.value,
            network=str(getattr(settings, "verification_network", "mainnet") or "mainnet"),
            error=None,
            tx_digest=None,
            object_id=None,
            quota_consumed=False,
            credits_consumed=False,
        )

        try:
            if should_charge_credits:
                await self._spend_credits(user=user, credits_required=credits_required)
                record.credits_consumed = True

            # Persist the record before enqueue so we have a durable ID to reference.
            self._db.add(record)
            await self._db.commit()
            await self._db.refresh(record)

            # Enqueue job (Redis) or leave for DB-polling verifier (Pattern A).
            if (getattr(settings, "verification_delivery", "redis") or "redis").strip().lower() != "db":
                await self._enqueue(record=record, saved_parlay_id=str(saved.id))

            if should_consume_quota:
                new_used = await usage.increment_inscriptions_used(user, count=1)
                logger.info(
                    "Verification queued (included quota): user=%s saved_parlay=%s used=%s",
                    getattr(user, "id", "unknown"),
                    str(getattr(saved, "id", "")),
                    int(new_used),
                )
                record.quota_consumed = True
                self._db.add(record)
                await self._db.commit()
                await self._db.refresh(record)

            return record
        except PaywallException:
            raise
        except ValueError:
            raise
        except Exception:
            # If something unexpected happens after we spent credits, try to refund.
            if should_charge_credits:
                try:
                    await self._refund_credits_and_revert_flag(record=record, user=user, credits=credits_required)
                except Exception:
                    logger.exception("Failed to refund credits after verification queue failure (record=%s)", record.id)
            raise

    async def _find_active_record(self, *, saved_parlay_id: str, data_hash: str) -> VerificationRecord | None:
        res = await self._db.execute(
            select(VerificationRecord)
            .where(VerificationRecord.saved_parlay_id == uuid.UUID(str(saved_parlay_id)))
            .where(VerificationRecord.data_hash == str(data_hash))
            .where(VerificationRecord.status.in_([VerificationStatus.queued.value, VerificationStatus.confirmed.value]))
            .order_by(VerificationRecord.created_at.desc())
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def _has_consumed_payment(self, *, saved_parlay_id: str, data_hash: str) -> bool:
        res = await self._db.execute(
            select(VerificationRecord.id)
            .where(VerificationRecord.saved_parlay_id == uuid.UUID(str(saved_parlay_id)))
            .where(VerificationRecord.data_hash == str(data_hash))
            .where(
                or_(
                    VerificationRecord.quota_consumed.is_(True),
                    VerificationRecord.credits_consumed.is_(True),
                )
            )
            .limit(1)
        )
        return res.first() is not None

    async def _enqueue(self, *, record: VerificationRecord, saved_parlay_id: str) -> None:
        queue = VerificationQueue()
        try:
            await queue.enqueue_verification_record(
                verification_record_id=str(record.id),
                saved_parlay_id=saved_parlay_id,
            )
        except Exception as exc:
            record.status = VerificationStatus.failed.value
            record.error = f"Enqueue failed: {exc.__class__.__name__}"
            self._db.add(record)
            await self._db.commit()
            await self._db.refresh(record)
            raise

    async def _spend_credits(self, *, user: User, credits_required: int) -> None:
        try:
            user_uuid = uuid.UUID(str(user.id))
        except Exception as exc:
            raise ValueError("Invalid user id") from exc

        stmt = (
            update(User)
            .where(User.id == user_uuid)
            .where(User.credit_balance >= int(credits_required))
            .values(credit_balance=User.credit_balance - int(credits_required))
        )
        res = await self._db.execute(stmt)
        if getattr(res, "rowcount", 0) != 1:
            await self._db.rollback()
            credit_unit = "credit" if int(credits_required) == 1 else "credits"
            raise PaywallException(
                error_code=AccessErrorCode.FREE_LIMIT_REACHED,
                message=f"Additional verifications cost {credits_required} {credit_unit} each. Buy credits to continue.",
                remaining_today=0,
                feature="inscriptions",  # legacy feature key
            )
        await self._db.commit()

    async def _refund_credits_and_revert_flag(self, *, record: VerificationRecord, user: User, credits: int) -> None:
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
            logger.exception("Credit refund failed (user=%s record=%s)", user.id, record.id)

        record.credits_consumed = False
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)


