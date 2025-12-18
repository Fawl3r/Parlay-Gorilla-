"""Test script to verify ATS/O/U percentages are calculated correctly"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.session import AsyncSessionLocal
from app.services.stats_scraper import StatsScraperService
from app.services.analysis.core_analysis_generator import CoreAnalysisGenerator
from app.models.game import Game
from app.models.team_stats import TeamStats
from sqlalchemy import select, and_


async def test_percentage_calculation():
    """Test that ATS/O/U percentages are calculated correctly"""
    print("\n" + "="*60)
    print("TEST: ATS/O/U Percentage Calculation")
    print("="*60 + "\n")
    
    async with AsyncSessionLocal() as db:
        scraper = StatsScraperService(db)
        generator = CoreAnalysisGenerator(db, stats_scraper=scraper)
        
        # Get a recent game
        result = await db.execute(
            select(Game)
            .where(Game.sport == "NFL")
            .order_by(Game.start_time.desc())
            .limit(1)
        )
        game = result.scalar_one_or_none()
        
        if not game:
            print("✗ No games found in database")
            return
        
        print(f"Testing with game: {game.away_team} @ {game.home_team}")
        print("-" * 40)
        
        # Get team stats from database
        home_result = await db.execute(
            select(TeamStats).where(
                and_(
                    TeamStats.team_name == game.home_team,
                    TeamStats.season == str(game.start_time.year),
                    TeamStats.week.is_(None)
                )
            )
        )
        home_stats = home_result.scalar_one_or_none()
        
        away_result = await db.execute(
            select(TeamStats).where(
                and_(
                    TeamStats.team_name == game.away_team,
                    TeamStats.season == str(game.start_time.year),
                    TeamStats.week.is_(None)
                )
            )
        )
        away_stats = away_result.scalar_one_or_none()
        
        if home_stats:
            print(f"\n{game.home_team} ATS Stats:")
            print(f"  Wins: {home_stats.ats_wins}, Losses: {home_stats.ats_losses}")
            print(f"  Win % (DB): {home_stats.ats_win_percentage:.2f}")
            
            # Calculate expected percentage
            ats_total = home_stats.ats_wins + home_stats.ats_losses
            if ats_total > 0:
                expected_pct = (home_stats.ats_wins / ats_total) * 100.0
                print(f"  Expected %: {expected_pct:.2f}")
                
                if abs(home_stats.ats_win_percentage - expected_pct) > 0.01:
                    print(f"  ⚠ WARNING: Percentage mismatch!")
                else:
                    print(f"  ✓ Percentage matches expected")
            
            print(f"\n{game.home_team} O/U Stats:")
            print(f"  Overs: {home_stats.over_wins}, Unders: {home_stats.under_wins}")
            print(f"  Over % (DB): {home_stats.over_percentage:.2f}")
            
            ou_total = home_stats.over_wins + home_stats.under_wins
            if ou_total > 0:
                expected_ou = (home_stats.over_wins / ou_total) * 100.0
                print(f"  Expected %: {expected_ou:.2f}")
                
                if abs(home_stats.over_percentage - expected_ou) > 0.01:
                    print(f"  ⚠ WARNING: Percentage mismatch!")
                else:
                    print(f"  ✓ Percentage matches expected")
        
        if away_stats:
            print(f"\n{game.away_team} ATS Stats:")
            print(f"  Wins: {away_stats.ats_wins}, Losses: {away_stats.ats_losses}")
            print(f"  Win % (DB): {away_stats.ats_win_percentage:.2f}")
            
            ats_total = away_stats.ats_wins + away_stats.ats_losses
            if ats_total > 0:
                expected_pct = (away_stats.ats_wins / ats_total) * 100.0
                print(f"  Expected %: {expected_pct:.2f}")
                
                if abs(away_stats.ats_win_percentage - expected_pct) > 0.01:
                    print(f"  ⚠ WARNING: Percentage mismatch!")
                else:
                    print(f"  ✓ Percentage matches expected")
        
        # Test the format functions
        print("\n" + "-" * 40)
        print("Testing format functions:")
        print("-" * 40)
        
        season = str(game.start_time.year)
        matchup_data = await scraper.get_matchup_data(
            home_team=game.home_team,
            away_team=game.away_team,
            league=game.sport,
            season=season,
            game_time=game.start_time
        )
        
        home_ats = matchup_data.get("home_team_stats", {}).get("ats_trends", {})
        away_ats = matchup_data.get("away_team_stats", {}).get("ats_trends", {})
        home_ou = matchup_data.get("home_team_stats", {}).get("over_under_trends", {})
        away_ou = matchup_data.get("away_team_stats", {}).get("over_under_trends", {})
        
        # Test _format_ats
        if home_ats:
            home_ats_text = CoreAnalysisGenerator._format_ats(
                team=game.home_team,
                ats=home_ats
            )
            print(f"\nHome ATS Format: {home_ats_text}")
            
            # Check for 10000% issue
            if "10000" in home_ats_text or "10000.0" in home_ats_text:
                print(f"  ✗ ERROR: Found 10000% in formatted text!")
            else:
                print(f"  ✓ No 10000% issue")
        
        # Test _compare_ats
        if home_ats and away_ats:
            comparison = CoreAnalysisGenerator._compare_ats(
                home=home_ats,
                away=away_ats,
                home_team=game.home_team,
                away_team=game.away_team
            )
            print(f"\nATS Comparison: {comparison}")
            
            if "10000" in comparison or "10000.0" in comparison:
                print(f"  ✗ ERROR: Found 10000% in comparison!")
            else:
                print(f"  ✓ No 10000% issue")
        
        # Test _compare_ou
        if home_ou and away_ou:
            ou_comparison = CoreAnalysisGenerator._compare_ou(
                home=home_ou,
                away=away_ou,
                home_team=game.home_team,
                away_team=game.away_team
            )
            print(f"\nO/U Comparison: {ou_comparison}")
            
            if "10000" in ou_comparison or "10000.0" in ou_comparison:
                print(f"  ✗ ERROR: Found 10000% in O/U comparison!")
            else:
                print(f"  ✓ No 10000% issue")
        
        print("\n" + "="*60)
        print("Test complete!")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_percentage_calculation())



