"""
Create or promote a user to admin (email/password). Safe to re-run: if user exists,
promotes to admin and updates password; otherwise creates new admin user.

Usage (from backend directory, with .env or DATABASE_URL set):
    python scripts/create_admin_user.py <email> <password>

Example:
    python scripts/create_admin_user.py Fawl3r85@gmail.com 'Nefatari1985!'
"""

import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func
from app.database.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.services.auth_service import create_user, get_password_hash

async def create_or_promote_admin(email: str, password: str) -> bool:
    async with AsyncSessionLocal() as db:
        normalized = email.strip().lower()
        if not normalized:
            print("[FAIL] Email is required")
            return False

        result = await db.execute(select(User).where(func.lower(User.email) == normalized))
        user = result.scalar_one_or_none()

        if user:
            user.role = UserRole.admin.value
            user.password_hash = get_password_hash(password)
            await db.commit()
            await db.refresh(user)
            print(f"[OK] User promoted to admin: {user.email} (ID: {user.id})")
            return True

        try:
            user = await create_user(db, email.strip(), password)
            user.role = UserRole.admin.value
            await db.commit()
            await db.refresh(user)
            print(f"[OK] Admin user created: {user.email} (ID: {user.id})")
            return True
        except ValueError as e:
            print(f"[FAIL] {e}")
            return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/create_admin_user.py <email> <password>")
        sys.exit(1)

    email = sys.argv[1].strip()
    password = sys.argv[2].strip()
    if password.startswith("'") and password.endswith("'"):
        password = password[1:-1]
    elif password.startswith('"') and password.endswith('"'):
        password = password[1:-1]

    try:
        ok = asyncio.run(create_or_promote_admin(email, password))
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
