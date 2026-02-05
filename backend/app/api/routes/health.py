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
        # Database is unhealthy - return 503 and alert operators
        error_msg = str(e)[:100]  # Truncate long error messages
        try:
            from app.services.alerting import get_alerting_service
            await get_alerting_service().emit(
                "database.connection_error",
                "critical",
                {
                    "environment": getattr(settings, "environment", "unknown"),
                    "error_type": type(e).__name__,
                    "error_message": error_msg,
                },
            )
        except Exception:
            pass  # Never let alerting break health response
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


@router.get("/health/games")
async def health_games(request: Request):
    """Database state diagnostic endpoint for games/odds.
    
    Returns:
        - Total games by sport
        - Games with markets/odds
        - Games in "scheduled" status
        - Date range of available games
        - Helps diagnose "not enough games" errors
    """
    from fastapi import status
    from datetime import timezone
    from app.database.session import AsyncSessionLocal
    from app.models.game import Game
    from app.models.market import Market
    from sqlalchemy import select, func, or_
    from datetime import datetime, timedelta
    
    try:
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            future_cutoff = now + timedelta(days=14)
            past_cutoff = now - timedelta(days=7)
            
            # Get total games by sport
            result = await db.execute(
                select(Game.sport, func.count(Game.id).label("count"))
                .group_by(Game.sport)
            )
            games_by_sport = {row.sport: row.count for row in result.all()}
            
            # Get scheduled games by sport
            scheduled_statuses = ("scheduled", "status_scheduled")
            result = await db.execute(
                select(Game.sport, func.count(Game.id).label("count"))
                .where(or_(Game.status.is_(None), func.lower(Game.status).in_(scheduled_statuses)))
                .group_by(Game.sport)
            )
            scheduled_by_sport = {row.sport: row.count for row in result.all()}
            
            # Get upcoming games (next 14 days) by sport
            result = await db.execute(
                select(Game.sport, func.count(Game.id).label("count"))
                .where(Game.start_time >= now)
                .where(Game.start_time <= future_cutoff)
                .where(or_(Game.status.is_(None), func.lower(Game.status).in_(scheduled_statuses)))
                .group_by(Game.sport)
            )
            upcoming_by_sport = {row.sport: row.count for row in result.all()}
            
            # Get games with markets by sport
            result = await db.execute(
                select(Game.sport, func.count(func.distinct(Game.id)).label("count"))
                .join(Market, Market.game_id == Game.id)
                .where(Game.start_time >= past_cutoff)
                .where(Game.start_time <= future_cutoff)
                .group_by(Game.sport)
            )
            games_with_markets_by_sport = {row.sport: row.count for row in result.all()}
            
            # Get date ranges for each sport
            date_ranges = {}
            for sport in games_by_sport.keys():
                result = await db.execute(
                    select(
                        func.min(Game.start_time).label("earliest"),
                        func.max(Game.start_time).label("latest")
                    )
                    .where(Game.sport == sport)
                    .where(Game.start_time >= past_cutoff)
                    .where(Game.start_time <= future_cutoff)
                )
                row = result.first()
                if row and row.earliest and row.latest:
                    date_ranges[sport] = {
                        "earliest": row.earliest.isoformat(),
                        "latest": row.latest.isoformat(),
                    }
            
            response_data = {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "games": {
                    "total_by_sport": games_by_sport,
                    "scheduled_by_sport": scheduled_by_sport,
                    "upcoming_by_sport": upcoming_by_sport,
                    "with_markets_by_sport": games_with_markets_by_sport,
                    "date_ranges": date_ranges,
                },
                "query_window": {
                    "past_days": 7,
                    "future_days": 14,
                    "now": now.isoformat(),
                },
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
                status_code=status.HTTP_200_OK,
                headers=headers
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in games health check: {e}", exc_info=True)
        
        response_data = {
            "status": "error",
            "error": str(e)[:200],
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            headers=headers
        )


@router.get("/health/parlay-generation")
async def health_parlay_generation(request: Request):
    """Diagnostic endpoint for parlay generation: window, games in window, markets, placeholders, candidate legs (bounded)."""
    from fastapi import status
    from datetime import timezone
    from app.database.session import AsyncSessionLocal
    from app.models.game import Game
    from sqlalchemy import select, or_
    from sqlalchemy.orm import selectinload
    from app.services.probability_engine_impl.candidate_window_resolver import resolve_candidate_window
    from app.services.season_state_service import SeasonStateService
    from app.utils.placeholders import is_placeholder_team

    sport = request.query_params.get("sport", "NFL").upper()
    max_candidate_sample = min(100, max(0, int(request.query_params.get("max_candidates", "50"))))

    try:
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            season_svc = SeasonStateService(db)
            season_state = await season_svc.get_season_state(sport, now_utc=now)
            window_start, window_end, mode = resolve_candidate_window(
                sport,
                requested_week=None,
                now_utc=now,
                season_state=season_state,
                trace_id=None,
            )
            result = await db.execute(
                select(Game)
                .where(Game.sport == sport)
                .where(Game.start_time >= window_start)
                .where(Game.start_time <= window_end)
                .order_by(Game.start_time)
                .limit(500)
                .options(selectinload(Game.markets))
            )
            games = result.scalars().all()
        games_in_window = len(games)
        games_with_markets = sum(1 for g in games if getattr(g, "markets", None) and len(getattr(g, "markets", []) or []) > 0)
        total_markets = sum(len(getattr(g, "markets", []) or []) for g in games)
        placeholder_count = sum(
            1 for g in games
            if is_placeholder_team(getattr(g, "home_team", None) or "")
            or is_placeholder_team(getattr(g, "away_team", None) or "")
        )
        candidate_leg_count = None
        try:
            from app.services.probability_engine import get_probability_engine
            async with AsyncSessionLocal() as db:
                engine = get_probability_engine(db, sport)
                candidates = await engine.get_candidate_legs(
                    sport=sport,
                    week=None,
                    include_player_props=False,
                    trace_id=None,
                    now_utc=now,
                )
                candidate_leg_count = min(len(candidates), max_candidate_sample)
        except Exception:
            pass

        response_data = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sport": sport,
            "window": {
                "start": window_start.isoformat(),
                "end": window_end.isoformat(),
                "mode": mode,
            },
            "games_in_window": games_in_window,
            "markets_coverage": {
                "games_with_markets": games_with_markets,
                "total_markets": total_markets,
            },
            "placeholder_count": placeholder_count,
            "candidate_leg_count": candidate_leg_count,
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
        return JSONResponse(content=response_data, status_code=status.HTTP_200_OK, headers=headers)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Error in parlay-generation health check: %s", e, exc_info=True)
        response_data = {
            "status": "error",
            "error": str(e)[:200],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sport": sport,
        }
        return JSONResponse(
            content=response_data,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
