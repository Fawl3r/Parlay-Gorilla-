"""Authentication service for JWT-based auth"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
import uuid
import logging

from app.core.config import settings
from app.models.user import User
from app.services.accounts.account_number_service import AccountNumberAllocator
from app.services.auth import EmailNormalizer
from app.services.auth.password_hasher import PasswordHasher

logger = logging.getLogger(__name__)

# Password hashing/verification.
#
# We default to PBKDF2-SHA256 for new hashes in production to avoid brittle bcrypt backend
# initialization issues on some platforms (e.g., Python 3.12 / Render).
#
# We still verify legacy hashes:
# - bcrypt ($2b$...) and
# - passlib bcrypt_sha256 ($bcrypt-sha256$...).
_password_hasher = PasswordHasher()

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def verify_and_update_password(plain_password: str, hashed_password: str) -> Tuple[bool, Optional[str]]:
    """
    Verify the password and, if needed, return an upgraded hash.

    Returns:
      (is_valid, new_hash_or_none)
    """
    return _password_hasher.verify_and_update_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password (production-safe default)."""
    return _password_hasher.hash_password(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password"""
    normalized_email = EmailNormalizer().normalize(email)
    if not normalized_email:
        return None

    result = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    # Check if user has a password hash (new system)
    if user.password_hash:
        ok, new_hash = verify_and_update_password(password, user.password_hash)
        if not ok:
            return None

        # Opportunistic upgrade (PasswordHasher decides when it is safe).
        if new_hash:
            user.password_hash = new_hash
    else:
        # Legacy: if no password hash, reject (user needs to reset password)
        return None
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    
    return user


async def create_user(db: AsyncSession, email: str, password: str, username: Optional[str] = None) -> User:
    """Create a new user"""
    normalized_email = EmailNormalizer().normalize(email)
    if not normalized_email:
        raise ValueError("Email is required")

    # Check if user already exists
    result = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise ValueError("User with this email already exists")
    
    allocator = AccountNumberAllocator()

    # Create new user (retry only for extremely unlikely account_number collisions)
    for _ in range(3):
        user = User(
            id=uuid.uuid4(),
            email=normalized_email,
            account_number=await allocator.allocate(db),
            username=username,
            password_hash=get_password_hash(password),
        )
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError as exc:
            await db.rollback()

            # Could be either: account_number collision OR email uniqueness violation (legacy mixed-case rows).
            email_exists = await db.execute(select(User.id).where(func.lower(User.email) == normalized_email))
            if email_exists.scalar_one_or_none() is not None:
                raise ValueError("User with this email already exists") from exc

            # Otherwise treat as collision and retry.
            continue
        except Exception:
            # Guarantee rollback for all other DB failures (pooled DBs, disconnects, etc.).
            await db.rollback()
            raise

    raise RuntimeError("Failed to create user (could not allocate unique account number)")

