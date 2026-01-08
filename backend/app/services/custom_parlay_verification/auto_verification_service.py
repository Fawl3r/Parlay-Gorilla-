from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.model_config import MODEL_VERSION
from app.models.user import User
from app.models.verification_record import VerificationRecord, VerificationStatus
from app.schemas.parlay import CustomParlayLeg, CustomParlayLegAnalysis
from app.services.custom_parlay_verification.fingerprint import (
    CustomParlayFingerprintGenerator,
    CustomParlayFingerprintLeg,
)
from app.services.verification_records.verification_queue import VerificationQueue

logger = logging.getLogger(__name__)


class CustomParlayAutoVerificationService:
    """
    Automatic, server-side verification record creation for Custom AI parlays.

    Design goals:
    - Zero user friction (never fails the analysis request)
    - Abuse-safe + cost-controlled (deterministic fingerprint idempotency)
    - DB-level hard stop (unique constraint on parlay_fingerprint)
    - Retry-safe (idempotent reads + safe enqueue)
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._queue = VerificationQueue()
        self._fingerprints = CustomParlayFingerprintGenerator(
            model_version=MODEL_VERSION,
            window_seconds=int(getattr(settings, "custom_parlay_verification_window_seconds", 600) or 600),
        )

    async def ensure_verification_record(
        self,
        *,
        user: User,
        request_legs: Sequence[CustomParlayLeg],
        analysis_legs: Sequence[CustomParlayLegAnalysis],
        now_utc: Optional[datetime] = None,
    ) -> Optional[VerificationRecord]:
        if not bool(getattr(settings, "enable_custom_parlay_verification", True)):
            return None
        if not bool(getattr(settings, "verification_enabled", True)):
            return None

        if not self._queue.is_available():
            # Keep this silent for end-users; log for operators.
            logger.info("Custom parlay verification skipped (Redis not configured)")
            return None

        now = now_utc or datetime.now(timezone.utc)

        # Optional soft limit (additional to plan/rate limits).
        max_per_hour = int(getattr(settings, "custom_parlay_verification_soft_max_per_hour", 0) or 0)
        if max_per_hour > 0:
            if await self._is_over_soft_limit(user=user, now=now, max_per_hour=max_per_hour):
                logger.warning("Custom parlay verification skipped (soft limit hit) user=%s", getattr(user, "id", ""))
                return None

        fingerprint = self._fingerprint_for_request(
            user=user,
            request_legs=request_legs,
            analysis_legs=analysis_legs,
            now=now,
        )

        existing = await self._find_by_fingerprint(user=user, parlay_fingerprint=fingerprint)
        if existing is not None:
            # Retry path: if failed and no receipt exists, re-enqueue (best-effort).
            if str(getattr(existing, "status", "")).lower() == VerificationStatus.failed.value and not existing.tx_digest:
                await self._enqueue_best_effort(existing)
            return existing

        record = VerificationRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            saved_parlay_id=None,
            parlay_fingerprint=fingerprint,
            data_hash=fingerprint,  # hash-only payload stored/proved
            status=VerificationStatus.queued.value,
            network=str(getattr(settings, "verification_network", "mainnet") or "mainnet"),
            error=None,
            tx_digest=None,
            object_id=None,
            quota_consumed=False,
            credits_consumed=False,
        )

        try:
            self._db.add(record)
            await self._db.commit()
            await self._db.refresh(record)
        except IntegrityError:
            await self._db.rollback()
            existing = await self._find_by_fingerprint(user=user, parlay_fingerprint=fingerprint)
            return existing

        await self._enqueue_best_effort(record)
        return record

    async def _enqueue_best_effort(self, record: VerificationRecord) -> None:
        try:
            await self._queue.enqueue_verification_record(
                verification_record_id=str(record.id),
                saved_parlay_id=str(getattr(record, "saved_parlay_id", "") or ""),
                job_name="verify_custom_parlay",
            )
        except Exception as exc:
            # Mark as failed so the UI can display status; keep request successful.
            record.status = VerificationStatus.failed.value
            record.error = f"Enqueue failed: {exc.__class__.__name__}"
            self._db.add(record)
            try:
                await self._db.commit()
                await self._db.refresh(record)
            except Exception:
                await self._db.rollback()

    def _fingerprint_for_request(
        self,
        *,
        user: User,
        request_legs: Sequence[CustomParlayLeg],
        analysis_legs: Sequence[CustomParlayLegAnalysis],
        now: datetime,
    ) -> str:
        legs = self._build_fingerprint_legs(request_legs=request_legs, analysis_legs=analysis_legs)
        res = self._fingerprints.compute(
            user_id=str(getattr(user, "id", "") or ""),
            legs=legs,
            now_utc=now,
        )
        return str(res.parlay_fingerprint)

    @staticmethod
    def _build_fingerprint_legs(
        *,
        request_legs: Sequence[CustomParlayLeg],
        analysis_legs: Sequence[CustomParlayLegAnalysis],
    ) -> list[CustomParlayFingerprintLeg]:
        by_key: dict[tuple[str, str, str], CustomParlayLegAnalysis] = {}
        for a in analysis_legs or []:
            key = (str(a.game_id), str(a.market_type).lower(), str(a.pick).lower())
            by_key[key] = a

        out: list[CustomParlayFingerprintLeg] = []
        for leg in request_legs or []:
            game_id = str(getattr(leg, "game_id", "") or "")
            market_type = str(getattr(leg, "market_type", "") or "h2h").lower()
            pick = str(getattr(leg, "pick", "") or "").lower()

            odds_snapshot = str(getattr(leg, "odds", "") or "").strip()
            if not odds_snapshot:
                matched = by_key.get((game_id, market_type, pick))
                if matched:
                    odds_snapshot = str(getattr(matched, "odds", "") or "").strip()
            if not odds_snapshot:
                odds_snapshot = "-110"

            out.append(
                CustomParlayFingerprintLeg(
                    matchup_id=game_id,
                    market_type=market_type,
                    pick=pick,
                    point=getattr(leg, "point", None),
                    odds_snapshot=odds_snapshot,
                    market_id=str(getattr(leg, "market_id", "") or "").strip() or None,
                )
            )
        return out

    async def _find_by_fingerprint(self, *, user: User, parlay_fingerprint: str) -> Optional[VerificationRecord]:
        fp = str(parlay_fingerprint or "").strip()
        if not fp:
            return None
        res = await self._db.execute(
            select(VerificationRecord)
            .where(VerificationRecord.user_id == user.id)
            .where(VerificationRecord.parlay_fingerprint == fp)
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def _is_over_soft_limit(self, *, user: User, now: datetime, max_per_hour: int) -> bool:
        cutoff = now - timedelta(hours=1)
        q = (
            select(func.count(VerificationRecord.id))
            .where(VerificationRecord.user_id == user.id)
            .where(VerificationRecord.parlay_fingerprint.is_not(None))
            .where(VerificationRecord.created_at >= cutoff)
        )
        res = await self._db.execute(q)
        count = int(res.scalar() or 0)
        return count >= int(max_per_hour)


