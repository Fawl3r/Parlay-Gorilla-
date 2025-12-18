"""Check if affiliate tables exist and create them if missing"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.database.session import engine, is_sqlite

async def check_and_create():
    async with engine.begin() as conn:
        if is_sqlite:
            # Check which tables exist
            result = await conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'affiliate%'
            """))
            existing = {row[0] for row in result}
            
            required = {
                'affiliates',
                'affiliate_clicks', 
                'affiliate_referrals',
                'affiliate_commissions'
            }
            
            missing = required - existing
            
            if missing:
                print(f"Missing affiliate tables: {', '.join(missing)}")
                print("Run: python scripts/create_affiliates_tables_sqlite.py")
                return False
            else:
                print("✅ All affiliate tables exist!")
                return True
        else:
            # PostgreSQL - check via information_schema
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'affiliate%'
            """))
            existing = {row[0] for row in result}
            
            required = {
                'affiliates',
                'affiliate_clicks', 
                'affiliate_referrals',
                'affiliate_commissions'
            }
            
            missing = required - existing
            
            if missing:
                print(f"Missing affiliate tables: {', '.join(missing)}")
                print("Run: alembic upgrade head")
                return False
            else:
                print("✅ All affiliate tables exist!")
                return True

if __name__ == "__main__":
    asyncio.run(check_and_create())

