"""Test SportsRadar game results to see if we can calculate ATS/Over-Under"""

import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SPORTSRADAR_API_KEY")
BASE_URL = "https://api.sportradar.us/nfl/official/trial/v7/en"

async def test_game_results():
    """Test if we can get game results with scores from SportsRadar"""
    print(f"\n{'='*60}")
    print("SPORTRADAR GAME RESULTS TEST")
    print(f"{'='*60}\n")
    
    # Test a completed game from the schedule
    # From earlier test, we know Week 15 has games
    endpoint = "games/2024/REG/15/schedule.json"
    url = f"{BASE_URL}/{endpoint}"
    params = {"api_key": API_KEY}
    
    print(f"Testing: Week 15 Schedule (to find completed games)")
    print(f"URL: {url}\n")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                week = data.get('week', {})
                games = week.get('games', [])
                
                print(f"✓ Found {len(games)} games in Week 15\n")
                
                # Find a completed game
                completed_game = None
                for game in games:
                    if game.get('status') == 'closed':
                        completed_game = game
                        break
                
                if completed_game:
                    game_id = completed_game.get('id')
                    print(f"Found completed game: {game_id}")
                    print(f"  Home: {completed_game.get('home', {}).get('name', 'N/A')}")
                    print(f"  Away: {completed_game.get('away', {}).get('name', 'N/A')}")
                    print(f"  Status: {completed_game.get('status', 'N/A')}")
                    
                    # Check if scores are in schedule
                    home_score = completed_game.get('home', {}).get('points', completed_game.get('scoring', {}).get('home', {}).get('points'))
                    away_score = completed_game.get('away', {}).get('points', completed_game.get('scoring', {}).get('away', {}).get('points'))
                    
                    if home_score is not None or away_score is not None:
                        print(f"  ✓ Scores in schedule: Home {home_score}, Away {away_score}")
                    else:
                        print(f"  ✗ No scores in schedule data")
                    
                    # Try game boxscore endpoint
                    print(f"\n  Testing game boxscore endpoint...")
                    boxscore_url = f"{BASE_URL}/games/{game_id}/boxscore.json"
                    boxscore_response = await client.get(boxscore_url, params=params)
                    
                    if boxscore_response.status_code == 200:
                        boxscore = boxscore_response.json()
                        print(f"  ✓ Boxscore endpoint works!")
                        print(f"  Boxscore keys: {list(boxscore.keys())[:10]}")
                        
                        # Check for scores - scoring might be a list or dict
                        scoring = boxscore.get('scoring')
                        if scoring:
                            if isinstance(scoring, list):
                                print(f"  Scoring is a list with {len(scoring)} items")
                                if scoring:
                                    print(f"  First scoring item: {scoring[0]}")
                            elif isinstance(scoring, dict):
                                print(f"  Scoring structure: {list(scoring.keys())}")
                        
                        # Check home/away scores
                        home = boxscore.get('home', {})
                        away = boxscore.get('away', {})
                        
                        print(f"\n  Home team data:")
                        if isinstance(home, dict):
                            print(f"    Keys: {list(home.keys())[:15]}")
                            if 'points' in home:
                                print(f"    Points: {home.get('points')}")
                            if 'scoring' in home:
                                print(f"    Has scoring data")
                        
                        print(f"  Away team data:")
                        if isinstance(away, dict):
                            print(f"    Keys: {list(away.keys())[:15]}")
                            if 'points' in away:
                                print(f"    Points: {away.get('points')}")
                            if 'scoring' in away:
                                print(f"    Has scoring data")
                        
                        # Save sample for inspection
                        with open("sportsradar_boxscore_sample.json", "w") as f:
                            json.dump(boxscore, f, indent=2)
                        print(f"\n  Sample boxscore saved to: sportsradar_boxscore_sample.json")
                    elif boxscore_response.status_code == 404:
                        print(f"  ✗ Boxscore endpoint not available (404) - trial limitation")
                    else:
                        print(f"  ✗ Boxscore error: {boxscore_response.status_code}")
                else:
                    print("No completed games found in Week 15")
            else:
                print(f"✗ ERROR {response.status_code}")
                
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_game_results())

