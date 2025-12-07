"""
Script to add is_lifetime column to subscriptions table if it doesn't exist.
This is a one-time fix for SQLite databases that may be missing this column.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import AsyncSessionLocal
from sqlalchemy import text


async def add_is_lifetime_column():
    """Add is_lifetime column to subscriptions table if it doesn't exist."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if column exists (SQLite specific)
            result = await session.execute(
                text("PRAGMA table_info(subscriptions)")
            )
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'is_lifetime' not in column_names:
                print("Adding is_lifetime column to subscriptions table...")
                await session.execute(
                    text("ALTER TABLE subscriptions ADD COLUMN is_lifetime BOOLEAN DEFAULT 0 NOT NULL")
                )
                await session.commit()
                print("✓ Successfully added is_lifetime column")
            else:
                print("✓ is_lifetime column already exists")
                
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(add_is_lifetime_column())

