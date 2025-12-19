"""Authenticated affiliate routes (/affiliates/me/*)."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.affiliate_service import AffiliateService

from .schemas import AffiliateResponse, AffiliateStatsResponse, CreateAffiliateRequest, UpdatePayoutInfoRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/affiliates/register", response_model=AffiliateResponse)
async def register_as_affiliate(
    request: CreateAffiliateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Register current user as an affiliate.

    Creates an affiliate account with a unique referral code.
    """
    service = AffiliateService(db)

    existing = await service.get_affiliate_by_user_id(str(user.id))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already registered as an affiliate",
        )

    affiliate = await service.create_affiliate(str(user.id))

    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create affiliate account",
        )

    # Update payout info if provided
    if request.payout_email:
        await service.update_payout_info(
            str(affiliate.id),
            request.payout_email,
            request.payout_method or "paypal",
        )
        await db.refresh(affiliate)

    return AffiliateResponse(**affiliate.to_dict())


@router.get("/affiliates/me", response_model=AffiliateResponse)
async def get_my_affiliate_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's affiliate account.

    Returns 404 if user is not an affiliate.
    """
    service = AffiliateService(db)
    affiliate = await service.get_affiliate_by_user_id(str(user.id))

    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered as an affiliate",
        )

    # Keep stored tier + commission rates synced to current config so the dashboard reflects
    # the latest tier definitions immediately (not only after the next commission event).
    affiliate.recalculate_tier()
    if db.is_modified(affiliate):
        await db.commit()
        await db.refresh(affiliate)

    return AffiliateResponse(**affiliate.to_dict())


@router.get("/affiliates/me/stats", response_model=AffiliateStatsResponse)
async def get_my_affiliate_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed statistics for current user's affiliate account."""
    service = AffiliateService(db)
    affiliate = await service.get_affiliate_by_user_id(str(user.id))

    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered as an affiliate",
        )

    stats = await service.get_affiliate_stats(str(affiliate.id))
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch affiliate stats",
        )

    return AffiliateStatsResponse(**stats.to_dict())


@router.get("/affiliates/me/referrals")
async def get_my_referrals(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of users referred by current affiliate."""
    service = AffiliateService(db)
    affiliate = await service.get_affiliate_by_user_id(str(user.id))

    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered as an affiliate",
        )

    referrals = await service.get_affiliate_referrals(
        str(affiliate.id),
        limit=limit,
        offset=offset,
    )

    return {"referrals": referrals, "total": int(affiliate.total_referrals)}


@router.get("/affiliates/me/commissions")
async def get_my_commissions(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get commission history for current affiliate.

    Optional filter by status: pending, ready, paid, cancelled
    """
    service = AffiliateService(db)
    affiliate = await service.get_affiliate_by_user_id(str(user.id))

    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered as an affiliate",
        )

    commissions = await service.get_affiliate_commissions(
        str(affiliate.id),
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return {"commissions": [c.to_dict() for c in commissions]}


@router.put("/affiliates/me/payout", response_model=AffiliateResponse)
async def update_my_payout_info(
    request: UpdatePayoutInfoRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update payout information for current affiliate."""
    service = AffiliateService(db)
    affiliate = await service.get_affiliate_by_user_id(str(user.id))

    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered as an affiliate",
        )

    success = await service.update_payout_info(
        str(affiliate.id),
        request.payout_email,
        request.payout_method,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update payout information",
        )

    affiliate = await service.get_affiliate_by_id(str(affiliate.id))
    return AffiliateResponse(**affiliate.to_dict())


