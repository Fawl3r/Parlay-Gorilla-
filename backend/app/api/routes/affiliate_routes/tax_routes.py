"""Affiliate tax form routes (authenticated)."""

from __future__ import annotations

from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.affiliate_service import AffiliateService

from .schemas import TaxFormResponse, W8BENTaxFormRequest, W9TaxFormRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/affiliates/me/tax-status", response_model=TaxFormResponse)
async def get_tax_form_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tax form status for the current affiliate.

    Returns whether a tax form is required, submitted, or verified.
    """
    service = AffiliateService(db)
    affiliate = await service.get_affiliate_by_user_id(str(user.id))

    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered as an affiliate",
        )

    return TaxFormResponse(
        form_type=affiliate.tax_form_type,
        form_status=affiliate.tax_form_status,
        requires_form=affiliate.requires_tax_form,
        form_complete=affiliate.tax_form_complete,
        submitted_at=affiliate.tax_form_submitted_at.isoformat() if affiliate.tax_form_submitted_at else None,
        verified_at=affiliate.tax_form_verified_at.isoformat() if affiliate.tax_form_verified_at else None,
        threshold=float(affiliate.tax_form_required_threshold),
        earnings=float(affiliate.total_commission_earned),
        masked_tax_id=affiliate.mask_tax_id() if affiliate.tax_id_number else None,
    )


@router.post("/affiliates/me/tax-form/w9")
async def submit_w9_tax_form(
    form_data: W9TaxFormRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit W-9 tax form for US affiliates.

    Required for affiliates earning $600+ per year in the US.
    """
    service = AffiliateService(db)
    affiliate = await service.get_affiliate_by_user_id(str(user.id))

    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered as an affiliate",
        )

    ip_address = request.client.host if request.client else None

    affiliate.tax_form_type = "w9"
    affiliate.legal_name = form_data.legal_name
    affiliate.business_name = form_data.business_name
    affiliate.tax_classification = form_data.tax_classification
    affiliate.tax_address_street = form_data.address_street
    affiliate.tax_address_city = form_data.address_city
    affiliate.tax_address_state = form_data.address_state
    affiliate.tax_address_zip = form_data.address_zip
    affiliate.tax_address_country = form_data.address_country
    affiliate.tax_id_number = form_data.tax_id_number
    affiliate.tax_id_type = form_data.tax_id_type
    affiliate.tax_form_status = "submitted"

    now = datetime.now(timezone.utc)
    affiliate.tax_form_submitted_at = now
    affiliate.tax_form_signed_at = now
    affiliate.tax_form_ip_address = ip_address

    try:
        await db.commit()
        await db.refresh(affiliate)
        logger.info("W-9 form submitted for affiliate %s", affiliate.id)
        return {
            "success": True,
            "message": "Tax form submitted successfully. It will be reviewed and verified.",
            "status": "submitted",
        }
    except Exception as e:
        await db.rollback()
        logger.error("Error submitting W-9 form: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit tax form",
        )


@router.post("/affiliates/me/tax-form/w8ben")
async def submit_w8ben_tax_form(
    form_data: W8BENTaxFormRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit W-8BEN tax form for international affiliates.

    Required for non-US affiliates to claim tax treaty benefits.
    """
    service = AffiliateService(db)
    affiliate = await service.get_affiliate_by_user_id(str(user.id))

    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered as an affiliate",
        )

    ip_address = request.client.host if request.client else None

    affiliate.tax_form_type = "w8ben"
    affiliate.legal_name = form_data.legal_name
    affiliate.business_name = form_data.business_name
    affiliate.country_of_residence = form_data.country_of_residence
    affiliate.foreign_tax_id = form_data.foreign_tax_id
    affiliate.tax_address_street = form_data.address_street
    affiliate.tax_address_city = form_data.address_city
    affiliate.tax_address_state = form_data.address_state
    affiliate.tax_address_zip = form_data.address_zip
    affiliate.tax_address_country = form_data.address_country
    affiliate.tax_form_status = "submitted"

    now = datetime.now(timezone.utc)
    affiliate.tax_form_submitted_at = now
    affiliate.tax_form_signed_at = now
    affiliate.tax_form_ip_address = ip_address

    try:
        await db.commit()
        await db.refresh(affiliate)
        logger.info("W-8BEN form submitted for affiliate %s", affiliate.id)
        return {
            "success": True,
            "message": "Tax form submitted successfully. It will be reviewed and verified.",
            "status": "submitted",
        }
    except Exception as e:
        await db.rollback()
        logger.error("Error submitting W-8BEN form: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit tax form",
        )


