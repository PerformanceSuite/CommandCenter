# federation/app/database.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
import os

Base = declarative_base()

# Only create engine if not in Alembic migration mode
# SKIP_ASYNC_ENGINE is set during Alembic migrations to prevent the async engine
# from being created, since Alembic uses its own synchronous engine for migrations.
# This avoids conflicts and allows migrations to run without application startup.
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
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "Database engine not initialized. Ensure SKIP_ASYNC_ENGINE is not set in application context."
        )
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_async_session():
    """Context manager for background workers."""
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "Database engine not initialized. Ensure SKIP_ASYNC_ENGINE is not set in application context."
        )
    async with AsyncSessionLocal() as session:
        yield session
