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
    """Health check endpoint with explicit CORS headers. Always returns 200."""
    from datetime import timezone
    from fastapi import status
    
    try:
        origin = request.headers.get("origin", "")
        
        # Create response data - never throw exceptions
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
        
        return JSONResponse(content=response_data, headers=headers, status_code=status.HTTP_200_OK)
    except Exception as e:
        # Even if something goes wrong, return 200 with error status
        # This ensures health check never fails
        return JSONResponse(
            content={
                "status": "degraded",
                "error": "Health check error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "Parlay Gorilla API",
            },
            status_code=status.HTTP_200_OK
        )


@router.get("/health/db")
async def health_db(request: Request):
    """Database health check endpoint. Returns 200 if healthy, 503 if unhealthy."""
    from fastapi import status
    from datetime import timezone
    from app.database.session import AsyncSessionLocal
    from sqlalchemy import text
    
    try:
        # Test database connectivity
        async with AsyncSessionLocal() as db:
            start = datetime.now()
            await db.execute(text("SELECT 1"))
            latency_ms = round((datetime.now() - start).total_seconds() * 1000, 2)
            
            response_data = {
                "status": "healthy",
                "database": "connected",
                "latency_ms": latency_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "Parlay Gorilla API",
            }
            
            return JSONResponse(
                content=response_data,
                status_code=status.HTTP_200_OK
            )
    except Exception as e:
        # Database is unhealthy - return 503
        error_msg = str(e)[:100]  # Truncate long error messages
        response_data = {
            "status": "unhealthy",
            "database": "disconnected",
            "error": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "Parlay Gorilla API",
        }
        
        return JSONResponse(
            content=response_data,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


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


@router.get("/health/settlement")
async def health_settlement(request: Request):
    """Settlement system health check endpoint.
    
    Returns:
        - Worker status (running/stopped)
        - Last settlement run time
        - Error rate
        - Circuit breaker status
        - Feature flag status
    """
    from fastapi import status
    from datetime import timezone
    from app.database.session import AsyncSessionLocal
    from app.models.system_heartbeat import SystemHeartbeat
    from sqlalchemy import select
    from app.workers.settlement_worker import get_settlement_worker
    
    try:
        # Get worker status
        worker = get_settlement_worker()
        worker_running = worker.running
        circuit_open = getattr(worker, '_circuit_open', False)
        consecutive_errors = getattr(worker, '_consecutive_errors', 0)
        circuit_open_since = getattr(worker, '_circuit_open_since', None)
        
        # Get heartbeat data
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(SystemHeartbeat).where(SystemHeartbeat.name == "settlement_worker")
            )
            heartbeat = result.scalar_one_or_none()
            
            last_beat = heartbeat.last_beat_at if heartbeat else None
            heartbeat_meta = heartbeat.meta if heartbeat else {}
            
            # Calculate time since last beat
            time_since_beat = None
            if last_beat:
                time_since_beat = (datetime.now(timezone.utc) - last_beat).total_seconds()
        
        # Determine overall health status
        health_status = "healthy"
        status_code = status.HTTP_200_OK
        
        if not settings.feature_settlement:
            health_status = "disabled"
        elif circuit_open:
            health_status = "circuit_open"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif not worker_running:
            health_status = "stopped"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif time_since_beat and time_since_beat > 600:  # No heartbeat in 10 minutes
            health_status = "stale"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif consecutive_errors >= 3:
            health_status = "degraded"
        
        response_data = {
            "status": health_status,
            "feature_enabled": settings.feature_settlement,
            "worker": {
                "running": worker_running,
                "circuit_breaker": {
                    "open": circuit_open,
                    "consecutive_errors": consecutive_errors,
                    "opened_at": circuit_open_since.isoformat() if circuit_open_since else None,
                },
            },
            "heartbeat": {
                "last_beat": last_beat.isoformat() if last_beat else None,
                "seconds_since_beat": round(time_since_beat, 2) if time_since_beat else None,
                "meta": heartbeat_meta,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(request.state, "request_id", None) if hasattr(request, "state") else None,
        }
        
        # Add CORS headers
        origin = request.headers.get("origin", "")
        headers = {}
        if origin and ("localhost" in origin or "127.0.0.1" in origin):
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Expose-Headers": "*",
            }
        
        return JSONResponse(
            content=response_data,
            status_code=status_code,
            headers=headers
        )
    
    except Exception as e:
        # Never crash health check
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in settlement health check: {e}", exc_info=True)
        
        response_data = {
            "status": "error",
            "error": str(e)[:100],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(request.state, "request_id", None) if hasattr(request, "state") else None,
        }
        
        origin = request.headers.get("origin", "")
        headers = {}
        if origin and ("localhost" in origin or "127.0.0.1" in origin):
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Expose-Headers": "*",
            }
        
        return JSONResponse(
            content=response_data,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers=headers
        )

