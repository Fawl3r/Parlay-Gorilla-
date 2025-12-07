"""
Quick fix script to add is_lifetime column to subscriptions table.
Run this if you get 'no such column: subscriptions.is_lifetime' error.
"""

import sqlite3
import os
from pathlib import Path

# Find the database file
db_path = Path(__file__).parent.parent / "instance" / "parlay_gorilla.db"
if not db_path.exists():
    # Try alternative locations
    db_path = Path(__file__).parent.parent / "parlay_gorilla.db"
    if not db_path.exists():
        print("Could not find database file. Please specify the path.")
        print("Looking for: parlay_gorilla.db")
        exit(1)

print(f"Found database at: {db_path}")

# Connect to database
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # Check if column exists
    cursor.execute("PRAGMA table_info(subscriptions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'is_lifetime' in columns:
        print("✓ is_lifetime column already exists")
    else:
        print("Adding is_lifetime column...")
        cursor.execute("""
            ALTER TABLE subscriptions 
            ADD COLUMN is_lifetime BOOLEAN DEFAULT 0 NOT NULL
        """)
        conn.commit()
        print("✓ Successfully added is_lifetime column")
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()

print("Done!")

