"""Test SportsRadar schedule endpoints to see what data is available"""

import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SPORTSRADAR_API_KEY")
BASE_URL = "https://api.sportradar.us/nfl/official/trial/v7/en"

async def test_schedule_endpoints():
    """Test schedule endpoints that work with trial"""
    print(f"\n{'='*60}")
    print("SPORTRADAR SCHEDULE ENDPOINTS TEST")
    print(f"{'='*60}\n")
    
    # Test week schedule
    endpoint = "games/2024/REG/15/schedule.json"
    url = f"{BASE_URL}/{endpoint}"
    params = {"api_key": API_KEY}
    
    print(f"Testing: Week 15 Schedule")
    print(f"URL: {url}\n")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ SUCCESS - Status 200")
                print(f"\nResponse structure:")
                print(f"  Keys: {list(data.keys())}")
                
                if 'weeks' in data:
                    weeks = data.get('weeks', [])
                    print(f"\n  Found {len(weeks)} weeks")
                    if weeks:
                        week = weeks[0]
                        print(f"  First week keys: {list(week.keys())}")
                        if 'games' in week:
                            games = week.get('games', [])
                            print(f"  Games in first week: {len(games)}")
                            if games:
                                game = games[0]
                                print(f"\n  Sample game structure:")
                                print(f"    Keys: {list(game.keys())[:15]}")
                                if 'home' in game:
                                    home = game.get('home', {})
                                    print(f"    Home team keys: {list(home.keys())[:10]}")
                                    print(f"    Home team: {home.get('name', 'N/A')}")
                                    print(f"    Home team ID: {home.get('id', 'N/A')}")
                                if 'away' in game:
                                    away = game.get('away', {})
                                    print(f"    Away team: {away.get('name', 'N/A')}")
                                    print(f"    Away team ID: {away.get('id', 'N/A')}")
                
                # Save sample to file for inspection
                with open("sportsradar_schedule_sample.json", "w") as f:
                    json.dump(data, f, indent=2)
                print(f"\n  Sample saved to: sportsradar_schedule_sample.json")
                
            else:
                print(f"✗ ERROR {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_schedule_endpoints())

