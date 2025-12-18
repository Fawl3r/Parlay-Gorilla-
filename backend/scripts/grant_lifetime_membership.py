"""
Grant lifetime membership to a user by email.

Usage:
    python scripts/grant_lifetime_membership.py Fawl3r85@gmail.com
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.models.user import User, UserPlan
from app.models.subscription import Subscription, SubscriptionStatus
from app.services.payment_service import PaymentService

async def grant_lifetime_membership(email: str):
    """Grant lifetime membership to a user"""
    
    async with AsyncSessionLocal() as db:
        # Find user by email (case-insensitive)
        from sqlalchemy import func
        result = await db.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email {email} not found")
            return False
        
        print(f"✅ Found user: {user.email} (ID: {user.id})")
        print(f"   Current plan: {user.plan}")
        
        # Check if user already has a lifetime subscription
        payment_service = PaymentService(db)
        existing_sub = await payment_service.get_active_subscription(str(user.id))
        
        if existing_sub and existing_sub.is_lifetime:
            print(f"⚠️  User already has a lifetime subscription (ID: {existing_sub.id})")
            response = input("Do you want to keep the existing subscription? (yes/no): ")
            if response.lower() != 'no':
                print("Keeping existing subscription.")
                return True
            # Mark old subscription as cancelled
            existing_sub.status = SubscriptionStatus.cancelled.value
            existing_sub.cancelled_at = datetime.now(timezone.utc)
        
        # Create lifetime subscription
        print("\nCreating lifetime subscription...")
        
        # Use elite plan for lifetime members
        plan = "elite"
        
        subscription = Subscription(
            user_id=user.id,
            plan=plan,
            provider="manual",
            provider_subscription_id=f"lifetime_{user.id}",
            status=SubscriptionStatus.active.value,
            is_lifetime=True,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=None,  # Lifetime has no end date
            cancel_at_period_end=False,
            provider_metadata={
                "granted_by": "admin_script",
                "granted_at": datetime.now(timezone.utc).isoformat(),
                "reason": "manual_lifetime_grant"
            }
        )
        
        db.add(subscription)
        
        # Update user plan to elite
        user.plan = UserPlan.elite.value
        user.subscription_plan = plan
        user.subscription_status = "active"
        
        await db.commit()
        await db.refresh(subscription)
        await db.refresh(user)
        
        print(f"✅ Successfully granted lifetime membership!")
        print(f"   Subscription ID: {subscription.id}")
        print(f"   Plan: {plan}")
        print(f"   Status: {subscription.status}")
        print(f"   Is Lifetime: {subscription.is_lifetime}")
        print(f"   User plan updated to: {user.plan}")
        
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/grant_lifetime_membership.py <email>")
        print("Example: python scripts/grant_lifetime_membership.py Fawl3r85@gmail.com")
        sys.exit(1)
    
    email = sys.argv[1].strip()
    print(f"Granting lifetime membership to: {email}\n")
    
    try:
        success = asyncio.run(grant_lifetime_membership(email))
        if success:
            print("\n✅ Done!")
            sys.exit(0)
        else:
            print("\n❌ Failed to grant lifetime membership")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

