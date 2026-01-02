"""
Integration tests for Repository API endpoints
"""

from datetime import datetime

import pytest
from httpx import AsyncClient
from tests.utils import create_test_repository


@pytest.mark.integration
class TestRepositoriesAPI:
    """Test Repository API endpoints"""

    async def test_list_repositories_empty(self, api_client: AsyncClient):
        """Test listing repositories when none exist"""
        response = await api_client.get("/repositories/")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_repositories(self, api_client: AsyncClient, db_session):
        """Test listing repositories"""
        # Create test repositories
        await create_test_repository(db_session, full_name="owner1/repo1")
        await create_test_repository(db_session, full_name="owner2/repo2")

        response = await api_client.get("/repositories/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_list_repositories_pagination(self, api_client: AsyncClient, db_session):
        """Test repository listing with pagination"""
        # Create multiple repositories
        for i in range(5):
            await create_test_repository(db_session, full_name=f"owner/repo{i}")

        # Test limit
        response = await api_client.get("/repositories/?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Test skip
        response = await api_client.get("/repositories/?skip=3")
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_get_repository(self, api_client: AsyncClient, db_session):
        """Test getting a specific repository"""
        repo = await create_test_repository(db_session)

        response = await api_client.get(f"/repositories/{repo.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == repo.id
        assert data["full_name"] == repo.full_name
        assert data["owner"] == repo.owner
        assert data["name"] == repo.name

    async def test_get_repository_not_found(self, api_client: AsyncClient):
        """Test getting non-existent repository"""
        response = await api_client.get("/repositories/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_create_repository(self, api_client: AsyncClient):
        """Test creating a new repository"""
        data = {
            "owner": "testowner",
            "name": "testrepo",
            "description": "Test repository",
            "is_private": False,
        }

        response = await api_client.post("/repositories/", json=data)

        assert response.status_code == 201
        created = response.json()
        assert created["owner"] == "testowner"
        assert created["name"] == "testrepo"
        assert created["full_name"] == "testowner/testrepo"
        assert created["description"] == "Test repository"
        assert "id" in created

    async def test_create_repository_duplicate(self, api_client: AsyncClient, db_session):
        """Test creating duplicate repository"""
        # Create first repository
        await create_test_repository(db_session, full_name="owner/repo")

        # Try to create duplicate
        data = {"owner": "owner", "name": "repo", "description": "Duplicate"}

        response = await api_client.post("/repositories/", json=data)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_create_repository_invalid_name(self, api_client: AsyncClient):
        """Test creating repository with invalid name"""
        data = {"owner": "-invalid", "name": "testrepo"}

        response = await api_client.post("/repositories/", json=data)

        assert response.status_code == 422  # Validation error

    async def test_update_repository(self, api_client: AsyncClient, db_session):
        """Test updating repository"""
        repo = await create_test_repository(db_session)

        update_data = {"description": "Updated description", "is_private": True}

        response = await api_client.patch(f"/repositories/{repo.id}", json=update_data)

        assert response.status_code == 200
        updated = response.json()
        assert updated["description"] == "Updated description"
        assert updated["is_private"] is True

    async def test_update_repository_not_found(self, api_client: AsyncClient):
        """Test updating non-existent repository"""
        update_data = {"description": "Updated"}

        response = await api_client.patch("/repositories/999", json=update_data)

        assert response.status_code == 404

    async def test_delete_repository(self, api_client: AsyncClient, db_session):
        """Test deleting repository"""
        repo = await create_test_repository(db_session)

        response = await api_client.delete(f"/repositories/{repo.id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await api_client.get(f"/repositories/{repo.id}")
        assert get_response.status_code == 404

    async def test_delete_repository_not_found(self, api_client: AsyncClient):
        """Test deleting non-existent repository"""
        response = await api_client.delete("/repositories/999")

        assert response.status_code == 404

    async def test_sync_repository(self, api_client: AsyncClient, db_session, mocker):
        """Test syncing repository with GitHub"""
        repo = await create_test_repository(db_session)

        # Mock GitHub async service - patch where it's used (in the service module)
        mock_sync_info = {
            "synced": True,
            "full_name": "testowner/testrepo",
            "last_commit_sha": "abc123",
            "last_commit_message": "Test commit",
            "last_commit_author": "Test Author",
            "last_commit_date": datetime.utcnow(),
            "last_synced_at": datetime.utcnow(),
            "changes_detected": True,
            "stars": 150,
            "forks": 20,
            "language": "Python",
        }

        mock_github_service = mocker.patch("app.services.repository_service.GitHubAsyncService")
        mock_instance = mocker.AsyncMock()
        mock_instance.sync_repository = mocker.AsyncMock(return_value=mock_sync_info)
        mock_github_service.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_instance)
        mock_github_service.return_value.__aexit__ = mocker.AsyncMock(return_value=None)

        sync_request = {"force": False}
        response = await api_client.post(f"/repositories/{repo.id}/sync", json=sync_request)

        assert response.status_code == 200
        data = response.json()
        assert data["repository_id"] == repo.id
        assert data["synced"] is True
        assert data["last_commit_sha"] == "abc123"
        assert data["changes_detected"] is True

    async def test_sync_repository_not_found(self, api_client: AsyncClient):
        """Test syncing non-existent repository"""
        sync_request = {"force": False}
        response = await api_client.post("/repositories/999/sync", json=sync_request)

        assert response.status_code == 404

    async def test_sync_repository_github_error(self, api_client: AsyncClient, db_session, mocker):
        """Test sync repository with GitHub error"""
        repo = await create_test_repository(db_session)

        # Mock GitHub async service to raise error - patch where it's used
        mock_github_service = mocker.patch("app.services.repository_service.GitHubAsyncService")
        mock_instance = mocker.AsyncMock()
        mock_instance.sync_repository = mocker.AsyncMock(side_effect=Exception("GitHub API error"))
        mock_github_service.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_instance)
        mock_github_service.return_value.__aexit__ = mocker.AsyncMock(return_value=None)

        sync_request = {"force": False}
        response = await api_client.post(f"/repositories/{repo.id}/sync", json=sync_request)

        assert response.status_code == 500
        assert "Failed to sync" in response.json()["detail"]
