"""
Pytest configuration and shared fixtures
"""

import os
import asyncio
from typing import AsyncGenerator, Generator
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient

from app.database import Base, get_db
from app.main import app
from app.config import settings


# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-chars"
os.environ["GITHUB_TOKEN"] = "test_github_token"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Database fixtures
@pytest.fixture(scope="function")
async def async_engine():
    """Create async engine for testing"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async session for testing"""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def db_session(async_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Database session fixture"""
    yield async_session
    await async_session.rollback()


# FastAPI test client fixture
@pytest.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async client for testing FastAPI endpoints"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# Authentication fixtures
@pytest.fixture
def mock_github_token() -> str:
    """Mock GitHub token for testing"""
    return "ghp_test_token_1234567890abcdef"


@pytest.fixture
def test_user_data() -> dict:
    """Test user data"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "github_token": "ghp_test_token",
    }


# Repository fixtures
@pytest.fixture
def test_repository_data() -> dict:
    """Test repository data"""
    return {
        "owner": "testowner",
        "name": "testrepo",
        "full_name": "testowner/testrepo",
        "description": "A test repository",
        "url": "https://github.com/testowner/testrepo",
        "clone_url": "https://github.com/testowner/testrepo.git",
        "default_branch": "main",
        "is_private": False,
        "github_id": 12345,
    }


@pytest.fixture
def test_technology_data() -> dict:
    """Test technology data"""
    return {
        "name": "Python",
        "category": "language",
        "ring": "adopt",
        "description": "A high-level programming language",
        "moved": 0,
    }


@pytest.fixture
def test_research_task_data() -> dict:
    """Test research task data"""
    return {
        "title": "Research FastAPI best practices",
        "description": "Investigate best practices for FastAPI development",
        "status": "pending",
        "priority": "high",
        "repository_id": 1,
    }


# Mock service fixtures
@pytest.fixture
def mock_github_service(mocker):
    """Mock GitHub service"""
    mock = mocker.MagicMock()
    mock.authenticate_repo.return_value = True
    mock.list_user_repos.return_value = []
    mock.sync_repository.return_value = {
        "synced": True,
        "changes_detected": False,
    }
    return mock


@pytest.fixture
def mock_rag_service(mocker):
    """Mock RAG service"""
    mock = mocker.MagicMock()
    mock.index_repository.return_value = {"indexed": True, "documents": 10}
    mock.query.return_value = {
        "answer": "Test answer",
        "sources": [],
    }
    return mock
