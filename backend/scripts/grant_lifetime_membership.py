"""
Grant lifetime membership to a user by email.

Usage:
    python scripts/grant_lifetime_membership.py Fawl3r85@gmail.com
    
    # For production, set DATABASE_URL environment variable:
    DATABASE_URL=postgresql://... python scripts/grant_lifetime_membership.py Fawl3r85@gmail.com
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.user import User, UserPlan
from app.models.subscription import Subscription, SubscriptionStatus
from app.services.payment_service import PaymentService


def get_production_session():
    """Get database session, using DATABASE_URL from environment if set."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fall back to default session
        from app.database.session import AsyncSessionLocal
        return AsyncSessionLocal
    
    # Ensure asyncpg driver for PostgreSQL
    if db_url.startswith("postgresql+asyncpg://"):
        pass
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def grant_lifetime_membership(email: str):
    """Grant lifetime membership to a user"""
    
    SessionLocal = get_production_session()
    async with SessionLocal() as db:
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
            print("Keeping existing subscription.")
            return True
        
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

