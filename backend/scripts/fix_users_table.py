"""
Quick fix script to update users table schema
Run this once to add password_hash column and make supabase_user_id nullable
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import AsyncSessionLocal, engine, Base
from app.models.user import User

async def fix_users_table():
    """Fix users table schema"""
    print("Checking users table schema...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if password_hash exists
            result = await db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='password_hash'
            """))
            has_password_hash = result.scalar() is not None
            
            if not has_password_hash:
                print("Adding password_hash column...")
                await db.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
                await db.commit()
                print("✅ Added password_hash column")
            else:
                print("✅ password_hash column already exists")
            
            # Check if supabase_user_id is nullable
            result = await db.execute(text("""
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='supabase_user_id'
            """))
            nullable = result.scalar()
            
            if nullable == 'NO':
                print("Making supabase_user_id nullable...")
                # First, set any NULL values to a temporary value
                await db.execute(text("""
                    UPDATE users 
                    SET supabase_user_id = 'temp_' || id::text 
                    WHERE supabase_user_id IS NULL
                """))
                await db.commit()
                
                # Now make it nullable
                await db.execute(text("ALTER TABLE users ALTER COLUMN supabase_user_id DROP NOT NULL"))
                await db.commit()
                print("✅ Made supabase_user_id nullable")
            else:
                print("✅ supabase_user_id is already nullable")
            
            print("\n✅ Users table schema is now correct!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(fix_users_table())

