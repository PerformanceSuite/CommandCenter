"""
Integration tests for IngestionSource model
"""
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion_source import IngestionSource, SourceStatus, SourceType
from app.models.project import Project


@pytest.mark.integration
async def test_create_rss_source(db_session: AsyncSession, sample_project: Project):
    """Test creating an RSS ingestion source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="Tech Blog Feed",
        url="https://example.com/feed.xml",
        schedule="0 * * * *",  # Every hour
        priority=8,
        enabled=True,
    )
    db_session.add(source)
    await db_session.commit()

    assert source.id is not None
    assert source.type == SourceType.RSS
    assert source.status == SourceStatus.PENDING
    assert source.last_run is None
    assert source.error_count == 0


@pytest.mark.integration
async def test_create_documentation_source(db_session: AsyncSession, sample_project: Project):
    """Test creating a documentation scraper source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.DOCUMENTATION,
        name="FastAPI Docs",
        url="https://fastapi.tiangolo.com",
        schedule="0 0 * * 0",  # Weekly
        priority=9,
        enabled=True,
        config={"doc_system": "mkdocs", "max_depth": 3},
    )
    db_session.add(source)
    await db_session.commit()

    assert source.id is not None
    assert source.config["doc_system"] == "mkdocs"
    assert source.priority == 9


@pytest.mark.integration
async def test_create_webhook_source(db_session: AsyncSession, sample_project: Project):
    """Test creating a webhook receiver source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.WEBHOOK,
        name="GitHub Webhook",
        url="/api/webhooks/github",
        priority=10,
        enabled=True,
        config={"secret": "webhook-secret-key", "events": ["push", "release"]},
    )
    db_session.add(source)
    await db_session.commit()

    assert source.id is not None
    assert source.schedule is None  # Webhooks don't have schedules


@pytest.mark.integration
async def test_create_file_watcher_source(db_session: AsyncSession, sample_project: Project):
    """Test creating a file system watcher source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.FILE_WATCHER,
        name="Research Documents",
        path="/home/user/Documents/Research",
        priority=7,
        enabled=True,
        config={"patterns": ["*.pdf", "*.md"], "ignore": [".git", "node_modules"]},
    )
    db_session.add(source)
    await db_session.commit()

    assert source.id is not None
    assert source.path == "/home/user/Documents/Research"


@pytest.mark.integration
async def test_source_priority_ordering(db_session: AsyncSession, sample_project: Project):
    """Test sources can be ordered by priority"""
    # Create sources with different priorities
    low = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="Low Priority",
        url="https://low.com/feed",
        priority=3,
        enabled=True,
    )
    high = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="High Priority",
        url="https://high.com/feed",
        priority=9,
        enabled=True,
    )
    medium = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="Medium Priority",
        url="https://medium.com/feed",
        priority=6,
        enabled=True,
    )

    db_session.add_all([low, high, medium])
    await db_session.commit()

    # Query sources ordered by priority descending
    result = await db_session.execute(
        select(IngestionSource)
        .filter(IngestionSource.project_id == sample_project.id)
        .order_by(IngestionSource.priority.desc())
    )
    sources = result.scalars().all()

    assert sources[0].name == "High Priority"
    assert sources[1].name == "Medium Priority"
    assert sources[2].name == "Low Priority"


@pytest.mark.integration
async def test_update_source_status(db_session: AsyncSession, sample_project: Project):
    """Test updating source status after run"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="Test Source",
        url="https://test.com/feed",
        priority=5,
        enabled=True,
    )
    db_session.add(source)
    await db_session.commit()

    # Simulate successful run
    source.status = SourceStatus.SUCCESS
    source.last_run = datetime.utcnow()
    source.last_success = datetime.utcnow()
    source.documents_ingested = 15
    await db_session.commit()

    assert source.status == SourceStatus.SUCCESS
    assert source.last_run is not None
    assert source.documents_ingested == 15

    # Simulate error
    source.status = SourceStatus.ERROR
    source.error_count += 1
    source.last_error = "Connection timeout"
    await db_session.commit()

    assert source.status == SourceStatus.ERROR
    assert source.error_count == 1
    assert source.last_error == "Connection timeout"


@pytest.mark.integration
async def test_disable_source(db_session: AsyncSession, sample_project: Project):
    """Test disabling a source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="Test Source",
        url="https://test.com/feed",
        priority=5,
        enabled=True,
    )
    db_session.add(source)
    await db_session.commit()

    source.enabled = False
    await db_session.commit()

    # Query only enabled sources
    result = await db_session.execute(
        select(IngestionSource)
        .filter(IngestionSource.project_id == sample_project.id)
        .filter(IngestionSource.enabled == True)
    )
    enabled_sources = result.scalars().all()

    assert len(enabled_sources) == 0
