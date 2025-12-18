"""
Affiliate stats/reporting service.

Separated from `affiliate_service.py` to keep files small and responsibilities focused.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate import Affiliate
from app.models.affiliate_click import AffiliateClick
from app.models.affiliate_commission import AffiliateCommission
from app.models.affiliate_referral import AffiliateReferral
from app.models.user import User


@dataclass
class AffiliateStats:
    """Statistics for an affiliate."""

    total_clicks: int
    total_referrals: int
    total_revenue: Decimal
    total_commission_earned: Decimal
    total_commission_paid: Decimal
    pending_commission: Decimal
    conversion_rate: float

    # Recent activity
    clicks_last_30_days: int
    referrals_last_30_days: int
    revenue_last_30_days: Decimal

    def to_dict(self) -> dict:
        return {
            "total_clicks": self.total_clicks,
            "total_referrals": self.total_referrals,
            "total_revenue": float(self.total_revenue),
            "total_commission_earned": float(self.total_commission_earned),
            "total_commission_paid": float(self.total_commission_paid),
            "pending_commission": float(self.pending_commission),
            "conversion_rate": self.conversion_rate,
            "last_30_days": {
                "clicks": self.clicks_last_30_days,
                "referrals": self.referrals_last_30_days,
                "revenue": float(self.revenue_last_30_days),
            },
        }


class AffiliateStatsService:
    """Reporting utilities for affiliates (stats, referrals list, leaderboard)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_affiliate_stats(self, affiliate_id: str) -> Optional[AffiliateStats]:
        """Get detailed statistics for an affiliate."""
        affiliate = await self._get_affiliate_by_id(affiliate_id)
        if not affiliate:
            return None

        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        clicks_30d = (
            await self.db.execute(
                select(func.count(AffiliateClick.id)).where(
                    and_(
                        AffiliateClick.affiliate_id == affiliate.id,
                        AffiliateClick.created_at >= thirty_days_ago,
                    )
                )
            )
        ).scalar() or 0

        referrals_30d = (
            await self.db.execute(
                select(func.count(AffiliateReferral.id)).where(
                    and_(
                        AffiliateReferral.affiliate_id == affiliate.id,
                        AffiliateReferral.created_at >= thirty_days_ago,
                    )
                )
            )
        ).scalar() or 0

        revenue_30d = (
            await self.db.execute(
                select(func.sum(AffiliateCommission.base_amount)).where(
                    and_(
                        AffiliateCommission.affiliate_id == affiliate.id,
                        AffiliateCommission.created_at >= thirty_days_ago,
                    )
                )
            )
        ).scalar() or Decimal("0")

        total_clicks = int(affiliate.total_clicks)
        total_referrals = int(affiliate.total_referrals)
        conversion_rate = (
            (total_referrals / total_clicks * 100) if total_clicks > 0 else 0.0
        )

        return AffiliateStats(
            total_clicks=total_clicks,
            total_referrals=total_referrals,
            total_revenue=affiliate.total_referred_revenue,
            total_commission_earned=affiliate.total_commission_earned,
            total_commission_paid=affiliate.total_commission_paid,
            pending_commission=affiliate.pending_commission,
            conversion_rate=round(conversion_rate, 2),
            clicks_last_30_days=clicks_30d,
            referrals_last_30_days=referrals_30d,
            revenue_last_30_days=revenue_30d,
        )

    async def get_affiliate_referrals(
        self,
        affiliate_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get list of referrals for an affiliate with user info."""
        try:
            aff_uuid = uuid.UUID(affiliate_id)
        except ValueError:
            return []

        result = await self.db.execute(
            select(AffiliateReferral, User)
            .join(User, AffiliateReferral.referred_user_id == User.id)
            .where(AffiliateReferral.affiliate_id == aff_uuid)
            .order_by(desc(AffiliateReferral.created_at))
            .limit(limit)
            .offset(offset)
        )

        referrals: List[Dict[str, Any]] = []
        for referral, user in result.all():
            # Defensive masking; user.email should always contain '@' but we guard anyway.
            email = user.email or ""
            if "@" in email and len(email) >= 3:
                masked_email = email[:3] + "***" + email[email.index("@") :]
            else:
                masked_email = "***"

            referrals.append(
                {
                    "id": str(referral.id),
                    "user_id": str(user.id),
                    "email": masked_email,
                    "username": user.username or user.display_name,
                    "created_at": referral.created_at.isoformat()
                    if referral.created_at
                    else None,
                    "has_subscription": user.has_active_subscription,
                }
            )

        return referrals

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top affiliates by total referred revenue."""
        result = await self.db.execute(
            select(Affiliate, User)
            .join(User, Affiliate.user_id == User.id)
            .where(Affiliate.is_active.is_(True))
            .order_by(desc(Affiliate.total_referred_revenue))
            .limit(limit)
        )

        leaderboard: List[Dict[str, Any]] = []
        for i, (affiliate, user) in enumerate(result.all(), 1):
            leaderboard.append(
                {
                    "rank": i,
                    "username": user.username or user.display_name or "Anonymous",
                    "tier": affiliate.tier,
                    "total_referrals": int(affiliate.total_referrals),
                    "total_revenue": float(affiliate.total_referred_revenue),
                }
            )

        return leaderboard

    async def _get_affiliate_by_id(self, affiliate_id: str) -> Optional[Affiliate]:
        """Get affiliate by ID (internal helper)."""
        try:
            aff_uuid = uuid.UUID(affiliate_id)
        except ValueError:
            return None

        result = await self.db.execute(select(Affiliate).where(Affiliate.id == aff_uuid))
        return result.scalar_one_or_none()


