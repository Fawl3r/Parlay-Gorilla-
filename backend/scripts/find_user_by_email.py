"""Find user by email (case-insensitive search)"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func
from app.database.session import AsyncSessionLocal
from app.models.user import User

async def find_user(email: str):
    """Find user by email (case-insensitive)"""
    
    async with AsyncSessionLocal() as db:
        # Try exact match first
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"✅ Found user (exact match):")
            print(f"   Email: {user.email}")
            print(f"   ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Plan: {user.plan}")
            print(f"   Role: {user.role}")
            return user
        
        # Try case-insensitive search
        result = await db.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"✅ Found user (case-insensitive match):")
            print(f"   Email: {user.email}")
            print(f"   ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Plan: {user.plan}")
            print(f"   Role: {user.role}")
            return user
        
        # Try partial match
        result = await db.execute(
            select(User).where(User.email.like(f"%{email.lower()}%"))
        )
        users = result.scalars().all()
        
        if users:
            print(f"Found {len(users)} user(s) with similar email:")
            for u in users:
                print(f"   - {u.email} (ID: {u.id}, Plan: {u.plan})")
            return users[0] if len(users) == 1 else None
        
        print(f"❌ No user found with email: {email}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/find_user_by_email.py <email>")
        sys.exit(1)
    
    email = sys.argv[1].strip()
    asyncio.run(find_user(email))

