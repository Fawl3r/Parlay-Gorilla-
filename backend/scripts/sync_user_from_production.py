"""Sync a user from production database to local database.

This script allows you to copy your production user account to local development
so you can login with the same credentials.

Usage:
    python scripts/sync_user_from_production.py --email your@email.com --prod-db-url "postgresql://..." --local-db-url "postgresql://..."
    
Or set environment variables:
    PROD_DATABASE_URL=postgresql://...
    LOCAL_DATABASE_URL=postgresql://...
    USER_EMAIL=your@email.com
    python scripts/sync_user_from_production.py
"""

import asyncio
import os
import sys
import argparse
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.user import User
from app.services.auth import EmailNormalizer


async def sync_user(
    prod_db_url: str,
    local_db_url: str,
    email: str,
    overwrite: bool = False
):
    """Sync a user from production to local database."""
    
    # Normalize email
    email_normalizer = EmailNormalizer()
    normalized_email = email_normalizer.normalize(email)
    if not normalized_email:
        print(f"❌ Invalid email: {email}")
        return False
    
    print(f"🔄 Syncing user: {normalized_email}")
    print(f"   Production DB: {prod_db_url.split('@')[1] if '@' in prod_db_url else 'hidden'}")
    print(f"   Local DB: {local_db_url.split('@')[1] if '@' in local_db_url else 'hidden'}")
    
    # Create database connections
    prod_engine = create_async_engine(prod_db_url, echo=False)
    local_engine = create_async_engine(local_db_url, echo=False)
    
    prod_session_factory = async_sessionmaker(prod_engine, class_=AsyncSession, expire_on_commit=False)
    local_session_factory = async_sessionmaker(local_engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        # Fetch user from production
        async with prod_session_factory() as prod_session:
            result = await prod_session.execute(
                select(User).where(func.lower(User.email) == normalized_email)
            )
            prod_user = result.scalar_one_or_none()
            
            if not prod_user:
                print(f"❌ User not found in production database: {normalized_email}")
                return False
            
            print(f"✅ Found user in production:")
            print(f"   ID: {prod_user.id}")
            print(f"   Email: {prod_user.email}")
            print(f"   Username: {prod_user.username or 'N/A'}")
            print(f"   Role: {prod_user.role}")
            print(f"   Plan: {prod_user.plan}")
            print(f"   Has password: {'Yes' if prod_user.password_hash else 'No'}")
            
            # Check if user exists in local
            async with local_session_factory() as local_session:
                result = await local_session.execute(
                    select(User).where(func.lower(User.email) == normalized_email)
                )
                local_user = result.scalar_one_or_none()
                
                if local_user:
                    if not overwrite:
                        print(f"⚠️  User already exists in local database.")
                        print(f"   Use --overwrite to replace existing user.")
                        return False
                    else:
                        print(f"🔄 Updating existing user in local database...")
                        # Update existing user
                        for key, value in [
                            ('id', prod_user.id),
                            ('email', prod_user.email),
                            ('account_number', prod_user.account_number),
                            ('username', prod_user.username),
                            ('password_hash', prod_user.password_hash),
                            ('role', prod_user.role),
                            ('plan', prod_user.plan),
                            ('is_active', prod_user.is_active),
                            ('email_verified', prod_user.email_verified),
                            ('profile_completed', prod_user.profile_completed),
                            ('free_parlays_total', prod_user.free_parlays_total),
                            ('free_parlays_used', prod_user.free_parlays_used),
                            ('subscription_plan', prod_user.subscription_plan),
                            ('subscription_status', prod_user.subscription_status),
                            ('subscription_renewal_date', prod_user.subscription_renewal_date),
                            ('subscription_last_billed_at', prod_user.subscription_last_billed_at),
                            ('stripe_customer_id', prod_user.stripe_customer_id),
                            ('stripe_subscription_id', prod_user.stripe_subscription_id),
                            ('daily_parlays_used', prod_user.daily_parlays_used),
                            ('daily_parlays_usage_date', prod_user.daily_parlays_usage_date),
                            ('premium_ai_parlays_used', prod_user.premium_ai_parlays_used),
                            ('premium_ai_parlays_period_start', prod_user.premium_ai_parlays_period_start),
                            ('premium_custom_builder_used', prod_user.premium_custom_builder_used),
                            ('premium_custom_builder_period_start', prod_user.premium_custom_builder_period_start),
                            ('premium_inscriptions_used', prod_user.premium_inscriptions_used),
                            ('premium_inscriptions_period_start', prod_user.premium_inscriptions_period_start),
                            ('credit_balance', prod_user.credit_balance),
                            ('default_risk_profile', prod_user.default_risk_profile),
                            ('favorite_teams', prod_user.favorite_teams),
                            ('favorite_sports', prod_user.favorite_sports),
                            ('display_name', prod_user.display_name),
                            ('leaderboard_visibility', prod_user.leaderboard_visibility),
                            ('avatar_url', prod_user.avatar_url),
                            ('bio', prod_user.bio),
                            ('timezone', prod_user.timezone),
                            ('created_at', prod_user.created_at),
                            ('updated_at', prod_user.updated_at),
                            ('last_login', prod_user.last_login),
                        ]:
                            setattr(local_user, key, value)
                        
                        await local_session.commit()
                        await local_session.refresh(local_user)
                        print(f"✅ User updated successfully!")
                        return True
                else:
                    print(f"➕ Creating new user in local database...")
                    # Create new user with production data
                    new_user = User(
                        id=prod_user.id,
                        email=prod_user.email,
                        account_number=prod_user.account_number,
                        username=prod_user.username,
                        password_hash=prod_user.password_hash,
                        role=prod_user.role,
                        plan=prod_user.plan,
                        is_active=prod_user.is_active,
                        email_verified=prod_user.email_verified,
                        profile_completed=prod_user.profile_completed,
                        free_parlays_total=prod_user.free_parlays_total,
                        free_parlays_used=prod_user.free_parlays_used,
                        subscription_plan=prod_user.subscription_plan,
                        subscription_status=prod_user.subscription_status,
                        subscription_renewal_date=prod_user.subscription_renewal_date,
                        subscription_last_billed_at=prod_user.subscription_last_billed_at,
                        stripe_customer_id=prod_user.stripe_customer_id,
                        stripe_subscription_id=prod_user.stripe_subscription_id,
                        daily_parlays_used=prod_user.daily_parlays_used,
                        daily_parlays_usage_date=prod_user.daily_parlays_usage_date,
                        premium_ai_parlays_used=prod_user.premium_ai_parlays_used,
                        premium_ai_parlays_period_start=prod_user.premium_ai_parlays_period_start,
                        premium_custom_builder_used=prod_user.premium_custom_builder_used,
                        premium_custom_builder_period_start=prod_user.premium_custom_builder_period_start,
                        premium_inscriptions_used=prod_user.premium_inscriptions_used,
                        premium_inscriptions_period_start=prod_user.premium_inscriptions_period_start,
                        credit_balance=prod_user.credit_balance,
                        default_risk_profile=prod_user.default_risk_profile,
                        favorite_teams=prod_user.favorite_teams,
                        favorite_sports=prod_user.favorite_sports,
                        display_name=prod_user.display_name,
                        leaderboard_visibility=prod_user.leaderboard_visibility,
                        avatar_url=prod_user.avatar_url,
                        bio=prod_user.bio,
                        timezone=prod_user.timezone,
                        created_at=prod_user.created_at,
                        updated_at=prod_user.updated_at,
                        last_login=prod_user.last_login,
                    )
                    local_session.add(new_user)
                    await local_session.commit()
                    await local_session.refresh(new_user)
                    print(f"✅ User created successfully!")
                    return True
                    
    except Exception as e:
        print(f"❌ Error syncing user: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await prod_engine.dispose()
        await local_engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Sync user from production to local database")
    parser.add_argument(
        "--email",
        type=str,
        help="Email of the user to sync",
        default=os.getenv("USER_EMAIL")
    )
    parser.add_argument(
        "--prod-db-url",
        type=str,
        help="Production database URL",
        default=os.getenv("PROD_DATABASE_URL")
    )
    parser.add_argument(
        "--local-db-url",
        type=str,
        help="Local database URL",
        default=os.getenv("LOCAL_DATABASE_URL")
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing user in local database"
    )
    
    args = parser.parse_args()
    
    if not args.email:
        print("❌ Email is required. Use --email or set USER_EMAIL environment variable.")
        sys.exit(1)
    
    if not args.prod_db_url:
        print("❌ Production database URL is required. Use --prod-db-url or set PROD_DATABASE_URL environment variable.")
        sys.exit(1)
    
    if not args.local_db_url:
        print("❌ Local database URL is required. Use --local-db-url or set LOCAL_DATABASE_URL environment variable.")
        sys.exit(1)
    
    # Convert postgresql:// to postgresql+asyncpg:// if needed
    if args.prod_db_url.startswith("postgresql://") and "+asyncpg" not in args.prod_db_url:
        args.prod_db_url = args.prod_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    if args.local_db_url.startswith("postgresql://") and "+asyncpg" not in args.local_db_url:
        args.local_db_url = args.local_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    success = asyncio.run(sync_user(
        prod_db_url=args.prod_db_url,
        local_db_url=args.local_db_url,
        email=args.email,
        overwrite=args.overwrite
    ))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


