"""
Script to add password_hash column to users table
Run this if the database migration hasn't been applied yet
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import AsyncSessionLocal, engine

async def add_password_hash_column():
    """Add password_hash column to users table if it doesn't exist"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if column exists (SQLite and PostgreSQL compatible)
            if 'sqlite' in str(engine.url):
                # SQLite
                result = await db.execute(text("""
                    SELECT COUNT(*) as cnt 
                    FROM pragma_table_info('users') 
                    WHERE name='password_hash'
                """))
                exists = result.scalar() > 0
            else:
                # PostgreSQL
                result = await db.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='password_hash'
                """))
                exists = result.scalar() > 0
            
            if not exists:
                print("Adding password_hash column to users table...")
                await db.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
                await db.commit()
                print("✅ password_hash column added successfully!")
            else:
                print("✅ password_hash column already exists")
            
            # Make supabase_user_id nullable if it isn't already
            if 'sqlite' in str(engine.url):
                # SQLite doesn't support ALTER COLUMN, but we can check
                print("Note: SQLite doesn't support ALTER COLUMN. If supabase_user_id is NOT NULL, you may need to recreate the table.")
            else:
                # PostgreSQL
                result = await db.execute(text("""
                    SELECT is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='supabase_user_id'
                """))
                nullable = result.scalar()
                if nullable == 'NO':
                    print("Making supabase_user_id nullable...")
                    await db.execute(text("ALTER TABLE users ALTER COLUMN supabase_user_id DROP NOT NULL"))
                    await db.commit()
                    print("✅ supabase_user_id is now nullable")
                else:
                    print("✅ supabase_user_id is already nullable")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(add_password_hash_column())

