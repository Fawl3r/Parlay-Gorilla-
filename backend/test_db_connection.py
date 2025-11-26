"""Quick test script to check database connection"""
import asyncio
from app.database.session import AsyncSessionLocal
from app.models.game import Game
from sqlalchemy import select, text

async def test_db():
    try:
        async with AsyncSessionLocal() as db:
            # Test basic connection
            result = await db.execute(text("SELECT 1"))
            print("✓ Database connection successful")
            
            # Test Game model query
            result = await db.execute(select(Game).limit(1))
            games = result.scalars().all()
            print(f"✓ Game query successful, found {len(games)} games")
            
            # Test with relationships
            from sqlalchemy.orm import selectinload
            from app.models.market import Market
            result = await db.execute(
                select(Game)
                .options(selectinload(Game.markets).selectinload(Market.odds))
                .limit(1)
            )
            games = result.scalars().all()
            print(f"✓ Game query with relationships successful")
            
    except Exception as e:
        print(f"✗ Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db())

