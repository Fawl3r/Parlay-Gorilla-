"""
Create affiliates tables for SQLite database.

This script creates the affiliates-related tables directly in SQLite
when migrations can't be run (e.g., SQLite doesn't support all PostgreSQL features).

Run this if you get "no such table: affiliates" error.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.database.session import engine, DATABASE_URL, is_sqlite


async def create_affiliates_tables():
    """Create affiliates tables in SQLite database"""
    
    if not is_sqlite:
        print("⚠️  This script is for SQLite databases only.")
        print(f"   Current database: {DATABASE_URL[:50]}...")
        print("   For PostgreSQL, run: alembic upgrade head")
        return
    
    print("Creating affiliates tables in SQLite database...")
    print(f"Database: {DATABASE_URL}")
    
    async with engine.begin() as conn:
        # Check if tables already exist
        result = await conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('affiliates', 'affiliate_referrals', 'affiliate_clicks', 'affiliate_commissions')
        """))
        existing = [row[0] for row in result]
        
        if existing:
            print(f"\n⚠️  Tables already exist: {', '.join(existing)}")
            response = input("Do you want to drop and recreate them? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                return
            
            for table in existing:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                print(f"  Dropped {table}")
        
        # Create affiliates table
        print("\nCreating affiliates table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS affiliates (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE,
                referral_code TEXT NOT NULL UNIQUE,
                tier TEXT NOT NULL DEFAULT 'rookie',
                commission_rate_sub_first NUMERIC(5, 4) NOT NULL DEFAULT 0.20,
                commission_rate_sub_recurring NUMERIC(5, 4) NOT NULL DEFAULT 0.00,
                commission_rate_credits NUMERIC(5, 4) NOT NULL DEFAULT 0.20,
                total_referred_revenue NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
                total_commission_earned NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
                total_commission_paid NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
                total_clicks NUMERIC(10, 0) NOT NULL DEFAULT 0,
                total_referrals NUMERIC(10, 0) NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                is_approved BOOLEAN NOT NULL DEFAULT 1,
                payout_email TEXT,
                payout_method TEXT,
                tax_form_type TEXT,
                tax_form_status TEXT,
                tax_form_submitted_at TIMESTAMP,
                tax_form_verified_at TIMESTAMP,
                legal_name TEXT,
                business_name TEXT,
                tax_classification TEXT,
                tax_address_street TEXT,
                tax_address_city TEXT,
                tax_address_state TEXT,
                tax_address_zip TEXT,
                tax_address_country TEXT,
                tax_id_number TEXT,
                tax_id_type TEXT,
                country_of_residence TEXT,
                foreign_tax_id TEXT,
                tax_form_signed_at TIMESTAMP,
                tax_form_ip_address TEXT,
                tax_form_required_threshold NUMERIC(10, 2) NOT NULL DEFAULT 600.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        # Create indexes
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliates_user_id ON affiliates(user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliates_referral_code ON affiliates(referral_code)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliates_tier ON affiliates(tier)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliates_is_active ON affiliates(is_active)"))
        print("  ✓ Created affiliates table with indexes")
        
        # Create affiliate_referrals table
        print("\nCreating affiliate_referrals table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS affiliate_referrals (
                id TEXT PRIMARY KEY,
                affiliate_id TEXT NOT NULL,
                referred_user_id TEXT NOT NULL UNIQUE,
                click_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates(id),
                FOREIGN KEY (referred_user_id) REFERENCES users(id),
                FOREIGN KEY (click_id) REFERENCES affiliate_clicks(id)
            )
        """))
        
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_referrals_affiliate_id ON affiliate_referrals(affiliate_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_referrals_referred_user_id ON affiliate_referrals(referred_user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_referrals_created_at ON affiliate_referrals(created_at)"))
        print("  ✓ Created affiliate_referrals table with indexes")
        
        # Create affiliate_clicks table
        print("\nCreating affiliate_clicks table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS affiliate_clicks (
                id TEXT PRIMARY KEY,
                affiliate_id TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                referrer TEXT,
                landing_page TEXT,
                clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                converted BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates(id)
            )
        """))
        
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_affiliate_id ON affiliate_clicks(affiliate_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_clicked_at ON affiliate_clicks(clicked_at)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_converted ON affiliate_clicks(converted)"))
        print("  ✓ Created affiliate_clicks table with indexes")
        
        # Create affiliate_commissions table
        print("\nCreating affiliate_commissions table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS affiliate_commissions (
                id TEXT PRIMARY KEY,
                affiliate_id TEXT NOT NULL,
                referral_id TEXT NOT NULL,
                sale_type TEXT NOT NULL,
                sale_amount NUMERIC(12, 2) NOT NULL,
                commission_rate NUMERIC(5, 4) NOT NULL,
                commission_amount NUMERIC(12, 2) NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                paid_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates(id),
                FOREIGN KEY (referral_id) REFERENCES affiliate_referrals(id)
            )
        """))
        
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_commissions_affiliate_id ON affiliate_commissions(affiliate_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_commissions_referral_id ON affiliate_commissions(referral_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_commissions_status ON affiliate_commissions(status)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_commissions_created_at ON affiliate_commissions(created_at)"))
        print("  ✓ Created affiliate_commissions table with indexes")
        
        # Add foreign key columns to users table if they don't exist
        print("\nChecking users table for affiliate columns...")
        result = await conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        
        if 'affiliate_id' not in columns:
            print("  Adding affiliate_id column to users table...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN affiliate_id TEXT"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_affiliate_id ON users(affiliate_id)"))
            print("  ✓ Added affiliate_id column")
        
        if 'referred_by_affiliate_id' not in columns:
            print("  Adding referred_by_affiliate_id column to users table...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN referred_by_affiliate_id TEXT"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_referred_by_affiliate_id ON users(referred_by_affiliate_id)"))
            print("  ✓ Added referred_by_affiliate_id column")
        
        print("\n✅ All affiliates tables created successfully!")
        print("\nYou can now use the affiliate system.")


if __name__ == "__main__":
    asyncio.run(create_affiliates_tables())




