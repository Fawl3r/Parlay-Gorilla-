"""Test script to check The Odds API directly"""

import asyncio
import httpx
import os
import time
from dotenv import load_dotenv

import pytest

load_dotenv()


@pytest.mark.asyncio
async def test_odds_api():
    """Test The Odds API directly"""
    print("=" * 60)
    print("Testing The Odds API")
    print("=" * 60)
    
    api_key = os.getenv("THE_ODDS_API_KEY", "")
    if not api_key:
        print("ERROR: THE_ODDS_API_KEY not found in environment")
        return
    
    base_url = "https://api.the-odds-api.com/v4"
    
    print(f"\nAPI Key: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            print("\n1. Fetching NFL odds...")
            start = time.time()
            
            response = await client.get(
                f"{base_url}/sports/americanfootball_nfl/odds",
                params={
                    "apiKey": api_key,
                    "regions": "us",
                    "markets": "h2h,spreads,totals",
                    "oddsFormat": "american",
                },
            )
            
            elapsed = time.time() - start
            print(f"   Status: {response.status_code}")
            print(f"   Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Games returned: {len(data)}")
                
                if data:
                    first_game = data[0]
                    print(f"\n   First game:")
                    print(f"   - {first_game.get('away_team')} @ {first_game.get('home_team')}")
                    print(f"   - Commence time: {first_game.get('commence_time')}")
                    print(f"   - Bookmakers: {len(first_game.get('bookmakers', []))}")
                    
                    if first_game.get('bookmakers'):
                        bookmaker = first_game['bookmakers'][0]
                        print(f"   - First bookmaker: {bookmaker.get('key')}")
                        print(f"   - Markets: {len(bookmaker.get('markets', []))}")
            else:
                print(f"   ERROR: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                
    except httpx.TimeoutException:
        print("   ERROR: Request timed out")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import time
    asyncio.run(test_odds_api())

