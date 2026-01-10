"""
Stripe reconciliation routes (webhook fallback).

These endpoints allow the frontend to trigger a reconciliation run that:
- Fetches Stripe Checkout Session(s)
- Applies fulfillment (subscription activation / credit packs / parlay purchases)

This is intentionally gated behind auth and validates that the Stripe session
belongs to the current user (by metadata.user_id or customer_id match).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.stripe_reconciliation_service import StripeReconciliationService

router = APIRouter()


class StripeReconcileRequest(BaseModel):
    session_id: str = Field(..., min_length=5, max_length=255)


class StripeReconcileResponse(BaseModel):
    status: str
    message: str
    session_id: str | None = None
    mode: str | None = None
    purchase_type: str | None = None
    subscription_id: str | None = None


@router.post("/billing/stripe/reconcile", response_model=StripeReconcileResponse)
async def reconcile_stripe_session(
    payload: StripeReconcileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StripeReconciliationService(db)
    result = await service.reconcile_session_for_user(user=user, session_id=payload.session_id)

    # Translate service result into HTTP semantics
    if result.status == "error":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.message)

    return StripeReconcileResponse(
        status=result.status,
        message=result.message,
        session_id=result.session_id,
        mode=result.mode,
        purchase_type=result.purchase_type,
        subscription_id=result.subscription_id,
    )


@router.post("/billing/stripe/reconcile-latest", response_model=StripeReconcileResponse)
async def reconcile_latest_stripe_session(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StripeReconciliationService(db)
    result = await service.reconcile_latest_for_user(user=user, limit=10)

    if result.status == "error":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.message)

    return StripeReconcileResponse(
        status=result.status,
        message=result.message,
        session_id=result.session_id,
        mode=result.mode,
        purchase_type=result.purchase_type,
        subscription_id=result.subscription_id,
    )


