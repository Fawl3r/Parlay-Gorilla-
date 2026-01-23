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

router = APIRouter(prefix="/games", tags=["games"])


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
        query = select(Game)
        
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
        
        # Order by start time
        query = query.order_by(Game.start_time)
        
        result = await db.execute(query)
        games = result.scalars().all()
        
        return [
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
                is_stale=game.is_stale if hasattr(game, "is_stale") else False,
            )
            for game in games
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching game feed: {str(e)}")
