"""Test script to debug the analysis endpoint timeout issue"""

import asyncio
import time
import httpx
from datetime import datetime

async def test_endpoint():
    """Test the analysis endpoint with timing"""
    url = "http://localhost:8000/api/analysis/nfl/upcoming"
    params = {"limit": 50}
    
    print(f"[TEST] Testing endpoint: {url}")
    print(f"[TEST] Params: {params}")
    print(f"[TEST] Starting request at {datetime.now()}")
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, params=params)
            elapsed = time.time() - start_time
            
            print(f"[TEST] Response status: {response.status_code}")
            print(f"[TEST] Elapsed time: {elapsed:.2f}s")
            print(f"[TEST] Response size: {len(response.content)} bytes")
            
            if response.status_code == 200:
                data = response.json()
                print(f"[TEST] Number of items: {len(data)}")
                if data:
                    print(f"[TEST] First item: {data[0]}")
                return True
            else:
                print(f"[TEST] Error response: {response.text[:200]}")
                return False
                
    except httpx.TimeoutException:
        elapsed = time.time() - start_time
        print(f"[TEST] TIMEOUT after {elapsed:.2f}s")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[TEST] ERROR after {elapsed:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_query():
    """Test the database query directly"""
    print("\n[DB TEST] Testing database query directly...")
    
    try:
        from app.database.session import AsyncSessionLocal
        from app.models.game import Game
        from app.models.game_analysis import GameAnalysis
        from sqlalchemy import select
        from datetime import timedelta
        from app.services.sports_config import get_sport_config
        from app.utils.timezone_utils import TimezoneNormalizer
        
        sport_config = get_sport_config("nfl")
        league = sport_config.code
        now = datetime.utcnow()
        future_cutoff = now + timedelta(days=sport_config.lookahead_days)
        
        print(f"[DB TEST] League: {league}")
        print(f"[DB TEST] Now: {now}")
        print(f"[DB TEST] Future cutoff: {future_cutoff}")
        
        start_time = time.time()
        
        async with AsyncSessionLocal() as db:
            print(f"[DB TEST] Database session created in {(time.time() - start_time):.2f}s")
            
            query_start = time.time()
            result = await db.execute(
                select(GameAnalysis, Game)
                .join(Game, GameAnalysis.game_id == Game.id)
                .where(
                    GameAnalysis.league == league,
                    Game.start_time >= now,
                    Game.start_time <= future_cutoff
                )
                .order_by(Game.start_time)
                .limit(50)
            )
            query_elapsed = time.time() - query_start
            print(f"[DB TEST] Query executed in {query_elapsed:.2f}s")
            
            fetch_start = time.time()
            rows = result.all()
            fetch_elapsed = time.time() - fetch_start
            print(f"[DB TEST] Fetched {len(rows)} rows in {fetch_elapsed:.2f}s")
            
            process_start = time.time()
            items = []
            for analysis, game in rows:
                items.append({
                    "id": str(analysis.id),
                    "slug": analysis.slug,
                    "league": analysis.league,
                    "matchup": analysis.matchup,
                    "game_time": TimezoneNormalizer.ensure_utc(game.start_time),
                    "generated_at": TimezoneNormalizer.ensure_utc(analysis.generated_at),
                })
            process_elapsed = time.time() - process_start
            print(f"[DB TEST] Processed {len(items)} items in {process_elapsed:.2f}s")
            
            total_elapsed = time.time() - start_time
            print(f"[DB TEST] Total time: {total_elapsed:.2f}s")
            
            return True
            
    except Exception as e:
        print(f"[DB TEST] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("ANALYSIS ENDPOINT DEBUG TEST")
    print("=" * 60)
    
    # Test 1: HTTP endpoint
    print("\n[TEST 1] Testing HTTP endpoint...")
    endpoint_ok = await test_endpoint()
    
    # Test 2: Database query
    print("\n[TEST 2] Testing database query...")
    db_ok = await test_database_query()
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"  Endpoint test: {'PASS' if endpoint_ok else 'FAIL'}")
    print(f"  Database test: {'PASS' if db_ok else 'FAIL'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

