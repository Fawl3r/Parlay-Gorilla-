"""Health check endpoint"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    service: str
    environment: str


@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint with explicit CORS headers"""
    from datetime import timezone
    origin = request.headers.get("origin", "")
    
    # Create response data
    response_data = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Parlay Gorilla API",
        "environment": settings.environment,
    }
    
    # Always add CORS headers if origin is present
    headers = {}
    if origin and ("localhost" in origin or "127.0.0.1" in origin):
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Expose-Headers": "*",
        }
    
    return JSONResponse(content=response_data, headers=headers)


@router.get("/health/metrics")
async def health_metrics(request: Request):
    """Lightweight operational metrics with database connectivity check."""
    from app.database.session import AsyncSessionLocal
    from sqlalchemy import text
    
    db_status = "unknown"
    db_latency_ms = None
    
    try:
        async with AsyncSessionLocal() as db:
            start = datetime.now()
            await db.execute(text("SELECT 1"))
            latency = (datetime.now() - start).total_seconds() * 1000
            db_status = "connected"
            db_latency_ms = round(latency, 2)
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"
    
    response_data = {
        "service": "Parlay Gorilla API",
        "environment": settings.environment,
        "debug": settings.debug,
        "background_jobs_enabled": settings.enable_background_jobs,
        "rate_limit": {
          "requests": settings.rate_limit_requests,
          "period_seconds": settings.rate_limit_period,
        },
        "database": {
            "status": db_status,
            "latency_ms": db_latency_ms,
        },
        "request_id": getattr(request.state, "request_id", None) if hasattr(request, "state") else None,
    }
    
    return response_data

