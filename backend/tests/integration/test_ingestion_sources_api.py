"""
Integration tests for ingestion sources API
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion_source import SourceStatus, SourceType
from app.models.project import Project


@pytest.mark.asyncio
async def test_create_rss_source(async_client: AsyncClient, sample_project: Project):
    """Test creating RSS ingestion source"""
    payload = {
        "project_id": sample_project.id,
        "type": "rss",
        "name": "Tech Blog",
        "url": "https://example.com/feed.xml",
        "schedule": "0 * * * *",
        "priority": 8,
        "enabled": True,
    }

    response = await async_client.post("/api/ingestion/sources", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tech Blog"
    assert data["type"] == "rss"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_sources(
    async_client: AsyncClient, sample_project: Project, db_session: AsyncSession
):
    """Test listing ingestion sources"""
    from app.models.ingestion_source import IngestionSource

    # Create test sources
    source1 = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="Source 1",
        url="https://example.com/feed1",
        priority=5,
        enabled=True,
    )
    source2 = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.DOCUMENTATION,
        name="Source 2",
        url="https://example.com/docs",
        priority=7,
        enabled=True,
    )
    db_session.add_all([source1, source2])
    await db_session.commit()

    response = await async_client.get(f"/api/ingestion/sources?project_id={sample_project.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["sources"]) == 2


@pytest.mark.asyncio
async def test_get_source_by_id(
    async_client: AsyncClient, sample_project: Project, db_session: AsyncSession
):
    """Test getting single source"""
    from app.models.ingestion_source import IngestionSource

    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="Test Source",
        url="https://example.com/feed",
        priority=5,
        enabled=True,
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    response = await async_client.get(f"/api/ingestion/sources/{source.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == source.id
    assert data["name"] == "Test Source"


@pytest.mark.asyncio
async def test_update_source(
    async_client: AsyncClient, sample_project: Project, db_session: AsyncSession
):
    """Test updating source"""
    from app.models.ingestion_source import IngestionSource

    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="Old Name",
        url="https://example.com/feed",
        priority=5,
        enabled=True,
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    update_payload = {"name": "New Name", "priority": 9, "enabled": False}

    response = await async_client.put(f"/api/ingestion/sources/{source.id}", json=update_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["priority"] == 9
    assert data["enabled"] == False


@pytest.mark.asyncio
async def test_delete_source(
    async_client: AsyncClient, sample_project: Project, db_session: AsyncSession
):
    """Test deleting source"""
    from sqlalchemy import select

    from app.models.ingestion_source import IngestionSource

    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="To Delete",
        url="https://example.com/feed",
        priority=5,
        enabled=True,
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    source_id = source.id

    response = await async_client.delete(f"/api/ingestion/sources/{source_id}")

    assert response.status_code == 204

    # Verify deleted
    result = await db_session.execute(
        select(IngestionSource).filter(IngestionSource.id == source_id)
    )
    deleted_source = result.scalar_one_or_none()
    assert deleted_source is None


@pytest.mark.asyncio
async def test_trigger_manual_run(
    async_client: AsyncClient, sample_project: Project, db_session: AsyncSession
):
    """Test manually triggering source run"""
    from unittest.mock import patch

    from app.models.ingestion_source import IngestionSource

    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="Manual Source",
        url="https://example.com/feed",
        priority=5,
        enabled=True,
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    with patch("app.tasks.ingestion_tasks.scrape_rss_feed.delay") as mock_task:
        mock_task.return_value.id = "task-123"

        response = await async_client.post(f"/api/ingestion/sources/{source.id}/run")

        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        mock_task.assert_called_once_with(source.id)
