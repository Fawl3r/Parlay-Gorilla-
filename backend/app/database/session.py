"""Database session management for PostgreSQL"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

def get_database_url() -> str:
    """
    Get the appropriate database URL based on environment.
    
    Priority:
    1. SQLite (fallback for quick local testing, when USE_SQLITE=true)
    2. DATABASE_URL (Render PostgreSQL / local PostgreSQL)
    """
    # Check for SQLite fallback mode
    if settings.use_sqlite:
        sqlite_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "parlay_gorilla.db"
        )
        return f"sqlite+aiosqlite:///{sqlite_path}"
    
    db_url = settings.database_url
    
    # Ensure asyncpg driver for PostgreSQL
    if db_url.startswith("postgresql+asyncpg://"):
        return db_url
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if db_url.startswith("postgres://"):
        # Common on Render and other providers.
        return db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    return db_url


DATABASE_URL = get_database_url()
is_sqlite = "sqlite" in DATABASE_URL

# Engine configuration based on database type
if is_sqlite:
    # SQLite settings (for fallback/testing)
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.debug,
        future=True,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL (Render / local Docker) - use connection pooling
    # Set statement_timeout via server_settings to prevent hanging queries
    connect_args = {
        "server_settings": {
            "statement_timeout": "30000",  # 30 seconds in milliseconds
        }
    }
    
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.debug,
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args=connect_args,
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
    # Ensure all models are registered with SQLAlchemy metadata.
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await engine.dispose()
