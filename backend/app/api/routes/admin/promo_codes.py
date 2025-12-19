"""Admin promo code management routes."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.promo_code import PromoCode, PromoRewardType
from app.models.user import User
from app.schemas.promo_codes import (
    PromoCodeBulkCreateRequest,
    PromoCodeCreateRequest,
    PromoCodeListResponse,
    PromoCodeResponse,
)
from app.services.promo_codes import PromoCodeService

from .auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_response(promo: PromoCode) -> PromoCodeResponse:
    return PromoCodeResponse(
        id=str(promo.id),
        code=promo.code,
        reward_type=PromoRewardType(promo.reward_type),
        expires_at=promo.expires_at.isoformat(),
        max_uses_total=int(promo.max_uses_total),
        redeemed_count=int(promo.redeemed_count),
        is_active=bool(promo.is_active),
        deactivated_at=promo.deactivated_at.isoformat() if promo.deactivated_at else None,
        created_at=promo.created_at.isoformat() if promo.created_at else "",
    )


@router.post("", response_model=PromoCodeResponse)
async def create_promo_code(
    payload: PromoCodeCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = PromoCodeService(db)
    try:
        promo = await service.create_code(
            reward_type=payload.reward_type,
            expires_at=payload.expires_at,
            max_uses_total=payload.max_uses_total,
            created_by_user_id=str(admin.id),
            code=payload.code,
            notes=payload.notes,
        )
        return _to_response(promo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk", response_model=list[PromoCodeResponse])
async def bulk_create_promo_codes(
    payload: PromoCodeBulkCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = PromoCodeService(db)
    try:
        promos = await service.bulk_create_codes(
            reward_type=payload.reward_type,
            expires_at=payload.expires_at,
            count=payload.count,
            max_uses_total=payload.max_uses_total,
            created_by_user_id=str(admin.id),
            notes=payload.notes,
        )
        return [_to_response(p) for p in promos]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=PromoCodeListResponse)
async def list_promo_codes(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by code"),
    reward_type: Optional[PromoRewardType] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = PromoCodeService(db)
    promos, total = await service.list_codes(
        page=page,
        page_size=page_size,
        search=search,
        reward_type=reward_type,
        is_active=is_active,
    )
    return PromoCodeListResponse(
        codes=[_to_response(p) for p in promos],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{promo_code_id}/deactivate", response_model=PromoCodeResponse)
async def deactivate_promo_code(
    promo_code_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = PromoCodeService(db)
    try:
        promo = await service.deactivate(promo_code_id=promo_code_id)
        logger.info("Admin %s deactivated promo_code_id=%s", admin.id, promo_code_id)
        return _to_response(promo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


