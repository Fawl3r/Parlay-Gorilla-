"""Comprehensive diagnostic script for games loading issue"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def diagnose():
    """Run comprehensive diagnostics"""
    print("=" * 70)
    print("F3 Parlay AI - Games Loading Diagnostic")
    print("=" * 70)
    
    # Test 1: Environment variables
    print("\n1. Checking Environment Variables...")
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL", "")
    odds_api_key = os.getenv("THE_ODDS_API_KEY", "")
    
    print(f"   DATABASE_URL: {'✓ Set' if database_url else '✗ Missing'}")
    if database_url:
        # Mask password
        if "@" in database_url:
            parts = database_url.split("@")
            if len(parts) > 1:
                print(f"   Database: {parts[1][:50]}...")
    
    print(f"   THE_ODDS_API_KEY: {'✓ Set' if odds_api_key else '✗ Missing'}")
    if odds_api_key:
        print(f"   Key: {odds_api_key[:10]}...{odds_api_key[-5:]}")
    
    # Test 2: Database connection
    print("\n2. Testing Database Connection...")
    try:
        from app.database.session import AsyncSessionLocal, engine
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text
            result = await db.execute(text("SELECT 1"))
            result.scalar()
            print("   ✓ Database connection successful")
            
            # Check for games
            from app.models.game import Game
            from sqlalchemy import select, func
            result = await db.execute(select(func.count(Game.id)).where(Game.sport == "NFL"))
            count = result.scalar()
            print(f"   Games in database: {count}")
            
            if count > 0:
                # Check recent games
                cutoff = datetime.utcnow() - timedelta(hours=24)
                result = await db.execute(
                    select(func.count(Game.id))
                    .where(Game.sport == "NFL")
                    .where(Game.start_time >= cutoff)
                )
                recent_count = result.scalar()
                print(f"   Recent games (last 24h): {recent_count}")
    except Exception as e:
        print(f"   ✗ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: The Odds API
    print("\n3. Testing The Odds API...")
    if not odds_api_key:
        print("   ✗ Cannot test - API key missing")
    else:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                print("   Making API request...")
                start = datetime.now()
                response = await client.get(
                    "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds",
                    params={
                        "apiKey": odds_api_key,
                        "regions": "us",
                        "markets": "h2h",
                        "oddsFormat": "american",
                    },
                )
                elapsed = (datetime.now() - start).total_seconds()
                
                print(f"   Status: {response.status_code}")
                print(f"   Time: {elapsed:.2f}s")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✓ API working - {len(data)} games returned")
                    if data:
                        print(f"   First game: {data[0].get('away_team')} @ {data[0].get('home_team')}")
                elif response.status_code == 401:
                    print("   ✗ API key invalid or expired")
                elif response.status_code == 429:
                    print("   ✗ API rate limit exceeded")
                else:
                    print(f"   ✗ API error: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
        except httpx.TimeoutException:
            print("   ✗ API request timed out")
        except Exception as e:
            print(f"   ✗ API test failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Test 4: OddsFetcherService
    print("\n4. Testing OddsFetcherService...")
    try:
        from app.services.odds_fetcher import OddsFetcherService
        async with AsyncSessionLocal() as db:
            fetcher = OddsFetcherService(db)
            
            print("   Testing get_or_fetch_games('nfl') (no refresh)...")
            start = datetime.now()
            games = await fetcher.get_or_fetch_games("nfl", force_refresh=False)
            elapsed = (datetime.now() - start).total_seconds()
            
            print(f"   ✓ Service working")
            print(f"   Time: {elapsed:.2f}s")
            print(f"   Games returned: {len(games)}")
            
            if games:
                print(f"   First game: {games[0].home_team} vs {games[0].away_team}")
                print(f"   Markets in first game: {len(games[0].markets)}")
    except Exception as e:
        print(f"   ✗ Service test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Backend server (if running)
    print("\n5. Testing Backend Server...")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("   ✓ Backend server is running")
                
                # Test games endpoint
                print("   Testing /api/sports/nfl/games endpoint...")
                start = datetime.now()
                response = await client.get("http://localhost:8000/api/sports/nfl/games", timeout=30.0)
                elapsed = (datetime.now() - start).total_seconds()
                
                print(f"   Status: {response.status_code}")
                print(f"   Time: {elapsed:.2f}s")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✓ Endpoint working - {len(data)} games")
                else:
                    print(f"   ✗ Endpoint error: {response.status_code}")
                    print(f"   Response: {response.text[:300]}")
            else:
                print(f"   ✗ Backend returned: {response.status_code}")
    except httpx.ConnectError:
        print("   ✗ Backend server is not running")
        print("   Start it with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"   ✗ Backend test failed: {e}")
    
    print("\n" + "=" * 70)
    print("Diagnostic Complete")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(diagnose())

