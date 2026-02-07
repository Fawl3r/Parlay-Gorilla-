"""
Minimal game row queries for candidate leg building (no ORM relationship loading).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game


async def fetch_minimal_game_rows(
    db: AsyncSession,
    *,
    sport: str,
    cutoff_time: datetime,
    future_cutoff: datetime,
    scheduled_statuses: Tuple[str, ...] = ("scheduled", "status_scheduled"),
    limit: int = 20,
) -> List[dict]:
    """
    Fetch minimal game rows (no markets/odds). Returns list of dicts with:
    id, sport, start_time, status, home_team, away_team, external_game_id.
    """
    q = (
        select(
            Game.id,
            Game.sport,
            Game.start_time,
            Game.status,
            Game.home_team,
            Game.away_team,
            Game.external_game_id,
        )
        .where(Game.sport == sport)
        .where(Game.start_time >= cutoff_time)
        .where(Game.start_time <= future_cutoff)
        .where(or_(Game.status.is_(None), func.lower(Game.status).in_(scheduled_statuses)))
        .order_by(Game.start_time)
        .limit(limit)
    )
    result = await db.execute(q)
    rows = result.all()
    return [
        {
            "id": r.id,
            "sport": r.sport,
            "start_time": r.start_time,
            "status": r.status,
            "home_team": r.home_team,
            "away_team": r.away_team,
            "external_game_id": r.external_game_id,
        }
        for r in rows
    ]
