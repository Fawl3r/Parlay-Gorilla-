"""Utilities to clear in-process caches when fresh data arrives."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cache_manager import CacheManager


def clear_games_cache():
    """Clear in-memory games cache (used by /api/games)."""
    try:
        from app.api.routes.games_response_cache import games_response_cache

        games_response_cache.clear()
    except Exception:
        # Fails silently; cache will naturally expire
        pass


def clear_analysis_cache():
    """Clear in-memory analysis list cache (used by /api/analysis/{sport}/upcoming)."""
    try:
        from app.api.routes import analysis as analysis_routes

        analysis_routes._analysis_list_cache.clear()
    except Exception:
        pass


async def clear_parlay_cache(db: AsyncSession, sport: Optional[str] = None):
    """Clear parlay cache (DB + in-memory)."""
    try:
        manager = CacheManager(db)
        await manager.clear_cache_for_params(sport=sport)
        manager.clear_memory_cache()
    except Exception:
        pass


async def invalidate_after_odds_update(db: AsyncSession, sport: Optional[str] = None):
    """Clear caches that depend on fresh odds/games data."""
    clear_games_cache()
    clear_analysis_cache()
    await clear_parlay_cache(db, sport=sport)


async def invalidate_after_stats_update(db: AsyncSession, sport: Optional[str] = None):
    """Clear caches that depend on fresh team stats data."""
    # Clear analysis cache so fresh analyses are shown
    clear_analysis_cache()
    
    # Clear StatsScraperService cache (in-memory)
    # Note: This requires a StatsScraperService instance, but we can't easily access all instances
    # The cache will naturally expire with the reduced TTL (15 minutes)
    # For immediate effect, we'd need to track instances or use a shared cache
    
    # Clear parlay cache since it depends on team stats
    await clear_parlay_cache(db, sport=sport)
    
    print(f"[CACHE] Invalidated caches after stats update for {sport or 'all sports'}")


