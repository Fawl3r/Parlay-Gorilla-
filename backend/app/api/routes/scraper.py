"""Scraper API routes for manual updates"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.dependencies import get_db
from app.services.stats_scraper import StatsScraperService
from app.services.odds_fetcher import OddsFetcherService
from app.services.sports_config import get_sport_config

router = APIRouter()


@router.post("/scraper/update")
async def trigger_scraper_update(
    sport: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger scraper update for odds and stats
    
    Args:
        sport: Optional sport to update (nfl, nba, mlb, nhl). If None, updates all.
    """
    try:
        if sport:
            # Update specific sport
            sport_config = get_sport_config(sport)
            fetcher = OddsFetcherService(db)
            
            # Fetch and store odds
            api_data = await fetcher.fetch_odds_for_sport(sport_config)
            if api_data:
                await fetcher.normalize_and_store_odds(api_data, sport_config)
                await db.commit()
            
            return {
                "message": f"Successfully updated {sport.upper()} odds and stats",
                "sport": sport,
                "games_updated": len(api_data) if api_data else 0,
            }
        else:
            # Update all sports
            sports = ["americanfootball_nfl", "basketball_nba", "icehockey_nhl", "baseball_mlb"]
            total_games = 0
            
            for sport_key in sports:
                try:
                    sport_config = get_sport_config(sport_key)
                    fetcher = OddsFetcherService(db)
                    
                    api_data = await fetcher.fetch_odds_for_sport(sport_config)
                    if api_data:
                        await fetcher.normalize_and_store_odds(api_data, sport_config)
                        total_games += len(api_data)
                except Exception as e:
                    print(f"Error updating {sport_key}: {e}")
                    continue
            
            await db.commit()
            
            return {
                "message": "Successfully updated all sports",
                "total_games_updated": total_games,
            }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update scrapers: {str(e)}")


@router.post("/scraper/update-stats")
async def trigger_stats_update(
    sport: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger team stats scraper update
    """
    try:
        scraper = StatsScraperService()
        
        if sport:
            # Update specific sport
            stats = await scraper.fetch_team_stats(sport)
            return {
                "message": f"Successfully updated {sport.upper()} team stats",
                "stats_count": len(stats) if stats else 0,
            }
        else:
            # Update all sports
            sports = ["nfl", "nba", "nhl", "mlb"]
            total_stats = 0
            
            for sport_key in sports:
                try:
                    stats = await scraper.fetch_team_stats(sport_key)
                    total_stats += len(stats) if stats else 0
                except Exception as e:
                    print(f"Error updating {sport_key} stats: {e}")
                    continue
            
            return {
                "message": "Successfully updated all team stats",
                "total_stats_updated": total_stats,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update stats: {str(e)}")

