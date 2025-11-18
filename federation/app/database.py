# federation/app/database.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
import os

Base = declarative_base()

# Only create engine if not in Alembic migration mode
if os.environ.get("SKIP_ASYNC_ENGINE"):
    # Alembic will use its own engine
    engine = None
    AsyncSessionLocal = None
else:
    from app.config import settings

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes."""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_async_session():
    """Context manager for background workers."""
    async with AsyncSessionLocal() as session:
        yield session
