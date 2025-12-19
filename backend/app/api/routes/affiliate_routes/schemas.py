"""
Pydantic request/response schemas for affiliate routes.

Kept in a dedicated module so route files stay focused and small.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, validator


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
    settlement_breakdown: dict


class AffiliatePublicResponse(BaseModel):
    """Public affiliate info (for referral landing)"""

    referral_code: str
    tier: str
    tier_name: str
    lemonsqueezy_affiliate_code: Optional[str] = None


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
            cleaned = "".join(filter(str.isdigit, v))
            if len(cleaned) != 9:
                raise ValueError("SSN must be 9 digits")
        elif tax_id_type == "ein":
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


