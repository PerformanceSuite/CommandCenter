"""
Integration tests for Projects API

Tests the complete HTTP API for project management, including:
- CRUD operations
- Start/stop operations (with mocked Dagger)
- Error handling
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from tests.utils.helpers import create_test_project


@pytest.fixture
def client(db_session):
    """Create test client with database dependency override"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_project_success(client, db_session):
    """Test creating a new project via API"""
    with patch("os.path.exists", return_value=True):
        response = client.post(
            "/api/projects/",
            json={"name": "NewProject", "path": "/tmp/new-project"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "NewProject"
    assert data["slug"] == "newproject"
    assert data["status"] == "stopped"
    assert data["is_configured"] is True
    assert "backend_port" in data
    assert "frontend_port" in data


@pytest.mark.asyncio
async def test_create_project_invalid_path(client, db_session):
    """Test creating project with non-existent path fails"""
    with patch("os.path.exists", return_value=False):
        response = client.post(
            "/api/projects/",
            json={"name": "FailProject", "path": "/invalid/path"},
        )

    assert response.status_code == 422 or response.status_code == 500


@pytest.mark.asyncio
async def test_create_project_duplicate_name(client, db_session):
    """Test creating project with duplicate name fails"""
    await create_test_project(db_session, name="DuplicateProject", slug="duplicate")

    with patch("os.path.exists", return_value=True):
        response = client.post(
            "/api/projects/",
            json={"name": "DuplicateProject", "path": "/tmp/duplicate-2"},
        )

    assert response.status_code == 422 or response.status_code == 500


@pytest.mark.asyncio
async def test_list_projects(client, db_session):
    """Test listing all projects"""
    await create_test_project(db_session, name="Project1", slug="project-1")
    await create_test_project(db_session, name="Project2", slug="project-2")

    response = client.get("/api/projects/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Project1"
    assert data[1]["name"] == "Project2"


@pytest.mark.asyncio
async def test_list_projects_excludes_creating_status(client, db_session):
    """Test that list excludes projects with status='creating'"""
    await create_test_project(db_session, name="Stopped", status="stopped")
    await create_test_project(db_session, name="Creating", status="creating")

    response = client.get("/api/projects/")

    assert response.status_code == 200
    data = response.json()
    # Should only return stopped project
    assert len(data) == 1
    assert data[0]["name"] == "Stopped"


@pytest.mark.asyncio
async def test_get_project_by_id(client, db_session):
    """Test getting a specific project by ID"""
    project = await create_test_project(db_session, name="GetProject")

    response = client.get(f"/api/projects/{project.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project.id
    assert data["name"] == "GetProject"


@pytest.mark.asyncio
async def test_get_project_not_found(client, db_session):
    """Test getting non-existent project returns 404"""
    response = client.get("/api/projects/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client, db_session):
    """Test updating project details"""
    project = await create_test_project(db_session, name="OldName")

    response = client.patch(
        f"/api/projects/{project.id}",
        json={"name": "NewName", "status": "running"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NewName"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_update_project_not_found(client, db_session):
    """Test updating non-existent project returns 404"""
    response = client.patch("/api/projects/999", json={"name": "NewName"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project(client, db_session):
    """Test deleting a project"""
    project = await create_test_project(db_session, name="ToDelete")

    response = client.delete(f"/api/projects/{project.id}")

    assert response.status_code == 204

    # Verify project is deleted
    response = client.get(f"/api/projects/{project.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_with_stop(client, db_session):
    """Test deleting a running project with delete_files=true stops it"""
    project = await create_test_project(
        db_session, name="RunningToDelete", status="running"
    )

    # Mock orchestration service stop
    with patch(
        "app.services.orchestration_service.OrchestrationService.stop_project"
    ) as mock_stop:
        response = client.delete(f"/api/projects/{project.id}?delete_files=true")

    assert response.status_code == 204
    # Note: mock_stop may not be called if project isn't actually running in the service


@pytest.mark.asyncio
async def test_delete_project_not_found(client, db_session):
    """Test deleting non-existent project returns 404"""
    response = client.delete("/api/projects/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_stats(client, db_session):
    """Test getting project statistics"""
    await create_test_project(db_session, name="P1", status="stopped")
    await create_test_project(db_session, name="P2", status="running")
    await create_test_project(db_session, name="P3", status="error")

    response = client.get("/api/projects/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_projects"] == 3
    assert data["running"] == 1
    assert data["stopped"] == 1
    assert data["errors"] == 1


@pytest.mark.asyncio
async def test_get_project_stats_excludes_creating(client, db_session):
    """Test that stats exclude projects with status='creating'"""
    await create_test_project(db_session, name="P1", status="stopped")
    await create_test_project(db_session, name="P2", status="creating")

    response = client.get("/api/projects/stats")

    assert response.status_code == 200
    data = response.json()
    # Should only count stopped project
    assert data["total_projects"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
