"""
Verify that a lifetime user has all features unlocked.

Usage:
    python scripts/verify_lifetime_features.py <email>
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

async def verify_features(email: str):
    """Verify lifetime user has all features unlocked"""
    
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
        print(f"   Plan: {user.plan}")
        print(f"   Subscription Plan: {user.subscription_plan}")
        print(f"   Subscription Status: {user.subscription_status}")
        
        # Get access level
        service = SubscriptionService(db)
        access = await service.get_user_access_level(str(user.id))
        
        print(f"\n📊 Access Level Details:")
        print(f"   Tier: {access.tier}")
        print(f"   Plan Code: {access.plan_code}")
        print(f"   Is Lifetime: {access.is_lifetime}")
        print(f"   Subscription End: {access.subscription_end or 'Never (Lifetime)'}")
        
        print(f"\n🔓 Feature Access:")
        print(f"   ✅ Custom Builder: {access.can_use_custom_builder}")
        print(f"   ✅ Upset Finder: {access.can_use_upset_finder}")
        print(f"   ✅ Multi-Sport: {access.can_use_multi_sport}")
        print(f"   ✅ Save Parlays: {access.can_save_parlays}")
        print(f"   ✅ AI Parlays Per Day: {'Unlimited' if access.max_ai_parlays_per_day == -1 else access.max_ai_parlays_per_day}")
        print(f"   ✅ Remaining AI Parlays Today: {'Unlimited' if access.remaining_ai_parlays_today == -1 else access.remaining_ai_parlays_today}")
        
        # Check if all features are unlocked
        all_unlocked = (
            access.tier == "premium" and
            access.can_use_custom_builder and
            access.can_use_upset_finder and
            access.can_use_multi_sport and
            access.can_save_parlays and
            access.max_ai_parlays_per_day == -1 and
            access.is_lifetime
        )
        
        if all_unlocked:
            print(f"\n✅ All features are unlocked! User has full lifetime access.")
        else:
            print(f"\n⚠️  Some features may not be fully unlocked:")
            if access.tier != "premium":
                print(f"   - Tier is '{access.tier}' but should be 'premium'")
            if not access.can_use_custom_builder:
                print(f"   - Custom Builder is disabled")
            if not access.can_use_upset_finder:
                print(f"   - Upset Finder is disabled")
            if not access.can_use_multi_sport:
                print(f"   - Multi-Sport is disabled")
            if not access.can_save_parlays:
                print(f"   - Save Parlays is disabled")
            if access.max_ai_parlays_per_day != -1:
                print(f"   - AI Parlays limit is {access.max_ai_parlays_per_day} (should be unlimited)")
            if not access.is_lifetime:
                print(f"   - Subscription is not marked as lifetime")
        
        return all_unlocked

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/verify_lifetime_features.py <email>")
        print("Example: python scripts/verify_lifetime_features.py Fawl3r85@gmail.com")
        sys.exit(1)
    
    email = sys.argv[1].strip()
    print(f"Verifying lifetime features for: {email}\n")
    
    try:
        success = asyncio.run(verify_features(email))
        if success:
            print("\n✅ Verification complete - all features unlocked!")
            sys.exit(0)
        else:
            print("\n⚠️  Verification complete - some features may need attention")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

