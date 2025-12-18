"""Debug script to see raw ESPN API response"""

import asyncio
import httpx
import json
from app.services.data_fetchers.espn_scraper import ESPNScraper

async def debug_espn_raw():
    """Debug raw ESPN API response"""
    scraper = ESPNScraper()
    
    team_name = "Tampa Bay Buccaneers"
    sport = "nfl"
    team_abbr = scraper._get_team_abbr(team_name, sport)
    
    if not team_abbr:
        print(f"Could not find abbreviation for {team_name}")
        return
    
    base_url = scraper._get_base_url(sport)
    url = f"{base_url}/teams/{team_abbr}"
    
    print(f"Fetching from: {url}")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            
            print("\n=== TOP LEVEL KEYS ===")
            print(f"Keys: {list(data.keys())}")
            
            team = data.get('team', {})
            print(f"\n=== TEAM KEYS ===")
            print(f"Team keys: {list(team.keys())}")
            
            record = team.get('record', {})
            print(f"\n=== RECORD STRUCTURE ===")
            print(f"Record keys: {list(record.keys())}")
            print(f"Record items: {record.get('items', [])}")
            
            stats = team.get('statistics', [])
            print(f"\n=== STATISTICS STRUCTURE ===")
            print(f"Statistics type: {type(stats)}")
            print(f"Statistics length: {len(stats) if isinstance(stats, list) else 'N/A'}")
            
            if isinstance(stats, list) and len(stats) > 0:
                print(f"\nFirst stat group:")
                first_group = stats[0]
                print(f"  Keys: {list(first_group.keys())}")
                print(f"  Name: {first_group.get('name', 'N/A')}")
                print(f"  Categories: {len(first_group.get('categories', []))} categories")
                
                categories = first_group.get('categories', [])
                if categories:
                    print(f"\nFirst category:")
                    first_cat = categories[0]
                    print(f"  Keys: {list(first_cat.keys())}")
                    print(f"  Name: {first_cat.get('name', 'N/A')}")
                    print(f"  Stats: {len(first_cat.get('stats', []))} stats")
                    
                    cat_stats = first_cat.get('stats', [])
                    if cat_stats:
                        print(f"\nFirst stat in category:")
                        first_stat = cat_stats[0]
                        print(f"  Keys: {list(first_stat.keys())}")
                        print(f"  Name: {first_stat.get('name', 'N/A')}")
                        print(f"  Value: {first_stat.get('value', 'N/A')}")
                        print(f"  DisplayValue: {first_stat.get('displayValue', 'N/A')}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(debug_espn_raw())

