"""Admin affiliate reporting routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.user import User
from app.api.routes.admin.auth import require_admin
from app.services.admin_affiliate_service import AdminAffiliateService

router = APIRouter()


@router.get("", summary="List affiliates with stats")
async def list_affiliates(
    time_range: str = Query("30d", regex="^(24h|7d|30d|90d)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    search: str | None = Query(None, description="Search email or referral code"),
    sort: str | None = Query(
        "revenue_desc",
        description="Sort by: revenue_desc|revenue_asc|commission_desc|commission_asc|created_desc|created_asc",
    ),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin-only listing of affiliates with aggregated stats over a time window.

    Returns:
    - clicks, referrals, revenue, commission earned/paid/pending
    - conversion rate
    - pagination metadata
    """
    service = AdminAffiliateService(db)
    return await service.list_affiliates(
        time_range=time_range,
        page=page,
        page_size=page_size,
        search=search,
        sort=sort,
    )


