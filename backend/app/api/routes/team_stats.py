"""Team statistics API routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.dependencies import get_db
from app.models.team_stats import TeamStats
from app.schemas.team_stats import TeamStatsResponse

router = APIRouter()


@router.get("/team-stats/{sport}/{team}", response_model=TeamStatsResponse)
async def get_team_stats(
    sport: str,
    team: str,
    season: Optional[str] = None,
    week: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get team statistics for a specific team
    
    Args:
        sport: Sport code (nfl, nba, mlb, nhl)
        team: Team name (e.g., "Kansas City Chiefs")
        season: Season year (e.g., "2024") - defaults to current season
        week: Week number (for NFL) - if None, returns season totals
    """
    try:
        # Normalize team name (handle URL encoding)
        team_name = team.replace("-", " ").replace("_", " ").title()
        
        # Build query
        query = select(TeamStats).where(
            TeamStats.team_name == team_name,
            TeamStats.season == (season or "2024"),
        )
        
        if week is not None:
            query = query.where(TeamStats.week == week)
        else:
            query = query.where(TeamStats.week.is_(None))  # Season totals
        
        result = await db.execute(query)
        stats = result.scalar_one_or_none()
        
        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"Team stats not found for {team_name} in {season or '2024'}"
            )
        
        return TeamStatsResponse(
            id=str(stats.id),
            team_name=stats.team_name,
            season=stats.season,
            week=stats.week,
            wins=stats.wins,
            losses=stats.losses,
            ties=stats.ties,
            win_percentage=float(stats.win_percentage),
            points_per_game=float(stats.points_per_game),
            yards_per_game=float(stats.yards_per_game),
            points_allowed_per_game=float(stats.points_allowed_per_game),
            ats_record_overall=f"{stats.ats_wins}-{stats.ats_losses}-{stats.ats_pushes}",
            ats_record_home=f"{stats.ats_home_wins}-{stats.ats_home_losses}",
            ats_record_away=f"{stats.ats_away_wins}-{stats.ats_away_losses}",
            ou_record_overall=f"{stats.over_wins}-{stats.under_wins}",
            ou_record_home=f"{stats.over_wins}-{stats.under_wins}",  # Simplified
            ou_record_away=f"{stats.over_wins}-{stats.under_wins}",  # Simplified
            offensive_rating=float(stats.offensive_rating),
            defensive_rating=float(stats.defensive_rating),
            overall_rating=float(stats.overall_rating),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team stats: {str(e)}")

