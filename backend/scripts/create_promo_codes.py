"""
Create specific promo codes for F3 Parlay Gorilla.

Usage:
    python backend/scripts/create_promo_codes.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.session import AsyncSessionLocal
from app.models.promo_code import PromoRewardType
from app.services.promo_codes import PromoCodeService


async def create_promo_codes():
    """Create the standard promo codes for F3 Parlay Gorilla."""
    
    async with AsyncSessionLocal() as db:
        service = PromoCodeService(db)
        
        # Set expiration to 1 year from now
        expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        
        codes_created = []
        
        # 1. Free Month of Premium Code
        try:
            premium_code = await service.create_code(
                reward_type=PromoRewardType.premium_month,
                expires_at=expires_at,
                max_uses_total=100,  # Allow multiple users to use this
                code="F3FREEMONTH",  # Custom code
                notes="Free month of Premium access - promotional code"
            )
            codes_created.append({
                "code": premium_code.code,
                "type": "premium_month",
                "reward": "30 days of Premium access",
                "max_uses": premium_code.max_uses_total
            })
            print(f"✅ Created Premium Free Month code: {premium_code.code}")
        except ValueError as e:
            if "already exists" in str(e):
                print(f"⚠️  Premium code already exists (may need to check existing codes)")
            else:
                print(f"❌ Failed to create Premium code: {e}")
        
        # Note: F3LIFETIME code cannot be created via promo system yet
        # as lifetime is not a supported reward type.
        # Use grant_lifetime_membership.py script instead.
        print("\n📝 Note: F3LIFETIME code requires special handling.")
        print("   Lifetime membership is not yet supported as a promo reward type.")
        print("   Use backend/scripts/grant_lifetime_membership.py to grant lifetime access.")
        
        print(f"\n✅ Created {len(codes_created)} promo code(s)")
        return codes_created


if __name__ == "__main__":
    asyncio.run(create_promo_codes())



