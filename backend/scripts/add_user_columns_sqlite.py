"""
Add missing user columns to SQLite database.

This script adds the columns from migration 008_add_affiliate_and_credits.py
to the SQLite users table when migrations can't be run.

Run this if you get "no such column: users.free_parlays_total" error.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.database.session import engine, DATABASE_URL, is_sqlite


async def add_user_columns():
    """Add missing columns to users table in SQLite database"""
    
    if not is_sqlite:
        print("⚠️  This script is for SQLite databases only.")
        print(f"   Current database: {DATABASE_URL[:50]}...")
        print("   For PostgreSQL, run: alembic upgrade head")
        return
    
    print("Adding missing columns to users table in SQLite database...")
    print(f"Database: {DATABASE_URL}")
    
    async with engine.begin() as conn:
        # Get existing columns
        result = await conn.execute(text("PRAGMA table_info(users)"))
        columns = {row[1]: row for row in result}
        
        print(f"\nFound {len(columns)} existing columns in users table")
        
        # Define columns to add with their SQLite types and defaults
        columns_to_add = [
            # Free tier / trial access
            ('free_parlays_total', 'INTEGER NOT NULL DEFAULT 2'),
            ('free_parlays_used', 'INTEGER NOT NULL DEFAULT 0'),
            
            # Subscription status (extended fields)
            ('subscription_plan', 'VARCHAR(50)'),
            ('subscription_status', 'VARCHAR(20) NOT NULL DEFAULT \'none\''),
            ('subscription_renewal_date', 'TIMESTAMP'),
            ('subscription_last_billed_at', 'TIMESTAMP'),
            
            # Daily parlay usage tracking
            ('daily_parlays_used', 'INTEGER NOT NULL DEFAULT 0'),
            ('daily_parlays_usage_date', 'DATE'),
            
            # Credit balance
            ('credit_balance', 'INTEGER NOT NULL DEFAULT 0'),
        ]
        
        added_count = 0
        skipped_count = 0
        
        for col_name, col_def in columns_to_add:
            if col_name in columns:
                print(f"  ℹ️  Column {col_name} already exists, skipping")
                skipped_count += 1
            else:
                try:
                    # SQLite doesn't support IF NOT EXISTS for ALTER TABLE
                    # So we check first and add if missing
                    await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                    print(f"  ✓ Added column: {col_name}")
                    added_count += 1
                except Exception as e:
                    error_msg = str(e).lower()
                    if "duplicate column" in error_msg or "already exists" in error_msg:
                        print(f"  ℹ️  Column {col_name} already exists (detected during add)")
                        skipped_count += 1
                    else:
                        print(f"  ❌ Error adding {col_name}: {e}")
                        raise
        
        # Update existing rows with default values for NOT NULL columns
        if added_count > 0:
            print("\nUpdating existing rows with default values...")
            try:
                # Set default values for existing users
                await conn.execute(text("""
                    UPDATE users 
                    SET free_parlays_total = 2 
                    WHERE free_parlays_total IS NULL
                """))
                await conn.execute(text("""
                    UPDATE users 
                    SET free_parlays_used = 0 
                    WHERE free_parlays_used IS NULL
                """))
                await conn.execute(text("""
                    UPDATE users 
                    SET subscription_status = 'none' 
                    WHERE subscription_status IS NULL
                """))
                await conn.execute(text("""
                    UPDATE users 
                    SET daily_parlays_used = 0 
                    WHERE daily_parlays_used IS NULL
                """))
                await conn.execute(text("""
                    UPDATE users 
                    SET credit_balance = 0 
                    WHERE credit_balance IS NULL
                """))
                print("  ✓ Updated existing rows with default values")
            except Exception as e:
                print(f"  ⚠️  Warning updating defaults: {e}")
        
        # Create indexes for subscription status
        print("\nCreating indexes...")
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_subscription_status ON users(subscription_status)"))
            print("  ✓ Created index on subscription_status")
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"  ⚠️  Could not create index: {e}")
        
        print(f"\n✅ Successfully processed columns!")
        print(f"   Added: {added_count}")
        print(f"   Skipped (already exist): {skipped_count}")
        print("\nThe users table now has all required columns.")


if __name__ == "__main__":
    asyncio.run(add_user_columns())

