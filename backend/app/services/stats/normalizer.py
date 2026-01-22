"""Normalization service to convert raw snapshots to canonical format and update current tables."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.stats.schemas.canonical_stats import normalize_stats
from app.services.stats.schemas.canonical_injuries import normalize_injuries
from app.services.sports.sport_registry import get_sport_capability


class StatsNormalizer:
    """Normalizes raw stats and injury data to canonical format."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def normalize_and_update_stats(
        self,
        team_name: str,
        sport: str,
        season: str,
        raw_stats: Dict,
    ) -> Dict:
        """Normalize raw stats and update team_stats_current table.
        
        Args:
            team_name: Team name
            sport: Sport identifier
            season: Season year
            raw_stats: Raw stats dictionary from snapshot
        
        Returns:
            Normalized canonical stats dictionary
        """
        # Normalize to canonical format
        normalized = normalize_stats(raw_stats, sport)
        
        # Upsert into team_stats_current
        await self.db.execute(
            text("""
                INSERT INTO team_stats_current
                (team_name, sport, season, updated_at, metrics_json)
                VALUES
                (:team_name, :sport, :season, :updated_at, :metrics_json)
                ON CONFLICT (team_name, sport, season)
                DO UPDATE SET
                    updated_at = :updated_at,
                    metrics_json = :metrics_json
            """),
            {
                "team_name": team_name,
                "sport": sport,
                "season": season,
                "updated_at": datetime.utcnow(),
                "metrics_json": normalized,
            }
        )
        await self.db.flush()
        
        return normalized
    
    async def normalize_and_update_injuries(
        self,
        team_name: str,
        sport: str,
        season: str,
        raw_injuries: Dict,
    ) -> Dict:
        """Normalize raw injuries and update injury_current table.
        
        Args:
            team_name: Team name
            sport: Sport identifier
            season: Season year
            raw_injuries: Raw injury dictionary from snapshot
        
        Returns:
            Normalized canonical injury dictionary
        """
        # Get sport capability for unit mappings
        capability = get_sport_capability(sport)
        unit_mappings = capability.unit_mappings
        
        # Normalize to canonical format
        normalized = normalize_injuries(raw_injuries, sport, unit_mappings)
        
        # Upsert into injury_current
        await self.db.execute(
            text("""
                INSERT INTO injury_current
                (team_name, sport, season, updated_at, injury_json)
                VALUES
                (:team_name, :sport, :season, :updated_at, :injury_json)
                ON CONFLICT (team_name, sport, season)
                DO UPDATE SET
                    updated_at = :updated_at,
                    injury_json = :injury_json
            """),
            {
                "team_name": team_name,
                "sport": sport,
                "season": season,
                "updated_at": datetime.utcnow(),
                "injury_json": normalized,
            }
        )
        await self.db.flush()
        
        return normalized
    
    async def get_current_stats(
        self,
        team_name: str,
        sport: str,
        season: str,
    ) -> Optional[Dict]:
        """Get current canonical stats for a team.
        
        Args:
            team_name: Team name
            sport: Sport identifier
            season: Season year
        
        Returns:
            Canonical stats dictionary or None if not found
        """
        result = await self.db.execute(
            text("""
                SELECT metrics_json, updated_at FROM team_stats_current
                WHERE team_name = :team_name
                  AND sport = :sport
                  AND season = :season
            """),
            {
                "team_name": team_name,
                "sport": sport,
                "season": season,
            }
        )
        row = result.fetchone()
        if row:
            return row[0]  # metrics_json
        return None
    
    async def get_current_injuries(
        self,
        team_name: str,
        sport: str,
        season: str,
    ) -> Optional[Dict]:
        """Get current canonical injuries for a team.
        
        Args:
            team_name: Team name
            sport: Sport identifier
            season: Season year
        
        Returns:
            Canonical injury dictionary or None if not found
        """
        result = await self.db.execute(
            text("""
                SELECT injury_json, updated_at FROM injury_current
                WHERE team_name = :team_name
                  AND sport = :sport
                  AND season = :season
            """),
            {
                "team_name": team_name,
                "sport": sport,
                "season": season,
            }
        )
        row = result.fetchone()
        if row:
            return row[0]  # injury_json
        return None
