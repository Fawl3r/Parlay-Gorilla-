"""
Script to generate analyses for all upcoming games
Run: python -m scripts.generate_all_analyses
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.session import AsyncSessionLocal
from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.services.analysis_generator import AnalysisGeneratorService
from app.services.sports_config import get_sport_config


async def generate_all_analyses():
    """Generate analyses for all upcoming games that don't have one yet."""
    
    sports_to_process = ["nba", "nhl", "nfl"]  # Add sports to generate for
    
    async with AsyncSessionLocal() as db:
        for sport in sports_to_process:
            sport_config = get_sport_config(sport)
            league = sport_config.code
            
            print(f"\n{'='*50}")
            print(f"Processing {league} games...")
            print(f"{'='*50}")
            
            now = datetime.utcnow()
            future_cutoff = now + timedelta(days=sport_config.lookahead_days)
            
            # Get upcoming games without analyses
            result = await db.execute(
                select(Game)
                .outerjoin(GameAnalysis, Game.id == GameAnalysis.game_id)
                .where(
                    Game.sport == league,
                    Game.start_time >= now,
                    Game.start_time <= future_cutoff,
                    GameAnalysis.id == None  # No analysis exists
                )
                .order_by(Game.start_time)
            )
            
            games_without_analyses = result.scalars().all()
            
            print(f"Found {len(games_without_analyses)} {league} games without analyses")
            
            if not games_without_analyses:
                print(f"All {league} games already have analyses!")
                continue
            
            # Generate analyses
            generator = AnalysisGeneratorService(db)
            
            for i, game in enumerate(games_without_analyses):
                try:
                    print(f"\n[{i+1}/{len(games_without_analyses)}] Generating analysis for: {game.away_team} @ {game.home_team}")
                    
                    analysis_content = await generator.generate_game_analysis(
                        game_id=str(game.id),
                        sport=sport,
                    )
                    
                    # Generate slug
                    from app.api.routes.analysis import _generate_slug
                    slug = _generate_slug(
                        home_team=game.home_team,
                        away_team=game.away_team,
                        league=league,
                        game_time=game.start_time
                    )
                    
                    # Generate SEO metadata
                    seo_metadata = {
                        "title": f"{game.away_team} vs {game.home_team} Prediction, Picks & Best Bets | {league}",
                        "description": analysis_content.get("opening_summary", "")[:160],
                        "keywords": f"{game.away_team}, {game.home_team}, {league}, prediction, picks, best bets",
                    }
                    
                    # Create analysis
                    analysis = GameAnalysis(
                        game_id=game.id,
                        slug=slug,
                        league=league,
                        matchup=f"{game.away_team} @ {game.home_team}",
                        analysis_content=analysis_content,
                        seo_metadata=seo_metadata,
                        expires_at=game.start_time + timedelta(hours=2),
                    )
                    db.add(analysis)
                    await db.commit()
                    
                    print(f"   ✓ Generated: {slug}")
                    
                except Exception as e:
                    print(f"   ✗ Error: {e}")
                    await db.rollback()
                    continue
            
        print(f"\n{'='*50}")
        print("Done generating analyses!")
        print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(generate_all_analyses())

