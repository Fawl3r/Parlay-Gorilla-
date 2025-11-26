"""Health check endpoint"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    service: str


@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint with explicit CORS headers"""
    from datetime import timezone
    origin = request.headers.get("origin", "")
    
    # Create response data
    response_data = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "F3 Parlay AI API",
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

