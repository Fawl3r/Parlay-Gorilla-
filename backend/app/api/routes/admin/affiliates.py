"""Admin affiliate reporting routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.dependencies import get_db
from app.models.affiliate import Affiliate
from app.models.user import User
from app.api.routes.admin.auth import require_admin
from app.services.admin_affiliate_service import AdminAffiliateService

router = APIRouter()


@router.get("", summary="List affiliates with stats")
async def list_affiliates(
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
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


class UpdateLemonSqueezyAffiliateCodeRequest(BaseModel):
    lemonsqueezy_affiliate_code: str | None = Field(default=None, max_length=50)


@router.patch("/{affiliate_id}/lemonsqueezy-affiliate-code", summary="Update LemonSqueezy affiliate code mapping")
async def update_lemonsqueezy_affiliate_code(
    affiliate_id: str,
    request: UpdateLemonSqueezyAffiliateCodeRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Set/clear the LemonSqueezy affiliate code for this affiliate.

    This enables bridging `?ref=CODE` (our system) -> `?aff=1234` (LemonSqueezy) for card payouts.
    """
    try:
        affiliate_uuid = uuid.UUID(affiliate_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid affiliate_id")

    affiliate = (await db.execute(select(Affiliate).where(Affiliate.id == affiliate_uuid))).scalar_one_or_none()
    if not affiliate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Affiliate not found")

    value = (request.lemonsqueezy_affiliate_code or "").strip() or None
    affiliate.lemonsqueezy_affiliate_code = value
    await db.commit()

    return {
        "success": True,
        "affiliate_id": str(affiliate.id),
        "lemonsqueezy_affiliate_code": affiliate.lemonsqueezy_affiliate_code,
    }


