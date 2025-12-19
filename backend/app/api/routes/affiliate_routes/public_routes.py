"""Public affiliate routes (no auth required)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.billing_config import AFFILIATE_TIERS, get_all_affiliate_tiers
from app.core.dependencies import get_db
from app.services.affiliate_service import AffiliateService

from .schemas import AffiliatePublicResponse, RecordClickRequest, RecordClickResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/affiliates/public/{referral_code}", response_model=AffiliatePublicResponse)
async def get_affiliate_public_info(
    referral_code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get public affiliate info by referral code.

    Used on landing pages to verify and display affiliate info.
    """
    service = AffiliateService(db)
    affiliate = await service.get_affiliate_by_code(referral_code)

    if not affiliate or not affiliate.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Affiliate not found",
        )

    tier_config = AFFILIATE_TIERS.get(affiliate.tier)
    tier_name = tier_config.name if tier_config else affiliate.tier.title()

    return AffiliatePublicResponse(
        referral_code=affiliate.referral_code,
        tier=affiliate.tier,
        tier_name=tier_name,
        lemonsqueezy_affiliate_code=getattr(affiliate, "lemonsqueezy_affiliate_code", None),
    )


@router.post("/affiliates/click", response_model=RecordClickResponse)
async def record_affiliate_click(
    request: RecordClickRequest,
    req: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Record a click on an affiliate referral link.

    This should be called when a user lands on the site with a referral code.
    Returns a click_id that should be stored in a cookie for attribution.
    """
    service = AffiliateService(db)

    ip_address = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")
    referer_url = req.headers.get("referer")

    click = await service.record_click(
        referral_code=request.referral_code,
        ip_address=ip_address,
        user_agent=user_agent,
        referer_url=referer_url,
        landing_page=request.landing_page,
        utm_source=request.utm_source,
        utm_medium=request.utm_medium,
        utm_campaign=request.utm_campaign,
    )

    if click:
        # Set cookie for attribution
        response.set_cookie(
            key="pg_affiliate_ref",
            value=request.referral_code,
            max_age=30 * 24 * 60 * 60,  # 30 days
            httponly=True,
            samesite="lax",
        )
        response.set_cookie(
            key="pg_affiliate_click",
            value=str(click.id),
            max_age=30 * 24 * 60 * 60,  # 30 days
            httponly=True,
            samesite="lax",
        )

        return RecordClickResponse(
            success=True,
            click_id=str(click.id),
            affiliate_code=request.referral_code,
        )

    return RecordClickResponse(success=False)


@router.get("/affiliates/tiers")
async def get_affiliate_tiers():
    """
    Get all affiliate tier information.

    Public endpoint for displaying tier benefits on affiliate landing page.
    """
    return {"tiers": get_all_affiliate_tiers()}


@router.get("/affiliates/leaderboard")
async def get_affiliate_leaderboard(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Get top affiliates leaderboard.

    Public endpoint showing top affiliates by referred revenue.
    """
    service = AffiliateService(db)
    leaderboard = await service.get_leaderboard(limit=limit)
    return {"leaderboard": leaderboard}


