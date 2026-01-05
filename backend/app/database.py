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

# Database URL from env
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://osool:osool_password@localhost:5432/osool_db")

# Async Engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
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
