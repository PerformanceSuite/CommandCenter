"""
Optimized database configuration with proper connection pooling.
Performance improvements for production deployments.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from typing import AsyncGenerator, List, Optional
import asyncio

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""



class OptimizedDatabaseConfig:
    """
    Optimized database configuration with connection pooling
    and read replica support.
    """

    def __init__(
        self,
        database_url: str,
        read_replica_urls: Optional[List[str]] = None,
        debug: bool = False,
    ):
        """
        Initialize optimized database configuration.

        Args:
            database_url: Primary database URL (write operations)
            read_replica_urls: Optional list of read replica URLs
            debug: Enable SQL echo for debugging
        """
        self.database_url = database_url
        self.read_replica_urls = read_replica_urls or []
        self.debug = debug
        self._read_index = 0
        self._lock = asyncio.Lock()

        # Create optimized write engine with connection pooling
        self.write_engine = self._create_engine(database_url, is_write=True)

        # Create read engines for replicas
        self.read_engines = (
            [self._create_engine(url, is_write=False) for url in self.read_replica_urls]
            if self.read_replica_urls
            else [self.write_engine]
        )

        # Create session factories
        self.write_session_factory = async_sessionmaker(
            self.write_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        self.read_session_factories = [
            async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            for engine in self.read_engines
        ]

    def _create_engine(self, database_url: str, is_write: bool = False) -> AsyncEngine:
        """
        Create optimized async engine with proper pooling.

        Args:
            database_url: Database connection URL
            is_write: Whether this is a write connection

        Returns:
            Configured AsyncEngine
        """
        # Use NullPool for SQLite (development)
        if "sqlite" in database_url:
            return create_async_engine(
                database_url,
                echo=self.debug,
                poolclass=NullPool,
                future=True,
            )

        # Optimized pooling for PostgreSQL (production)
        pool_size = 20 if is_write else 10  # More connections for write pool
        max_overflow = 10 if is_write else 5

        return create_async_engine(
            database_url,
            echo=self.debug,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=pool_size,  # Base number of connections
            max_overflow=max_overflow,  # Additional connections under load
            pool_timeout=30,  # Timeout waiting for connection
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Verify connections before use
            connect_args={
                "server_settings": {
                    "application_name": f"commandcenter_{'write' if is_write else 'read'}",
                    "jit": "off",  # Disable JIT for more predictable performance
                },
                "command_timeout": 60,  # Command timeout
                "prepared_statement_cache_size": 0,  # Disable prepared statements cache
            },
            future=True,
        )

    async def get_write_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session for write operations.

        Yields:
            AsyncSession for write operations
        """
        async with self.write_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def get_read_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session for read operations.
        Uses round-robin selection for read replicas.

        Yields:
            AsyncSession for read operations
        """
        # Round-robin selection of read replica
        async with self._lock:
            session_factory = self.read_session_factories[self._read_index]
            self._read_index = (self._read_index + 1) % len(self.read_session_factories)

        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def init_db(self) -> None:
        """Initialize database tables"""
        async with self.write_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close_all(self) -> None:
        """Close all database connections"""
        await self.write_engine.dispose()
        for engine in self.read_engines:
            if engine != self.write_engine:  # Don't dispose write engine twice
                await engine.dispose()


# Create global optimized database configuration
_db_config: Optional[OptimizedDatabaseConfig] = None


def get_db_config() -> OptimizedDatabaseConfig:
    """
    Get or create the optimized database configuration.

    Returns:
        OptimizedDatabaseConfig instance
    """
    global _db_config
    if _db_config is None:
        # Parse read replica URLs from environment (comma-separated)
        read_replicas = []
        if hasattr(settings, "read_replica_urls") and settings.read_replica_urls:
            read_replicas = [
                url.strip() for url in settings.read_replica_urls.split(",") if url.strip()
            ]

        _db_config = OptimizedDatabaseConfig(
            database_url=settings.database_url,
            read_replica_urls=read_replicas,
            debug=settings.debug,
        )
    return _db_config


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions (write operations).
    Backwards compatible with existing code.

    Yields:
        AsyncSession for database operations
    """
    config = get_db_config()
    async for session in config.get_write_session():
        yield session


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions (read operations).
    Use this for read-only endpoints to distribute load.

    Yields:
        AsyncSession for read operations
    """
    config = get_db_config()
    async for session in config.get_read_session():
        yield session


# Example usage in routers:
# @router.get("/items", response_model=List[Item])
# async def list_items(db: AsyncSession = Depends(get_read_db)):
#     # Read-only operation uses read replica
#     return await db.execute(select(Item))
#
# @router.post("/items", response_model=Item)
# async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
#     # Write operation uses primary database
#     db.add(Item(**item.dict()))
#     await db.commit()
