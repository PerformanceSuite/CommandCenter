"""
Integration test fixtures and configuration.
"""

import os
import asyncio
import pytest
import json
from typing import AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from fastapi import WebSocket

from app.database import Base, get_db
from app.main import app
from app.models import Project, Repository, Technology, Job, JobStatus
from app.services.job_service import JobService


# Mark all tests in this directory as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="function")
async def test_project(db_session: AsyncSession) -> Project:
    """Create a test project."""
    project = Project(
        name="Test Project",
        description="A test project for integration tests",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture(scope="function")
async def test_repository(
    db_session: AsyncSession, test_project: Project
) -> Repository:
    """Create a test repository."""
    repository = Repository(
        project_id=test_project.id,
        owner="testowner",
        name="testrepo",
        full_name="testowner/testrepo",
        description="Test repository",
        url="https://github.com/testowner/testrepo",
        clone_url="https://github.com/testowner/testrepo.git",
        default_branch="main",
        is_private=False,
        github_id=12345,
    )
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)
    return repository


@pytest.fixture(scope="function")
async def test_technology(
    db_session: AsyncSession, test_project: Project
) -> Technology:
    """Create a test technology."""
    technology = Technology(
        project_id=test_project.id,
        name="Python",
        category="languages",
        ring="adopt",
        description="Python programming language",
        moved=0,
    )
    db_session.add(technology)
    await db_session.commit()
    await db_session.refresh(technology)
    return technology


@pytest.fixture(scope="function")
async def test_job(
    db_session: AsyncSession, test_project: Project
) -> Job:
    """Create a test job."""
    job = Job(
        project_id=test_project.id,
        job_type="analyze_repository",
        status=JobStatus.PENDING,
        parameters={"repository_id": 1},
        created_by="test_user",
        progress=0,
        current_step="Initializing",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.fixture(scope="function")
async def test_analysis_data(
    db_session: AsyncSession,
    test_project: Project,
    test_repository: Repository,
    test_technology: Technology,
) -> Dict[str, Any]:
    """
    Create complete test analysis data for export testing.

    Returns a dictionary with all necessary data for export format testing.
    """
    # Add more technologies for comprehensive testing
    tech2 = Technology(
        project_id=test_project.id,
        name="FastAPI",
        category="frameworks",
        ring="adopt",
        description="FastAPI web framework",
        moved=0,
    )
    tech3 = Technology(
        project_id=test_project.id,
        name="PostgreSQL",
        category="databases",
        ring="adopt",
        description="PostgreSQL database",
        moved=0,
    )
    db_session.add(tech2)
    db_session.add(tech3)
    await db_session.commit()

    return {
        "project_id": test_project.id,
        "repository_id": test_repository.id,
        "technologies": [test_technology.id, tech2.id, tech3.id],
        "project": test_project,
        "repository": test_repository,
    }


@pytest.fixture(scope="function")
async def job_service(db_session: AsyncSession) -> JobService:
    """Create a JobService instance for testing."""
    return JobService(db_session)


@pytest.fixture(scope="function")
async def websocket_test_client(db_session: AsyncSession) -> AsyncClient:
    """
    Create an async client for WebSocket testing.

    This fixture provides a client that can be used to test WebSocket endpoints.
    """

    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.rollback()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# Celery testing utilities
@pytest.fixture(scope="function")
def celery_config() -> Dict[str, Any]:
    """Configure Celery for testing."""
    return {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "task_always_eager": True,  # Execute tasks synchronously
        "task_eager_propagates": True,  # Propagate exceptions
    }


@pytest.fixture(scope="function")
def mock_celery_task(mocker: Any):
    """Mock Celery task execution for testing."""
    from unittest.mock import MagicMock
    mock_task = mocker.MagicMock()
    mock_task.delay.return_value.id = "test-task-id-123"
    mock_task.delay.return_value.state = "PENDING"
    return mock_task


# Export testing utilities
@pytest.fixture(scope="function")
def export_test_data() -> Dict[str, Any]:
    """
    Provide sample export data for testing export formats.

    This data mimics the structure returned by analysis operations.
    """
    return {
        "technologies": [
            {
                "name": "Python",
                "category": "languages",
                "version": "3.11",
                "status": "current",
            },
            {
                "name": "FastAPI",
                "category": "frameworks",
                "version": "0.109.0",
                "status": "current",
            },
            {
                "name": "Django",
                "category": "frameworks",
                "version": "2.2",
                "status": "outdated",
            },
        ],
        "dependencies": [
            {
                "name": "requests",
                "version": "2.31.0",
                "latest_version": "2.31.0",
                "is_outdated": False,
            },
            {
                "name": "numpy",
                "version": "1.20.0",
                "latest_version": "1.26.0",
                "is_outdated": True,
            },
        ],
        "gaps": [
            {
                "technology": "Python",
                "current_version": "3.9",
                "latest_version": "3.11",
                "gap_type": "major",
            },
        ],
        "metrics": {
            "total_technologies": 3,
            "outdated_technologies": 1,
            "total_dependencies": 2,
            "outdated_dependencies": 1,
            "research_gaps": 1,
        },
    }
