"""
Create profile/badge/verification tables for SQLite.

Run this if you're using SQLite instead of PostgreSQL:
    python scripts/create_sqlite_profile_tables.py
"""

import asyncio
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.session import AsyncSessionLocal, engine, Base
from app.models.verification_token import VerificationToken
from app.models.badge import Badge
from app.models.user_badge import UserBadge


async def create_sqlite_tables():
    """Create tables for SQLite with compatible types."""
    print("Creating SQLite-compatible tables...")
    
    async with engine.begin() as conn:
        # Check if we're using SQLite
        is_sqlite = "sqlite" in str(engine.url)
        
        if not is_sqlite:
            print("⚠️  Not using SQLite. This script is for SQLite only.")
            print("   For PostgreSQL, use: alembic upgrade head")
            return
        
        print("✓ Detected SQLite database")
        
        # Create tables using SQLAlchemy (will use compatible types)
        # We need to temporarily modify the models to use String instead of GUID for SQLite
        try:
            await conn.run_sync(Base.metadata.create_all)
            print("✓ Tables created successfully!")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            print("\nTrying alternative method...")
            
            # Alternative: Create tables manually with SQL
            await create_tables_manually(conn)
    
    print("\n✅ Done! You can now run: python scripts/seed_badges.py")


async def create_tables_manually(conn):
    """Manually create tables using raw SQL for SQLite."""
    sql_statements = [
        # Create badges table
        """CREATE TABLE IF NOT EXISTS badges (
            id TEXT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(50) NOT NULL UNIQUE,
            description TEXT,
            icon VARCHAR(100),
            requirement_type VARCHAR(50) NOT NULL,
            requirement_value INTEGER NOT NULL DEFAULT 1,
            display_order INTEGER NOT NULL DEFAULT 0,
            is_active VARCHAR(1) NOT NULL DEFAULT '1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Create indexes for badges
        "CREATE INDEX IF NOT EXISTS idx_badge_slug ON badges(slug)",
        "CREATE INDEX IF NOT EXISTS idx_badge_requirement_type ON badges(requirement_type)",
        "CREATE INDEX IF NOT EXISTS idx_badge_display_order ON badges(display_order)",
        
        # Create user_badges table
        """CREATE TABLE IF NOT EXISTS user_badges (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            badge_id TEXT NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (badge_id) REFERENCES badges(id) ON DELETE CASCADE,
            UNIQUE(user_id, badge_id)
        )""",
        
        # Create indexes for user_badges
        "CREATE INDEX IF NOT EXISTS idx_user_badge_user ON user_badges(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_badge_badge ON user_badges(badge_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_badge_unlocked ON user_badges(unlocked_at)",
        
        # Create verification_tokens table
        """CREATE TABLE IF NOT EXISTS verification_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token_hash VARCHAR(64) NOT NULL,
            token_type VARCHAR(20) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""",
        
        # Create indexes for verification_tokens
        "CREATE INDEX IF NOT EXISTS idx_verification_token_hash ON verification_tokens(token_hash)",
        "CREATE INDEX IF NOT EXISTS idx_verification_token_expires ON verification_tokens(expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_verification_token_user_type ON verification_tokens(user_id, token_type)",
        "CREATE INDEX IF NOT EXISTS idx_verification_token_type ON verification_tokens(token_type)",
    ]
    
    for sql in sql_statements:
        try:
            await conn.execute(text(sql))
            print(f"  ✓ Executed: {sql[:50]}...")
        except Exception as e:
            print(f"  ⚠️  Warning: {e}")
    
    # Also add columns to users table if they don't exist
    user_columns = [
        ("email_verified", "INTEGER DEFAULT 0"),
        ("profile_completed", "INTEGER DEFAULT 0"),
        ("bio", "TEXT"),
        ("timezone", "VARCHAR(50)"),
    ]
    
    for col_name, col_type in user_columns:
        try:
            # SQLite doesn't support IF NOT EXISTS for ALTER TABLE
            # So we'll just try to add it and ignore if it exists
            await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
            print(f"  ✓ Added column: users.{col_name}")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"  ℹ️  Column users.{col_name} already exists")
            else:
                print(f"  ⚠️  Could not add users.{col_name}: {e}")


if __name__ == "__main__":
    asyncio.run(create_sqlite_tables())

