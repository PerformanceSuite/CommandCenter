"""
Pytest fixtures for Hub testing

This module provides comprehensive test fixtures for:
- Database setup (async SQLite)
- Test clients (FastAPI TestClient)
- Mock Dagger SDK
- Project factories
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient

from app.models import Base, Project
from app.database import get_db
from app.main import app


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def db_engine():
    """Create in-memory SQLite engine for testing"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    return engine


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
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


# ============================================================================
# FastAPI Client Fixtures
# ============================================================================

@pytest.fixture
def test_client(db_session):
    """Create FastAPI TestClient with dependency override"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ============================================================================
# Mock Dagger Fixtures
# ============================================================================

@pytest.fixture
def mock_dagger_client():
    """Mock Dagger client for testing orchestration without actual containers"""
    client = MagicMock()

    # Mock container builder
    mock_container = MagicMock()
    mock_container.from_ = MagicMock(return_value=mock_container)
    mock_container.with_env_variable = MagicMock(return_value=mock_container)
    mock_container.with_exposed_port = MagicMock(return_value=mock_container)
    mock_container.with_mounted_directory = MagicMock(return_value=mock_container)
    mock_container.with_workdir = MagicMock(return_value=mock_container)
    mock_container.with_exec = MagicMock(return_value=mock_container)
    mock_container.as_service = MagicMock(return_value=MagicMock())

    client.container = MagicMock(return_value=mock_container)
    client.host = MagicMock(return_value=MagicMock(directory=MagicMock(return_value=MagicMock())))

    return client


@pytest.fixture
def mock_dagger_connection(mock_dagger_client):
    """Mock Dagger Connection for testing CommandCenterStack"""
    connection = AsyncMock()
    connection.__aenter__ = AsyncMock(return_value=mock_dagger_client)
    connection.__aexit__ = AsyncMock(return_value=None)
    return connection


@pytest.fixture
def mock_dagger_stack():
    """Mock CommandCenterStack for testing orchestration service"""
    stack = AsyncMock()
    stack.__aenter__ = AsyncMock(return_value=stack)
    stack.__aexit__ = AsyncMock(return_value=None)
    stack.start = AsyncMock(return_value={
        "success": True,
        "message": "Stack started successfully",
        "services": {
            "postgres": {"port": 5432},
            "redis": {"port": 6379},
            "backend": {"port": 8000},
            "frontend": {"port": 3000},
        }
    })
    stack.stop = AsyncMock(return_value={
        "success": True,
        "message": "Stack stopped successfully"
    })
    stack.status = AsyncMock(return_value={
        "status": "running",
        "health": "healthy",
        "containers": []
    })
    return stack


# ============================================================================
# Project Factory Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def sample_project(db_session) -> Project:
    """Create a sample project for testing"""
    project = Project(
        name="TestProject",
        slug="test-project",
        path="/tmp/test-project",
        status="stopped",
        backend_port=8010,
        frontend_port=3010,
        postgres_port=5442,
        redis_port=6389,
        is_configured=True
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def running_project(db_session) -> Project:
    """Create a running project for testing"""
    project = Project(
        name="RunningProject",
        slug="running-project",
        path="/tmp/running-project",
        status="running",
        health="healthy",
        backend_port=8020,
        frontend_port=3020,
        postgres_port=5452,
        redis_port=6399,
        is_configured=True
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def multiple_projects(db_session) -> list[Project]:
    """Create multiple projects with different statuses for testing"""
    projects = [
        Project(
            name="Project1",
            slug="project-1",
            path="/tmp/project-1",
            status="stopped",
            backend_port=8010,
            frontend_port=3010,
            postgres_port=5442,
            redis_port=6389,
            is_configured=True
        ),
        Project(
            name="Project2",
            slug="project-2",
            path="/tmp/project-2",
            status="running",
            health="healthy",
            backend_port=8020,
            frontend_port=3020,
            postgres_port=5452,
            redis_port=6399,
            is_configured=True
        ),
        Project(
            name="Project3",
            slug="project-3",
            path="/tmp/project-3",
            status="error",
            backend_port=8030,
            frontend_port=3030,
            postgres_port=5462,
            redis_port=6409,
            is_configured=True
        ),
    ]

    for project in projects:
        db_session.add(project)

    await db_session.commit()

    for project in projects:
        await db_session.refresh(project)

    return projects


# ============================================================================
# Mock Port Checking Fixtures
# ============================================================================

@pytest.fixture
def mock_port_available():
    """Mock port availability checks to always return available"""
    with patch('socket.socket') as mock_socket:
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 1  # Port not in use
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=None)
        mock_socket.return_value = mock_sock
        yield mock_socket


@pytest.fixture
def mock_port_unavailable():
    """Mock port availability checks to always return unavailable"""
    with patch('socket.socket') as mock_socket:
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0  # Port in use
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=None)
        mock_socket.return_value = mock_sock
        yield mock_socket
