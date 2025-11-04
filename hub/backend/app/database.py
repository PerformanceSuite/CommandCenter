"""
Database configuration for Hub
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

# SQLite database for project registry
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:////app/data/hub.db")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Disable SQL echo for cleaner logs
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for async SQLAlchemy models."""
    pass


async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        yield session
