"""Test script to debug analysis generation"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.game import Game
from app.services.analysis_generator import AnalysisGeneratorService
from sqlalchemy import select
import uuid

async def test_generation():
    """Test analysis generation for Rams vs Seahawks"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Find the game
        result = await db.execute(
            select(Game).where(
                Game.home_team.ilike("%Seattle%"),
                Game.away_team.ilike("%Los Angeles Rams%"),
                Game.sport == "NFL"
            ).order_by(Game.start_time.desc())
        )
        game = result.scalar_one_or_none()
        
        if not game:
            print("ERROR: Game not found")
            return
        
        print(f"Found game: {game.away_team} @ {game.home_team}")
        print(f"Game ID: {game.id}")
        print(f"Start time: {game.start_time}")
        
        # Try to generate analysis
        generator = AnalysisGeneratorService(db)
        print("\nAttempting to generate analysis...")
        
        try:
            analysis = await asyncio.wait_for(
                generator.generate_game_analysis(
                    game_id=str(game.id),
                    sport="nfl"
                ),
                timeout=60.0
            )
            
            print("\n=== GENERATION SUCCESS ===")
            print(f"Has opening_summary: {bool(analysis.get('opening_summary'))}")
            print(f"Opening summary: {str(analysis.get('opening_summary', ''))[:200]}")
            print(f"Has ATS trends: {bool(analysis.get('ats_trends'))}")
            print(f"Has totals trends: {bool(analysis.get('totals_trends'))}")
            print(f"Has spread pick: {bool(analysis.get('ai_spread_pick', {}).get('pick'))}")
            print(f"Has total pick: {bool(analysis.get('ai_total_pick', {}).get('pick'))}")
            print(f"Has full article: {bool(analysis.get('full_article'))}")
            
            if analysis.get('opening_summary', '').startswith("Analysis is being prepared"):
                print("\n⚠️  WARNING: This is still a placeholder!")
            else:
                print("\n✅ Analysis appears to be generated!")
                
        except asyncio.TimeoutError:
            print("\n❌ ERROR: Generation timed out after 60 seconds")
        except Exception as e:
            print(f"\n❌ ERROR: Generation failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_generation())

