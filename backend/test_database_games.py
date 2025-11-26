"""Test script to check database for games directly"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import AsyncSessionLocal
from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload


@pytest.mark.asyncio
async def test_database():
    """Test database queries directly"""
    print("=" * 60)
    print("Testing Database Queries")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # Test 1: Count games
        print("\n1. Counting games in database...")
        result = await db.execute(select(func.count(Game.id)).where(Game.sport == "NFL"))
        count = result.scalar()
        print(f"   Total NFL games: {count}")
        
        # Test 2: Get recent games
        print("\n2. Getting recent games...")
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        future_cutoff = datetime.utcnow() + timedelta(days=7)
        
        result = await db.execute(
            select(Game)
            .where(Game.sport == "NFL")
            .where(Game.start_time >= cutoff_time)
            .where(Game.start_time <= future_cutoff)
            .order_by(Game.start_time)
            .limit(10)
        )
        games = result.scalars().all()
        print(f"   Recent games found: {len(games)}")
        
        for game in games:
            print(f"   - {game.away_team} @ {game.home_team} ({game.start_time})")
        
        # Test 3: Check markets and odds
        if games:
            print("\n3. Checking markets and odds for first game...")
            game = games[0]
            result = await db.execute(
                select(Game)
                .where(Game.id == game.id)
                .options(selectinload(Game.markets).selectinload(Market.odds))
            )
            game_with_data = result.scalar_one_or_none()
            
            if game_with_data:
                print(f"   Markets: {len(game_with_data.markets)}")
                total_odds = sum(len(m.odds) for m in game_with_data.markets)
                print(f"   Total odds: {total_odds}")
                
                if game_with_data.markets:
                    market = game_with_data.markets[0]
                    print(f"   First market: {market.market_type} from {market.book}")
                    print(f"   Odds in first market: {len(market.odds)}")
        
        # Test 4: Check oldest game
        print("\n4. Checking oldest game...")
        result = await db.execute(
            select(Game)
            .where(Game.sport == "NFL")
            .order_by(Game.start_time.desc())
            .limit(1)
        )
        oldest = result.scalar_one_or_none()
        if oldest:
            age = datetime.utcnow() - oldest.start_time.replace(tzinfo=None) if oldest.start_time else timedelta(0)
            print(f"   Oldest game: {oldest.away_team} @ {oldest.home_team}")
            print(f"   Age: {age.days} days, {age.seconds // 3600} hours old")

if __name__ == "__main__":
    asyncio.run(test_database())

