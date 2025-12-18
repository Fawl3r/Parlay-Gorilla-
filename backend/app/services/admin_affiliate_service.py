"""Admin affiliate aggregation service."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate import Affiliate
from app.models.affiliate_click import AffiliateClick
from app.models.affiliate_referral import AffiliateReferral
from app.models.affiliate_commission import AffiliateCommission, CommissionStatus
from app.models.user import User


TimeRange = Tuple[datetime, datetime]


def parse_time_range(range_str: str) -> TimeRange:
    """Convert shorthand time range (e.g., 24h, 7d) to a start/end tuple."""
    now = datetime.utcnow()
    ranges = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
    }
    delta = ranges.get(range_str, timedelta(days=30))
    return now - delta, now


class AdminAffiliateService:
    """Aggregations for admin affiliate reporting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_affiliates(
        self,
        time_range: str,
        page: int = 1,
        page_size: int = 25,
        search: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_date, end_date = parse_time_range(time_range)

        # Subqueries for period stats
        clicks_subq = (
            select(func.count(AffiliateClick.id))
            .where(
                and_(
                    AffiliateClick.affiliate_id == Affiliate.id,
                    AffiliateClick.created_at >= start_date,
                    AffiliateClick.created_at <= end_date,
                )
            )
            .correlate(Affiliate)
            .scalar_subquery()
        )

        referrals_subq = (
            select(func.count(AffiliateReferral.id))
            .where(
                and_(
                    AffiliateReferral.affiliate_id == Affiliate.id,
                    AffiliateReferral.created_at >= start_date,
                    AffiliateReferral.created_at <= end_date,
                )
            )
            .correlate(Affiliate)
            .scalar_subquery()
        )

        revenue_subq = (
            select(func.coalesce(func.sum(AffiliateCommission.base_amount), 0))
            .where(
                and_(
                    AffiliateCommission.affiliate_id == Affiliate.id,
                    AffiliateCommission.created_at >= start_date,
                    AffiliateCommission.created_at <= end_date,
                )
            )
            .correlate(Affiliate)
            .scalar_subquery()
        )

        commission_earned_subq = (
            select(func.coalesce(func.sum(AffiliateCommission.amount), 0))
            .where(
                and_(
                    AffiliateCommission.affiliate_id == Affiliate.id,
                    AffiliateCommission.created_at >= start_date,
                    AffiliateCommission.created_at <= end_date,
                )
            )
            .correlate(Affiliate)
            .scalar_subquery()
        )

        commission_paid_subq = (
            select(func.coalesce(func.sum(AffiliateCommission.amount), 0))
            .where(
                and_(
                    AffiliateCommission.affiliate_id == Affiliate.id,
                    AffiliateCommission.status == CommissionStatus.PAID.value,
                    AffiliateCommission.paid_at.isnot(None),
                    AffiliateCommission.paid_at >= start_date,
                    AffiliateCommission.paid_at <= end_date,
                )
            )
            .correlate(Affiliate)
            .scalar_subquery()
        )

        base_query = (
            select(
                Affiliate,
                User.email.label("email"),
                User.username.label("username"),
                clicks_subq.label("clicks"),
                referrals_subq.label("referrals"),
                revenue_subq.label("revenue"),
                commission_earned_subq.label("commission_earned"),
                commission_paid_subq.label("commission_paid"),
            )
            .join(User, User.id == Affiliate.user_id)
        )

        if search:
            like = f"%{search.lower()}%"
            base_query = base_query.where(
                or_(
                    func.lower(User.email).like(like),
                    func.lower(Affiliate.referral_code).like(like),
                )
            )

        # Sorting options
        sort_map = {
            "revenue_desc": revenue_subq.desc(),
            "revenue_asc": revenue_subq.asc(),
            "commission_desc": commission_earned_subq.desc(),
            "commission_asc": commission_earned_subq.asc(),
            "created_desc": Affiliate.created_at.desc(),
            "created_asc": Affiliate.created_at.asc(),
        }
        order_clause = sort_map.get(sort or "", revenue_subq.desc())
        base_query = base_query.order_by(order_clause)

        # Total count without pagination
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        paged_query = base_query.offset(offset).limit(page_size)
        rows = (await self.db.execute(paged_query)).all()

        items: List[Dict[str, Any]] = []
        for row in rows:
            affiliate: Affiliate = row.Affiliate
            clicks = int(row.clicks or 0)
            referrals = int(row.referrals or 0)
            revenue = float(row.revenue or 0)
            commission_earned = float(row.commission_earned or 0)
            commission_paid = float(row.commission_paid or 0)
            pending_commission = commission_earned - commission_paid
            conversion_rate = (
                (referrals / clicks) * 100.0 if clicks > 0 else 0.0
            )

            items.append(
                {
                    "id": str(affiliate.id),
                    "user_id": str(affiliate.user_id),
                    "email": row.email,
                    "username": row.username,
                    "referral_code": affiliate.referral_code,
                    "tier": affiliate.tier,
                    "created_at": affiliate.created_at.isoformat()
                    if affiliate.created_at
                    else None,
                    "is_active": affiliate.is_active,
                    "stats": {
                        "clicks": clicks,
                        "referrals": referrals,
                        "conversion_rate": conversion_rate,
                        "revenue": revenue,
                        "commission_earned": commission_earned,
                        "commission_paid": commission_paid,
                        "pending_commission": pending_commission,
                    },
                }
            )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
            "time_range": time_range,
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }


