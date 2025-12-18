"""Fix affiliate_clicks table column name mismatch"""

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
        # Check if clicked_at column exists
        result = await conn.execute(text("PRAGMA table_info(affiliate_clicks)"))
        columns = {row[1]: row for row in result}
        
        if 'clicked_at' in columns and 'created_at' not in columns:
            print("Fixing affiliate_clicks table: renaming clicked_at to created_at...")
            # SQLite doesn't support RENAME COLUMN directly, so we need to recreate
            # But first, let's check if there's data
            count_result = await conn.execute(text("SELECT COUNT(*) FROM affiliate_clicks"))
            count = count_result.scalar() or 0
            
            if count > 0:
                print(f"⚠️  Table has {count} rows. Creating backup and migrating data...")
                # Create new table with correct schema
                await conn.execute(text("""
                    CREATE TABLE affiliate_clicks_new (
                        id TEXT PRIMARY KEY,
                        affiliate_id TEXT NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        referer_url TEXT,
                        landing_page TEXT,
                        utm_source TEXT,
                        utm_medium TEXT,
                        utm_campaign TEXT,
                        converted TEXT NOT NULL DEFAULT 'N',
                        converted_user_id TEXT,
                        converted_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (affiliate_id) REFERENCES affiliates(id)
                    )
                """))
                
                # Copy data
                await conn.execute(text("""
                    INSERT INTO affiliate_clicks_new 
                    (id, affiliate_id, ip_address, user_agent, referer_url, landing_page, 
                     utm_source, utm_medium, utm_campaign, converted, converted_user_id, 
                     converted_at, created_at)
                    SELECT 
                        id, affiliate_id, ip_address, user_agent, referrer, landing_page,
                        NULL, NULL, NULL, 
                        CASE WHEN converted = 1 THEN 'Y' ELSE 'N' END,
                        NULL, NULL, clicked_at
                    FROM affiliate_clicks
                """))
                
                # Drop old table
                await conn.execute(text("DROP TABLE affiliate_clicks"))
                
                # Rename new table
                await conn.execute(text("ALTER TABLE affiliate_clicks_new RENAME TO affiliate_clicks"))
                
                # Recreate indexes
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_affiliate_id ON affiliate_clicks(affiliate_id)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_created_at ON affiliate_clicks(created_at)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_converted ON affiliate_clicks(converted)"))
                
                print("✅ Table fixed successfully!")
            else:
                # No data, just recreate
                await conn.execute(text("DROP TABLE affiliate_clicks"))
                await conn.execute(text("""
                    CREATE TABLE affiliate_clicks (
                        id TEXT PRIMARY KEY,
                        affiliate_id TEXT NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        referer_url TEXT,
                        landing_page TEXT,
                        utm_source TEXT,
                        utm_medium TEXT,
                        utm_campaign TEXT,
                        converted TEXT NOT NULL DEFAULT 'N',
                        converted_user_id TEXT,
                        converted_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (affiliate_id) REFERENCES affiliates(id)
                    )
                """))
                
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_affiliate_id ON affiliate_clicks(affiliate_id)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_created_at ON affiliate_clicks(created_at)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_affiliate_clicks_converted ON affiliate_clicks(converted)"))
                
                print("✅ Table recreated with correct schema!")
        elif 'created_at' in columns:
            print("✅ Table already has created_at column - no fix needed")
        else:
            print("⚠️  Table structure is unexpected. Please check manually.")

if __name__ == "__main__":
    asyncio.run(fix_table())

