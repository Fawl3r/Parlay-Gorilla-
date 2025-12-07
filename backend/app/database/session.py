"""Database session management for PostgreSQL"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import settings

def get_database_url() -> str:
    """
    Get the appropriate database URL based on environment.
    
    Priority:
    1. Neon (production)
    2. Local PostgreSQL (Docker)
    3. SQLite (fallback for quick testing)
    """
    # Check for SQLite fallback mode
    if settings.use_sqlite:
        sqlite_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "parlay_gorilla.db"
        )
        return f"sqlite+aiosqlite:///{sqlite_path}"
    
    # Use effective database URL (Neon in production, local PostgreSQL otherwise)
    db_url = settings.effective_database_url
    
    # Ensure asyncpg driver for PostgreSQL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    return db_url


DATABASE_URL = get_database_url()
is_sqlite = "sqlite" in DATABASE_URL
is_neon = "neon.tech" in DATABASE_URL or "neon" in DATABASE_URL.lower()

# Engine configuration based on database type
if is_sqlite:
    # SQLite settings (for fallback/testing)
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.debug,
        future=True,
        connect_args={"check_same_thread": False},
    )
elif is_neon:
    # Neon PostgreSQL - use NullPool for serverless
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.debug,
        future=True,
        poolclass=NullPool,  # Neon handles connection pooling
    )
else:
    # Local PostgreSQL (Docker) - use connection pooling
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.debug,
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await engine.dispose()
