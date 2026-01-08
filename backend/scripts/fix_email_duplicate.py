"""Fix duplicate email by keeping the most recent user and deleting older ones."""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def fix_duplicate(email: str, db_url: str):
    engine = create_async_engine(db_url, echo=True)
    try:
        async with engine.begin() as conn:
            # Find all users with this email (case-insensitive)
            result = await conn.execute(
                text("""
                    SELECT id, email, created_at 
                    FROM users 
                    WHERE lower(email) = lower(:email)
                    ORDER BY created_at DESC
                """),
                {"email": email}
            )
            rows = result.fetchall()
            
            if len(rows) <= 1:
                print(f"No duplicates found for {email}")
                return
            
            print(f"Found {len(rows)} users with email {email}:")
            for i, row in enumerate(rows):
                print(f"  {i+1}. ID: {row[0]}, Email: {row[1]}, Created: {row[2]}")
            
            # Keep the most recent (first in DESC order), delete the rest
            to_keep = rows[0]
            to_delete = rows[1:]
            
            print(f"\nKeeping user ID: {to_keep[0]} (most recent)")
            print(f"Deleting {len(to_delete)} duplicate(s):")
            
            for row in to_delete:
                user_id = row[0]
                print(f"  - Deleting user ID: {user_id}")
                await conn.execute(
                    text("DELETE FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
            
            print(f"\n✅ Fixed duplicate email issue for {email}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "fawl3r85@gmail.com"
    db_url = sys.argv[2] if len(sys.argv) > 2 else "postgresql+asyncpg://devuser:devpass@localhost:5432/parlaygorilla"
    
    asyncio.run(fix_duplicate(email, db_url))

