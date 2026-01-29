"""
Simple script to fetch games using the correct API
"""
import asyncio
import os

# Set SQLite mode
os.environ["USE_SQLITE"] = "true"

async def fetch_games():
    """Fetch games using the proper service method"""
    print("=" * 60)
    print("Fetching Games")
    print("=" * 60)
    
    from app.database.session import AsyncSessionLocal
    from app.services.odds_fetcher import OddsFetcherService
    
    async with AsyncSessionLocal() as db:
        fetcher = OddsFetcherService(db)
        
        sports = ["nfl", "nba", "nhl"]
        
        for sport in sports:
            try:
                print(f"\nFetching {sport.upper()} games...")
                games = await fetcher.get_or_fetch_games(sport, force_refresh=True)
                print(f"✓ Fetched {len(games)} {sport.upper()} games")
                if games:
                    print(f"  Example: {games[0].away_team} @ {games[0].home_team}")
            except Exception as e:
                print(f"✗ Error fetching {sport}: {e}")
                import traceback
                traceback.print_exc()
        
        # Commit any pending changes
        await db.commit()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(fetch_games())
