"""Quick fix to add missing external_game_key column to games table"""
import asyncio
import os

os.environ["USE_SQLITE"] = "true"

async def fix_schema():
    from app.database.session import AsyncSessionLocal, engine
    from sqlalchemy import text
    
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text("PRAGMA table_info(games)"))
        columns = [row[1] for row in result]
        
        if "external_game_key" not in columns:
            print("Adding external_game_key column to games table...")
            await conn.execute(text("ALTER TABLE games ADD COLUMN external_game_key VARCHAR"))
            print("✓ Column added successfully!")
        else:
            print("✓ Column already exists")
        
        # Also check other missing columns from migration 037
        missing_cols = {
            "home_score": "INTEGER",
            "away_score": "INTEGER",
            "period": "VARCHAR",
            "clock": "VARCHAR",
            "last_scraped_at": "TIMESTAMP",
            "data_source": "VARCHAR",
            "is_stale": "BOOLEAN NOT NULL DEFAULT 0",
        }
        
        for col_name, col_type in missing_cols.items():
            if col_name not in columns:
                print(f"Adding {col_name} column...")
                await conn.execute(text(f"ALTER TABLE games ADD COLUMN {col_name} {col_type}"))
                print(f"✓ {col_name} added")
    
    print("\n✅ Schema fix complete! Restart your backend server.")

if __name__ == "__main__":
    asyncio.run(fix_schema())
