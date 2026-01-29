"""Snapshot management service for immutable stats and injury data storage."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.types import GUID


class SnapshotManager:
    """Manages immutable snapshots of stats and injury data."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _compute_hash(self, data: Dict) -> str:
        """Compute SHA256 hash of JSON data for deduplication."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    async def save_stats_snapshot(
        self,
        team_name: str,
        sport: str,
        season: str,
        source: str,
        raw_json: Dict,
    ) -> Optional[str]:
        """Save immutable stats snapshot.
        
        Args:
            team_name: Team name
            sport: Sport identifier
            season: Season year
            source: Source identifier (e.g., "api_espn", "api_sports")
            raw_json: Raw stats data as dictionary
        
        Returns:
            Snapshot ID if saved, None if duplicate (hash already exists)
        """
        # Compute hash
        hash_value = self._compute_hash(raw_json)
        
        # Check if hash already exists for this team/sport/season/source
        from sqlalchemy import text
        result = await self.db.execute(
            text("""
                SELECT id FROM team_stats_snapshots
                WHERE team_name = :team_name
                  AND sport = :sport
                  AND season = :season
                  AND source = :source
                  AND hash = :hash
                LIMIT 1
            """),
            {
                "team_name": team_name,
                "sport": sport,
                "season": season,
                "source": source,
                "hash": hash_value,
            }
        )
        existing = result.scalar_one_or_none()
        if existing:
            return None  # Duplicate, skip insert
        
        # Insert new snapshot
        snapshot_id = uuid4()
        await self.db.execute(
            text("""
                INSERT INTO team_stats_snapshots
                (id, team_name, sport, season, source, collected_at, raw_json, hash)
                VALUES
                (:id, :team_name, :sport, :season, :source, :collected_at, :raw_json, :hash)
            """),
            {
                "id": snapshot_id,
                "team_name": team_name,
                "sport": sport,
                "season": season,
                "source": source,
                "collected_at": datetime.utcnow(),
                "raw_json": json.dumps(raw_json),
                "hash": hash_value,
            }
        )
        await self.db.flush()
        return str(snapshot_id)
    
    async def save_injury_snapshot(
        self,
        team_name: str,
        sport: str,
        season: str,
        source: str,
        raw_json: Dict,
    ) -> Optional[str]:
        """Save immutable injury snapshot.
        
        Args:
            team_name: Team name
            sport: Sport identifier
            season: Season year
            source: Source identifier
            raw_json: Raw injury data as dictionary
        
        Returns:
            Snapshot ID if saved, None if duplicate (hash already exists)
        """
        # Compute hash
        hash_value = self._compute_hash(raw_json)
        
        # Check if hash already exists
        from sqlalchemy import text
        result = await self.db.execute(
            text("""
                SELECT id FROM injury_snapshots
                WHERE team_name = :team_name
                  AND sport = :sport
                  AND season = :season
                  AND source = :source
                  AND hash = :hash
                LIMIT 1
            """),
            {
                "team_name": team_name,
                "sport": sport,
                "season": season,
                "source": source,
                "hash": hash_value,
            }
        )
        existing = result.scalar_one_or_none()
        if existing:
            return None  # Duplicate, skip insert
        
        # Insert new snapshot
        snapshot_id = uuid4()
        await self.db.execute(
            text("""
                INSERT INTO injury_snapshots
                (id, team_name, sport, season, source, collected_at, raw_json, hash)
                VALUES
                (:id, :team_name, :sport, :season, :source, :collected_at, :raw_json, :hash)
            """),
            {
                "id": snapshot_id,
                "team_name": team_name,
                "sport": sport,
                "season": season,
                "source": source,
                "collected_at": datetime.utcnow(),
                "raw_json": json.dumps(raw_json),
                "hash": hash_value,
            }
        )
        await self.db.flush()
        return str(snapshot_id)
    
    async def get_latest_stats_snapshot(
        self,
        team_name: str,
        sport: str,
        season: str,
        source: Optional[str] = None,
    ) -> Optional[Dict]:
        """Get latest stats snapshot for team/sport/season.
        
        Args:
            team_name: Team name
            sport: Sport identifier
            season: Season year
            source: Optional source filter
        
        Returns:
            Raw JSON data from latest snapshot, or None if not found
        """
        from sqlalchemy import text
        query = """
            SELECT raw_json FROM team_stats_snapshots
            WHERE team_name = :team_name
              AND sport = :sport
              AND season = :season
        """
        params = {
            "team_name": team_name,
            "sport": sport,
            "season": season,
        }
        
        if source:
            query += " AND source = :source"
            params["source"] = source
        
        query += " ORDER BY collected_at DESC LIMIT 1"
        
        result = await self.db.execute(text(query), params)
        row = result.fetchone()
        if row:
            return json.loads(row[0])
        return None
    
    async def get_latest_injury_snapshot(
        self,
        team_name: str,
        sport: str,
        season: str,
        source: Optional[str] = None,
    ) -> Optional[Dict]:
        """Get latest injury snapshot for team/sport/season.
        
        Args:
            team_name: Team name
            sport: Sport identifier
            season: Season year
            source: Optional source filter
        
        Returns:
            Raw JSON data from latest snapshot, or None if not found
        """
        from sqlalchemy import text
        query = """
            SELECT raw_json FROM injury_snapshots
            WHERE team_name = :team_name
              AND sport = :sport
              AND season = :season
        """
        params = {
            "team_name": team_name,
            "sport": sport,
            "season": season,
        }
        
        if source:
            query += " AND source = :source"
            params["source"] = source
        
        query += " ORDER BY collected_at DESC LIMIT 1"
        
        result = await self.db.execute(text(query), params)
        row = result.fetchone()
        if row:
            return json.loads(row[0])
        return None
    
    async def get_stats_snapshot_history(
        self,
        team_name: str,
        sport: str,
        season: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Get stats snapshot history for trend analysis.
        
        Args:
            team_name: Team name
            sport: Sport identifier
            season: Season year
            limit: Maximum number of snapshots to return
        
        Returns:
            List of raw JSON data from snapshots, ordered by collected_at DESC
        """
        from sqlalchemy import text
        result = await self.db.execute(
            text("""
                SELECT raw_json, collected_at FROM team_stats_snapshots
                WHERE team_name = :team_name
                  AND sport = :sport
                  AND season = :season
                ORDER BY collected_at DESC
                LIMIT :limit
            """),
            {
                "team_name": team_name,
                "sport": sport,
                "season": season,
                "limit": limit,
            }
        )
        return [json.loads(row[0]) for row in result.fetchall()]
    
    async def get_injury_snapshot_history(
        self,
        team_name: str,
        sport: str,
        season: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Get injury snapshot history for trend analysis.
        
        Args:
            team_name: Team name
            sport: Sport identifier
            season: Season year
            limit: Maximum number of snapshots to return
        
        Returns:
            List of raw JSON data from snapshots, ordered by collected_at DESC
        """
        from sqlalchemy import text
        result = await self.db.execute(
            text("""
                SELECT raw_json, collected_at FROM injury_snapshots
                WHERE team_name = :team_name
                  AND sport = :sport
                  AND season = :season
                ORDER BY collected_at DESC
                LIMIT :limit
            """),
            {
                "team_name": team_name,
                "sport": sport,
                "season": season,
                "limit": limit,
            }
        )
        return [json.loads(row[0]) for row in result.fetchall()]
