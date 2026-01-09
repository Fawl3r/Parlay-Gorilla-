"""
Seed script to add Stripe credit pack subscription plans.

This script reads Stripe Price IDs from environment variables and creates/updates
subscription plans in the database for credit packs.

Run with:
    cd backend
    python scripts/seed_stripe_credit_packs.py

Environment variables required:
    STRIPE_PRICE_ID_CREDITS_10=price_xxxxx
    STRIPE_PRICE_ID_CREDITS_25=price_xxxxx
    STRIPE_PRICE_ID_CREDITS_50=price_xxxxx
    STRIPE_PRICE_ID_CREDITS_100=price_xxxxx

This creates or updates:
- PG_CREDITS_10 (10 Credits - $9.99)
- PG_CREDITS_25 (25 Credits - $19.99)
- PG_CREDITS_50 (50 Credits - $34.99)
- PG_CREDITS_100 (100 Credits - $59.99)
"""

import asyncio
import sys
import os
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import AsyncSessionLocal
from app.models.subscription_plan import SubscriptionPlan, BillingCycle, PaymentProvider
from app.core.config import settings
from app.core.billing_config import CREDIT_PACKS, CreditPackId


CREDIT_PACK_PLANS = [
    {
        "code": f"PG_{CreditPackId.CREDITS_10.value.upper()}",
        "credit_pack_id": CreditPackId.CREDITS_10.value,
        "env_var": "stripe_price_id_credits_10",
    },
    {
        "code": f"PG_{CreditPackId.CREDITS_25.value.upper()}",
        "credit_pack_id": CreditPackId.CREDITS_25.value,
        "env_var": "stripe_price_id_credits_25",
    },
    {
        "code": f"PG_{CreditPackId.CREDITS_50.value.upper()}",
        "credit_pack_id": CreditPackId.CREDITS_50.value,
        "env_var": "stripe_price_id_credits_50",
    },
    {
        "code": f"PG_{CreditPackId.CREDITS_100.value.upper()}",
        "credit_pack_id": CreditPackId.CREDITS_100.value,
        "env_var": "stripe_price_id_credits_100",
    },
]


async def seed_stripe_credit_packs():
    """Create or update Stripe credit pack subscription plans."""
    print("=" * 60)
    print("Seeding Stripe Credit Pack Plans")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for plan_config in CREDIT_PACK_PLANS:
            code = plan_config["code"]
            credit_pack_id = plan_config["credit_pack_id"]
            env_var_name = plan_config["env_var"]
            
            # Get Stripe Price ID from env var
            price_id = getattr(settings, env_var_name, None)
            
            if not price_id:
                print(f"\n⚠️  Skipping '{code}': {env_var_name} not set in environment")
                skipped_count += 1
                continue
            
            # Get credit pack config for pricing
            credit_pack = CREDIT_PACKS.get(credit_pack_id)
            if not credit_pack:
                print(f"\n⚠️  Skipping '{code}': Credit pack '{credit_pack_id}' not found in config")
                skipped_count += 1
                continue
            
            # Check if plan already exists
            result = await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.code == code)
            )
            existing = result.scalar_one_or_none()
            
            plan_data = {
                "code": code,
                "name": f"{credit_pack.name} (Stripe)",
                "description": f"Purchase {credit_pack.total_credits} credits for AI parlays and custom builder actions",
                "price_cents": credit_pack.price_cents,
                "currency": credit_pack.currency,
                "billing_cycle": BillingCycle.one_time.value,
                "provider": PaymentProvider.stripe.value,
                "provider_price_id": price_id,
                "is_active": True,
                "is_featured": credit_pack.is_featured,
                # Credit packs don't grant subscription features
                "max_ai_parlays_per_day": 0,
                "can_use_custom_builder": False,
                "can_use_upset_finder": False,
                "can_use_multi_sport": False,
                "can_save_parlays": False,
                "ad_free": False,
            }
            
            if existing:
                print(f"\n✅ Plan '{code}' already exists. Updating...")
                # Update existing plan
                for key, value in plan_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                await db.commit()
                updated_count += 1
                print(f"   Updated: {credit_pack.name} - ${credit_pack.price:.2f}")
                print(f"   Stripe Price ID: {price_id}")
                print(f"   Credits: {credit_pack.total_credits}")
            else:
                print(f"\n📝 Creating new plan '{code}'...")
                # Create new plan
                plan = SubscriptionPlan(**plan_data)
                db.add(plan)
                await db.commit()
                created_count += 1
                print(f"   ✅ Created successfully!")
                print(f"   Name: {credit_pack.name}")
                print(f"   Price: ${credit_pack.price:.2f}")
                print(f"   Stripe Price ID: {price_id}")
                print(f"   Credits: {credit_pack.total_credits}")
        
        print("\n" + "=" * 60)
        print("✅ Credit pack seeding complete!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  Created: {created_count}")
        print(f"  Updated: {updated_count}")
        print(f"  Skipped: {skipped_count}")
        
        if skipped_count > 0:
            print(f"\n⚠️  {skipped_count} plan(s) were skipped because Stripe Price IDs are not set.")
            print("   Set the following environment variables:")
            for plan_config in CREDIT_PACK_PLANS:
                env_var = plan_config["env_var"]
                price_id = getattr(settings, env_var, None)
                if not price_id:
                    print(f"     {env_var.upper()}=price_xxxxx")


if __name__ == "__main__":
    asyncio.run(seed_stripe_credit_packs())

