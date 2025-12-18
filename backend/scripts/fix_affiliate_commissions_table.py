"""Fix affiliate_commissions table schema to match model"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.database.session import engine, is_sqlite

async def fix_table():
    if not is_sqlite:
        print("This script is for SQLite only. For PostgreSQL, run: alembic upgrade head")
        return
    
    async with engine.begin() as conn:
        # Check current schema
        result = await conn.execute(text("PRAGMA table_info(affiliate_commissions)"))
        columns = {row[1]: row for row in result}
        
        # Required columns from the model
        required_columns = {
            'id', 'affiliate_id', 'referred_user_id', 'sale_id', 'sale_type',
            'base_amount', 'commission_rate', 'amount', 'currency',
            'is_first_subscription_payment', 'subscription_plan', 'credit_pack_id',
            'status', 'created_at', 'ready_at', 'paid_at', 'cancelled_at',
            'payout_id', 'payout_notes'
        }
        
        missing = required_columns - set(columns.keys())
        
        # Check if it has old schema (referral_id instead of referred_user_id, etc.)
        has_old_schema = 'referral_id' in columns or 'sale_amount' in columns or 'commission_amount' in columns
        
        if has_old_schema or missing:
            print("Fixing affiliate_commissions table schema...")
            
            count_result = await conn.execute(text("SELECT COUNT(*) FROM affiliate_commissions"))
            count = count_result.scalar() or 0
            
            if count > 0:
                print(f"⚠️  Table has {count} rows. This will migrate data...")
                # For now, just warn - data migration would be more complex
                print("⚠️  Please backup your data before running this!")
                return
            
            # Recreate table with correct schema
            await conn.execute(text("DROP TABLE IF EXISTS affiliate_commissions"))
            await conn.execute(text("""
                CREATE TABLE affiliate_commissions (
                    id TEXT PRIMARY KEY,
                    affiliate_id TEXT NOT NULL,
                    referred_user_id TEXT NOT NULL,
                    sale_id TEXT NOT NULL,
                    sale_type TEXT NOT NULL,
                    base_amount NUMERIC(12, 2) NOT NULL,
                    commission_rate NUMERIC(5, 4) NOT NULL,
                    amount NUMERIC(12, 2) NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    is_first_subscription_payment BOOLEAN NOT NULL DEFAULT 0,
                    subscription_plan TEXT,
                    credit_pack_id TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ready_at TIMESTAMP,
                    paid_at TIMESTAMP,
                    cancelled_at TIMESTAMP,
                    payout_id TEXT,
                    payout_notes TEXT,
                    FOREIGN KEY (affiliate_id) REFERENCES affiliates(id),
                    FOREIGN KEY (referred_user_id) REFERENCES users(id)
                )
            """))
            
            # Create indexes
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_commissions_affiliate_id ON affiliate_commissions(affiliate_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_commissions_referred_user_id ON affiliate_commissions(referred_user_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_commissions_sale_id ON affiliate_commissions(sale_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_commissions_status ON affiliate_commissions(status)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_commissions_ready_at ON affiliate_commissions(ready_at)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_commissions_sale_type ON affiliate_commissions(sale_type)"))
            
            print("✅ Table recreated with correct schema!")
        else:
            print("✅ Table already has correct schema - no fix needed")

if __name__ == "__main__":
    asyncio.run(fix_table())

