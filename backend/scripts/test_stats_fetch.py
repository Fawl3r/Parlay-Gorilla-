"""Test script to verify stats are being fetched from external APIs"""

import asyncio
from datetime import datetime
from app.database.session import AsyncSessionLocal
from app.services.stats_scraper import StatsScraperService

async def test_stats_fetch():
    """Test fetching stats for NFL teams"""
    print("=" * 60)
    print("TESTING STATS FETCH FROM EXTERNAL APIS")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        scraper = StatsScraperService(db)
        
        # Test NFL teams
        home_team = "Tampa Bay Buccaneers"
        away_team = "Atlanta Falcons"
        league = "NFL"
        season = "2024"
        game_time = datetime(2024, 12, 12, 18, 0)
        
        print(f"\n[TEST] Fetching matchup data for:")
        print(f"  Home: {home_team}")
        print(f"  Away: {away_team}")
        print(f"  League: {league}")
        print(f"  Season: {season}")
        
        try:
            matchup_data = await scraper.get_matchup_data(
                home_team=home_team,
                away_team=away_team,
                league=league,
                season=season,
                game_time=game_time
            )
            
            print("\n[RESULTS]")
            print(f"  Home stats: {'FOUND' if matchup_data.get('home_team_stats') else 'NOT FOUND'}")
            print(f"  Away stats: {'FOUND' if matchup_data.get('away_team_stats') else 'NOT FOUND'}")
            
            if matchup_data.get('home_team_stats'):
                home_stats = matchup_data['home_team_stats']
                print(f"\n  Home Team Stats:")
                print(f"    Record: {home_stats.get('record', {})}")
                print(f"    Offense: {home_stats.get('offense', {})}")
                print(f"    Defense: {home_stats.get('defense', {})}")
            
            if matchup_data.get('away_team_stats'):
                away_stats = matchup_data['away_team_stats']
                print(f"\n  Away Team Stats:")
                print(f"    Record: {away_stats.get('record', {})}")
                print(f"    Offense: {away_stats.get('offense', {})}")
                print(f"    Defense: {away_stats.get('defense', {})}")
            
            if not matchup_data.get('home_team_stats') or not matchup_data.get('away_team_stats'):
                print("\n[WARNING] Stats not found - external API fetch may have failed")
                print("  Check logs above for error messages")
            
        except Exception as e:
            print(f"\n[ERROR] Failed to fetch matchup data: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stats_fetch())

