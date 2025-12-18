"""Test script to check ATS and O/U data for teams across all sports"""
import asyncio
from app.database.session import AsyncSessionLocal
from sqlalchemy import select, func
from app.models.team_stats import TeamStats
from app.services.stats_scraper import StatsScraperService

async def test_ats_ou_data():
    """Check ATS and O/U data for teams across all sports"""
    async with AsyncSessionLocal() as db:
        scraper = StatsScraperService(db)
        
        sports = ["NFL", "NBA", "NHL", "MLB"]
        current_year = 2025
        season = str(current_year)
        
        print("=" * 80)
        print("ATS AND O/U DATA TEST - ALL SPORTS")
        print("=" * 80)
        
        for sport in sports:
            print(f"\n{'='*80}")
            print(f"SPORT: {sport}")
            print(f"{'='*80}")
            
            # Get all teams for this sport
            result = await db.execute(
                select(TeamStats).where(
                    TeamStats.season == season,
                    TeamStats.week.is_(None)
                ).order_by(TeamStats.team_name)
            )
            all_stats = result.scalars().all()
            
            # Filter by sport (check if team appears in games for this sport)
            from app.models.game import Game
            # Get distinct home teams
            home_result = await db.execute(
                select(func.distinct(Game.home_team)).where(Game.sport == sport)
            )
            # Get distinct away teams
            away_result = await db.execute(
                select(func.distinct(Game.away_team)).where(Game.sport == sport)
            )
            sport_teams = set()
            for row in home_result.all():
                if row[0]:
                    sport_teams.add(row[0])
            for row in away_result.all():
                if row[0]:
                    sport_teams.add(row[0])
            
            # Filter stats to teams in this sport
            sport_stats = [s for s in all_stats if s.team_name in sport_teams]
            
            if not sport_stats:
                print(f"  No team stats found for {sport}")
                continue
            
            print(f"\nFound {len(sport_stats)} teams with stats:\n")
            
            # Show stats for each team
            for stats in sport_stats[:10]:  # Limit to first 10 teams per sport
                print(f"  {stats.team_name}:")
                print(f"    Record: {stats.wins}-{stats.losses}-{stats.ties} (Win%: {stats.win_percentage:.1f}%)")
                print(f"    PPG: {stats.points_per_game:.1f}, PAPG: {stats.points_allowed_per_game:.1f}")
                
                # ATS Data
                ats_total = stats.ats_wins + stats.ats_losses
                if ats_total > 0:
                    print(f"    ATS: {stats.ats_wins}-{stats.ats_losses}-{stats.ats_pushes} "
                          f"(Win%: {stats.ats_win_percentage:.2f}%, "
                          f"Recent: {stats.ats_recent_wins}-{stats.ats_recent_losses})")
                else:
                    print(f"    ATS: No data (0-0-0)")
                
                # O/U Data
                ou_total = stats.over_wins + stats.under_wins
                if ou_total > 0:
                    print(f"    O/U: Over {stats.over_wins}-Under {stats.under_wins} "
                          f"(Over%: {stats.over_percentage:.2f}%, "
                          f"Avg Total: {stats.avg_total_points:.1f})")
                else:
                    print(f"    O/U: No data (0-0)")
                
                # Test what scraper returns
                scraper_stats = await scraper.get_team_stats(stats.team_name, season)
                if scraper_stats:
                    ats_trends = scraper_stats.get("ats_trends", {})
                    ou_trends = scraper_stats.get("over_under_trends", {})
                    print(f"    Scraper Returns:")
                    print(f"      ATS: {ats_trends.get('wins', 0)}-{ats_trends.get('losses', 0)}-{ats_trends.get('pushes', 0)} "
                          f"(Win%: {ats_trends.get('win_percentage', 0):.2f})")
                    print(f"      O/U: Over {ou_trends.get('overs', 0)}-Under {ou_trends.get('unders', 0)} "
                          f"(Over%: {ou_trends.get('over_percentage', 0):.2f})")
                print()
            
            if len(sport_stats) > 10:
                print(f"  ... and {len(sport_stats) - 10} more teams")
            
            # Summary statistics
            teams_with_ats = sum(1 for s in sport_stats if (s.ats_wins + s.ats_losses) > 0)
            teams_with_ou = sum(1 for s in sport_stats if (s.over_wins + s.under_wins) > 0)
            
            print(f"\n  Summary for {sport}:")
            print(f"    Total teams: {len(sport_stats)}")
            print(f"    Teams with ATS data: {teams_with_ats}")
            print(f"    Teams with O/U data: {teams_with_ou}")
            
            if teams_with_ats > 0:
                avg_ats_pct = sum(s.ats_win_percentage for s in sport_stats if (s.ats_wins + s.ats_losses) > 0) / teams_with_ats
                print(f"    Average ATS win%: {avg_ats_pct:.2f}%")
            
            if teams_with_ou > 0:
                avg_ou_pct = sum(s.over_percentage for s in sport_stats if (s.over_wins + s.under_wins) > 0) / teams_with_ou
                print(f"    Average O/U over%: {avg_ou_pct:.2f}%")
        
        print(f"\n{'='*80}")
        print("TEST COMPLETE")
        print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(test_ats_ou_data())

