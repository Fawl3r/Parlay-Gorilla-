"""Affiliate attribution route (authenticated)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.affiliate_service import AffiliateService

router = APIRouter()


@router.post("/affiliates/attribute")
async def attribute_signup(
    referral_code: str = Query(...),
    click_id: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Attribute a user signup to an affiliate.

    Called after successful signup when a referral code is present
    (from URL param or cookie).
    """
    service = AffiliateService(db)

    if user.referred_by_affiliate_id:
        return {"success": False, "message": "User already has a referral attribution"}

    success = await service.attribute_user_to_affiliate(
        user_id=str(user.id),
        referral_code=referral_code,
        click_id=click_id,
    )

    if success:
        return {"success": True, "message": "Successfully attributed to affiliate"}

    return {"success": False, "message": "Attribution failed - invalid referral code"}


