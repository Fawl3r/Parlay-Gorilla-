"""
Admin routes for managing affiliate payouts.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
import logging

from sqlalchemy import select

from app.core.dependencies import get_db
from app.api.routes.admin.auth import require_admin
from app.models.user import User
from app.models.affiliate import Affiliate
from app.models.affiliate_commission import AffiliateCommission, CommissionStatus
from app.models.affiliate_payout import AffiliatePayout, PayoutStatus
from app.services.payout_service import PayoutService
from app.services.affiliate_service import AffiliateService

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class CreatePayoutRequest(BaseModel):
    """Request to create a payout"""
    affiliate_id: str
    commission_ids: List[str]
    payout_method: str  # paypal, crypto, bank
    notes: Optional[str] = None


class ProcessPayoutRequest(BaseModel):
    """Request to process a payout"""
    payout_id: str


class PayoutResponse(BaseModel):
    """Payout response"""
    id: str
    affiliate_id: str
    amount: float
    currency: str
    payout_method: str
    recipient_email: str
    status: str
    provider_payout_id: Optional[str]
    error_message: Optional[str]
    created_at: Optional[str]
    completed_at: Optional[str]


class ReadyCommissionsResponse(BaseModel):
    """Response with ready commissions for an affiliate"""
    affiliate_id: str
    affiliate_email: str
    total_ready_amount: float
    commission_count: int
    commissions: List[dict]


# =============================================================================
# ROUTES
# =============================================================================

@router.get("/ready-commissions")
async def get_ready_commissions(
    affiliate_id: Optional[str] = Query(None),
    min_amount: float = Query(10.0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get all affiliates with ready commissions for payout.
    
    Returns affiliates who have commissions ready to be paid out.
    """
    payout_service = PayoutService(db)
    affiliate_service = AffiliateService(db)
    
    # Get all affiliates or specific affiliate
    if affiliate_id:
        affiliates_result = await db.execute(
            select(Affiliate).where(Affiliate.id == affiliate_id)
        )
        affiliates = [affiliates_result.scalar_one_or_none()]
        affiliates = [a for a in affiliates if a is not None]
    else:
        affiliates_result = await db.execute(
            select(Affiliate).where(Affiliate.is_active == True)
        )
        affiliates = list(affiliates_result.scalars().all())
    
    results = []
    
    for affiliate in affiliates:
        # Get ready commissions
        commissions = await payout_service.get_ready_commissions_for_affiliate(
            str(affiliate.id),
            min_amount=Decimal(str(min_amount))
        )
        
        if commissions:
            total = sum(c.amount for c in commissions)
            
            # Get user email
            user_result = await db.execute(
                select(User).where(User.id == affiliate.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            results.append({
                "affiliate_id": str(affiliate.id),
                "affiliate_email": user.email if user else "N/A",
                "affiliate_code": affiliate.referral_code,
                "total_ready_amount": float(total),
                "commission_count": len(commissions),
                "commissions": [c.to_dict() for c in commissions],
            })
    
    return {
        "ready_affiliates": results,
        "total_affiliates": len(results),
    }


@router.post("/create", response_model=PayoutResponse)
async def create_payout(
    request: CreatePayoutRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Create a new payout for an affiliate.
    
    This creates a payout record but doesn't process it yet.
    Use /process to actually send the payment.
    """
    payout_service = PayoutService(db)
    
    payout = await payout_service.create_payout(
        affiliate_id=request.affiliate_id,
        commission_ids=request.commission_ids,
        payout_method=request.payout_method,
        notes=request.notes,
    )
    
    if not payout:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create payout. Check affiliate and commission IDs.",
        )
    
    await db.commit()
    
    return PayoutResponse(**payout.to_dict())


@router.post("/process", response_model=dict)
async def process_payout(
    request: ProcessPayoutRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Process a payout (send payment via PayPal or crypto).
    
    This actually sends the money to the affiliate.
    """
    payout_service = PayoutService(db)
    
    # Get payout to determine method
    payout_result = await db.execute(
        select(AffiliatePayout).where(AffiliatePayout.id == request.payout_id)
    )
    payout = payout_result.scalar_one_or_none()
    
    if not payout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payout not found",
        )
    
    # Process based on method
    if payout.payout_method == "paypal":
        result = await payout_service.process_paypal_payout(request.payout_id)
    elif payout.payout_method == "crypto":
        result = await payout_service.process_crypto_payout(request.payout_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported payout method: {payout.payout_method}",
        )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to process payout"),
        )
    
    return result


@router.get("", response_model=List[PayoutResponse])
async def list_payouts(
    affiliate_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all payouts with optional filters.
    """
    payout_service = PayoutService(db)
    
    payouts = await payout_service.get_payout_history(
        affiliate_id=affiliate_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    
    return [PayoutResponse(**p.to_dict()) for p in payouts]


@router.get("/summary")
async def get_payout_summary(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get summary statistics of all payouts.
    """
    payout_service = PayoutService(db)
    summary = await payout_service.get_payout_summary()
    
    return summary


@router.post("/process-ready")
async def process_ready_commissions(
    min_amount: float = Query(10.0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Automatically process all ready commissions for all affiliates.
    
    Creates and processes payouts for all affiliates with ready commissions
    above the minimum amount.
    
    WARNING: This will automatically send payments. Use with caution.
    """
    payout_service = PayoutService(db)
    affiliate_service = AffiliateService(db)
    
    # First, process commissions that are ready (move PENDING -> READY)
    await affiliate_service.process_ready_commissions()
    
    # Get all affiliates
    affiliates_result = await db.execute(
        select(Affiliate).where(Affiliate.is_active == True)
    )
    affiliates = list(affiliates_result.scalars().all())
    
    results = []
    errors = []
    
    for affiliate in affiliates:
        try:
            # Get ready commissions
            commissions = await payout_service.get_ready_commissions_for_affiliate(
                str(affiliate.id),
                min_amount=Decimal(str(min_amount))
            )
            
            if not commissions:
                continue
            
            # Determine payout method from affiliate preference
            payout_method = affiliate.payout_method or "paypal"
            
            if not affiliate.payout_email:
                errors.append({
                    "affiliate_id": str(affiliate.id),
                    "error": "No payout email configured",
                })
                continue
            
            # Create payout
            commission_ids = [str(c.id) for c in commissions]
            payout = await payout_service.create_payout(
                affiliate_id=str(affiliate.id),
                commission_ids=commission_ids,
                payout_method=payout_method,
                notes="Auto-processed from ready commissions",
            )
            
            if not payout:
                errors.append({
                    "affiliate_id": str(affiliate.id),
                    "error": "Failed to create payout",
                })
                continue
            
            # Process payout
            if payout_method == "paypal":
                process_result = await payout_service.process_paypal_payout(str(payout.id))
            elif payout_method == "crypto":
                process_result = await payout_service.process_crypto_payout(str(payout.id))
            else:
                errors.append({
                    "affiliate_id": str(affiliate.id),
                    "error": f"Unsupported payout method: {payout_method}",
                })
                continue
            
            if process_result.get("success"):
                results.append({
                    "affiliate_id": str(affiliate.id),
                    "payout_id": str(payout.id),
                    "amount": float(payout.amount),
                    "status": "success",
                })
            else:
                errors.append({
                    "affiliate_id": str(affiliate.id),
                    "payout_id": str(payout.id),
                    "error": process_result.get("error"),
                })
                
        except Exception as e:
            logger.error(f"Error processing payout for affiliate {affiliate.id}: {e}", exc_info=True)
            errors.append({
                "affiliate_id": str(affiliate.id),
                "error": str(e),
            })
    
    return {
        "success": len(errors) == 0,
        "processed": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors,
    }


@router.get("/{payout_id}", response_model=PayoutResponse)
async def get_payout(
    payout_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get details of a specific payout.
    """
    payout_result = await db.execute(
        select(AffiliatePayout).where(AffiliatePayout.id == payout_id)
    )
    payout = payout_result.scalar_one_or_none()

    if not payout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payout not found",
        )

    return PayoutResponse(**payout.to_dict())

