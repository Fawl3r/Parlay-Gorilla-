"""Quick verification script for fixes"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database.session import AsyncSessionLocal
from app.models.team_stats import TeamStats
from sqlalchemy import select, and_, func


async def verify_fixes():
    """Verify all fixes are working"""
    print("\n" + "="*60)
    print("VERIFICATION: Checking Fixes")
    print("="*60 + "\n")
    
    async with AsyncSessionLocal() as db:
        # Check 1: No percentages > 100%
        result = await db.execute(
            select(func.count(TeamStats.id))
            .where(
                and_(
                    TeamStats.ats_win_percentage > 100.0
                )
            )
        )
        bad_ats = result.scalar() or 0
        
        result = await db.execute(
            select(func.count(TeamStats.id))
            .where(
                and_(
                    TeamStats.over_percentage > 100.0
                )
            )
        )
        bad_ou = result.scalar() or 0
        
        print(f"1. Percentage Check:")
        print(f"   Teams with ATS % > 100: {bad_ats}")
        print(f"   Teams with O/U % > 100: {bad_ou}")
        if bad_ats == 0 and bad_ou == 0:
            print(f"   PASS: No percentage issues found")
        else:
            print(f"   FAIL: Found percentage issues!")
        
        # Check 2: Teams with offensive stats
        result = await db.execute(
            select(func.count(TeamStats.id))
            .where(
                and_(
                    TeamStats.season == "2024",
                    TeamStats.week.is_(None),
                    TeamStats.points_per_game > 0
                )
            )
        )
        teams_with_stats = result.scalar() or 0
        
        print(f"\n2. Offensive Stats Check:")
        print(f"   Teams with PPG > 0: {teams_with_stats}")
        if teams_with_stats > 0:
            print(f"   PASS: Stats are being stored")
        else:
            print(f"   WARNING: No offensive stats found")
        
        # Check 3: Teams with yards data
        result = await db.execute(
            select(func.count(TeamStats.id))
            .where(
                and_(
                    TeamStats.season == "2024",
                    TeamStats.week.is_(None),
                    TeamStats.yards_per_game > 0
                )
            )
        )
        teams_with_ypg = result.scalar() or 0
        
        print(f"\n3. Yards Per Game Check:")
        print(f"   Teams with YPG > 0: {teams_with_ypg}")
        if teams_with_ypg > 0:
            print(f"   PASS: YPG is being extracted")
        else:
            print(f"   WARNING: YPG extraction may need improvement")
        
        # Check 4: Sample team stats
        result = await db.execute(
            select(TeamStats)
            .where(
                and_(
                    TeamStats.season == "2024",
                    TeamStats.week.is_(None),
                    TeamStats.points_per_game > 0
                )
            )
            .limit(3)
        )
        sample_teams = result.scalars().all()
        
        print(f"\n4. Sample Team Stats:")
        for team in sample_teams:
            print(f"   {team.team_name}:")
            print(f"     PPG: {team.points_per_game:.1f}, YPG: {team.yards_per_game:.1f}")
            print(f"     PAPG: {team.points_allowed_per_game:.1f}, YAPG: {team.yards_allowed_per_game:.1f}")
            print(f"     ATS: {team.ats_wins}-{team.ats_losses} ({team.ats_win_percentage:.1f}%)")
            print(f"     O/U: {team.over_wins}-{team.under_wins} ({team.over_percentage:.1f}%)")
        
        print("\n" + "="*60)
        print("Verification complete!")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(verify_fixes())



