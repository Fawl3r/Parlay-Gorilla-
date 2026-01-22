"""Traffic ranker - determine which games get props based on page views."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_page_views import AnalysisPageViews


class TrafficRanker:
    """Rank games by traffic to enable props gating."""
    
    def __init__(self, db: AsyncSession):
        self._db = db
        self._top_games_cache: Optional[Dict[str, Set[UUID]]] = None
        self._cache_expires_at: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 minutes
    
    async def get_top_game_ids(
        self,
        league: str,
        window_days: int = 2,
        limit: int = 5,
    ) -> List[UUID]:
        """
        Get top game IDs by page views over last N days.
        
        Args:
            league: League code (NFL, NBA, etc.)
            window_days: Number of days to look back
            limit: Maximum number of games to return
            
        Returns:
            List of game IDs (UUIDs)
        """
        # Check cache
        if self._top_games_cache and self._cache_expires_at:
            if datetime.now(tz=timezone.utc) < self._cache_expires_at:
                return list(self._top_games_cache.get(league.upper(), set()))[:limit]
        
        # Query database
        cutoff_date = date.today() - timedelta(days=window_days)
        
        result = await self._db.execute(
            select(
                AnalysisPageViews.game_id,
                func.sum(AnalysisPageViews.views).label("total_views"),
            )
            .where(AnalysisPageViews.league == league.upper())
            .where(AnalysisPageViews.view_bucket_date >= cutoff_date)
            .group_by(AnalysisPageViews.game_id)
            .order_by(func.sum(AnalysisPageViews.views).desc())
            .limit(limit)
        )
        
        game_ids = [row.game_id for row in result.all()]
        
        # Update cache
        if self._top_games_cache is None:
            self._top_games_cache = {}
        self._top_games_cache[league.upper()] = set(game_ids)
        self._cache_expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=self._cache_ttl_seconds)
        
        return game_ids
    
    async def is_props_enabled_for_game(self, game_id: UUID, league: str) -> bool:
        """
        Check if props should be enabled for a game based on traffic rank.
        
        Args:
            game_id: Game UUID
            league: League code
            
        Returns:
            True if game is in top N by traffic, False otherwise
        """
        top_games = await self.get_top_game_ids(league=league, window_days=2, limit=5)
        return game_id in top_games
