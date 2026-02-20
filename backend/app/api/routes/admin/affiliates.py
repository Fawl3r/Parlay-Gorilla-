"""Admin affiliate reporting routes. Never returns 500."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, ProgrammingError
import uuid

from app.core.dependencies import get_db
from app.models.affiliate import Affiliate
from app.models.user import User
from app.api.routes.admin.auth import require_admin
from app.services.admin_affiliate_service import AdminAffiliateService

logger = logging.getLogger(__name__)
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
    Returns safe empty on DB/table errors.
    """
    try:
        service = AdminAffiliateService(db)
        out = await service.list_affiliates(
            time_range=time_range,
            page=page,
            page_size=page_size,
            search=search,
            sort=sort,
        )
        logger.info("admin.endpoint.success", extra={"endpoint": "affiliates.list"})
        return out
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "affiliates.list", "error": str(e)}, exc_info=True)
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}


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

    try:
        affiliate = (await db.execute(select(Affiliate).where(Affiliate.id == affiliate_uuid))).scalar_one_or_none()
        if not affiliate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Affiliate not found")
        value = (request.lemonsqueezy_affiliate_code or "").strip() or None
        affiliate.lemonsqueezy_affiliate_code = value
        await db.commit()
        logger.info("admin.endpoint.success", extra={"endpoint": "affiliates.update-lemonsqueezy"})
        return {"success": True, "affiliate_id": str(affiliate.id), "lemonsqueezy_affiliate_code": affiliate.lemonsqueezy_affiliate_code}
    except HTTPException:
        raise
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "affiliates.update-lemonsqueezy", "error": str(e)}, exc_info=True)
        return {"success": False, "affiliate_id": affiliate_id, "lemonsqueezy_affiliate_code": None}


