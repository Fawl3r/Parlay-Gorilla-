"""
Seed script to add subscription plans (Crypto + Card).

Run with:
    cd backend
    python scripts/seed_lifetime_plan.py

This creates or updates:
- PG_LIFETIME (crypto lifetime) for $499.99
- PG_PREMIUM_MONTHLY_CRYPTO (crypto monthly, time-based)
- PG_PREMIUM_ANNUAL_CRYPTO (crypto annual, time-based)
- PG_LIFETIME_CARD (card lifetime) for $499.99 (requires LemonSqueezy variant)
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import AsyncSessionLocal
from app.models.subscription_plan import SubscriptionPlan, BillingCycle, PaymentProvider


LIFETIME_PLAN = {
    "code": "PG_LIFETIME",
    "name": "Gorilla Lifetime",
    "description": "One-time payment for lifetime access to all premium features. Pay with Bitcoin (BTC) or USDC. Never pay again!",
    "price_cents": 49999,  # $499.99
    "currency": "USD",
    "billing_cycle": BillingCycle.lifetime.value,
    "provider": PaymentProvider.coinbase.value,
    "provider_product_id": None,  # Coinbase generates charge IDs dynamically
    "provider_price_id": None,
    "is_active": True,
    "is_featured": True,
    # Premium features
    "max_ai_parlays_per_day": -1,  # Unlimited
    "can_use_custom_builder": True,
    "can_use_upset_finder": True,
    "can_use_multi_sport": True,
    "can_save_parlays": True,
    "ad_free": True,
}

CRYPTO_MONTHLY_PLAN = {
    "code": "PG_PREMIUM_MONTHLY_CRYPTO",
    "name": "Gorilla Premium Monthly (Crypto)",
    "description": "Monthly premium access paid with crypto. Does not auto-renew — renew manually each month.",
    "price_cents": 1999,  # $19.99
    "currency": "USD",
    "billing_cycle": BillingCycle.monthly.value,
    "provider": PaymentProvider.coinbase.value,
    "provider_product_id": None,  # Coinbase generates charge IDs dynamically
    "provider_price_id": None,
    "is_active": True,
    "is_featured": False,
    # Premium features
    "max_ai_parlays_per_day": -1,
    "can_use_custom_builder": True,
    "can_use_upset_finder": True,
    "can_use_multi_sport": True,
    "can_save_parlays": True,
    "ad_free": True,
}

CRYPTO_ANNUAL_PLAN = {
    "code": "PG_PREMIUM_ANNUAL_CRYPTO",
    "name": "Gorilla Premium Annual (Crypto)",
    "description": "Annual premium access paid with crypto. Does not auto-renew — renew manually each year.",
    "price_cents": 19999,  # $199.99
    "currency": "USD",
    "billing_cycle": BillingCycle.annual.value,
    "provider": PaymentProvider.coinbase.value,
    "provider_product_id": None,  # Coinbase generates charge IDs dynamically
    "provider_price_id": None,
    "is_active": True,
    "is_featured": False,
    # Premium features
    "max_ai_parlays_per_day": -1,
    "can_use_custom_builder": True,
    "can_use_upset_finder": True,
    "can_use_multi_sport": True,
    "can_save_parlays": True,
    "ad_free": True,
}

CARD_LIFETIME_PLAN = {
    "code": "PG_LIFETIME_CARD",
    "name": "Gorilla Lifetime (Card)",
    "description": "One-time payment for lifetime access to all premium features. Pay with card. Never pay again!",
    "price_cents": 49999,  # $499.99
    "currency": "USD",
    "billing_cycle": BillingCycle.lifetime.value,
    "provider": PaymentProvider.lemonsqueezy.value,
    "provider_product_id": None,  # Use env var resolver: LEMONSQUEEZY_LIFETIME_VARIANT_ID
    "provider_price_id": None,
    "is_active": True,
    "is_featured": True,
    # Premium features
    "max_ai_parlays_per_day": -1,
    "can_use_custom_builder": True,
    "can_use_upset_finder": True,
    "can_use_multi_sport": True,
    "can_save_parlays": True,
    "ad_free": True,
}


async def seed_lifetime_plan():
    """Create or update the lifetime crypto plan."""
    print("=" * 60)
    print("Seeding Subscription Plans (Crypto + Card)")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # Check if plan already exists
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.code == LIFETIME_PLAN["code"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"\n✅ Plan '{LIFETIME_PLAN['code']}' already exists. Updating...")
            # Update existing plan
            for key, value in LIFETIME_PLAN.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            await db.commit()
            print(f"   Updated price: ${LIFETIME_PLAN['price_cents'] / 100:.2f}")
            print(f"   Provider: {LIFETIME_PLAN['provider']}")
            print(f"   Billing cycle: {LIFETIME_PLAN['billing_cycle']}")
        else:
            print(f"\n📝 Creating new plan '{LIFETIME_PLAN['code']}'...")
            # Create new plan
            plan = SubscriptionPlan(**LIFETIME_PLAN)
            db.add(plan)
            await db.commit()
            print(f"   ✅ Created successfully!")
            print(f"   Price: ${LIFETIME_PLAN['price_cents'] / 100:.2f}")
            print(f"   Provider: {LIFETIME_PLAN['provider']}")
            print(f"   Billing cycle: {LIFETIME_PLAN['billing_cycle']}")
        
        # Also ensure monthly and annual plans exist for card payments
        await ensure_card_plans(db)
        # Ensure crypto monthly/annual plans exist (time-based)
        await ensure_crypto_time_based_plans(db)
        # Ensure lifetime card plan exists ($499.99)
        await ensure_card_lifetime_plan(db)
        
        print("\n" + "=" * 60)
        print("✅ Lifetime plan seeding complete!")
        print("=" * 60)
        print("\nUsers can now pay $499.99 with:")
        print("  • Bitcoin (BTC)")
        print("  • USDC")
        print("  • Other cryptocurrencies supported by Coinbase Commerce")


async def ensure_card_plans(db: AsyncSession):
    """Ensure card payment plans also exist."""
    card_plans = [
        {
            "code": "PG_PREMIUM_MONTHLY",
            "name": "Gorilla Premium Monthly",
            "description": "Monthly premium subscription with full access to all features.",
            "price_cents": 999,  # $9.99
            "currency": "USD",
            "billing_cycle": BillingCycle.monthly.value,
            "provider": PaymentProvider.lemonsqueezy.value,
            "is_active": True,
            "is_featured": True,
            "max_ai_parlays_per_day": -1,
            "can_use_custom_builder": True,
            "can_use_upset_finder": True,
            "can_use_multi_sport": True,
            "can_save_parlays": True,
        },
        {
            "code": "PG_PREMIUM_ANNUAL",
            "name": "Gorilla Premium Annual",
            "description": "Annual premium subscription - save 2 months! Full access to all features.",
            "price_cents": 9999,  # $99.99
            "currency": "USD",
            "billing_cycle": BillingCycle.annual.value,
            "provider": PaymentProvider.lemonsqueezy.value,
            "is_active": True,
            "is_featured": False,
            "max_ai_parlays_per_day": -1,
            "can_use_custom_builder": True,
            "can_use_upset_finder": True,
            "can_use_multi_sport": True,
            "can_save_parlays": True,
        },
        {
            "code": "PG_FREE",
            "name": "Free",
            "description": "Get started with Parlay Gorilla for free.",
            "price_cents": 0,
            "currency": "USD",
            "billing_cycle": BillingCycle.monthly.value,
            "provider": PaymentProvider.lemonsqueezy.value,
            "is_active": True,
            "is_featured": False,
            "max_ai_parlays_per_day": 1,
            "can_use_custom_builder": False,
            "can_use_upset_finder": False,
            "can_use_multi_sport": False,
            "can_save_parlays": False,
        },
    ]
    
    for plan_data in card_plans:
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.code == plan_data["code"])
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            print(f"\n📝 Also creating '{plan_data['code']}'...")
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)
    
    await db.commit()


async def ensure_crypto_time_based_plans(db: AsyncSession):
    """Ensure crypto monthly/annual plans exist (time-based, manual renew)."""
    for plan_data in [CRYPTO_MONTHLY_PLAN, CRYPTO_ANNUAL_PLAN]:
        result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == plan_data["code"]))
        existing = result.scalar_one_or_none()
        if not existing:
            print(f"\n📝 Creating '{plan_data['code']}'...")
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)
    await db.commit()


async def ensure_card_lifetime_plan(db: AsyncSession):
    """Ensure the lifetime card plan exists ($499.99 one-time via LemonSqueezy)."""
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == CARD_LIFETIME_PLAN["code"]))
    existing = result.scalar_one_or_none()
    if existing:
        print(f"\n✅ Plan '{CARD_LIFETIME_PLAN['code']}' already exists. Updating...")
        for key, value in CARD_LIFETIME_PLAN.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
    else:
        print(f"\n📝 Creating '{CARD_LIFETIME_PLAN['code']}'...")
        plan = SubscriptionPlan(**CARD_LIFETIME_PLAN)
        db.add(plan)
    await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_lifetime_plan())

