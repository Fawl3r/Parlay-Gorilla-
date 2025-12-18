"""Test script to directly test stats fetching for Tampa Bay and Atlanta"""

import asyncio
from datetime import datetime
from app.database.session import AsyncSessionLocal
from app.services.stats_scraper import StatsScraperService

async def test_stats():
    """Test fetching stats for Buccaneers and Falcons"""
    print("=" * 60)
    print("TESTING STATS FETCH FOR BUCCANEERS VS FALCONS")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        scraper = StatsScraperService(db)
        
        home_team = "Tampa Bay Buccaneers"
        away_team = "Atlanta Falcons"
        league = "NFL"
        season = "2024"
        game_time = datetime(2024, 12, 12, 1, 15)
        
        print(f"\n[TEST] Fetching matchup data:")
        print(f"  Home: {home_team}")
        print(f"  Away: {away_team}")
        print(f"  League: {league}")
        
        try:
            matchup_data = await scraper.get_matchup_data(
                home_team=home_team,
                away_team=away_team,
                league=league,
                season=season,
                game_time=game_time
            )
            
            print("\n[RESULTS]")
            home_stats = matchup_data.get('home_team_stats')
            away_stats = matchup_data.get('away_team_stats')
            
            print(f"  Home stats: {'FOUND' if home_stats else 'NOT FOUND'}")
            print(f"  Away stats: {'FOUND' if away_stats else 'NOT FOUND'}")
            
            if home_stats:
                print(f"\n  Home Team Stats Structure:")
                print(f"    Record: {home_stats.get('record', {})}")
                print(f"    Offense keys: {list(home_stats.get('offense', {}).keys())}")
                print(f"    Defense keys: {list(home_stats.get('defense', {}).keys())}")
                offense = home_stats.get('offense', {})
                defense = home_stats.get('defense', {})
                print(f"    PPG: {offense.get('points_per_game', 'MISSING')}")
                print(f"    YPG: {offense.get('yards_per_game', 'MISSING')}")
                print(f"    PAPG: {defense.get('points_allowed_per_game', 'MISSING')}")
                print(f"    YAPG: {defense.get('yards_allowed_per_game', 'MISSING')}")
            
            if away_stats:
                print(f"\n  Away Team Stats Structure:")
                print(f"    Record: {away_stats.get('record', {})}")
                offense = away_stats.get('offense', {})
                defense = away_stats.get('defense', {})
                print(f"    PPG: {offense.get('points_per_game', 'MISSING')}")
                print(f"    YPG: {offense.get('yards_per_game', 'MISSING')}")
                print(f"    PAPG: {defense.get('points_allowed_per_game', 'MISSING')}")
                print(f"    YAPG: {defense.get('yards_allowed_per_game', 'MISSING')}")
            
            if not home_stats or not away_stats:
                print("\n[WARNING] Stats not found - checking external API calls...")
                print("  Check backend logs for '[StatsScraper]' messages")
            
        except Exception as e:
            print(f"\n[ERROR] Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stats())

