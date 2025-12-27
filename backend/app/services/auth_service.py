"""Authentication service for JWT-based auth"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
import uuid

from app.core.config import settings
from app.models.user import User
from app.services.accounts.account_number_service import AccountNumberAllocator
from app.services.auth import EmailNormalizer

# Password hashing
#
# IMPORTANT:
# - Plain bcrypt only uses the first 72 bytes of the password (and some libs error on longer input).
# - bcrypt_sha256 removes this limitation by pre-hashing with SHA-256 before bcrypt.
# - We keep "bcrypt" enabled for backwards compatibility and mark it deprecated so we can
#   opportunistically upgrade hashes on successful login (when safe).
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def _is_legacy_bcrypt_hash(password_hash: str) -> bool:
    # bcrypt hashes typically start with "$2a$", "$2b$", "$2y$", etc.
    return isinstance(password_hash, str) and password_hash.startswith("$2")


def _is_bcrypt_72_byte_error(exc: Exception) -> bool:
    message = (str(exc) or "").lower()
    return "72" in message and "byte" in message and "password" in message


def _truncate_password_for_legacy_bcrypt(password: str) -> str:
    """
    Legacy compatibility:
    Some bcrypt backends reject passwords > 72 bytes instead of truncating.
    For old bcrypt hashes, we mimic bcrypt's effective behavior by truncating to 72 bytes.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) <= 72:
        return password

    truncated_bytes = password_bytes[:72]
    # Remove any incomplete UTF-8 sequences at the end
    while truncated_bytes and truncated_bytes[-1] & 0b11000000 == 0b10000000:
        truncated_bytes = truncated_bytes[:-1]
    return truncated_bytes.decode("utf-8", errors="ignore")


def verify_and_update_password(plain_password: str, hashed_password: str) -> Tuple[bool, Optional[str]]:
    """
    Verify the password and, if needed, return an upgraded hash.

    Returns:
      (is_valid, new_hash_or_none)
    """
    try:
        return pwd_context.verify_and_update(plain_password, hashed_password)
    except ValueError as e:
        # Backwards-compatible login for legacy bcrypt hashes when user enters a password >72 bytes.
        if _is_legacy_bcrypt_hash(hashed_password) and _is_bcrypt_72_byte_error(e):
            try:
                truncated = _truncate_password_for_legacy_bcrypt(plain_password)
                ok = pwd_context.verify(truncated, hashed_password)
                # Do NOT auto-upgrade in this path (long password suffix is ambiguous for legacy bcrypt).
                return ok, None
            except Exception:
                return False, None
        return False, None


def get_password_hash(password: str) -> str:
    """Hash a password using the current preferred scheme (supports long passwords)."""
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

        # Opportunistic upgrade:
        # Only upgrade when the password is <= 72 bytes to avoid ambiguity with legacy bcrypt hashes.
        if new_hash and len(password.encode("utf-8")) <= 72:
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

