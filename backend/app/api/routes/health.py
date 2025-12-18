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
async def health_metrics():
    """Lightweight operational metrics (no DB calls)."""
    return {
        "service": "Parlay Gorilla API",
        "environment": settings.environment,
        "debug": settings.debug,
        "background_jobs_enabled": settings.enable_background_jobs,
        "rate_limit": {
          "requests": settings.rate_limit_requests,
          "period_seconds": settings.rate_limit_period,
        },
    }

