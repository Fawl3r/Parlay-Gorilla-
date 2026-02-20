"""
Admin metrics API routes.

Provides dashboard metrics for:
- Overview
- User analytics
- Usage analytics
- Revenue analytics
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.dependencies import get_db
from app.core.admin_safe import (
    SAFE_METRICS_OVERVIEW,
    SAFE_METRICS_USERS,
    SAFE_METRICS_USAGE,
    SAFE_METRICS_REVENUE,
    SAFE_METRICS_TEMPLATES,
    SAFE_MODEL_PERFORMANCE,
)
from app.models.user import User
from app.services.admin_metrics_service import AdminMetricsService
from .auth import require_admin

logger = logging.getLogger(__name__)

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
    """Get overview dashboard metrics. Returns safe fallback on DB/table errors."""
    try:
        start_date, end_date = parse_time_range(time_range)
        service = AdminMetricsService(db)
        metrics = await service.get_overview_metrics(start_date, end_date)
        logger.info("admin.endpoint.success", extra={"endpoint": "metrics.overview"})
        return {"time_range": time_range, **metrics}
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "metrics.overview", "error": str(e)}, exc_info=True)
        return {"time_range": time_range, **SAFE_METRICS_OVERVIEW}


@router.get("/users")
async def get_user_metrics(
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get detailed user analytics. Returns safe fallback on DB/table errors."""
    try:
        start_date, end_date = parse_time_range(time_range)
        service = AdminMetricsService(db)
        metrics = await service.get_user_metrics(start_date, end_date)
        logger.info("admin.endpoint.success", extra={"endpoint": "metrics.users"})
        return {"time_range": time_range, **metrics}
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "metrics.users", "error": str(e)}, exc_info=True)
        return {"time_range": time_range, **SAFE_METRICS_USERS}


@router.get("/usage")
async def get_usage_metrics(
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get feature usage analytics. Returns safe fallback on DB/table errors."""
    try:
        start_date, end_date = parse_time_range(time_range)
        service = AdminMetricsService(db)
        metrics = await service.get_usage_metrics(start_date, end_date)
        logger.info("admin.endpoint.success", extra={"endpoint": "metrics.usage"})
        return {"time_range": time_range, **metrics}
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "metrics.usage", "error": str(e)}, exc_info=True)
        return {"time_range": time_range, **SAFE_METRICS_USAGE}


@router.get("/revenue")
async def get_revenue_metrics(
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get revenue and subscription analytics. Returns safe fallback on DB/table/serialization errors."""
    try:
        start_date, end_date = parse_time_range(time_range)
        service = AdminMetricsService(db)
        metrics = await service.get_revenue_metrics(start_date, end_date)
        logger.info("admin.endpoint.success", extra={"endpoint": "metrics.revenue"})
        return {"time_range": time_range, **metrics}
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "metrics.revenue", "error": str(e)}, exc_info=True)
        return {"time_range": time_range, **SAFE_METRICS_REVENUE}


@router.get("/templates")
async def get_template_metrics(
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get Custom Builder QuickStart template analytics. Returns safe fallback on DB/table errors."""
    try:
        start_date, end_date = parse_time_range(time_range)
        service = AdminMetricsService(db)
        metrics = await service.get_template_metrics(start_date, end_date)
        logger.info("admin.endpoint.success", extra={"endpoint": "metrics.templates"})
        return {"time_range": time_range, **metrics}
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "metrics.templates", "error": str(e)}, exc_info=True)
        return {"time_range": time_range, **SAFE_METRICS_TEMPLATES}


@router.get("/model-performance")
async def get_model_performance(
    sport: Optional[str] = Query(None, description="Filter by sport"),
    lookback_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get model performance metrics. Returns safe fallback on DB/table errors."""
    try:
        from app.services.prediction_tracker import PredictionTrackerService
        from app.core.model_config import MODEL_VERSION

        tracker = PredictionTrackerService(db)
        stats = await tracker.get_accuracy_stats(
            sport=sport.upper() if sport else None,
            lookback_days=lookback_days,
        )
        logger.info("admin.endpoint.success", extra={"endpoint": "metrics.model-performance"})
        return {
            "model_version": getattr(MODEL_VERSION, "value", str(MODEL_VERSION)) if MODEL_VERSION is not None else "",
            "lookback_days": lookback_days,
            "sport_filter": sport,
            "metrics": stats or {},
        }
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "metrics.model-performance", "error": str(e)}, exc_info=True)
        return {**SAFE_MODEL_PERFORMANCE, "lookback_days": lookback_days, "sport_filter": sport}

