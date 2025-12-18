"""
Affiliate API routes for the affiliate program.

Handles:
- Affiliate registration and management
- Click tracking
- Dashboard data (stats, referrals, commissions)
- Public affiliate info
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Literal
from datetime import datetime
import logging

from app.core.dependencies import get_db, get_current_user, get_optional_current_user
from app.models.user import User
from app.services.affiliate_service import AffiliateService
from app.core.billing_config import get_all_affiliate_tiers, AFFILIATE_TIERS

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class CreateAffiliateRequest(BaseModel):
    """Request to become an affiliate"""
    payout_email: Optional[str] = None
    payout_method: Optional[str] = "paypal"


class UpdatePayoutInfoRequest(BaseModel):
    """Update payout information"""
    payout_email: EmailStr
    payout_method: str  # paypal, crypto, bank


class AffiliateResponse(BaseModel):
    """Affiliate account response"""
    id: str
    user_id: str
    referral_code: str
    referral_url: str
    tier: str
    commission_rates: dict
    stats: dict
    is_active: bool
    payout_email: Optional[str]
    payout_method: Optional[str]
    created_at: Optional[str]


class AffiliateStatsResponse(BaseModel):
    """Detailed affiliate statistics"""
    total_clicks: int
    total_referrals: int
    total_revenue: float
    total_commission_earned: float
    total_commission_paid: float
    pending_commission: float
    conversion_rate: float
    last_30_days: dict


class AffiliatePublicResponse(BaseModel):
    """Public affiliate info (for referral landing)"""
    referral_code: str
    tier: str
    tier_name: str


class RecordClickRequest(BaseModel):
    """Record a referral click"""
    referral_code: str
    landing_page: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class RecordClickResponse(BaseModel):
    """Response after recording click"""
    success: bool
    click_id: Optional[str] = None
    affiliate_code: Optional[str] = None


# =============================================================================
# TAX FORM SCHEMAS
# =============================================================================

class W9TaxFormRequest(BaseModel):
    """W-9 form data for US affiliates"""
    legal_name: str = Field(..., min_length=1, max_length=255)
    business_name: Optional[str] = Field(None, max_length=255)
    tax_classification: Literal["Individual", "Partnership", "C-Corp", "S-Corp", "LLC", "Other"] = Field(...)
    address_street: str = Field(..., min_length=1, max_length=255)
    address_city: str = Field(..., min_length=1, max_length=100)
    address_state: str = Field(..., min_length=2, max_length=50)
    address_zip: str = Field(..., min_length=5, max_length=20)
    address_country: str = Field(default="US", max_length=100)
    tax_id_number: str = Field(..., min_length=9, max_length=50)  # SSN or EIN
    tax_id_type: Literal["ssn", "ein"] = Field(...)
    
    @validator("tax_id_number")
    def validate_tax_id(cls, v, values):
        """Validate SSN or EIN format"""
        tax_id_type = values.get("tax_id_type")
        if tax_id_type == "ssn":
            # Remove dashes and spaces, should be 9 digits
            cleaned = "".join(filter(str.isdigit, v))
            if len(cleaned) != 9:
                raise ValueError("SSN must be 9 digits")
        elif tax_id_type == "ein":
            # Remove dashes and spaces, should be 9 digits
            cleaned = "".join(filter(str.isdigit, v))
            if len(cleaned) != 9:
                raise ValueError("EIN must be 9 digits")
        return cleaned


class W8BENTaxFormRequest(BaseModel):
    """W-8BEN form data for international affiliates"""
    legal_name: str = Field(..., min_length=1, max_length=255)
    business_name: Optional[str] = Field(None, max_length=255)
    country_of_residence: str = Field(..., min_length=2, max_length=100)
    foreign_tax_id: Optional[str] = Field(None, max_length=50)
    address_street: str = Field(..., min_length=1, max_length=255)
    address_city: str = Field(..., min_length=1, max_length=100)
    address_state: Optional[str] = Field(None, max_length=50)
    address_zip: str = Field(..., min_length=1, max_length=20)
    address_country: str = Field(..., min_length=2, max_length=100)


class TaxFormResponse(BaseModel):
    """Tax form status response"""
    form_type: Optional[str]
    form_status: str
    requires_form: bool
    form_complete: bool
    submitted_at: Optional[str]
    verified_at: Optional[str]
    threshold: float
    earnings: float
    masked_tax_id: Optional[str] = None


# =============================================================================
# PUBLIC ROUTES (No auth required)
# =============================================================================

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
            detail="Affiliate not found"
        )
    
    tier_config = AFFILIATE_TIERS.get(affiliate.tier)
    tier_name = tier_config.name if tier_config else affiliate.tier.title()
    
    return AffiliatePublicResponse(
        referral_code=affiliate.referral_code,
        tier=affiliate.tier,
        tier_name=tier_name,
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
    
    # Get request info
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
    return {
        "tiers": get_all_affiliate_tiers(),
    }


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
    
    return {
        "leaderboard": leaderboard,
    }


# =============================================================================
# AUTHENTICATED ROUTES
# =============================================================================

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
    
    # Check if already an affiliate
    existing = await service.get_affiliate_by_user_id(str(user.id))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already registered as an affiliate"
        )
    
    affiliate = await service.create_affiliate(str(user.id))
    
    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create affiliate account"
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
            detail="You are not registered as an affiliate"
        )
    
    return AffiliateResponse(**affiliate.to_dict())


@router.get("/affiliates/me/stats", response_model=AffiliateStatsResponse)
async def get_my_affiliate_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed statistics for current user's affiliate account.
    """
    service = AffiliateService(db)
    affiliate = await service.get_affiliate_by_user_id(str(user.id))
    
    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered as an affiliate"
        )
    
    stats = await service.get_affiliate_stats(str(affiliate.id))
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch affiliate stats"
        )
    
    return AffiliateStatsResponse(**stats.to_dict())


@router.get("/affiliates/me/referrals")
async def get_my_referrals(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of users referred by current affiliate.
    """
    service = AffiliateService(db)
    affiliate = await service.get_affiliate_by_user_id(str(user.id))
    
    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered as an affiliate"
        )
    
    referrals = await service.get_affiliate_referrals(
        str(affiliate.id),
        limit=limit,
        offset=offset,
    )
    
    return {
        "referrals": referrals,
        "total": int(affiliate.total_referrals),
    }


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
            detail="You are not registered as an affiliate"
        )
    
    commissions = await service.get_affiliate_commissions(
        str(affiliate.id),
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    
    return {
        "commissions": [c.to_dict() for c in commissions],
    }


@router.put("/affiliates/me/payout", response_model=AffiliateResponse)
async def update_my_payout_info(
    request: UpdatePayoutInfoRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update payout information for current affiliate.
    """
    service = AffiliateService(db)
    affiliate = await service.get_affiliate_by_user_id(str(user.id))
    
    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered as an affiliate"
        )
    
    success = await service.update_payout_info(
        str(affiliate.id),
        request.payout_email,
        request.payout_method,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update payout information"
        )
    
    # Refresh and return updated affiliate
    affiliate = await service.get_affiliate_by_id(str(affiliate.id))
    return AffiliateResponse(**affiliate.to_dict())


# =============================================================================
# SIGNUP ATTRIBUTION
# =============================================================================

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
    
    # Check if user was already referred
    if user.referred_by_affiliate_id:
        return {
            "success": False,
            "message": "User already has a referral attribution"
        }
    
    success = await service.attribute_user_to_affiliate(
        user_id=str(user.id),
        referral_code=referral_code,
        click_id=click_id,
    )
    
    if success:
        return {
            "success": True,
            "message": "Successfully attributed to affiliate"
        }
    
    return {
        "success": False,
        "message": "Attribution failed - invalid referral code"
    }


# =============================================================================
# TAX FORM ROUTES
# =============================================================================

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
            detail="You are not registered as an affiliate"
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
            detail="You are not registered as an affiliate"
        )
    
    # Get IP address for signature tracking
    ip_address = request.client.host if request.client else None
    
    # Update affiliate with tax information
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
        
        logger.info(f"W-9 form submitted for affiliate {affiliate.id}")
        
        return {
            "success": True,
            "message": "Tax form submitted successfully. It will be reviewed and verified.",
            "status": "submitted"
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error submitting W-9 form: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit tax form"
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
            detail="You are not registered as an affiliate"
        )
    
    # Get IP address for signature tracking
    ip_address = request.client.host if request.client else None
    
    # Update affiliate with tax information
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
        
        logger.info(f"W-8BEN form submitted for affiliate {affiliate.id}")
        
        return {
            "success": True,
            "message": "Tax form submitted successfully. It will be reviewed and verified.",
            "status": "submitted"
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error submitting W-8BEN form: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit tax form"
        )

