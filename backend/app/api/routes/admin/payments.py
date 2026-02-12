"""
Admin payments API routes.

Provides payment and subscription management:
- List payments
- View subscriptions
- Manual plan upgrades (for testing/support)
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
import uuid

from app.core.dependencies import get_db
from app.models.user import User
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.services.payment_service import PaymentService
from .auth import require_admin

router = APIRouter()


class PaymentResponse(BaseModel):
    """Payment response model."""
    id: str
    user_id: str
    amount: float
    currency: str
    plan: str
    provider: str
    status: str
    created_at: str
    paid_at: Optional[str]


class SubscriptionResponse(BaseModel):
    """Subscription response model."""
    id: str
    user_id: str
    plan: str
    provider: str
    status: str
    current_period_start: Optional[str]
    current_period_end: Optional[str]
    cancelled_at: Optional[str]
    created_at: str


class ManualUpgradeRequest(BaseModel):
    """Request for manual plan upgrade."""
    user_id: str
    plan: str
    duration_days: Optional[int] = 30  # None or 0 means lifetime
    is_lifetime: bool = False


@router.get("")
async def list_payments(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List payments with filters.
    """
    now = datetime.utcnow()
    ranges = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
    }
    start_date = now - ranges.get(time_range, timedelta(days=30))
    
    query = select(Payment).where(Payment.created_at >= start_date)
    
    if status_filter:
        query = query.where(Payment.status == status_filter)
    if provider:
        query = query.where(Payment.provider == provider)
    
    query = query.order_by(Payment.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    payments = result.scalars().all()
    
    return [
        PaymentResponse(
            id=str(p.id),
            user_id=str(p.user_id),
            amount=float(p.amount),
            currency=p.currency,
            plan=p.plan,
            provider=p.provider,
            status=p.status,
            created_at=p.created_at.isoformat() if p.created_at else "",
            paid_at=p.paid_at.isoformat() if p.paid_at else None,
        )
        for p in payments
    ]


@router.get("/stats")
async def get_payment_stats(
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get payment statistics.
    """
    now = datetime.utcnow()
    ranges = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
    }
    start_date = now - ranges.get(time_range, timedelta(days=30))
    
    # Total revenue
    revenue_result = await db.execute(
        select(func.sum(Payment.amount)).where(
            and_(
                Payment.status == "paid",
                Payment.paid_at >= start_date
            )
        )
    )
    total_revenue = float(revenue_result.scalar() or 0)
    
    # Payment count by status
    status_result = await db.execute(
        select(Payment.status, func.count(Payment.id)).where(
            Payment.created_at >= start_date
        ).group_by(Payment.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}
    
    # Revenue by provider
    provider_result = await db.execute(
        select(Payment.provider, func.sum(Payment.amount)).where(
            and_(
                Payment.status == "paid",
                Payment.paid_at >= start_date
            )
        ).group_by(Payment.provider)
    )
    by_provider = {row[0]: float(row[1]) for row in provider_result.all()}
    
    return {
        "time_range": time_range,
        "total_revenue": total_revenue,
        "by_status": by_status,
        "by_provider": by_provider,
    }


@router.get("/subscriptions")
async def list_subscriptions(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List subscriptions.
    """
    query = select(Subscription)
    
    if status_filter:
        query = query.where(Subscription.status == status_filter)
    
    query = query.order_by(Subscription.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    subscriptions = result.scalars().all()
    
    return [
        SubscriptionResponse(
            id=str(s.id),
            user_id=str(s.user_id),
            plan=s.plan,
            provider=s.provider,
            status=s.status,
            current_period_start=s.current_period_start.isoformat() if s.current_period_start else None,
            current_period_end=s.current_period_end.isoformat() if s.current_period_end else None,
            cancelled_at=s.cancelled_at.isoformat() if s.cancelled_at else None,
            created_at=s.created_at.isoformat() if s.created_at else "",
        )
        for s in subscriptions
    ]


@router.post("/manual-upgrade")
async def manual_upgrade(
    request: ManualUpgradeRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Manually upgrade a user's plan.
    
    For testing or customer support purposes.
    Creates a manual payment record and subscription.
    Supports both time-limited and lifetime subscriptions.
    """
    from app.models.subscription import Subscription, SubscriptionStatus
    from app.models.user import UserPlan
    from sqlalchemy import select
    
    service = PaymentService(db)
    
    # Verify user exists
    result = await db.execute(select(User).where(User.id == uuid.UUID(request.user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create manual payment
    payment = await service.create_payment(
        user_id=request.user_id,
        amount=0.0,  # Manual/free upgrade
        plan=request.plan,
        provider="manual",
        provider_metadata={
            "upgraded_by": str(admin.id),
            "reason": "manual_upgrade",
            "is_lifetime": request.is_lifetime,
        },
    )
    
    # Mark as paid immediately
    await service.mark_payment_paid(str(payment.id))
    
    # Cancel any existing active subscriptions
    # Find and cancel existing active subscriptions
    from app.models.subscription import SubscriptionStatus
    existing_subs_result = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.user_id == uuid.UUID(request.user_id),
                Subscription.status == SubscriptionStatus.active.value
            )
        )
    )
    existing_subs = existing_subs_result.scalars().all()
    for sub in existing_subs:
        sub.status = SubscriptionStatus.cancelled.value
        sub.cancelled_at = datetime.utcnow()
        sub.cancellation_reason = "Replaced by manual admin upgrade"
    
    # Create subscription
    now = datetime.utcnow()
    is_lifetime = request.is_lifetime or (request.duration_days is None or request.duration_days == 0)
    
    subscription = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.UUID(request.user_id),
        plan=request.plan,
        provider="manual",
        provider_subscription_id=f"manual_{request.user_id}_{uuid.uuid4()}" if not is_lifetime else f"lifetime_{request.user_id}",
        status=SubscriptionStatus.active.value,
        current_period_start=now,
        current_period_end=None if is_lifetime else (now + timedelta(days=request.duration_days or 30)),
        is_lifetime=is_lifetime,
        provider_metadata={
            "upgraded_by": str(admin.id),
            "granted_at": now.isoformat(),
            "reason": "manual_upgrade",
        },
    )
    
    db.add(subscription)
    
    # Upgrade user plan
    from app.models.user import UserPlan
    try:
        user.plan = UserPlan(request.plan).value
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {request.plan}. Must be one of: {[p.value for p in UserPlan]}")
    user.subscription_plan = request.plan
    user.subscription_status = "active"
    
    await db.commit()
    await db.refresh(subscription)
    
    return {
        "success": True,
        "payment_id": str(payment.id),
        "subscription_id": str(subscription.id),
        "plan": request.plan,
        "is_lifetime": is_lifetime,
        "expires_at": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
    }

