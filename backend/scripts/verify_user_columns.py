"""Quick script to verify user columns exist"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.database.session import engine, is_sqlite

async def verify():
    async with engine.begin() as conn:
        if is_sqlite:
            result = await conn.execute(text("PRAGMA table_info(users)"))
            cols = {row[1] for row in result}
        else:
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users'
            """))
            cols = {row[0] for row in result}
        
        required = [
            'free_parlays_total', 'free_parlays_used', 'subscription_plan',
            'subscription_status', 'credit_balance', 'daily_parlays_used'
        ]
        
        missing = [col for col in required if col not in cols]
        
        if missing:
            print(f"❌ Missing columns: {', '.join(missing)}")
            return False
        else:
            print("✅ All required columns exist!")
            return True

if __name__ == "__main__":
    asyncio.run(verify())

