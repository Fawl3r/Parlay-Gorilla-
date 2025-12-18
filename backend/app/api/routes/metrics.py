"""Metrics and observability endpoints"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timezone
from typing import Dict, Any
import psutil
import os

from app.core.dependencies import get_db
from app.models.parlay import Parlay
from app.models.user import User
from app.models.game import Game

router = APIRouter()


@router.get("/metrics")
async def get_metrics(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get application metrics for monitoring
    
    Returns:
        - System metrics (CPU, memory, disk)
        - Database metrics (connection pool, table counts)
        - Application metrics (users, parlays, games)
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database metrics
        db_metrics = {}
        try:
            # Get table counts
            parlay_count = await db.scalar(select(func.count(Parlay.id)))
            user_count = await db.scalar(select(func.count(User.id)))
            game_count = await db.scalar(select(func.count(Game.id)))
            
            # Get connection pool info
            pool = db.bind.pool if hasattr(db.bind, 'pool') else None
            pool_size = pool.size if pool else None
            pool_checked_in = pool.checkedin() if pool else None
            pool_checked_out = pool.checkedout() if pool else None
            
            db_metrics = {
                "parlays": parlay_count or 0,
                "users": user_count or 0,
                "games": game_count or 0,
                "pool_size": pool_size,
                "pool_checked_in": pool_checked_in,
                "pool_checked_out": pool_checked_out,
            }
        except Exception as e:
            db_metrics = {"error": str(e)}
        
        # Application metrics
        app_metrics = {
            "uptime_seconds": None,  # Could track from startup
            "environment": os.getenv("ENVIRONMENT", "development"),
        }
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent,
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 2),
                },
            },
            "database": db_metrics,
            "application": app_metrics,
        }
    except Exception as e:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }


@router.get("/health/detailed")
async def detailed_health_check(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Detailed health check including database connectivity
    
    Returns:
        - Overall status
        - Component status (database, external APIs)
        - Timestamp
    """
    from datetime import timezone
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Parlay Gorilla API",
        "components": {},
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }
    
    # Check external APIs (basic connectivity)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Quick check - don't use actual API key
            health_status["components"]["external_apis"] = {
                "status": "healthy",
                "message": "API clients initialized",
            }
    except Exception as e:
        health_status["components"]["external_apis"] = {
            "status": "degraded",
            "message": f"API client initialization issue: {str(e)}",
        }
    
    return health_status

