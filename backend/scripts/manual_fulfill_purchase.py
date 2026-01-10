"""
Manual fulfillment script for testing purchases.

Use this when a webhook failed or you need to manually grant access after a test purchase.

Usage:
    cd backend
    python scripts/manual_fulfill_purchase.py --type credit_pack --session-id cs_test_xxxxx --user-id <user-id> --pack-id credits_25
    python scripts/manual_fulfill_purchase.py --type lifetime --session-id cs_test_xxxxx --user-id <user-id> --plan-code PG_LIFETIME_CARD
"""

import asyncio
import sys
import os
import argparse
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import AsyncSessionLocal
from app.services.credit_pack_fulfillment_service import CreditPackFulfillmentService
from app.api.routes.webhooks.stripe_webhook_routes import _handle_lifetime_subscription_purchase
from app.services.stripe_service import StripeService


async def fulfill_credit_pack(
    user_id: str,
    credit_pack_id: str,
    session_id: str,
):
    """Manually fulfill a credit pack purchase."""
    async with AsyncSessionLocal() as db:
        service = CreditPackFulfillmentService(db)
        result = await service.fulfill_credit_pack_purchase(
            provider="stripe",
            provider_order_id=session_id,
            user_id=user_id,
            credit_pack_id=credit_pack_id,
        )
        
        if result.applied:
            print(f"✅ Successfully fulfilled credit pack purchase!")
            print(f"   Credits added: {result.credits_added}")
            print(f"   New balance: {result.new_balance}")
            print(f"   User ID: {user_id}")
            print(f"   Pack ID: {credit_pack_id}")
            print(f"   Session ID: {session_id}")
        else:
            print(f"⚠️  Purchase already fulfilled (idempotency check passed)")
            print(f"   Credits would have been: {result.credits_added}")
            print(f"   Current balance: {result.new_balance}")


async def fulfill_lifetime_subscription(
    user_id: str,
    plan_code: str,
    session_id: str,
):
    """Manually fulfill a lifetime subscription purchase."""
    async with AsyncSessionLocal() as db:
        stripe_service = StripeService(db)
        try:
            await _handle_lifetime_subscription_purchase(
                db=db,
                user_id=user_id,
                plan_code=plan_code,
                session_id=session_id,
                stripe_service=stripe_service,
            )
            print(f"✅ Successfully fulfilled lifetime subscription purchase!")
            print(f"   User ID: {user_id}")
            print(f"   Plan Code: {plan_code}")
            print(f"   Session ID: {session_id}")
        except Exception as e:
            print(f"❌ Error fulfilling lifetime subscription: {e}")
            raise


async def main():
    parser = argparse.ArgumentParser(description="Manually fulfill a Stripe purchase")
    parser.add_argument(
        "--type",
        required=True,
        choices=["credit_pack", "lifetime"],
        help="Type of purchase to fulfill",
    )
    parser.add_argument(
        "--session-id",
        required=True,
        help="Stripe checkout session ID (e.g., cs_test_xxxxx)",
    )
    parser.add_argument(
        "--user-id",
        required=True,
        help="User ID (UUID)",
    )
    parser.add_argument(
        "--pack-id",
        help="Credit pack ID (required for credit_pack type): credits_10, credits_25, credits_50, credits_100",
    )
    parser.add_argument(
        "--plan-code",
        default="PG_LIFETIME_CARD",
        help="Plan code for lifetime subscription (default: PG_LIFETIME_CARD)",
    )
    
    args = parser.parse_args()
    
    # Validate user_id is a valid UUID
    try:
        uuid.UUID(args.user_id)
    except ValueError:
        print(f"❌ Invalid user ID format: {args.user_id}")
        print("   User ID must be a valid UUID")
        return
    
    if args.type == "credit_pack":
        if not args.pack_id:
            print("❌ --pack-id is required for credit_pack type")
            print("   Options: credits_10, credits_25, credits_50, credits_100")
            return
        
        if args.pack_id not in ["credits_10", "credits_25", "credits_50", "credits_100"]:
            print(f"❌ Invalid pack ID: {args.pack_id}")
            print("   Options: credits_10, credits_25, credits_50, credits_100")
            return
        
        await fulfill_credit_pack(
            user_id=args.user_id,
            credit_pack_id=args.pack_id,
            session_id=args.session_id,
        )
    
    elif args.type == "lifetime":
        await fulfill_lifetime_subscription(
            user_id=args.user_id,
            plan_code=args.plan_code,
            session_id=args.session_id,
        )


if __name__ == "__main__":
    asyncio.run(main())

