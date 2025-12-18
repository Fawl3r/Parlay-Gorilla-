"""Debug script to see what ESPN actually returns"""

import asyncio
from app.services.data_fetchers.espn_scraper import ESPNScraper

async def debug_espn():
    """Debug ESPN response structure"""
    scraper = ESPNScraper()
    
    team_name = "Tampa Bay Buccaneers"
    sport = "nfl"
    
    print(f"Fetching stats for {team_name} ({sport})...")
    result = await scraper.scrape_team_stats(team_name, sport)
    
    if result:
        print("\n=== ESPN RESULT STRUCTURE ===")
        print(f"Keys: {list(result.keys())}")
        print(f"\nRecord: {result.get('record', {})}")
        print(f"\nOffense keys: {list(result.get('offense', {}).keys())}")
        print(f"\nOffense sample (first 5):")
        offense = result.get('offense', {})
        for i, (key, value) in enumerate(list(offense.items())[:5]):
            print(f"  {key}: {value}")
        
        print(f"\nDefense keys: {list(result.get('defense', {}).keys())}")
        print(f"\nDefense sample (first 5):")
        defense = result.get('defense', {})
        for i, (key, value) in enumerate(list(defense.items())[:5]):
            print(f"  {key}: {value}")
        
        # Look for points/yards related keys
        print("\n=== SEARCHING FOR STATS ===")
        all_offense_keys = list(offense.keys())
        points_keys = [k for k in all_offense_keys if 'point' in k.lower()]
        yards_keys = [k for k in all_offense_keys if 'yard' in k.lower()]
        print(f"Keys with 'point': {points_keys}")
        print(f"Keys with 'yard': {yards_keys}")
        
        if points_keys:
            print(f"\nSample points stat: {points_keys[0]} = {offense[points_keys[0]]}")
        if yards_keys:
            print(f"Sample yards stat: {yards_keys[0]} = {offense[yards_keys[0]]}")
    else:
        print("No result from ESPN")

if __name__ == "__main__":
    asyncio.run(debug_espn())

