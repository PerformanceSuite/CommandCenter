import pytest
from datetime import datetime, timezone
from freezegun import freeze_time
from app.services.catalog_service import CatalogService
from app.models.project import ProjectStatus


@pytest.mark.asyncio
async def test_register_project_creates_new(db_session):
    """Test registering a new project."""
    service = CatalogService(db_session)

    project = await service.register_project(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:8000",
        mesh_namespace="hub.commandcenter",
        tags=["python", "fastapi"]
    )

    assert project.id is not None
    assert project.slug == "commandcenter"
    assert project.name == "CommandCenter"
    assert project.status == ProjectStatus.OFFLINE
    assert project.tags == ["python", "fastapi"]


@pytest.mark.asyncio
async def test_heartbeat_updates_status(db_session):
    """Test heartbeat updates status to online."""
    service = CatalogService(db_session)

    # Register project
    await service.register_project(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:8000",
        mesh_namespace="hub.commandcenter",
        tags=[]
    )

    # Send heartbeat
    await service.update_heartbeat("commandcenter")

    # Verify status
    project = await service.get_project("commandcenter")
    assert project.status == ProjectStatus.ONLINE
    assert project.last_heartbeat_at is not None


@pytest.mark.asyncio
async def test_get_projects_filter_by_status(db_session):
    """Test filtering projects by status."""
    service = CatalogService(db_session)

    # Create 2 projects
    await service.register_project(slug="project1", name="P1", hub_url="http://localhost:8000", mesh_namespace="hub.p1", tags=[])
    await service.register_project(slug="project2", name="P2", hub_url="http://localhost:8001", mesh_namespace="hub.p2", tags=[])

    # Heartbeat one
    await service.update_heartbeat("project1")

    # Filter online
    online = await service.get_projects(status_filter=ProjectStatus.ONLINE)
    assert len(online) == 1
    assert online[0].slug == "project1"

    # Filter offline
    offline = await service.get_projects(status_filter=ProjectStatus.OFFLINE)
    assert len(offline) == 1
    assert offline[0].slug == "project2"


@pytest.mark.asyncio
async def test_mark_stale_projects(db_session):
    """Test that projects are marked offline after 90s without heartbeat."""
    service = CatalogService(db_session)

    # Register and activate project
    await service.register_project(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:8000",
        mesh_namespace="hub.commandcenter",
        tags=[]
    )

    # Start time: 2025-01-01 12:00:00
    with freeze_time("2025-01-01 12:00:00"):
        await service.update_heartbeat("commandcenter")
        project = await service.get_project("commandcenter")
        assert project.status == ProjectStatus.ONLINE

    # Move time forward 89 seconds - should still be online
    with freeze_time("2025-01-01 12:01:29"):
        count = await service.mark_stale_projects()
        assert count == 0
        project = await service.get_project("commandcenter")
        assert project.status == ProjectStatus.ONLINE

    # Move time forward 91 seconds - should be marked offline
    with freeze_time("2025-01-01 12:01:31"):
        count = await service.mark_stale_projects()
        assert count == 1
        project = await service.get_project("commandcenter")
        assert project.status == ProjectStatus.OFFLINE


@pytest.mark.asyncio
async def test_update_heartbeat_missing_project(db_session):
    """Test that update_heartbeat raises ValueError for missing project."""
    service = CatalogService(db_session)

    with pytest.raises(ValueError, match="Project 'nonexistent' not found in catalog"):
        await service.update_heartbeat("nonexistent")
