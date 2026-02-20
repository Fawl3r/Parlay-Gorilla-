"""
Admin metrics API routes.

Provides dashboard metrics for:
- Overview
- User analytics
- Usage analytics
- Revenue analytics
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

from app.core.dependencies import get_db

logger = logging.getLogger(__name__)
from app.models.user import User
from app.services.admin_metrics_service import AdminMetricsService
from .auth import require_admin

router = APIRouter()


def parse_time_range(range_str: str) -> tuple[datetime, datetime]:
    """Parse time range string to start/end datetimes (timezone-aware UTC)."""
    now = datetime.now(timezone.utc)
    ranges = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
    }
    delta = ranges.get(range_str, timedelta(days=7))
    return now - delta, now


@router.get("/overview")
async def get_overview_metrics(
    time_range: str = Query("7d", pattern="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get overview dashboard metrics.
    """
    try:
        start_date, end_date = parse_time_range(time_range)
        service = AdminMetricsService(db)
        metrics = await service.get_overview_metrics(start_date, end_date)
        return {"time_range": time_range, **metrics}
    except Exception as e:
        logger.exception("Admin metrics overview failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load overview metrics")


@router.get("/users")
async def get_user_metrics(
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get detailed user analytics.

    Returns:
    - total_users, new_users
    - dau, wau, mau
    - users_by_plan, users_by_role
    - active_vs_inactive
    - signups_over_time
    """
    try:
        start_date, end_date = parse_time_range(time_range)
        service = AdminMetricsService(db)
        metrics = await service.get_user_metrics(start_date, end_date)
        return {"time_range": time_range, **metrics}
    except Exception as e:
        logger.exception("Admin metrics users failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load user metrics")


@router.get("/usage")
async def get_usage_metrics(
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get feature usage analytics.
    
    Returns:
    - analysis_views
    - parlay_sessions
    - upset_finder_usage
    - parlays_by_type
    - parlays_by_sport
    - avg_legs
    - feature_usage
    """
    start_date, end_date = parse_time_range(time_range)
    
    service = AdminMetricsService(db)
    metrics = await service.get_usage_metrics(start_date, end_date)
    
    return {
        "time_range": time_range,
        **metrics
    }


@router.get("/revenue")
async def get_revenue_metrics(
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get revenue and subscription analytics.
    
    Returns:
    - total_revenue
    - revenue_by_plan
    - active_subscriptions
    - new_subscriptions
    - churned_subscriptions
    - conversion_rate
    - revenue_over_time
    - recent_payments
    """
    start_date, end_date = parse_time_range(time_range)
    
    service = AdminMetricsService(db)
    metrics = await service.get_revenue_metrics(start_date, end_date)
    
    return {
        "time_range": time_range,
        **metrics
    }


@router.get("/templates")
async def get_template_metrics(
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get Custom Builder QuickStart template analytics."""
    try:
        start_date, end_date = parse_time_range(time_range)
        service = AdminMetricsService(db)
        metrics = await service.get_template_metrics(start_date, end_date)
        return {"time_range": time_range, **metrics}
    except Exception as e:
        logger.exception("Admin metrics templates failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load template metrics")


@router.get("/model-performance")
async def get_model_performance(
    sport: Optional[str] = Query(None, description="Filter by sport"),
    lookback_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get model performance metrics.
    
    Reuses existing prediction tracker service.
    """
    from app.services.prediction_tracker import PredictionTrackerService
    from app.core.model_config import MODEL_VERSION
    
    tracker = PredictionTrackerService(db)
    
    stats = await tracker.get_accuracy_stats(
        sport=sport.upper() if sport else None,
        lookback_days=lookback_days,
    )
    
    return {
        "model_version": MODEL_VERSION,
        "lookback_days": lookback_days,
        "sport_filter": sport,
        "metrics": stats,
    }

