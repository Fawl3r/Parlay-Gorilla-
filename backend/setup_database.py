"""
Database Setup Script
Creates all tables and seeds initial data from The Odds API
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
import uuid

# Set SQLite mode before importing app modules
os.environ["USE_SQLITE"] = "true"

async def setup_database():
    """Create tables and seed initial data"""
    print("=" * 60)
    print("Parlay Gorilla - Database Setup")
    print("=" * 60)
    
    # Import after setting env var
    from app.database.session import engine, Base, AsyncSessionLocal, DATABASE_URL
    from app.models import Game, Market, Odds, TeamStats
    
    print(f"\nDatabase URL: {DATABASE_URL}")
    
    # Create all tables
    print("\n1. Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   Tables created successfully!")
    
    # Seed data
    print("\n2. Seeding sample games and markets...")
    await seed_sample_data()
    
    # Verify
    print("\n3. Verifying database...")
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func
        
        result = await db.execute(select(func.count()).select_from(Game))
        games_count = result.scalar()
        
        result = await db.execute(select(func.count()).select_from(Market))
        markets_count = result.scalar()
        
        result = await db.execute(select(func.count()).select_from(Odds))
        odds_count = result.scalar()
        
        print(f"   Games: {games_count}")
        print(f"   Markets: {markets_count}")
        print(f"   Odds: {odds_count}")
    
    print("\n" + "=" * 60)
    print("Database setup complete!")
    print("=" * 60)
    print("\nYou can now start the backend server:")
    print("  python -m uvicorn app.main:app --reload --port 8000")


async def seed_sample_data():
    """Seed database with sample games if API fails"""
    from decimal import Decimal
    from app.database.session import AsyncSessionLocal
    from app.models import Game, Market, Odds
    
    sample_games = [
        # NFL Games
        {
            "sport": "NFL",
            "home_team": "Kansas City Chiefs",
            "away_team": "Denver Broncos",
            "start_time": datetime.utcnow() + timedelta(days=2),
        },
        {
            "sport": "NFL",
            "home_team": "Dallas Cowboys",
            "away_team": "Philadelphia Eagles",
            "start_time": datetime.utcnow() + timedelta(days=3),
        },
        {
            "sport": "NFL",
            "home_team": "San Francisco 49ers",
            "away_team": "Seattle Seahawks",
            "start_time": datetime.utcnow() + timedelta(days=3),
        },
        {
            "sport": "NFL",
            "home_team": "Buffalo Bills",
            "away_team": "Miami Dolphins",
            "start_time": datetime.utcnow() + timedelta(days=4),
        },
        {
            "sport": "NFL",
            "home_team": "Green Bay Packers",
            "away_team": "Chicago Bears",
            "start_time": datetime.utcnow() + timedelta(days=4),
        },
        # NBA Games
        {
            "sport": "NBA",
            "home_team": "Los Angeles Lakers",
            "away_team": "Golden State Warriors",
            "start_time": datetime.utcnow() + timedelta(days=1),
        },
        {
            "sport": "NBA",
            "home_team": "Boston Celtics",
            "away_team": "New York Knicks",
            "start_time": datetime.utcnow() + timedelta(days=1),
        },
        {
            "sport": "NBA",
            "home_team": "Phoenix Suns",
            "away_team": "Denver Nuggets",
            "start_time": datetime.utcnow() + timedelta(days=2),
        },
        # NHL Games
        {
            "sport": "NHL",
            "home_team": "New York Rangers",
            "away_team": "Boston Bruins",
            "start_time": datetime.utcnow() + timedelta(days=1),
        },
        {
            "sport": "NHL",
            "home_team": "Colorado Avalanche",
            "away_team": "Vegas Golden Knights",
            "start_time": datetime.utcnow() + timedelta(days=2),
        },
    ]
    
    async with AsyncSessionLocal() as db:
        for game_data in sample_games:
            game_id = uuid.uuid4()
            
            # Create game
            game = Game(
                id=game_id,
                external_game_id=f"sample_{game_id}",
                sport=game_data["sport"],
                home_team=game_data["home_team"],
                away_team=game_data["away_team"],
                start_time=game_data["start_time"],
                status="scheduled",
            )
            db.add(game)
            
            # Create spread market
            spread_market_id = uuid.uuid4()
            spread_value = round(-3.5 + (hash(game_data["home_team"]) % 7), 1)
            spread_market = Market(
                id=spread_market_id,
                game_id=game_id,
                market_type="spreads",
                book="consensus",
            )
            db.add(spread_market)
            
            # Create spread odds for home team
            spread_odds = Odds(
                id=uuid.uuid4(),
                market_id=spread_market_id,
                outcome=f"{game_data['home_team']} {spread_value:+.1f}",
                price="-110",
                decimal_price=Decimal("1.909"),
                implied_prob=Decimal("0.5238"),
            )
            db.add(spread_odds)
            
            # Create total market
            total_market_id = uuid.uuid4()
            total_value = 44.5 + (hash(game_data["home_team"]) % 10)
            total_market = Market(
                id=total_market_id,
                game_id=game_id,
                market_type="totals",
                book="consensus",
            )
            db.add(total_market)
            
            # Create total odds for over
            total_odds = Odds(
                id=uuid.uuid4(),
                market_id=total_market_id,
                outcome=f"Over {total_value}",
                price="-110",
                decimal_price=Decimal("1.909"),
                implied_prob=Decimal("0.5238"),
            )
            db.add(total_odds)
            
            # Create moneyline market
            ml_market_id = uuid.uuid4()
            ml_market = Market(
                id=ml_market_id,
                game_id=game_id,
                market_type="h2h",
                book="consensus",
            )
            db.add(ml_market)
            
            # Create moneyline odds
            ml_price = -150 + (hash(game_data["home_team"]) % 100)
            if ml_price < 0:
                decimal_odds = Decimal(str(100 / abs(ml_price) + 1))
                implied_prob = Decimal(str(abs(ml_price) / (abs(ml_price) + 100)))
            else:
                decimal_odds = Decimal(str(ml_price / 100 + 1))
                implied_prob = Decimal(str(100 / (ml_price + 100)))
            
            ml_odds = Odds(
                id=uuid.uuid4(),
                market_id=ml_market_id,
                outcome=game_data["home_team"],
                price=f"{ml_price:+d}",
                decimal_price=decimal_odds,
                implied_prob=implied_prob,
            )
            db.add(ml_odds)
        
        await db.commit()
        print(f"   Seeded {len(sample_games)} sample games with markets and odds")


if __name__ == "__main__":
    asyncio.run(setup_database())

