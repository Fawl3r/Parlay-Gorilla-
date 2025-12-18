"""Fix SQLite database by adding account_number column if missing.

This script adds the account_number column to the users table in SQLite
and backfills existing users with unique account numbers.
"""

import os
import sys
import secrets
import sqlite3
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.database.session import get_database_url


def generate_account_number() -> str:
    """Generate a 20-character hex account number."""
    return secrets.token_hex(10)


def fix_sqlite_account_number():
    """Add account_number column to SQLite database if missing."""
    db_url = get_database_url()
    
    if "sqlite" not in db_url:
        print(f"Database is not SQLite: {db_url}")
        print("This script is only for SQLite databases.")
        return False
    
    # Extract SQLite file path
    # Format: sqlite+aiosqlite:///path/to/db.db
    db_path = db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    print(f"Connecting to SQLite database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if account_number column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "account_number" in columns:
            print("✓ account_number column already exists")
            return True
        
        print("Adding account_number column...")
        
        # Add column as nullable first
        cursor.execute("ALTER TABLE users ADD COLUMN account_number VARCHAR(20)")
        
        # Get existing users
        cursor.execute("SELECT id FROM users WHERE account_number IS NULL OR account_number = ''")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        # Get existing account numbers to avoid collisions
        cursor.execute("SELECT account_number FROM users WHERE account_number IS NOT NULL AND account_number <> ''")
        existing = {row[0] for row in cursor.fetchall() if row[0]}
        
        # Backfill account numbers for existing users
        updated = 0
        for user_id in user_ids:
            while True:
                candidate = generate_account_number()
                if candidate in existing:
                    continue
                # Check if it already exists in DB
                cursor.execute("SELECT 1 FROM users WHERE account_number = ? LIMIT 1", (candidate,))
                if cursor.fetchone():
                    continue
                # Assign it
                cursor.execute("UPDATE users SET account_number = ? WHERE id = ?", (candidate, user_id))
                existing.add(candidate)
                updated += 1
                break
        
        print(f"✓ Backfilled account_number for {updated} users")
        
        # Make column NOT NULL (SQLite doesn't support ALTER COLUMN, so we need to recreate)
        # For now, we'll just ensure all rows have values (which we just did)
        # SQLite will enforce NOT NULL on new inserts via the model
        
        # Create unique index
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_account_number ON users(account_number)")
            print("✓ Created unique index on account_number")
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e).lower():
                raise
        
        conn.commit()
        print("✓ Successfully added account_number column to users table")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    if not settings.use_sqlite:
        print("USE_SQLITE is not set to true. This script is only for SQLite databases.")
        sys.exit(1)
    
    success = fix_sqlite_account_number()
    sys.exit(0 if success else 1)

