"""Authentication service for JWT-based auth"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import uuid

from app.core.config import settings
from app.models.user import User
from app.services.accounts.account_number_service import AccountNumberAllocator

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash
    
    Bcrypt has a 72-byte limit, so we truncate if necessary to match
    how the password was hashed during registration.
    """
    # Bcrypt limit is 72 bytes, truncate if necessary (must match get_password_hash)
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate bytes and decode back, handling potential incomplete UTF-8 sequences
        truncated_bytes = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while truncated_bytes and truncated_bytes[-1] & 0b11000000 == 0b10000000:
            truncated_bytes = truncated_bytes[:-1]
        plain_password = truncated_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password
    
    Bcrypt has a 72-byte limit, so we truncate if necessary.
    This is safe because:
    1. Passwords longer than 72 bytes are extremely rare
    2. The first 72 bytes are sufficient for security
    3. We truncate consistently for both hashing and verification
    """
    # Bcrypt limit is 72 bytes, truncate if necessary
    # Truncate string to ensure UTF-8 encoding doesn't exceed 72 bytes
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate bytes and decode back, handling potential incomplete UTF-8 sequences
        truncated_bytes = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while truncated_bytes and truncated_bytes[-1] & 0b11000000 == 0b10000000:
            truncated_bytes = truncated_bytes[:-1]
        password = truncated_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


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
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    # Check if user has a password hash (new system)
    if user.password_hash:
        if not verify_password(password, user.password_hash):
            return None
    else:
        # Legacy: if no password hash, reject (user needs to reset password)
        return None
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    
    return user


async def create_user(db: AsyncSession, email: str, password: str, username: Optional[str] = None) -> User:
    """Create a new user"""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise ValueError("User with this email already exists")
    
    allocator = AccountNumberAllocator()

    # Create new user (retry only for extremely unlikely account_number collisions)
    for _ in range(3):
        user = User(
            id=uuid.uuid4(),
            email=email,
            account_number=await allocator.allocate(db),
            username=username,
            password_hash=get_password_hash(password),
        )
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError:
            await db.rollback()
            # Very unlikely: account number collision. Retry.
            continue

    raise RuntimeError("Failed to create user (could not allocate unique account number)")

