"""Test script to identify timeout issues in analysis endpoint"""

import asyncio
import time
from datetime import datetime, timedelta
from app.database.session import AsyncSessionLocal
from app.models.game_analysis import GameAnalysis
from app.models.game import Game
from sqlalchemy import select
from app.services.sports_config import get_sport_config
from app.utils.timezone_utils import TimezoneNormalizer

async def test_query():
    """Test the database query that's timing out"""
    print("=" * 60)
    print("TESTING ANALYSIS ENDPOINT QUERY")
    print("=" * 60)
    
    sport = "nfl"
    limit = 50
    
    try:
        sport_config = get_sport_config(sport)
        league = sport_config.code
        now = datetime.utcnow()
        future_cutoff = now + timedelta(days=sport_config.lookahead_days)
        
        print(f"\n[TEST] Sport: {sport}, League: {league}")
        print(f"[TEST] Now: {now}")
        print(f"[TEST] Future cutoff: {future_cutoff}")
        print(f"[TEST] Limit: {limit}")
        
        start_time = time.time()
        
        async with AsyncSessionLocal() as db:
            print(f"\n[TEST] Database session created in {(time.time() - start_time):.3f}s")
            
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
                .limit(limit)
            )
            query_elapsed = time.time() - query_start
            print(f"[TEST] Query executed in {query_elapsed:.3f}s")
            
            if query_elapsed > 5.0:
                print(f"[TEST] ⚠️  WARNING: Query took {query_elapsed:.2f}s - this is very slow!")
            
            fetch_start = time.time()
            rows = result.all()
            fetch_elapsed = time.time() - fetch_start
            print(f"[TEST] Fetched {len(rows)} rows in {fetch_elapsed:.3f}s")
            
            if fetch_elapsed > 5.0:
                print(f"[TEST] ⚠️  WARNING: Fetch took {fetch_elapsed:.2f}s - this is very slow!")
            
            process_start = time.time()
            items = []
            for i, (analysis, game) in enumerate(rows):
                try:
                    game_time = TimezoneNormalizer.ensure_utc(game.start_time)
                    generated_at = TimezoneNormalizer.ensure_utc(analysis.generated_at)
                    items.append({
                        "id": str(analysis.id),
                        "slug": analysis.slug,
                        "league": analysis.league,
                        "matchup": analysis.matchup,
                        "game_time": game_time,
                        "generated_at": generated_at,
                    })
                except Exception as e:
                    print(f"[TEST] ⚠️  Error processing row {i}: {e}")
                    continue
            
            process_elapsed = time.time() - process_start
            print(f"[TEST] Processed {len(items)} items in {process_elapsed:.3f}s")
            
            total_elapsed = time.time() - start_time
            print(f"\n[TEST] Total time: {total_elapsed:.3f}s")
            
            if total_elapsed > 10.0:
                print(f"[TEST] ❌ ERROR: Total time {total_elapsed:.2f}s exceeds 10s threshold!")
                return False
            elif total_elapsed > 5.0:
                print(f"[TEST] ⚠️  WARNING: Total time {total_elapsed:.2f}s is slow but acceptable")
            else:
                print(f"[TEST] ✓ SUCCESS: Query completed in {total_elapsed:.2f}s")
            
            return True
            
    except Exception as e:
        print(f"\n[TEST] ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_query())
    exit(0 if success else 1)

