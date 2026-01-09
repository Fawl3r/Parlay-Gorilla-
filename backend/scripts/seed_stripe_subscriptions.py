"""
Seed script to add Stripe subscription plans.

This script reads Stripe Price IDs from environment variables and creates/updates
subscription plans in the database for Stripe subscriptions.

Run with:
    cd backend
    python scripts/seed_stripe_subscriptions.py

Environment variables required:
    STRIPE_PRICE_ID_PRO_MONTHLY=price_xxxxx
    STRIPE_PRICE_ID_PRO_ANNUAL=price_xxxxx
    STRIPE_PRICE_ID_PRO_LIFETIME=price_xxxxx

This creates or updates:
- PG_PRO_MONTHLY (Monthly Premium - $9.99/month)
- PG_PRO_ANNUAL (Annual Premium - $99.99/year)
- PG_LIFETIME_CARD (Lifetime - $499.99 one-time)
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
from app.core.config import settings


SUBSCRIPTION_PLANS = [
    {
        "code": "PG_PRO_MONTHLY",
        "name": "Gorilla Pro Monthly",
        "description": "Monthly premium subscription with full access to all features. Unlimited AI parlays, custom builder, and more.",
        "price_cents": 999,  # $9.99
        "currency": "USD",
        "billing_cycle": BillingCycle.monthly.value,
        "env_var": "stripe_price_id_pro_monthly",
        "is_featured": True,
    },
    {
        "code": "PG_PRO_ANNUAL",
        "name": "Gorilla Pro Annual",
        "description": "Annual premium subscription - save 17%! Full access to all features. Billed annually.",
        "price_cents": 9999,  # $99.99
        "currency": "USD",
        "billing_cycle": BillingCycle.annual.value,
        "env_var": "stripe_price_id_pro_annual",
        "is_featured": False,
    },
    {
        "code": "PG_LIFETIME_CARD",
        "name": "Gorilla Lifetime (Card)",
        "description": "One-time payment for lifetime access to all premium features. Pay with card. Never pay again!",
        "price_cents": 49999,  # $499.99
        "currency": "USD",
        "billing_cycle": BillingCycle.lifetime.value,
        "env_var": "stripe_price_id_pro_lifetime",
        "is_featured": True,
    },
]


async def seed_stripe_subscriptions():
    """Create or update Stripe subscription plans."""
    print("=" * 60)
    print("Seeding Stripe Subscription Plans")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for plan_config in SUBSCRIPTION_PLANS:
            code = plan_config["code"]
            env_var_name = plan_config["env_var"]
            
            # Get Stripe Price ID from env var
            price_id = getattr(settings, env_var_name, None)
            
            if not price_id:
                print(f"\n⚠️  Skipping '{code}': {env_var_name} not set in environment")
                skipped_count += 1
                continue
            
            # Check if plan already exists
            result = await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.code == code)
            )
            existing = result.scalar_one_or_none()
            
            plan_data = {
                "code": code,
                "name": plan_config["name"],
                "description": plan_config["description"],
                "price_cents": plan_config["price_cents"],
                "currency": plan_config["currency"],
                "billing_cycle": plan_config["billing_cycle"],
                "provider": PaymentProvider.stripe.value,
                "provider_price_id": price_id,
                "is_active": True,
                "is_featured": plan_config["is_featured"],
                # Premium features
                "max_ai_parlays_per_day": -1,  # Unlimited
                "can_use_custom_builder": True,
                "can_use_upset_finder": True,
                "can_use_multi_sport": True,
                "can_save_parlays": True,
                "ad_free": True,
            }
            
            if existing:
                print(f"\n✅ Plan '{code}' already exists. Updating...")
                # Update existing plan
                for key, value in plan_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                await db.commit()
                updated_count += 1
                print(f"   Updated: {plan_config['name']} - ${plan_config['price_cents'] / 100:.2f}")
                print(f"   Stripe Price ID: {price_id}")
                print(f"   Billing Cycle: {plan_config['billing_cycle']}")
            else:
                print(f"\n📝 Creating new plan '{code}'...")
                # Create new plan
                plan = SubscriptionPlan(**plan_data)
                db.add(plan)
                await db.commit()
                created_count += 1
                print(f"   ✅ Created successfully!")
                print(f"   Name: {plan_config['name']}")
                print(f"   Price: ${plan_config['price_cents'] / 100:.2f}")
                print(f"   Stripe Price ID: {price_id}")
                print(f"   Billing Cycle: {plan_config['billing_cycle']}")
        
        print("\n" + "=" * 60)
        print("✅ Stripe subscription seeding complete!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  Created: {created_count}")
        print(f"  Updated: {updated_count}")
        print(f"  Skipped: {skipped_count}")
        
        if skipped_count > 0:
            print(f"\n⚠️  {skipped_count} plan(s) were skipped because Stripe Price IDs are not set.")
            print("   Set the following environment variables:")
            for plan_config in SUBSCRIPTION_PLANS:
                env_var = plan_config["env_var"]
                price_id = getattr(settings, env_var, None)
                if not price_id:
                    print(f"     {env_var.upper()}=price_xxxxx")


if __name__ == "__main__":
    asyncio.run(seed_stripe_subscriptions())

