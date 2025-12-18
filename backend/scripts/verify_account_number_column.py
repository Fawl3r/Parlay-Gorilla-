"""Verify that account_number column exists in users table."""

import os
import sys
import sqlite3
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import get_database_url


def verify_account_number_column():
    """Verify account_number column exists and has data."""
    db_url = get_database_url()
    
    if "sqlite" not in db_url:
        print(f"Database is not SQLite: {db_url}")
        print("This script is only for SQLite databases.")
        return False
    
    # Extract SQLite file path
    db_path = db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    print(f"Verifying SQLite database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if account_number column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        if "account_number" not in columns:
            print("✗ account_number column does NOT exist")
            return False
        
        col_info = columns["account_number"]
        print(f"✓ account_number column exists")
        print(f"  - Type: {col_info[2]}")
        print(f"  - Nullable: {'Yes' if col_info[3] == 0 else 'No'}")
        
        # Check if index exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='ix_users_account_number'")
        index = cursor.fetchone()
        if index:
            print(f"✓ Unique index 'ix_users_account_number' exists")
        else:
            print(f"⚠ Unique index 'ix_users_account_number' does NOT exist")
        
        # Check data
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE account_number IS NOT NULL AND account_number <> ''")
        users_with_account = cursor.fetchone()[0]
        
        print(f"✓ Total users: {total_users}")
        print(f"✓ Users with account_number: {users_with_account}")
        
        if total_users > 0 and users_with_account == total_users:
            print("✓ All users have account_number assigned")
        elif total_users > 0:
            print(f"⚠ {total_users - users_with_account} users are missing account_number")
        
        # Check for duplicates
        cursor.execute("""
            SELECT account_number, COUNT(*) as cnt 
            FROM users 
            WHERE account_number IS NOT NULL AND account_number <> ''
            GROUP BY account_number 
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"✗ Found {len(duplicates)} duplicate account_numbers!")
            return False
        else:
            print("✓ No duplicate account_numbers found")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = verify_account_number_column()
    sys.exit(0 if success else 1)

