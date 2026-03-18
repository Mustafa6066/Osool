"""
Database Configuration
----------------------
Async setup for PostgreSQL using SQLAlchemy.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# Database URL from env (fail-fast for security)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable must be set. "
        "No fallback provided for security. "
        "Example: postgresql+asyncpg://user:password@localhost:5432/dbname"
    )

# Convert postgresql:// to postgresql+asyncpg:// for async driver
# Railway provides postgresql:// but async SQLAlchemy needs asyncpg driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("sqlite://") and "sqlite+aiosqlite" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)

# Async Engine — production-grade connection pooling for stability under load
# Pool parameters are PostgreSQL-only; SQLite (aiosqlite) uses StaticPool and
# rejects these kwargs, which would crash tests and local SQLite environments.
_pool_kwargs: dict = {}
if "postgresql" in DATABASE_URL or "postgres" in DATABASE_URL:
    _pool_kwargs = dict(
        pool_size=20,              # Base persistent connections
        max_overflow=30,           # Burst connections when pool is full
        pool_recycle=1800,         # Recycle connections every 30 min (prevent stale)
        pool_timeout=30,           # Wait max 30s for a connection from pool
    )

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,        # Verify connections before use (detect dead connections)
    **_pool_kwargs,
)

# Session Factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Base Class
class Base(DeclarativeBase):
    pass

async def get_db():
    """Dependency for getting async session"""
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # WARNING: Dev only
        await conn.run_sync(Base.metadata.create_all)
