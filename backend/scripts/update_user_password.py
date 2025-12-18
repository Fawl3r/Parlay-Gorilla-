"""
Update a user's password by email.

Usage:
    python scripts/update_user_password.py <email> <new_password>
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func
from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.services.auth_service import get_password_hash

async def update_password(email: str, new_password: str):
    """Update user password in the primary database (PostgreSQL on Render / SQLite in tests)."""
    
    async with AsyncSessionLocal() as db:
        # Find user by email (case-insensitive)
        result = await db.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email {email} not found")
            return False
        
        print(f"✅ Found user: {user.email} (ID: {user.id})")
        print(f"   Current plan: {user.plan}")
        
        # Hash the new password for PostgreSQL
        password_hash = get_password_hash(new_password)
        
        # Update password in PostgreSQL
        user.password_hash = password_hash
        
        await db.commit()
        await db.refresh(user)
        
        print(f"   ✅ PostgreSQL password hash updated")
        
        print(f"\n✅ Password updated successfully!")
        print(f"   User: {user.email}")
        print(f"   Password hash set: {'Yes' if user.password_hash else 'No'}")
        
        return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/update_user_password.py <email> <password>")
        print("Example: python scripts/update_user_password.py Fawl3r85@gmail.com 'Nefatari1985!'")
        sys.exit(1)
    
    email = sys.argv[1].strip()
    password = sys.argv[2].strip()
    
    # Remove quotes if present
    if password.startswith("'") and password.endswith("'"):
        password = password[1:-1]
    elif password.startswith('"') and password.endswith('"'):
        password = password[1:-1]
    
    print(f"Updating password for: {email}\n")
    
    try:
        success = asyncio.run(update_password(email, password))
        if success:
            print("\n✅ Done! User can now login with the new password.")
            sys.exit(0)
        else:
            print("\n❌ Failed to update password")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

