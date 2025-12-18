"""
Test the subscription status API endpoint for a user.

Usage:
    python scripts/test_subscription_api.py <email>
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func
from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.services.subscription_service import SubscriptionService

async def test_subscription_api(email: str):
    """Test what the subscription API would return"""
    
    async with AsyncSessionLocal() as db:
        # Find user by email (case-insensitive)
        result = await db.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email {email} not found")
            return False
        
        print(f"✅ Found user: {user.email} (ID: {user.id})")
        
        # Get access level (what the API endpoint uses)
        service = SubscriptionService(db)
        access = await service.get_user_access_level(str(user.id))
        
        print(f"\n📊 API Response (what frontend receives):")
        print(f"   tier: '{access.tier}'")
        print(f"   plan_code: {access.plan_code}")
        print(f"   can_use_custom_builder: {access.can_use_custom_builder}")
        print(f"   can_use_upset_finder: {access.can_use_upset_finder}")
        print(f"   can_use_multi_sport: {access.can_use_multi_sport}")
        print(f"   can_save_parlays: {access.can_save_parlays}")
        print(f"   max_ai_parlays_per_day: {access.max_ai_parlays_per_day}")
        print(f"   remaining_ai_parlays_today: {access.remaining_ai_parlays_today}")
        print(f"   unlimited_ai_parlays: {access.max_ai_parlays_per_day == -1}")
        print(f"   is_lifetime: {access.is_lifetime}")
        print(f"   subscription_end: {access.subscription_end or 'None'}")
        
        # Check what frontend would compute
        is_premium = access.tier == 'premium'
        can_use_custom = access.can_use_custom_builder
        
        print(f"\n🔍 Frontend Computed Values:")
        print(f"   isPremium: {is_premium}")
        print(f"   canUseCustomBuilder: {can_use_custom}")
        print(f"   canUseUpsetFinder: {access.can_use_upset_finder}")
        print(f"   canUseMultiSport: {access.can_use_multi_sport}")
        
        if not is_premium or not can_use_custom:
            print(f"\n⚠️  ISSUE DETECTED:")
            if not is_premium:
                print(f"   - Frontend will show isPremium=false (tier is '{access.tier}')")
            if not can_use_custom:
                print(f"   - Frontend will show canUseCustomBuilder=false")
            print(f"\n   This would cause premium feature walls to appear!")
        else:
            print(f"\n✅ All values look correct - frontend should show features unlocked")
        
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_subscription_api.py <email>")
        print("Example: python scripts/test_subscription_api.py Fawl3r85@gmail.com")
        sys.exit(1)
    
    email = sys.argv[1].strip()
    print(f"Testing subscription API for: {email}\n")
    
    try:
        asyncio.run(test_subscription_api(email))
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

