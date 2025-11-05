"""Integration test fixtures for Hub background tasks"""
import pytest
import asyncio
import time
# from celery.result import AsyncResult
# from app.celery_app import celery_app
from app.database import AsyncSessionLocal, engine, Base
from app.models import Project


@pytest.fixture(scope="session")
def celery_config():
    """Celery configuration for tests"""
    return {
        'broker_url': 'redis://localhost:6379/1',  # Use DB 1 for tests
        'result_backend': 'redis://localhost:6379/1',
        'task_always_eager': False,  # Run tasks asynchronously
        'task_eager_propagates': True,
    }


@pytest.fixture(scope="session")
def celery_worker_parameters():
    """Celery worker parameters for tests"""
    return {
        'queues': ('celery',),
        'loglevel': 'info',
    }


@pytest.fixture(scope="function")
async def test_db():
    """Create test database"""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_project(test_db):
    """Create a test project"""
    async with AsyncSessionLocal() as db:
        project = Project(
            name="Integration Test Project",
            path="/tmp/test-project",
            status="stopped",
            backend_port=8888,
            frontend_port=3888,
            postgres_port=5555,
            redis_port=6666
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
