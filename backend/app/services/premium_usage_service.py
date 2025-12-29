"""
Premium usage tracking (rolling periods).

This module centralizes "included quota" counters for premium features, modeled as
rolling N-day periods (not calendar months), similar to the existing premium AI
parlay limit.

Why a dedicated service:
- Keeps `subscription_service.py` from becoming a God file
- Provides one place to manage period reset logic and avoid subtle drift
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.utils.datetime_utils import coerce_utc, now_utc

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PeriodUsageSnapshot:
    """A read model for a rolling-period quota."""

    used: int
    limit: int
    remaining: int
    period_start: Optional[datetime]
    period_end: Optional[datetime]

    def to_iso_dict(self) -> dict:
        return {
            "used": int(self.used),
            "limit": int(self.limit),
            "remaining": int(self.remaining),
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }


class PremiumUsageService:
    """
    Manages rolling-period usage counters stored on the `users` table.

    Counters:
    - premium AI parlay usage (already exists)
    - custom builder actions included in premium
    - inscriptions included in premium
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_premium_ai_snapshot(self, user: User) -> PeriodUsageSnapshot:
        await self._ensure_period(
            user,
            start_attr="premium_ai_parlays_period_start",
            used_attr="premium_ai_parlays_used",
            period_days=settings.premium_ai_parlays_period_days,
            label="premium_ai_parlays",
        )
        return self._snapshot(
            user,
            start_attr="premium_ai_parlays_period_start",
            used_attr="premium_ai_parlays_used",
            limit=settings.premium_ai_parlays_per_month,
            period_days=settings.premium_ai_parlays_period_days,
        )

    async def increment_premium_ai_used(self, user: User, *, count: int = 1) -> int:
        n = max(1, int(count or 1))
        await self._ensure_period(
            user,
            start_attr="premium_ai_parlays_period_start",
            used_attr="premium_ai_parlays_used",
            period_days=settings.premium_ai_parlays_period_days,
            label="premium_ai_parlays",
        )
        user.premium_ai_parlays_used = int(getattr(user, "premium_ai_parlays_used", 0) or 0) + n
        await self._db.commit()
        await self._db.refresh(user)
        return int(getattr(user, "premium_ai_parlays_used", 0) or 0)

    async def get_custom_builder_snapshot(self, user: User) -> PeriodUsageSnapshot:
        await self._ensure_period(
            user,
            start_attr="premium_custom_builder_period_start",
            used_attr="premium_custom_builder_used",
            period_days=settings.premium_custom_builder_period_days,
            label="premium_custom_builder",
        )
        return self._snapshot(
            user,
            start_attr="premium_custom_builder_period_start",
            used_attr="premium_custom_builder_used",
            limit=settings.premium_custom_builder_per_month,
            period_days=settings.premium_custom_builder_period_days,
        )

    async def increment_custom_builder_used(self, user: User, *, count: int = 1) -> int:
        n = max(1, int(count or 1))
        await self._ensure_period(
            user,
            start_attr="premium_custom_builder_period_start",
            used_attr="premium_custom_builder_used",
            period_days=settings.premium_custom_builder_period_days,
            label="premium_custom_builder",
        )
        user.premium_custom_builder_used = int(getattr(user, "premium_custom_builder_used", 0) or 0) + n
        await self._db.commit()
        await self._db.refresh(user)
        return int(getattr(user, "premium_custom_builder_used", 0) or 0)

    async def get_inscriptions_snapshot(self, user: User) -> PeriodUsageSnapshot:
        await self._ensure_period(
            user,
            start_attr="premium_inscriptions_period_start",
            used_attr="premium_inscriptions_used",
            period_days=settings.premium_inscriptions_period_days,
            label="premium_inscriptions",
        )
        return self._snapshot(
            user,
            start_attr="premium_inscriptions_period_start",
            used_attr="premium_inscriptions_used",
            limit=settings.premium_inscriptions_per_month,
            period_days=settings.premium_inscriptions_period_days,
        )

    async def increment_inscriptions_used(self, user: User, *, count: int = 1) -> int:
        n = max(1, int(count or 1))
        await self._ensure_period(
            user,
            start_attr="premium_inscriptions_period_start",
            used_attr="premium_inscriptions_used",
            period_days=settings.premium_inscriptions_period_days,
            label="premium_inscriptions",
        )
        user.premium_inscriptions_used = int(getattr(user, "premium_inscriptions_used", 0) or 0) + n
        await self._db.commit()
        await self._db.refresh(user)
        return int(getattr(user, "premium_inscriptions_used", 0) or 0)

    async def _ensure_period(
        self,
        user: User,
        *,
        start_attr: str,
        used_attr: str,
        period_days: int,
        label: str,
    ) -> None:
        """
        Ensure rolling period is initialized and reset if expired.

        Commits only when a reset/initialization occurs.
        """
        days = max(1, int(period_days or 1))
        now = now_utc()

        raw_start = getattr(user, start_attr, None)
        if raw_start is None:
            setattr(user, start_attr, now)
            setattr(user, used_attr, 0)
            await self._db.commit()
            await self._db.refresh(user)
            return

        try:
            start = coerce_utc(raw_start)
        except Exception:
            # Defensive: treat invalid stored timestamp as expired.
            start = now

        end = start + timedelta(days=days)
        if now < end:
            return

        setattr(user, start_attr, now)
        setattr(user, used_attr, 0)
        await self._db.commit()
        await self._db.refresh(user)
        logger.info("Reset %s rolling period for user %s", label, getattr(user, "id", "unknown"))

    def _snapshot(
        self,
        user: User,
        *,
        start_attr: str,
        used_attr: str,
        limit: int,
        period_days: int,
    ) -> PeriodUsageSnapshot:
        lim = max(0, int(limit or 0))
        used = max(0, int(getattr(user, used_attr, 0) or 0))

        start_raw = getattr(user, start_attr, None)
        start = coerce_utc(start_raw) if start_raw else None
        days = max(1, int(period_days or 1))
        end = (start + timedelta(days=days)) if start else None

        remaining = max(0, lim - used) if lim > 0 else 0
        return PeriodUsageSnapshot(
            used=used,
            limit=lim,
            remaining=remaining,
            period_start=start,
            period_end=end,
        )


