"""FastAPI application entry point"""

import asyncio
from fastapi import FastAPI, Request, Response, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.routes import (
    health, games, sports, parlay, auth, analytics, social, websocket, variants, reports, analysis,
    parlay_extended, team_stats, scraper, user, events, admin_router, billing, webhooks,
    profile,
    me,
    subscription,
    notifications,
    live_games,
    parlay_tips,
    affiliate,
    custom_parlay,
    upset_finder,
    saved_parlays,
    saved_parlay_verification,
    promo_codes,
    parlays_results,
    leaderboards,
    analysis_feed,
    redirects,
    verification_records,
    gorilla_bot,
    meta,
    tools,
    feed,
    system,
    games_public_routes,
    internal_metrics,
)
from app.api.routes import bug_reports
from app.api.routes import metrics
from app.middleware.rate_limiter import limiter, rate_limit_handler
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.memory_log_middleware import MemoryLogMiddleware
from slowapi.errors import RateLimitExceeded
from app.core.config import settings

from urllib.parse import urlparse

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",  # Alternative port
    "http://localhost:3004",  # Current frontend dev port
    "http://127.0.0.1:3004",
]

def _add_allowed_origin(origin: str) -> None:
    origin = (origin or "").strip()
    if not origin:
        return
    if origin not in ALLOWED_ORIGINS:
        ALLOWED_ORIGINS.append(origin)


def _add_frontend_origin_variants(frontend_url: str) -> None:
    """
    Add both apex and www origins (and both http/https) for a given frontend URL.

    This supports typical production setups like:
    - https://www.parlaygorilla.com (primary)
    - https://parlaygorilla.com (redirects to www)
    """
    parsed = urlparse(frontend_url)
    if not parsed.scheme or not parsed.netloc:
        _add_allowed_origin(frontend_url)
        return

    scheme = parsed.scheme.lower()
    other_scheme = "http" if scheme == "https" else "https"
    host = parsed.netloc

    # Base + alternate scheme
    _add_allowed_origin(f"{scheme}://{host}")
    _add_allowed_origin(f"{other_scheme}://{host}")

    # Add/remove www.
    if host.startswith("www."):
        apex = host[len("www.") :]
        _add_allowed_origin(f"{scheme}://{apex}")
        _add_allowed_origin(f"{other_scheme}://{apex}")
    else:
        www = f"www.{host}"
        _add_allowed_origin(f"{scheme}://{www}")
        _add_allowed_origin(f"{other_scheme}://{www}")


# Add frontend origin dynamically from environment (Render-only in production)
if settings.frontend_url:
    _add_frontend_origin_variants(settings.frontend_url)

# CORS regex pattern for local network access and tunneling services
# Allows: localhost, 127.0.0.1, private network IPs, and common tunneling domains
LOCAL_NETWORK_REGEX = r"https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}):\d+"

# Tunneling services regex (ngrok, cloudflare, localtunnel, etc.)
# Matches common tunneling service domains
TUNNEL_REGEX = r"https?://([a-zA-Z0-9-]+\.(ngrok-free\.app|ngrok\.io|trycloudflare\.com|localtunnel\.me|serveo\.net|localhost\.run|loca\.lt|mole\.app)|.*\.trycloudflare\.com|.*\.ngrok-free\.app|.*\.ngrok\.io)"

# Render deployment regex (allows any *.onrender.com domain)
RENDER_REGEX = r"https?://([a-zA-Z0-9-]+\.onrender\.com|.*\.onrender\.com)"

ACCESS_CONTROL_METHODS = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
ACCESS_CONTROL_HEADERS = "*"

# Create FastAPI app
app = FastAPI(
    title="Parlay Gorilla API",
    description="AI-powered sports betting parlay engine",
    version="1.0.0",
)

# Request ID middleware - add early for tracing
app.add_middleware(RequestIDMiddleware)
# Memory telemetry for parlay routes (OOM diagnosis on 512MB Render)
app.add_middleware(MemoryLogMiddleware)

# CORS middleware - MUST be added FIRST, before any other middleware
# Allow specific origins plus regex for localhost/127.0.0.1, local network IPs, and tunneling services
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=f"({LOCAL_NETWORK_REGEX}|{TUNNEL_REGEX}|{RENDER_REGEX})",
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
    
    # Check if origin is allowed (exact match, localhost/network pattern, or tunneling service)
    is_allowed = False
    if origin:
        if origin in ALLOWED_ORIGINS:
            is_allowed = True
        elif re.match(LOCAL_NETWORK_REGEX, origin):
            is_allowed = True
        elif re.match(TUNNEL_REGEX, origin):
            is_allowed = True
        elif re.match(RENDER_REGEX, origin):
            is_allowed = True
    
    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        response = Response(status_code=200)
        if is_allowed and origin:
            # Reflect requested headers to satisfy Safari/WebKit preflight for Authorization.
            requested_headers = request.headers.get("access-control-request-headers")
            allow_headers = requested_headers or ACCESS_CONTROL_HEADERS
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = ACCESS_CONTROL_METHODS
            response.headers["Access-Control-Allow-Headers"] = allow_headers
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

# HTTPException handler (user-friendly errors) - must come before generic Exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPExceptions with CORS headers and request_id"""
    # Get request_id for correlation
    request_id = None
    try:
        if request is not None and hasattr(request, 'state'):
            request_id = getattr(request.state, 'request_id', None)
    except Exception:
        pass
    
    origin = ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else "*"
    try:
        if request is not None:
            if hasattr(request, 'headers') and request.headers is not None:
                origin = request.headers.get("origin", origin)
    except Exception:
        origin = ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else "*"
    
    response_content = {"detail": exc.detail}
    if request_id:
        response_content["request_id"] = request_id
    
    headers = {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": ACCESS_CONTROL_METHODS,
        "Access-Control-Allow-Headers": ACCESS_CONTROL_HEADERS,
    }
    if request_id:
        headers["X-Request-ID"] = request_id
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
        headers=headers
    )

# Global exception handler to ensure CORS headers on errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that ensures CORS headers are included.
    Never crashes - always returns a response with request_id for debugging.
    """
    from app.core.error_handling import get_user_friendly_error_message, should_log_error
    import traceback
    import logging
    
    # Get request_id for correlation - wrapped in try/except to never fail
    request_id = None
    try:
        if request is not None and hasattr(request, 'state'):
            request_id = getattr(request.state, 'request_id', None)
    except Exception:
        pass  # Ignore errors getting request_id
    
    logger = logging.getLogger(__name__)
    
    # Get user-friendly error message - wrapped in try/except
    try:
        user_message = get_user_friendly_error_message(exc)
    except Exception:
        user_message = "Something went wrong. Please try again or contact support if the problem persists."
    
    # Log technical details if needed (but don't expose to user)
    # Include request_id in all logs for correlation
    try:
        if should_log_error(exc):
            log_msg = f"Unhandled exception"
            if request_id:
                log_msg += f" [request_id={request_id}]"
            log_msg += f": {exc}"
            logger.error(log_msg, exc_info=True)
            
            # Also print to console with request_id
            print_msg = f"Global exception handler (logged)"
            if request_id:
                print_msg += f" [request_id={request_id}]"
            print_msg += f": {type(exc).__name__}: {exc}"
            print(print_msg)
            print(traceback.format_exc())

            # Emit Telegram alert (fire-and-forget; trim stack to 25 lines; include environment)
            try:
                from app.services.alerting.alerting_service import get_alerting_service
                from app.services.alerting.alerting_service import trim_stack_trace
                stack = trim_stack_trace(traceback.format_exc(), max_lines=25)
                payload = {
                    "environment": getattr(settings, "environment", "unknown"),
                    "request_id": request_id,
                    "exception_type": type(exc).__name__,
                    "message": str(exc)[:500],
                    "stack_trace": stack,
                }
                asyncio.create_task(
                    get_alerting_service().emit("api.unhandled_exception", "error", payload)
                )
            except Exception as alert_err:
                logger.debug("Alerting emit skipped: %s", alert_err)
    except Exception as log_error:
        # Even logging can fail - don't let that crash the handler
        print(f"Error in exception handler logging: {log_error}")
    
    # Get origin from request if available - with extra safety checks
    origin = ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else "*"
    try:
        if request is not None:
            if hasattr(request, 'headers') and request.headers is not None:
                origin = request.headers.get("origin", origin)
    except Exception as e:
        print(f"Error getting origin from request: {e}")
        origin = ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else "*"
    
    # Build response content with request_id
    response_content = {"detail": user_message}
    if request_id:
        response_content["request_id"] = request_id
    
    # Build headers - wrapped in try/except to never fail
    try:
        response_headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": ACCESS_CONTROL_METHODS,
            "Access-Control-Allow-Headers": ACCESS_CONTROL_HEADERS,
        }
        if request_id:
            response_headers["X-Request-ID"] = request_id
    except Exception:
        # Fallback headers if something goes wrong
        response_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        }
        if request_id:
            response_headers["X-Request-ID"] = request_id
    
    # Always return a response - never let handler crash
    try:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_content,
            headers=response_headers
        )
    except Exception as response_error:
        # Last resort - return minimal response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
            headers={"X-Request-ID": str(request_id) if request_id else "unknown"}
        )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers and request_id"""
    # Get request_id for correlation
    request_id = None
    try:
        if request is not None and hasattr(request, 'state'):
            request_id = getattr(request.state, 'request_id', None)
    except Exception:
        pass
    
    # Get origin from request if available - with extra safety checks
    origin = ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else "*"
    try:
        if request is not None:
            if hasattr(request, 'headers') and request.headers is not None:
                origin = request.headers.get("origin", origin)
    except Exception as e:
        print(f"Error getting origin from request: {e}")
        origin = ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else "*"
    
    response_content = {"detail": exc.errors()}
    if request_id:
        response_content["request_id"] = request_id
    
    headers = {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": ACCESS_CONTROL_METHODS,
        "Access-Control-Allow-Headers": ACCESS_CONTROL_HEADERS,
    }
    if request_id:
        headers["X-Request-ID"] = request_id
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_content,
        headers=headers
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "Parlay Gorilla API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])
app.include_router(games.router, prefix="/api", tags=["Games"])
app.include_router(games_public_routes.router, prefix="/api", tags=["Games Public"])
app.include_router(sports.router, prefix="/api", tags=["Sports"])
app.include_router(bug_reports.router, prefix="/api", tags=["Bug Reports"])
app.include_router(parlay.router, prefix="/api", tags=["Parlay"])
app.include_router(custom_parlay.router, prefix="/api", tags=["Custom Parlay"])
app.include_router(saved_parlays.router, prefix="/api", tags=["Saved Parlays"])
app.include_router(saved_parlay_verification.router, prefix="/api", tags=["Verification Records"])
app.include_router(parlays_results.router, prefix="/api", tags=["Parlay Results"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(me.router, prefix="/api/me", tags=["Me"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(social.router, prefix="/api/social", tags=["Social"])
app.include_router(variants.router, prefix="/api/parlay/variants", tags=["Parlay Variants"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(analysis_feed.router, prefix="/api", tags=["Analysis Feed"])
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(parlay_extended.router, prefix="/api", tags=["Parlay Extended"])
app.include_router(team_stats.router, prefix="/api", tags=["Team Stats"])
app.include_router(scraper.router, prefix="/api", tags=["Scraper"])
app.include_router(user.router, prefix="/api", tags=["User"])
app.include_router(events.router, prefix="/api", tags=["Events"])
app.include_router(leaderboards.router, prefix="/api", tags=["Leaderboards"])
app.include_router(verification_records.router, prefix="/api", tags=["Verification Records"])
app.include_router(upset_finder.router, prefix="/api", tags=["Upsets"])
app.include_router(admin_router, prefix="/api", tags=["Admin"])
app.include_router(redirects.router, tags=["Redirects"])
app.include_router(billing.router, prefix="/api", tags=["Billing"])
app.include_router(webhooks.router, prefix="/api", tags=["Webhooks"])
app.include_router(profile.router, prefix="/api", tags=["Profile"])
app.include_router(subscription.router, prefix="/api", tags=["Subscription"])
app.include_router(notifications.router, prefix="/api", tags=["Notifications"])
app.include_router(promo_codes.router, prefix="/api", tags=["Promo Codes"])
app.include_router(live_games.router, tags=["Live Games"])
app.include_router(parlay_tips.router, tags=["Parlay Tips"])
app.include_router(affiliate.router, prefix="/api", tags=["Affiliate"])
app.include_router(gorilla_bot.router, prefix="/api", tags=["Gorilla Bot"])
app.include_router(meta.router, prefix="/api/meta", tags=["Meta"])
app.include_router(tools.router, prefix="/api", tags=["Tools"])
app.include_router(feed.router, prefix="/api/v1", tags=["Feed"])
app.include_router(system.router, prefix="/api/v1", tags=["System"])
app.include_router(internal_metrics.router, prefix="/api/internal", tags=["Internal"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    from app.database.session import engine, Base, is_sqlite
    from sqlalchemy import text
    # Ensure ALL models are imported before create_all so new tables are created in dev/SQLite.
    # In production we rely on migrations, but dev uses create_all on startup.
    import app.models  # noqa: F401
    
    # Try to connect to database, but don't fail startup if it's unavailable
    try:
        # PostgreSQL: apply migrations (create_all does not add columns, and drift breaks auth).
        if not is_sqlite:
            from app.database.alembic_migration_manager import AlembicMigrationManager

            await AlembicMigrationManager().upgrade_head_async()

        async with engine.begin() as conn:
            if is_sqlite:
                # Create tables (SQLite/dev fallback). For PostgreSQL we rely on Alembic.
                await conn.run_sync(Base.metadata.create_all)
            
            # Check and fix schema drift in dev/SQLite (create_all does not add columns)
            try:
                if is_sqlite:
                    from app.database.sqlite_schema_patcher import SqliteSchemaPatcher

                    patcher = SqliteSchemaPatcher(conn)
                    await patcher.ensure_dev_schema()
                else:
                    # PostgreSQL: Use information_schema
                    # Check if password_hash column exists
                    result = await conn.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='users' AND column_name='password_hash'
                    """))
                    has_password_hash = result.scalar() is not None
                    
                    if not has_password_hash:
                        print("[STARTUP] Adding password_hash column to users table...")
                        await conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
                    
                    # Check required columns from migration 008
                    required_cols = [
                        'free_parlays_total', 'free_parlays_used', 'subscription_plan',
                        'subscription_status', 'subscription_renewal_date', 
                        'subscription_last_billed_at', 'daily_parlays_used',
                        'daily_parlays_usage_date', 'credit_balance'
                    ]
                    
                    for col_name in required_cols:
                        result = await conn.execute(text("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name='users' AND column_name=:col_name
                        """), {"col_name": col_name})
                        if result.scalar() is None:
                            print(f"[STARTUP] Warning: Column {col_name} is missing. Run: alembic upgrade head")
                    
            except Exception as schema_error:
                # If it's SQLite or schema check fails, that's OK
                if 'sqlite' not in str(engine.url).lower():
                    print(f"[STARTUP] Schema check warning: {schema_error}")
        
        print("[STARTUP] Database connection successful")
    except Exception as db_error:
        print(f"[STARTUP] Warning: Database connection failed: {db_error}")
        print("[STARTUP] Server will continue, but database-dependent features may not work")
        print("[STARTUP] Health endpoint and other non-database endpoints will still function")
        print("[STARTUP] To fix: Start PostgreSQL with 'docker-compose up -d postgres' or set USE_SQLITE=true")

        # In production, continuing without PostgreSQL is a broken state (auth/usage depend on DB).
        if settings.is_production and not is_sqlite:
            raise
    
    # Start background scheduler (will handle its own database connection errors)
    try:
        from app.services.scheduler import get_scheduler
        scheduler = get_scheduler()
        await scheduler.start()
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
    await scheduler.stop()
    
    from app.database.session import engine
    await engine.dispose()

