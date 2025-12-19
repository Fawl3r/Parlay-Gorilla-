"""Promo code redemption routes (user-facing)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.promo_codes import PromoCodeRedeemRequest, PromoCodeRedeemResponse
from app.services.promo_codes import PromoCodeService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/promo-codes/redeem", response_model=PromoCodeRedeemResponse)
async def redeem_promo_code(
    request: Request,
    payload: PromoCodeRedeemRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Redeem a promo code for the authenticated user.

    Rewards:
    - premium_month: adds 30 days of premium access (stackable)
    - credits_3: adds 3 credits
    """
    service = PromoCodeService(db)
    try:
        result = await service.redeem(
            user=user,
            code=payload.code,
            user_agent=request.headers.get("user-agent"),
            ip_address=getattr(getattr(request, "client", None), "host", None),
        )
        return PromoCodeRedeemResponse(
            success=True,
            reward_type=result.reward_type,
            message=result.message,
            credits_added=result.credits_added,
            new_credit_balance=result.new_credit_balance,
            premium_until=result.premium_until.isoformat() if result.premium_until else None,
        )
    except ValueError as e:
        msg = str(e) or "Invalid promo code"
        status_code = status.HTTP_400_BAD_REQUEST
        if "not found" in msg.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "already redeemed" in msg.lower():
            status_code = status.HTTP_409_CONFLICT
        elif "expired" in msg.lower():
            status_code = status.HTTP_410_GONE
        elif "no remaining uses" in msg.lower():
            status_code = status.HTTP_410_GONE

        logger.info("Promo redeem rejected user=%s code=%s reason=%s", user.id, payload.code, msg)
        raise HTTPException(status_code=status_code, detail=msg)


