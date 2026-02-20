"""
Admin logs API routes.

Provides system log viewing:
- Query logs by source/level
- Search logs
- Log statistics
Never returns 500: missing system_log table or empty DB returns safe fallback.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.exc import OperationalError, ProgrammingError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.core.dependencies import get_db
from app.core.admin_safe import SAFE_LOGS_LIST, SAFE_LOGS_STATS, SAFE_LOGS_SOURCES
from app.models.user import User
from app.models.system_log import SystemLog
from .auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


class LogResponse(BaseModel):
    """Log entry response model."""
    id: str
    source: str
    level: str
    message: str
    metadata: Optional[Dict[str, Any]]
    error_type: Optional[str]
    request_id: Optional[str]
    created_at: str


class LogStats(BaseModel):
    """Log statistics response."""
    total: int
    by_source: Dict[str, int]
    by_level: Dict[str, int]
    error_rate: float


@router.get("")
async def list_logs(
    source: Optional[str] = Query(None, description="Filter by source"),
    level: Optional[str] = Query(None, description="Filter by level"),
    search: Optional[str] = Query(None, description="Search in message"),
    time_range: str = Query("24h", pattern="^(1h|6h|24h|7d|30d)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """List system logs with filters. Returns [] if system_log table missing or error."""
    try:
        now = datetime.utcnow()
        ranges = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        start_date = now - ranges.get(time_range, timedelta(hours=24))

        query = select(SystemLog).where(SystemLog.created_at >= start_date)
        conditions = []
        if source:
            conditions.append(SystemLog.source == source)
        if level:
            conditions.append(SystemLog.level == level)
        if search:
            conditions.append(SystemLog.message.ilike(f"%{search}%"))
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(SystemLog.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        logs = result.scalars().all()

        logger.info("admin.endpoint.success", extra={"endpoint": "logs.list"})
        return [
            LogResponse(
                id=str(log.id),
                source=log.source or "",
                level=log.level or "",
                message=log.message or "",
                metadata=log.metadata_,
                error_type=log.error_type,
                request_id=log.request_id,
                created_at=log.created_at.isoformat() if log.created_at else "",
            )
            for log in logs
        ]
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "logs.list", "error": str(e)}, exc_info=True)
        return list(SAFE_LOGS_LIST)


@router.get("/stats", response_model=LogStats)
async def get_log_stats(
    time_range: str = Query("24h", pattern="^(1h|6h|24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get log statistics. Returns safe zeros if system_log table missing or error."""
    try:
        now = datetime.utcnow()
        ranges = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        start_date = now - ranges.get(time_range, timedelta(hours=24))

        total_result = await db.execute(
            select(func.count(SystemLog.id)).where(SystemLog.created_at >= start_date)
        )
        total = total_result.scalar() or 0

        source_result = await db.execute(
            select(SystemLog.source, func.count(SystemLog.id)).where(
                SystemLog.created_at >= start_date
            ).group_by(SystemLog.source)
        )
        by_source = {row[0]: row[1] for row in source_result.all()}

        level_result = await db.execute(
            select(SystemLog.level, func.count(SystemLog.id)).where(
                SystemLog.created_at >= start_date
            ).group_by(SystemLog.level)
        )
        by_level = {row[0]: row[1] for row in level_result.all()}

        errors = by_level.get("error", 0) + by_level.get("critical", 0)
        error_rate = (errors / total * 100) if total > 0 else 0.0

        logger.info("admin.endpoint.success", extra={"endpoint": "logs.stats"})
        return LogStats(
            total=total,
            by_source=by_source,
            by_level=by_level,
            error_rate=round(error_rate, 2),
        )
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "logs.stats", "error": str(e)}, exc_info=True)
        return LogStats(**SAFE_LOGS_STATS)


@router.get("/sources")
async def get_log_sources(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get list of all log sources. Returns [] if system_log table missing or error."""
    try:
        result = await db.execute(select(SystemLog.source).distinct())
        rows = result.all()
        logger.info("admin.endpoint.success", extra={"endpoint": "logs.sources"})
        return [row[0] for row in rows if row[0] is not None]
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "logs.sources", "error": str(e)}, exc_info=True)
        return list(SAFE_LOGS_SOURCES)

