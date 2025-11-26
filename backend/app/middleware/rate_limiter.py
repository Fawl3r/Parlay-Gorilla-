"""Rate limiting middleware using SlowAPI"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from typing import Callable

# Safe wrapper for get_remote_address that handles all edge cases
def safe_get_remote_address(request: Request) -> str:
    """Safely get remote address, handling None or missing attributes"""
    try:
        if request is None:
            return "unknown"
        
        # Check if request has necessary attributes
        if not hasattr(request, 'headers') or request.headers is None:
            # Try to get from client if available
            if hasattr(request, 'client') and request.client is not None:
                if hasattr(request.client, 'host'):
                    return str(request.client.host)
            return "unknown"
        
        # Try to get from headers first (most reliable)
        if hasattr(request, 'headers'):
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            
            real_ip = request.headers.get("x-real-ip")
            if real_ip:
                return real_ip
        
        # Fallback to client host
        if hasattr(request, 'client') and request.client is not None:
            if hasattr(request.client, 'host'):
                return str(request.client.host)
        
        # Last resort: use slowapi's function but catch errors
        try:
            return get_remote_address(request)
        except:
            return "unknown"
            
    except Exception as e:
        print(f"Error in safe_get_remote_address: {e}")
        import traceback
        traceback.print_exc()
        return "unknown"

# Create limiter instance with safe wrapper
limiter = Limiter(key_func=safe_get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "default": "100/hour",  # Default: 100 requests per hour
    "parlay_generation": "20/hour",  # Parlay generation: 20 per hour (expensive)
    "analytics": "50/hour",  # Analytics: 50 per hour
    "auth": "30/hour",  # Auth endpoints: 30 per hour
}


def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key based on user if authenticated"""
    try:
        if request is None:
            return "unknown"
        
        # Try to get user ID from request state (set by auth dependency)
        if hasattr(request, 'state'):
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                return str(user_id)
        
        # Fallback to IP address using safe wrapper
        return safe_get_remote_address(request)
    except Exception as e:
        # If anything fails, return a safe default
        print(f"Error getting rate limit key: {e}")
        import traceback
        traceback.print_exc()
        return "unknown"


def create_rate_limiter():
    """Create and configure rate limiter"""
    return Limiter(key_func=get_rate_limit_key)


# Decorator for rate limiting
def rate_limit(limit: str = "100/hour"):
    """
    Decorator for rate limiting endpoints
    
    Usage:
        @rate_limit("10/minute")
        async def my_endpoint():
            ...
    """
    def decorator(func: Callable):
        return limiter.limit(limit)(func)
    return decorator


# Exception handler for rate limit exceeded
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded exceptions"""
    # Get origin for CORS headers
    origin = "*"
    if request and hasattr(request, 'headers'):
        origin = request.headers.get("origin", "http://localhost:3000")
    
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Rate limit exceeded: {exc.detail}",
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    )

