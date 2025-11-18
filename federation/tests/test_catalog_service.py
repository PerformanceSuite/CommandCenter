import pytest
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
