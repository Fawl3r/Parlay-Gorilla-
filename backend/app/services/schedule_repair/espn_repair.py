"""
ESPN repair pass: ensure ESPN rows exist; prefer matches where Game.external_game_id starts with espn:.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.services.espn_schedule_games_service import EspnScheduleGamesService
from app.services.sports_config import SportConfig, get_sport_config
from app.utils.placeholders import is_placeholder_team

logger = logging.getLogger(__name__)


class EspnRepairPass:
    """Repair placeholder team names using ESPN schedule (prefer espn: external_game_id)."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def repair(
        self,
        sport: str,
        placeholder_games: List[Game],
        trace_id: Optional[str] = None,
    ) -> int:
        """
        Ensure ESPN games exist for the sport; for each placeholder game find a match
        (prefer Game.external_game_id.like('espn:%')) in the same time window and copy team names.
        Returns number of games updated.
        """
        if not placeholder_games:
            return 0
        sport_config = get_sport_config(sport)
        if not sport_config:
            return 0
        espn_service = EspnScheduleGamesService(self._db)
        await espn_service.ensure_upcoming_games(sport_config=sport_config)
        updated = 0
        for game in placeholder_games:
            if not game.start_time:
                continue
            time_window_hours = 6 if sport.upper() == "NFL" else 2
            time_window_start = game.start_time - timedelta(hours=time_window_hours)
            time_window_end = game.start_time + timedelta(hours=time_window_hours)
            # Prefer ESPN rows: external_game_id like 'espn:%'
            result = await self._db.execute(
                select(Game)
                .where(Game.sport == sport.upper())
                .where(Game.start_time >= time_window_start)
                .where(Game.start_time <= time_window_end)
                .where(Game.external_game_id.like("espn:%"))
                .where(~Game.home_team.in_(["TBD", "TBA", "AFC", "NFC"]))
                .where(~Game.away_team.in_(["TBD", "TBA", "AFC", "NFC"]))
                .where(Game.id != game.id)
                .order_by(Game.start_time)
                .limit(10)
            )
            candidates = result.scalars().all()
            best = None
            min_diff = None
            for c in candidates:
                if is_placeholder_team(c.home_team) or is_placeholder_team(c.away_team):
                    continue
                diff = abs((c.start_time - game.start_time).total_seconds())
                if best is None or diff < min_diff:
                    best = c
                    min_diff = diff
            if best:
                game.home_team = best.home_team
                game.away_team = best.away_team
                updated += 1
        return updated
