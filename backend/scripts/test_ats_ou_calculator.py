"""Test ATS/Over-Under calculator with Week 15 games"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import AsyncSessionLocal
from app.services.ats_ou_calculator import ATSOUCalculator


async def test_calculator():
    """Test ATS/OU calculator with Week 15"""
    print("\n" + "="*60)
    print("ATS/OVER-UNDER CALCULATOR TEST")
    print("="*60 + "\n")
    
    async with AsyncSessionLocal() as db:
        calculator = ATSOUCalculator(db)
        
        print("Testing with Week 15 games...")
        result = await calculator.calculate_season_trends(
            season="2024",
            season_type="REG",
            weeks=[15]  # Just Week 15 for testing
        )
        
        print(f"\n✓ Results:")
        print(f"  Games processed: {result.get('games_processed', 0)}")
        print(f"  Teams updated: {result.get('teams_updated', 0)}")
        
        if result.get('teams'):
            print(f"  Teams: {', '.join(result['teams'][:10])}")
            if len(result['teams']) > 10:
                print(f"  ... and {len(result['teams']) - 10} more")
        
        if result.get('error'):
            print(f"  ⚠ Error: {result['error']}")
        
        print("\n" + "="*60)
        print("Test complete!")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_calculator())

