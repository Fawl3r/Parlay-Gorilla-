"""Test full season schedule to get game and team data"""

import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SPORTSRADAR_API_KEY")
BASE_URL = "https://api.sportradar.us/nfl/official/trial/v7/en"

async def test_full_schedule():
    """Test full season schedule endpoint"""
    print(f"\n{'='*60}")
    print("SPORTRADAR FULL SEASON SCHEDULE TEST")
    print(f"{'='*60}\n")
    
    # Test full season schedule
    endpoint = "games/2024/REG/schedule.json"
    url = f"{BASE_URL}/{endpoint}"
    params = {"api_key": API_KEY}
    
    print(f"Testing: Full Season Schedule")
    print(f"URL: {url}\n")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ SUCCESS - Status 200")
                print(f"\nResponse structure:")
                print(f"  Top-level keys: {list(data.keys())}")
                
                if 'weeks' in data:
                    weeks = data.get('weeks', [])
                    print(f"\n  Found {len(weeks)} weeks")
                    
                    # Find a week with games
                    for week in weeks[:5]:  # Check first 5 weeks
                        week_num = week.get('sequence', week.get('number', 'N/A'))
                        games = week.get('games', [])
                        if games:
                            print(f"\n  Week {week_num} has {len(games)} games")
                            game = games[0]
                            print(f"    Sample game ID: {game.get('id', 'N/A')}")
                            print(f"    Sample game scheduled: {game.get('scheduled', 'N/A')}")
                            
                            if 'home' in game:
                                home = game.get('home', {})
                                print(f"    Home: {home.get('name', 'N/A')} (ID: {home.get('id', 'N/A')})")
                            if 'away' in game:
                                away = game.get('away', {})
                                print(f"    Away: {away.get('name', 'N/A')} (ID: {away.get('id', 'N/A')})")
                            
                            # Try to get game details
                            game_id = game.get('id')
                            if game_id:
                                print(f"\n  Testing game details endpoint: games/{game_id}/summary.json")
                                game_url = f"{BASE_URL}/games/{game_id}/summary.json"
                                game_response = await client.get(game_url, params=params)
                                if game_response.status_code == 200:
                                    print(f"    ✓ Game summary endpoint works!")
                                    game_data = game_response.json()
                                    print(f"    Game summary keys: {list(game_data.keys())[:10]}")
                                elif game_response.status_code == 404:
                                    print(f"    ✗ Game summary endpoint not available (404)")
                                else:
                                    print(f"    ✗ Game summary error: {game_response.status_code}")
                            
                            break  # Found a game, stop looking
                
                # Save full response (truncated)
                print(f"\n  Saving sample to: sportsradar_full_schedule_sample.json")
                with open("sportsradar_full_schedule_sample.json", "w") as f:
                    # Only save first week to avoid huge file
                    sample_data = {
                        'id': data.get('id'),
                        'year': data.get('year'),
                        'type': data.get('type'),
                        'name': data.get('name'),
                        'weeks': data.get('weeks', [])[:2]  # First 2 weeks only
                    }
                    json.dump(sample_data, f, indent=2)
                
            else:
                print(f"✗ ERROR {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_schedule())

