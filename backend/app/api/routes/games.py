"""Game feed endpoints."""

from __future__ import annotations

from typing import List, Literal, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.game import Game
from app.schemas.games import GameFeedResponse
from app.services.games_deduplication_service import GamesDeduplicationService

router = APIRouter(prefix="/games", tags=["games"])


def build_feed_response(games: List[Game]) -> List[GameFeedResponse]:
    """Build feed response list, skipping games with NULL start_time (avoids 500s)."""
    out = []
    for game in games:
        if game.start_time is None:
            continue
        out.append(
            GameFeedResponse(
                id=str(game.id),
                sport=game.sport,
                home_team=game.home_team,
                away_team=game.away_team,
                start_time=game.start_time.isoformat(),
                status=game.status,
                home_score=game.home_score,
                away_score=game.away_score,
                period=game.period,
                clock=game.clock,
                is_stale=bool(getattr(game, "is_stale", None) or False),
            )
        )
    return out


@router.get("/feed", response_model=List[GameFeedResponse])
async def get_game_feed(
    sport: Optional[str] = Query(None, description="Filter by sport code (NFL, NBA, etc.)"),
    window: Literal["today", "upcoming", "live", "all"] = Query("today", description="Time window filter"),
    db: AsyncSession = Depends(get_db),
):
    """Get game feed with scores and status.
    
    Returns games filtered by sport and window:
    - today: Games today (yesterday to tomorrow)
    - upcoming: Future games
    - live: Currently live games
    - all: All games in date range
    """
    try:
        now = datetime.utcnow()
        query = select(Game).where(Game.start_time.isnot(None))
        
        # Apply sport filter
        if sport:
            query = query.where(Game.sport == sport.upper())
        
        # Apply window filter
        if window == "today":
            yesterday = now - timedelta(days=1)
            tomorrow = now + timedelta(days=1)
            query = query.where(
                and_(
                    Game.start_time >= yesterday,
                    Game.start_time <= tomorrow,
                )
            )
        elif window == "upcoming":
            query = query.where(Game.start_time > now)
        elif window == "live":
            query = query.where(Game.status == "LIVE")
        # "all" doesn't add time filter
        
        # Deterministic ordering: soonest first (stable, reduces jitter)
        query = query.order_by(Game.start_time.asc())
        
        result = await db.execute(query)
        games = result.scalars().all()
        deduped = GamesDeduplicationService().dedupe(games)
        return build_feed_response(deduped)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching game feed: {str(e)}")
