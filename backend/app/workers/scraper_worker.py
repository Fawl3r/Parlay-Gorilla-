"""Scraper worker for fetching stats from ESPN, Covers, Rotowire"""

import asyncio
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.services.stats_scraper import StatsScraperService
from app.services.ats_ou_calculator import ATSOUCalculator
from app.models.team_stats import TeamStats
from app.services.sports_config import get_sport_config
from app.services.cache_invalidation import invalidate_after_stats_update


class ScraperWorker:
    """Background worker for calculating ATS/O/U trends from completed games"""
    
    def __init__(self):
        # StatsScraperService will be initialized with db session when needed
        self.scraper = None
    
    async def run_full_scrape(self, sport: str = None):
        """
        Run full scrape for a sport or all sports
        
        Args:
            sport: Sport to scrape (nfl, nba, mlb, nhl) or None for all
        """
        sports = [sport] if sport else ["nfl", "nba", "mlb", "nhl"]
        
        async with AsyncSessionLocal() as db:
            # Initialize scraper with database session
            self.scraper = StatsScraperService(db)
            
            for sport_key in sports:
                try:
                    print(f"[SCRAPER_WORKER] Processing {sport_key.upper()}...")
                    
                    # Fetch and store basic team stats (offensive/defensive) for all teams
                    await self._fetch_and_store_team_stats(db, sport_key)
                    
                    # Calculate ATS/O/U trends (this is the main purpose - updating trends from completed games)
                    await self._calculate_ats_ou_trends(db, sport_key)
                    
                    # Scrape injuries for teams in this sport
                    await self._scrape_injuries(db, sport_key)
                    
                    # Clear caches after stats update to ensure fresh data in analyses
                    self.scraper.clear_cache()  # Clear StatsScraperService in-memory cache
                    await invalidate_after_stats_update(db, sport=sport_key)
                    
                    # Commit all changes for this sport
                    await db.commit()
                        
                except Exception as e:
                    print(f"[SCRAPER_WORKER] Error processing {sport_key}: {e}")
                    import traceback
                    traceback.print_exc()
                    await db.rollback()
                    continue
    
    async def _fetch_and_store_team_stats(self, db: AsyncSession, sport: str):
        """
        Fetch and store basic team stats (offensive/defensive) for all teams in a sport
        
        Args:
            db: Database session
            sport: Sport code (nfl, nba, mlb, nhl)
        """
        try:
            sport_upper = sport.upper()
            current_year = datetime.now().year
            season = str(current_year)
            
            print(f"[SCRAPER_WORKER] Fetching and storing team stats for {sport_upper} {season}...")
            
            # Get list of teams from database
            from sqlalchemy import select, distinct
            from app.models.game import Game
            from app.models.team_stats import TeamStats
            
            # Get all teams from games
            result = await db.execute(
                select(distinct(Game.home_team))
                .where(Game.sport == sport_upper)
            )
            home_teams = [row[0] for row in result.all()]
            
            result = await db.execute(
                select(distinct(Game.away_team))
                .where(Game.sport == sport_upper)
            )
            away_teams = [row[0] for row in result.all()]
            
            # Combine and deduplicate
            all_teams = list(set(home_teams + away_teams))
            
            if not all_teams:
                print(f"[SCRAPER_WORKER] No teams found for {sport_upper}, skipping stats fetch")
                return
            
            print(f"[SCRAPER_WORKER] Found {len(all_teams)} teams for {sport_upper}, fetching stats...")
            
            # Fetch and store stats for each team (with rate limiting via delays)
            stats_fetched = 0
            stats_stored = 0
            
            for idx, team in enumerate(all_teams):
                try:
                    # Add small delay every 10 teams to avoid rate limits
                    if idx > 0 and idx % 10 == 0:
                        await asyncio.sleep(2)  # 2 second pause every 10 teams
                    
                    # Check if stats already exist and are recent (within last 24 hours)
                    result = await db.execute(
                        select(TeamStats)
                        .where(
                            TeamStats.team_name == team,
                            TeamStats.season == season,
                            TeamStats.week.is_(None)
                        )
                    )
                    existing = result.scalar_one_or_none()
                    
                    # Only fetch if stats don't exist or are stale (no offensive stats)
                    if existing and existing.points_per_game > 0:
                        # Stats exist and have data, skip
                        continue
                    
                    # Fetch and store stats
                    stats = await self.scraper.fetch_and_store_team_stats(
                        team_name=team,
                        league=sport_upper,
                        season=season
                    )
                    
                    stats_fetched += 1
                    if stats:
                        stats_stored += 1
                        if idx % 20 == 0:  # Progress update every 20 teams
                            print(f"[SCRAPER_WORKER] Progress: {idx + 1}/{len(all_teams)} teams processed...")
                    
                except Exception as team_error:
                    print(f"[SCRAPER_WORKER] Error fetching stats for {team}: {team_error}")
                    continue
            
            print(f"[SCRAPER_WORKER] [OK] Team stats: {stats_fetched} fetched, {stats_stored} stored for {sport_upper}")
            
        except Exception as e:
            print(f"[SCRAPER_WORKER] Error fetching/storing team stats for {sport}: {e}")
            import traceback
            traceback.print_exc()
            # Don't raise - allow scraper to continue even if stats fetch fails
    
    async def _calculate_ats_ou_trends(self, db: AsyncSession, sport: str):
        """
        Calculate ATS and Over/Under trends for the current season
        
        Args:
            db: Database session
            sport: Sport code (nfl, nba, mlb, nhl)
        """
        try:
            sport_upper = sport.upper()
            current_year = datetime.now().year
            season = str(current_year)
            
            print(f"[SCRAPER_WORKER] Calculating ATS/O/U trends for {sport_upper} {season}...")
            
            calculator = ATSOUCalculator(db, sport=sport_upper)
            
            # Determine season type and parameters based on sport
            if sport_upper in ["NFL", "NBA", "NHL"]:
                # For week-based sports, calculate for current season
                season_type = "REG"  # Regular season
                result = await calculator.calculate_season_trends(
                    season=season,
                    season_type=season_type,
                    weeks=None  # Process all weeks
                )
            elif sport_upper == "MLB":
                # For MLB, use date range for current season
                start_date = date(current_year, 3, 1)  # March 1
                end_date = date(current_year, 11, 1)   # November 1
                result = await calculator.calculate_season_trends(
                    season=season,
                    season_type="REG",
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                # For other sports, skip ATS/O/U calculation
                print(f"[SCRAPER_WORKER] Skipping ATS/O/U calculation for {sport_upper} (not supported)")
                return
            
            games_processed = result.get("games_processed", 0)
            teams_updated = result.get("teams_updated", 0)
            
            if games_processed > 0:
                print(f"[SCRAPER_WORKER] [OK] ATS/O/U trends calculated: {games_processed} games processed, {teams_updated} teams updated")
            else:
                print(f"[SCRAPER_WORKER] [WARN] No games processed for ATS/O/U calculation (may be no completed games yet)")
                
        except Exception as e:
            print(f"[SCRAPER_WORKER] Error calculating ATS/O/U trends for {sport}: {e}")
            import traceback
            traceback.print_exc()
            # Don't raise - allow scraper to continue even if ATS/O/U calc fails
    
    async def _scrape_injuries(self, db: AsyncSession, sport: str):
        """
        Scrape injuries for all teams in a sport
        
        Args:
            db: Database session
            sport: Sport code (nfl, nba, mlb, nhl)
        """
        try:
            sport_upper = sport.upper()
            print(f"[SCRAPER_WORKER] Scraping injuries for {sport_upper} teams...")
            
            # Get list of teams from database (from recent games or team_stats)
            from sqlalchemy import select, distinct
            from app.models.game import Game
            from app.models.team_stats import TeamStats
            
            # Get all teams from games (no limit - need all teams for all matchups)
            result = await db.execute(
                select(distinct(Game.home_team))
                .where(Game.sport == sport_upper)
            )
            home_teams = [row[0] for row in result.all()]
            
            result = await db.execute(
                select(distinct(Game.away_team))
                .where(Game.sport == sport_upper)
            )
            away_teams = [row[0] for row in result.all()]
            
            # Combine and deduplicate
            all_teams = list(set(home_teams + away_teams))
            
            if not all_teams:
                # Fallback: get teams from team_stats (no limit)
                result = await db.execute(
                    select(distinct(TeamStats.team_name))
                    .where(TeamStats.season == str(datetime.now().year))
                )
                all_teams = [row[0] for row in result.all()]
            
            if not all_teams:
                print(f"[SCRAPER_WORKER] No teams found for {sport_upper}, skipping injury scrape")
                return
            
            print(f"[SCRAPER_WORKER] Found {len(all_teams)} teams for {sport_upper}, scraping injuries...")
            
            # Scrape injuries for all teams (with rate limiting via delays)
            injuries_scraped = 0
            teams_with_injuries = 0
            
            for idx, team in enumerate(all_teams):
                try:
                    # Add small delay every 10 teams to avoid rate limits
                    if idx > 0 and idx % 10 == 0:
                        await asyncio.sleep(2)  # 2 second pause every 10 teams
                    
                    injury_report = await self.scraper.get_injury_report(team, sport_upper)
                    injuries_scraped += 1
                    
                    if injury_report and injury_report.get("key_players_out"):
                        teams_with_injuries += 1
                        key_players = len(injury_report.get('key_players_out', []))
                        print(f"[SCRAPER_WORKER] [OK] {team}: {key_players} key player(s) out")
                    elif idx % 20 == 0:  # Progress update every 20 teams
                        print(f"[SCRAPER_WORKER] Progress: {idx + 1}/{len(all_teams)} teams processed...")
                        
                except Exception as team_error:
                    print(f"[SCRAPER_WORKER] Error scraping injuries for {team}: {team_error}")
                    continue
            
            print(f"[SCRAPER_WORKER] [OK] Completed injury scrape: {injuries_scraped}/{len(all_teams)} teams processed, {teams_with_injuries} teams with key players out")
                
        except Exception as e:
            print(f"[SCRAPER_WORKER] Error scraping injuries for {sport}: {e}")
            import traceback
            traceback.print_exc()
            # Don't raise - allow scraper to continue even if injury scrape fails
    


async def run_scraper_worker():
    """Main entry point for scraper worker"""
    worker = ScraperWorker()
    await worker.run_full_scrape()


if __name__ == "__main__":
    asyncio.run(run_scraper_worker())

