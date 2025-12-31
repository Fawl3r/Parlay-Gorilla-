"""User stats service.

This service powers `/api/users/me/stats` with usage + leaderboard placement data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Any, Dict, Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.parlay import Parlay
from app.models.saved_parlay import InscriptionStatus, SavedParlay, SavedParlayType
from app.models.saved_parlay_results import SavedParlayResult
from app.models.user import User
from app.services.premium_usage_service import PremiumUsageService
from app.services.subscription_service import SubscriptionService
from app.utils.datetime_utils import coerce_utc


@dataclass(frozen=True)
class LeaderboardPlacement:
    rank: Optional[int]
    value: int

    def to_dict(self) -> dict:
        return {"rank": self.rank, "value": int(self.value)}


class UserStatsService:
    """Compute usage stats and leaderboard placements for a user."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._premium_usage = PremiumUsageService(db)
        self._subscriptions = SubscriptionService(db)

    async def get_user_stats(self, user: User) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        cutoff_30d = now - timedelta(days=30)
        cutoff_7d = now - timedelta(days=7)

        access = await self._subscriptions.get_user_access_level(str(user.id))
        is_premium = access.tier == "premium"

        ai_lifetime = await self._count_ai_parlays(user, cutoff=None)
        ai_30d = await self._count_ai_parlays(user, cutoff=cutoff_30d)
        ai_week = await self._count_ai_parlays(user, cutoff=cutoff_7d)
        most_active_day = await self._most_active_ai_day_of_week(user, cutoff=cutoff_7d)

        custom_saved_lifetime = await self._count_custom_saved_parlays(user, cutoff=None)
        custom_saved_30d = await self._count_custom_saved_parlays(user, cutoff=cutoff_30d)

        # Rolling period snapshots (only meaningful for premium; keep safe defaults otherwise).
        ai_period_used = 0
        ai_period_limit = 0
        ai_period_remaining = 0
        ai_period_start = None
        ai_period_end = None

        custom_period_used = 0
        custom_period_limit = 0
        custom_period_remaining = 0
        custom_period_start = None
        custom_period_end = None

        ins_period_used = 0
        ins_period_limit = 0
        ins_period_remaining = 0
        ins_period_start = None
        ins_period_end = None

        if is_premium:
            ai_snap = await self._premium_usage.get_premium_ai_snapshot(user)
            ai_period_used = int(ai_snap.used)
            ai_period_limit = int(ai_snap.limit)
            ai_period_remaining = int(ai_snap.remaining)
            ai_period_start = ai_snap.period_start.isoformat() if ai_snap.period_start else None
            ai_period_end = ai_snap.period_end.isoformat() if ai_snap.period_end else None

            custom_snap = await self._premium_usage.get_custom_builder_snapshot(user)
            custom_period_used = int(custom_snap.used)
            custom_period_limit = int(custom_snap.limit)
            custom_period_remaining = int(custom_snap.remaining)
            custom_period_start = custom_snap.period_start.isoformat() if custom_snap.period_start else None
            custom_period_end = custom_snap.period_end.isoformat() if custom_snap.period_end else None

            ins_snap = await self._premium_usage.get_inscriptions_snapshot(user)
            ins_period_used = int(ins_snap.used)
            ins_period_limit = int(ins_snap.limit)
            ins_period_remaining = int(ins_snap.remaining)
            ins_period_start = ins_snap.period_start.isoformat() if ins_snap.period_start else None
            ins_period_end = ins_snap.period_end.isoformat() if ins_snap.period_end else None

        custom_share_percent = self._compute_percent_share(
            part=int(custom_period_used or 0), whole=int(ai_period_used or 0) + int(custom_period_used or 0)
        )

        inscriptions_consumed_lifetime = await self._count_inscriptions_consumed(user, cutoff=None)
        credits_spent_lifetime = await self._count_inscription_credits_spent(user, cutoff=None)
        inscription_cost_credits = int(getattr(settings, "credits_cost_inscription", 1) or 1)

        verified_wins_lifetime = await self._count_verified_wins(user, cutoff=None)
        verified_wins_30d = await self._count_verified_wins(user, cutoff=cutoff_30d)

        # Leaderboard placements (respect user visibility: hidden users have no rank).
        visibility = str(getattr(user, "leaderboard_visibility", "public") or "public").strip().lower()
        verified_rank = None
        ai_rank_30d = None
        ai_rank_all_time = None

        if visibility != "hidden":
            verified_rank = await self._rank_verified_winners(user)
            ai_rank_30d = await self._rank_ai_usage(user, cutoff=cutoff_30d)
            ai_rank_all_time = await self._rank_ai_usage(user, cutoff=None)

        return {
            "ai_parlays": {
                "lifetime": int(ai_lifetime),
                "last_30_days": int(ai_30d),
                "period_used": int(ai_period_used),
                "period_limit": int(ai_period_limit),
                "period_remaining": int(ai_period_remaining),
                "period_start": ai_period_start,
                "period_end": ai_period_end,
            },
            "usage_breakdown": {
                "weekly_activity": {
                    "ai_parlays_this_week": int(ai_week),
                    "most_active_day": most_active_day,
                },
                "custom_ai_behavior": {
                    "custom_ai_share_percent": int(custom_share_percent),
                    "verified_on_chain_this_period": int(ins_period_used),
                },
            },
            "custom_ai_parlays": {
                # Lifetime: saved custom parlays (best available durable proxy).
                "saved_lifetime": int(custom_saved_lifetime),
                "saved_last_30_days": int(custom_saved_30d),
                # Period: premium custom builder rolling usage.
                "period_used": int(custom_period_used),
                "period_limit": int(custom_period_limit),
                "period_remaining": int(custom_period_remaining),
                "period_start": custom_period_start,
                "period_end": custom_period_end,
            },
            "inscriptions": {
                "consumed_lifetime": int(inscriptions_consumed_lifetime),
                "period_used": int(ins_period_used),
                "period_limit": int(ins_period_limit),
                "period_remaining": int(ins_period_remaining),
                "period_start": ins_period_start,
                "period_end": ins_period_end,
                "inscription_cost_credits": int(inscription_cost_credits),
                "credits_spent_lifetime": int(credits_spent_lifetime),
            },
            "verified_wins": {
                "lifetime": int(verified_wins_lifetime),
                "last_30_days": int(verified_wins_30d),
            },
            "leaderboards": {
                "verified_winners": {"rank": verified_rank},
                "ai_usage_30d": {"rank": ai_rank_30d},
                "ai_usage_all_time": {"rank": ai_rank_all_time},
            },
        }

    @staticmethod
    def _compute_percent_share(*, part: int, whole: int) -> int:
        w = max(0, int(whole or 0))
        if w <= 0:
            return 0
        p = max(0, int(part or 0))
        return int(round((p / w) * 100))

    async def _count_ai_parlays(self, user: User, *, cutoff: Optional[datetime]) -> int:
        q = select(func.count(Parlay.id)).where(Parlay.user_id == user.id)
        if cutoff is not None:
            q = q.where(Parlay.created_at >= cutoff)
        res = await self._db.execute(q)
        return int(res.scalar() or 0)

    async def _most_active_ai_day_of_week(self, user: User, *, cutoff: datetime) -> Optional[str]:
        """
        Most active day-of-week for AI parlay generations in the last 7 days (rolling).

        Note: implemented in Python for DB portability across SQLite/Postgres.
        """
        q = (
            select(Parlay.created_at)
            .where(Parlay.user_id == user.id)
            .where(Parlay.created_at >= cutoff)
        )
        res = await self._db.execute(q)
        created_ats = [dt for dt in res.scalars().all() if dt is not None]
        if not created_ats:
            return None

        # Track count + most recent timestamp per day for stable tie-breaking.
        counts: dict[str, int] = defaultdict(int)
        latest: dict[str, datetime] = {}

        for raw in created_ats:
            try:
                dt = coerce_utc(raw)
            except Exception:
                dt = raw.replace(tzinfo=timezone.utc) if getattr(raw, "tzinfo", None) is None else raw

            day = dt.strftime("%A")
            counts[day] += 1
            prev = latest.get(day)
            if prev is None or dt > prev:
                latest[day] = dt

        # Max by (count, recency, name) for determinism.
        return max(counts.keys(), key=lambda d: (counts[d], latest.get(d, datetime.min.replace(tzinfo=timezone.utc)), d))

    async def _count_custom_saved_parlays(self, user: User, *, cutoff: Optional[datetime]) -> int:
        q = (
            select(func.count(SavedParlay.id))
            .where(SavedParlay.user_id == user.id)
            .where(SavedParlay.parlay_type == SavedParlayType.custom.value)
        )
        if cutoff is not None:
            q = q.where(SavedParlay.created_at >= cutoff)
        res = await self._db.execute(q)
        return int(res.scalar() or 0)

    async def _count_inscriptions_consumed(self, user: User, *, cutoff: Optional[datetime]) -> int:
        q = (
            select(func.count(SavedParlay.id))
            .where(SavedParlay.user_id == user.id)
            .where(SavedParlay.parlay_type == SavedParlayType.custom.value)
            .where(SavedParlay.inscription_quota_consumed.is_(True))
        )
        if cutoff is not None:
            q = q.where(SavedParlay.created_at >= cutoff)
        res = await self._db.execute(q)
        return int(res.scalar() or 0)

    async def _count_inscription_credits_spent(self, user: User, *, cutoff: Optional[datetime]) -> int:
        """Count total credits spent on inscription verifications."""
        q = (
            select(func.count(SavedParlay.id))
            .where(SavedParlay.user_id == user.id)
            .where(SavedParlay.parlay_type == SavedParlayType.custom.value)
            .where(SavedParlay.inscription_credits_consumed.is_(True))
        )
        if cutoff is not None:
            q = q.where(SavedParlay.created_at >= cutoff)
        res = await self._db.execute(q)
        count = int(res.scalar() or 0)
        # Multiply by cost per inscription
        credits_per_inscription = int(getattr(settings, "credits_cost_inscription", 1) or 1)
        return count * credits_per_inscription

    async def _count_verified_wins(self, user: User, *, cutoff: Optional[datetime]) -> int:
        q = (
            select(func.count(SavedParlayResult.id))
            .select_from(SavedParlayResult)
            .join(SavedParlay, SavedParlay.id == SavedParlayResult.saved_parlay_id)
            .where(SavedParlayResult.user_id == user.id)
            .where(SavedParlayResult.parlay_type == SavedParlayType.custom.value)
            .where(SavedParlay.inscription_status == InscriptionStatus.confirmed.value)
            .where(SavedParlayResult.hit.is_(True))
            .where(SavedParlayResult.resolved_at.isnot(None))
        )
        if cutoff is not None:
            q = q.where(SavedParlayResult.resolved_at >= cutoff)
        res = await self._db.execute(q)
        return int(res.scalar() or 0)

    async def _rank_verified_winners(self, user: User) -> Optional[int]:
        wins_expr = func.sum(case((SavedParlayResult.hit.is_(True), 1), else_=0))
        total_expr = func.count(SavedParlayResult.id)
        win_rate_expr = (wins_expr * 1.0) / func.nullif(total_expr, 0)
        last_win_expr = func.max(case((SavedParlayResult.hit.is_(True), SavedParlayResult.resolved_at), else_=None))

        base = (
            select(
                SavedParlayResult.user_id.label("user_id"),
                wins_expr.label("verified_wins"),
                win_rate_expr.label("win_rate"),
                last_win_expr.label("last_win_at"),
            )
            .select_from(SavedParlayResult)
            .join(SavedParlay, SavedParlay.id == SavedParlayResult.saved_parlay_id)
            .join(User, User.id == SavedParlayResult.user_id)
            .where(SavedParlay.parlay_type == SavedParlayType.custom.value)
            .where(SavedParlay.inscription_status == InscriptionStatus.confirmed.value)
            .where(SavedParlayResult.hit.isnot(None))
            .where(SavedParlayResult.resolved_at.isnot(None))
            .where(User.leaderboard_visibility != "hidden")
            .group_by(SavedParlayResult.user_id)
            .having(wins_expr > 0)
        )
        sub = base.subquery()
        ranked = (
            select(
                sub.c.user_id,
                func.row_number()
                .over(order_by=[sub.c.verified_wins.desc(), sub.c.win_rate.desc(), sub.c.last_win_at.desc()])
                .label("rank"),
            )
        ).subquery()
        res = await self._db.execute(select(ranked.c.rank).where(ranked.c.user_id == user.id).limit(1))
        rank = res.scalar_one_or_none()
        return int(rank) if rank is not None else None

    async def _rank_ai_usage(self, user: User, *, cutoff: Optional[datetime]) -> Optional[int]:
        q_ai = (
            select(
                Parlay.user_id.label("user_id"),
                func.count(Parlay.id).label("count"),
                func.max(Parlay.created_at).label("last_at"),
            )
            .where(Parlay.user_id.isnot(None))
            .group_by(Parlay.user_id)
        )
        if cutoff is not None:
            q_ai = q_ai.where(Parlay.created_at >= cutoff)

        q_custom = (
            select(
                SavedParlay.user_id.label("user_id"),
                func.count(SavedParlay.id).label("count"),
                func.max(SavedParlay.created_at).label("last_at"),
            )
            .where(SavedParlay.user_id.isnot(None))
            .where(SavedParlay.parlay_type == SavedParlayType.custom.value)
            .group_by(SavedParlay.user_id)
        )
        if cutoff is not None:
            q_custom = q_custom.where(SavedParlay.created_at >= cutoff)

        union = q_ai.union_all(q_custom).subquery()
        agg = (
            select(
                union.c.user_id.label("user_id"),
                func.sum(union.c.count).label("total"),
                func.max(union.c.last_at).label("last_at"),
            )
            .group_by(union.c.user_id)
            .subquery()
        )

        ranked = (
            select(
                agg.c.user_id,
                func.row_number().over(order_by=[agg.c.total.desc(), agg.c.last_at.desc()]).label("rank"),
            )
            .select_from(agg)
            .join(User, User.id == agg.c.user_id)
            .where(User.leaderboard_visibility != "hidden")
        ).subquery()

        res = await self._db.execute(select(ranked.c.rank).where(ranked.c.user_id == user.id).limit(1))
        rank = res.scalar_one_or_none()
        return int(rank) if rank is not None else None


