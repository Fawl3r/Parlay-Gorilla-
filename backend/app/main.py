"""FastAPI application entry point"""

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.routes import health, games, parlay, auth, analytics, social, websocket, variants, reports
from app.middleware.rate_limiter import limiter, rate_limit_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",  # Alternative port
    "http://localhost:3004",  # Current frontend dev port
    "http://127.0.0.1:3004",
]
ACCESS_CONTROL_METHODS = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
ACCESS_CONTROL_HEADERS = "*"

# Create FastAPI app
app = FastAPI(
    title="F3 Parlay AI API",
    description="AI-powered sports betting parlay engine",
    version="1.0.0",
)

# CORS middleware - MUST be added FIRST, before any other middleware
# Allow specific origins plus regex for any localhost/127.0.0.1 port
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)


@app.middleware("http")
async def ensure_cors_headers(request: Request, call_next):
    """Guarantee CORS headers on every response, including health checks."""
    import re
    origin = request.headers.get("origin", "")
    
    # Check if origin is allowed (exact match or localhost pattern)
    is_allowed = False
    if origin:
        if origin in ALLOWED_ORIGINS:
            is_allowed = True
        elif re.match(r"https?://(localhost|127\.0\.0\.1):\d+", origin):
            is_allowed = True
    
    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        response = Response(status_code=200)
        if is_allowed and origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = ACCESS_CONTROL_METHODS
            response.headers["Access-Control-Allow-Headers"] = ACCESS_CONTROL_HEADERS
            response.headers["Access-Control-Max-Age"] = "3600"
        return response
    
    # Handle regular requests
    response = await call_next(request)
    
    # Always add CORS headers if origin is allowed - FORCE set the header
    if is_allowed and origin:
        # Force set header - this should work even if already set
        response.headers.__setitem__("Access-Control-Allow-Origin", origin)
        response.headers.__setitem__("Access-Control-Allow-Credentials", "true")
        response.headers.__setitem__("Access-Control-Allow-Methods", ACCESS_CONTROL_METHODS)
        response.headers.__setitem__("Access-Control-Allow-Headers", ACCESS_CONTROL_HEADERS)
        response.headers.__setitem__("Access-Control-Expose-Headers", ACCESS_CONTROL_HEADERS)
        response.headers.__setitem__("Vary", "Origin")
    
    return response

# Add rate limiter exception handler (before routers)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Global exception handler to ensure CORS headers on errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that ensures CORS headers are included"""
    import traceback
    error_detail = str(exc)
    print(f"Global exception handler: {error_detail}")
    print(traceback.format_exc())
    
    # Get origin from request if available - with extra safety checks
    origin = ALLOWED_ORIGINS[0]
    try:
        if request is not None:
            if hasattr(request, 'headers') and request.headers is not None:
                origin = request.headers.get("origin", ALLOWED_ORIGINS[0])
    except Exception as e:
        print(f"Error getting origin from request: {e}")
        origin = ALLOWED_ORIGINS[0]
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": error_detail},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": ACCESS_CONTROL_METHODS,
            "Access-Control-Allow-Headers": ACCESS_CONTROL_HEADERS,
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers"""
    # Get origin from request if available - with extra safety checks
    origin = ALLOWED_ORIGINS[0]
    try:
        if request is not None:
            if hasattr(request, 'headers') and request.headers is not None:
                origin = request.headers.get("origin", ALLOWED_ORIGINS[0])
    except Exception as e:
        print(f"Error getting origin from request: {e}")
        origin = ALLOWED_ORIGINS[0]
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": ACCESS_CONTROL_METHODS,
            "Access-Control-Allow-Headers": ACCESS_CONTROL_HEADERS,
        }
    )

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(games.router, prefix="/api", tags=["Games"])
app.include_router(parlay.router, prefix="/api", tags=["Parlay"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(social.router, prefix="/api/social", tags=["Social"])
app.include_router(variants.router, prefix="/api/parlay/variants", tags=["Parlay Variants"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(websocket.router, tags=["WebSocket"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    from app.database.session import engine, Base
    
    # Try to connect to database, but don't fail startup if it's unavailable
    try:
        # Create tables (in production, use Alembic migrations)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[STARTUP] Database connection successful")
    except Exception as db_error:
        print(f"[STARTUP] Warning: Database connection failed: {db_error}")
        print("[STARTUP] Server will continue, but database-dependent features may not work")
        print("[STARTUP] Health endpoint and other non-database endpoints will still function")
    
    # Start background scheduler (will handle its own database connection errors)
    try:
        from app.services.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.start()
        print("[STARTUP] Background scheduler started")
        
        # Run initial refresh check after a short delay
        import asyncio
        async def initial_check():
            await asyncio.sleep(5)  # Wait 5 seconds for everything to initialize
            try:
                await scheduler._initial_refresh()
            except Exception as refresh_error:
                print(f"[STARTUP] Initial refresh failed (non-critical): {refresh_error}")
        
        asyncio.create_task(initial_check())
    except Exception as scheduler_error:
        print(f"[STARTUP] Warning: Scheduler startup failed: {scheduler_error}")
        print("[STARTUP] Server will continue without background jobs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Stop background scheduler
    from app.services.scheduler import get_scheduler
    scheduler = get_scheduler()
    scheduler.stop()
    
    from app.database.session import engine
    await engine.dispose()

