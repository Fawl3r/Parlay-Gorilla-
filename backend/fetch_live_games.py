"""
Fetch live games from The Odds API and store in database
"""
import asyncio
import os

# Set SQLite mode
os.environ["USE_SQLITE"] = "true"

async def fetch_live_games():
    """Fetch live games from The Odds API"""
    print("=" * 60)
    print("Fetching Live Games from The Odds API")
    print("=" * 60)
    
    from app.database.session import AsyncSessionLocal, DATABASE_URL
    from app.services.odds_fetcher import OddsFetcherService
    from app.services.sports_config import get_sport_config
    from app.models import Game, Market, Odds
    from sqlalchemy import select, delete, func
    
    print(f"\nDatabase: {DATABASE_URL}")
    
    async with AsyncSessionLocal() as db:
        # Clear existing games to get fresh data
        print("\n1. Clearing existing games...")
        await db.execute(delete(Odds))
        await db.execute(delete(Market))
        await db.execute(delete(Game))
        await db.commit()
        print("   Cleared all games, markets, and odds")
        
        # Fetch games for multiple sports
        print("\n2. Fetching live games from The Odds API...")
        fetcher = OddsFetcherService(db)
        
        sports = [
            ("nfl", "americanfootball_nfl"),
            ("nba", "basketball_nba"),
            ("nhl", "icehockey_nhl"),
        ]
        
        total_games = 0
        for sport_name, sport_key in sports:
            try:
                print(f"\n   Fetching {sport_name.upper()}...")
                sport_config = get_sport_config(sport_key)
                
                # Fetch from API
                api_data = await fetcher.fetch_odds_for_sport(sport_config)
                print(f"   Got {len(api_data)} games from API")
                
                if api_data:
                    # Store in database
                    games = await fetcher.normalize_and_store_odds(api_data, sport_config)
                    await db.commit()
                    total_games += len(games)
                    print(f"   Stored {len(games)} {sport_name.upper()} games")
                    
            except Exception as e:
                print(f"   Error fetching {sport_name}: {e}")
                await db.rollback()  # Rollback on error
                import traceback
                traceback.print_exc()
        
        # Verify
        print("\n3. Verifying database...")
        result = await db.execute(select(func.count()).select_from(Game))
        games_count = result.scalar()
        
        result = await db.execute(select(func.count()).select_from(Market))
        markets_count = result.scalar()
        
        result = await db.execute(select(func.count()).select_from(Odds))
        odds_count = result.scalar()
        
        print(f"   Total Games: {games_count}")
        print(f"   Total Markets: {markets_count}")
        print(f"   Total Odds: {odds_count}")
        
        # Show breakdown by sport
        print("\n   Games by Sport:")
        for sport_name, _ in sports:
            result = await db.execute(
                select(func.count()).select_from(Game).where(Game.sport == sport_name.upper())
            )
            count = result.scalar()
            print(f"   - {sport_name.upper()}: {count} games")
    
    print("\n" + "=" * 60)
    print("Live games fetched successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(fetch_live_games())

