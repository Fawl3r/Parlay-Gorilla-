"""
API-Sports Results Fetcher

Fetches completed game results from API-Sports and stores them in the database.
Supports date-based and week-based sports.

This service is called by the background refresh job, not from user-facing endpoints.
"""

from __future__ import annotations

import logging
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.sports_data_repository import SportsDataRepository
from app.services.apisports.client import get_apisports_client
from app.services.apisports.data_adapter import ApiSportsDataAdapter

logger = logging.getLogger(__name__)


class ApiSportsResultsFetcher:
    """
    Fetches completed game results from API-Sports.
    
    Supports:
    - Date-based sports (NBA, NHL, MLB, Soccer): fetch by date range
    - Week-based sports (NFL): fetch by season/week (via fixtures filtered by status)
    """
    
    def __init__(self, db: AsyncSession):
        self._db = db
        self._repo = SportsDataRepository(db)
        self._client = get_apisports_client()
        self._adapter = ApiSportsDataAdapter()
    
    async def fetch_results_by_date_range(
        self,
        sport: str,
        league_id: int,
        from_date: date,
        to_date: date,
        season: Optional[int] = None
    ) -> int:
        """
        Fetch completed game results for a date range.
        
        Args:
            sport: Sport key (e.g., "basketball_nba", "icehockey_nhl", "baseball_mlb", "football")
            league_id: API-Sports league ID
            from_date: Start date
            to_date: End date
            season: Optional season year
        
        Returns:
            Number of results fetched and stored
        """
        if not self._client.is_configured():
            logger.warning("ApiSportsResultsFetcher: API-Sports not configured")
            return 0
        
        from_str = from_date.strftime("%Y-%m-%d")
        to_str = to_date.strftime("%Y-%m-%d")
        
        # Fetch fixtures for the date range, then filter for completed games
        data = await self._client.get_fixtures(
            league_id=league_id,
            season=season,
            from_date=from_str,
            to_date=to_str
        )
        
        if not data or not isinstance(data.get("response"), list):
            logger.warning(f"No fixtures data returned for {sport} league {league_id} from {from_str} to {to_str}")
            return 0
        
        fixtures = data["response"]
        results = []
        
        for fixture in fixtures:
            # Check if game is completed
            fixture_obj = fixture.get("fixture", {}) if isinstance(fixture.get("fixture"), dict) else {}
            status_obj = fixture_obj.get("status", {}) if isinstance(fixture_obj.get("status"), dict) else {}
            status_short = status_obj.get("short", "").upper()
            
            # Completed statuses: FT (Full Time), AET (After Extra Time), PEN (Penalties), etc.
            if status_short in ["FT", "AET", "PEN", "CANC", "SUSP", "INT", "ABAN", "AWARDED"]:
                # Extract score
                score_obj = fixture.get("score", {}) if isinstance(fixture.get("score"), dict) else {}
                fulltime_score = score_obj.get("fulltime", {}) if isinstance(score_obj.get("fulltime"), dict) else {}
                home_score = fulltime_score.get("home")
                away_score = fulltime_score.get("away")
                
                # Only include if we have scores
                if home_score is not None and away_score is not None:
                    results.append(fixture)
        
        if not results:
            logger.info(f"No completed games found for {sport} league {league_id} from {from_str} to {to_str}")
            return 0
        
        # Store results
        count = await self._repo.upsert_results(
            sport=sport,
            results=results,
            stale_after_seconds=86400 * 7,  # Results don't change, cache for 7 days
        )
        
        logger.info(f"Fetched and stored {count} completed game results for {sport} league {league_id}")
        return count
    
    async def fetch_results_for_team(
        self,
        sport: str,
        team_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch completed game results for a specific team.
        
        Args:
            sport: Sport key
            team_id: API-Sports team ID
            from_date: Optional start date
            to_date: Optional end date
        
        Returns:
            List of result dicts in internal format
        """
        results = await self._repo.get_results(
            sport=sport,
            from_date=from_date,
            to_date=to_date,
            team_id=team_id
        )
        
        # Convert to internal format
        internal_results = []
        for result in results:
            if result.home_score is not None and result.away_score is not None:
                internal_results.append({
                    "fixture_id": result.fixture_id,
                    "home_team_id": result.home_team_id,
                    "away_team_id": result.away_team_id,
                    "home_score": result.home_score,
                    "away_score": result.away_score,
                    "finished_at": result.finished_at,
                    "sport": sport,
                })
        
        return internal_results
    
    async def fetch_recent_results(
        self,
        sport: str,
        league_id: int,
        days_back: int = 30,
        season: Optional[int] = None
    ) -> int:
        """
        Fetch recent completed game results (last N days).
        
        Args:
            sport: Sport key
            league_id: API-Sports league ID
            days_back: Number of days to look back
            season: Optional season year
        
        Returns:
            Number of results fetched
        """
        to_date = date.today()
        from_date = to_date - timedelta(days=days_back)
        
        return await self.fetch_results_by_date_range(
            sport=sport,
            league_id=league_id,
            from_date=from_date,
            to_date=to_date,
            season=season
        )
