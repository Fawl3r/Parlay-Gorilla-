"""Test custom parlay analyze endpoint"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_custom_parlay_analyze():
    """Test custom parlay analyze endpoint"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Testing Custom Parlay Analyze Endpoint")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # First, get some games to use for the test
            print("\n1. Fetching NFL games...")
            games_response = await client.get(
                f"{base_url}/api/sports/nfl/games",
                headers={
                    "Origin": "http://localhost:3004",
                    "Content-Type": "application/json",
                }
            )
            
            if games_response.status_code != 200:
                print(f"Failed to fetch games: {games_response.status_code}")
                print(games_response.text)
                return
            
            games = games_response.json()
            print(f"Found {len(games)} games")
            
            if len(games) < 2:
                print("Not enough games to create a parlay")
                return
            
            # Find games with markets
            games_with_markets = [g for g in games if g.get("markets") and len(g["markets"]) > 0]
            if len(games_with_markets) < 2:
                print("Not enough games with markets")
                return
            
            print(f"Found {len(games_with_markets)} games with markets")
            
            # Build test legs from first 2 games
            legs = []
            for i, game in enumerate(games_with_markets[:2]):
                markets = game.get("markets", [])
                
                # Try to find a moneyline market
                h2h_market = next((m for m in markets if m.get("market_type") == "h2h"), None)
                if h2h_market and h2h_market.get("odds"):
                    # Use first odds option
                    odd = h2h_market["odds"][0]
                    outcome = odd.get("outcome", "").lower()
                    
                    # Determine pick based on outcome
                    if "home" in outcome or game["home_team"].lower() in outcome:
                        pick = game["home_team"]
                    elif "away" in outcome or game["away_team"].lower() in outcome:
                        pick = game["away_team"]
                    else:
                        pick = game["home_team"]  # Default
                    
                    leg = {
                        "game_id": game["id"],
                        "pick": pick,
                        "market_type": "h2h",
                        "odds": odd.get("price"),
                    }
                    legs.append(leg)
                    print(f"\nLeg {i+1}:")
                    print(f"  Game: {game['away_team']} @ {game['home_team']}")
                    print(f"  Pick: {pick}")
                    print(f"  Market: h2h")
                    print(f"  Odds: {odd.get('price')}")
            
            if len(legs) < 2:
                print("\nNot enough valid legs created")
                return
            
            # Test the analyze endpoint
            print(f"\n2. Sending POST request to /api/parlay/analyze...")
            print(f"Request body:")
            print(json.dumps({"legs": legs}, indent=2))
            
            response = await client.post(
                f"{base_url}/api/parlay/analyze",
                json={"legs": legs},
                headers={
                    "Origin": "http://localhost:3004",
                    "Content-Type": "application/json",
                }
            )
            
            print(f"\nStatus: {response.status_code}")
            print(f"Headers:")
            for key, value in response.headers.items():
                if "access-control" in key.lower() or "content-type" in key.lower():
                    print(f"  {key}: {value}")
            
            print(f"\nResponse body:")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(json.dumps({
                        "num_legs": data.get("num_legs"),
                        "combined_ai_probability": data.get("combined_ai_probability"),
                        "overall_confidence": data.get("overall_confidence"),
                        "ai_recommendation": data.get("ai_recommendation"),
                        "parlay_odds": data.get("parlay_odds"),
                    }, indent=2))
                    print("\n✅ SUCCESS: Custom parlay analysis completed!")
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
                    print(response.text[:500])
            else:
                print(f"❌ ERROR: {response.status_code}")
                try:
                    error_data = response.json()
                    print(json.dumps(error_data, indent=2))
                except:
                    print(response.text)
                    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_custom_parlay_analyze())

