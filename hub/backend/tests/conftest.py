"""
Pytest fixtures for testing
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.models import Base, Project


@pytest.fixture
def db_engine():
    """Create in-memory SQLite engine for testing"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    return engine


@pytest.fixture
async def db_session(db_engine):
    """Create async database session for testing"""
    # Create all tables
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Provide session for test
    async with async_session() as session:
        yield session

    # Cleanup
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def sample_project(db_session):
    """Create a sample project for testing"""
    project = Project(
        name="TestProject",
        slug="test-project",
        path="/tmp/test-project",
        cc_path="/tmp/test-project/commandcenter",
        compose_project_name="test-project-cc",
        status="stopped",
        backend_port=8000,
        frontend_port=3000,
        postgres_port=5432,
        redis_port=6379,
        is_configured=True
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project
