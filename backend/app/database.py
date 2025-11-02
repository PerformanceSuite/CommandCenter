"""
SQLAlchemy database setup and session management
Supports both SQLite (development) and PostgreSQL (production)

Phase C Enhancement: Query comment injection for correlation tracking
"""

from contextvars import ContextVar
from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings

# Context variable to store request_id for query comment injection
# This allows correlation IDs to propagate to database queries
request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""


# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool if "sqlite" in settings.database_url else None,
    future=True,
)


# Phase C: Event listener to inject correlation IDs into SQL queries
@event.listens_for(engine.sync_engine, "before_cursor_execute", retval=True)
def add_query_comment(conn, cursor, statement, parameters, context, executemany):
    """Inject correlation ID as SQL comment for pg_stat_statements tracking.

    This allows correlating slow queries with API requests by including
    the request_id in the SQL query as a comment:

        /* request_id: abc-123-xyz */ SELECT * FROM repositories;

    The comment is visible in:
    - PostgreSQL logs
    - pg_stat_statements (queryid grouping)
    - postgres_exporter slow query metrics

    Performance: < 0.1ms overhead per query
    """
    request_id = request_id_context.get()

    if request_id:
        # Prepend SQL comment with request_id
        # Format: /* request_id: {uuid} */ {original_statement}
        statement = f"/* request_id: {request_id} */ {statement}"

    return statement, parameters


# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions

    IMPORTANT: This function only provides the session and handles rollback/close.
    The service layer is responsible for calling session.commit() explicitly
    before returning from the endpoint handler.

    This ensures commits happen BEFORE the response is sent to the client,
    preventing silent data loss if the commit fails.

    Usage:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            # ... do work ...
            await db.commit()  # Commit explicitly in service/endpoint
            return result
    """
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
