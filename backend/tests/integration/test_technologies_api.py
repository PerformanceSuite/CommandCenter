"""
Integration tests for Technologies API endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils.factories import ProjectFactory, TechnologyFactory

from app.models.technology import TechnologyDomain, TechnologyStatus


@pytest.mark.integration
class TestTechnologiesAPI:
    """Test Technology API CRUD operations"""

    async def test_create_technology(self, api_client: AsyncClient, db_session: AsyncSession):
        """Test creating a technology via API"""
        # Create project first
        project = await ProjectFactory.create(db_session)

        # Create technology via API
        technology_data = {
            "title": "FastAPI",
            "domain": "infrastructure",
            "status": "evaluation",
            "relevance_score": 85,
            "priority": 4,
            "description": "Modern Python web framework",
            "repository_url": "https://github.com/tiangolo/fastapi",
        }

        response = await api_client.post(
            f"/technologies/?project_id={project.id}", json=technology_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "FastAPI"
        assert data["domain"] == "infrastructure"
        assert data["status"] == "evaluation"
        assert data["relevance_score"] == 85
        assert data["priority"] == 4
        assert "id" in data
        assert "created_at" in data

    async def test_list_technologies(self, api_client: AsyncClient, db_session: AsyncSession):
        """Test listing technologies"""
        # Create project and technologies
        project = await ProjectFactory.create(db_session)

        await TechnologyFactory.create(db=db_session, project_id=project.id, title="Python")
        await TechnologyFactory.create(db=db_session, project_id=project.id, title="Django")
        await TechnologyFactory.create(db=db_session, project_id=project.id, title="PostgreSQL")

        # List technologies
        response = await api_client.get(f"/technologies/?project_id={project.id}")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 3
        assert "total" in data
        assert data["total"] == 3

    async def test_get_technology_by_id(self, api_client: AsyncClient, db_session: AsyncSession):
        """Test getting a specific technology"""
        project = await ProjectFactory.create(db_session)
        tech = await TechnologyFactory.create(
            db=db_session,
            project_id=project.id,
            title="Redis",
            domain=TechnologyDomain.INFRASTRUCTURE,
            status=TechnologyStatus.IMPLEMENTATION,
        )

        # Get technology
        response = await api_client.get(f"/technologies/{tech.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tech.id
        assert data["title"] == "Redis"
        assert data["domain"] == "infrastructure"
        assert data["status"] == "implementation"

    async def test_update_technology(self, api_client: AsyncClient, db_session: AsyncSession):
        """Test updating a technology"""
        project = await ProjectFactory.create(db_session)
        tech = await TechnologyFactory.create(
            db=db_session,
            project_id=project.id,
            title="Kubernetes",
            status=TechnologyStatus.RESEARCH,
            priority=3,
        )

        # Update technology
        update_data = {
            "status": "implementation",
            "priority": 5,
            "notes": "Started implementation in Q1",
        }

        response = await api_client.patch(f"/technologies/{tech.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tech.id
        assert data["status"] == "implementation"
        assert data["priority"] == 5
        assert data["notes"] == "Started implementation in Q1"
        assert data["title"] == "Kubernetes"  # Unchanged

    async def test_delete_technology(self, api_client: AsyncClient, db_session: AsyncSession):
        """Test deleting a technology"""
        project = await ProjectFactory.create(db_session)
        tech = await TechnologyFactory.create(db=db_session, project_id=project.id, title="OldTech")

        # Delete technology
        response = await api_client.delete(f"/technologies/{tech.id}")

        assert response.status_code == 204

        # Verify deletion
        response = await api_client.get(f"/technologies/{tech.id}")
        assert response.status_code == 404

    async def test_filter_technologies_by_domain(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering technologies by domain"""
        project = await ProjectFactory.create(db_session)

        # Create technologies with different domains
        await TechnologyFactory.create(
            db=db_session,
            project_id=project.id,
            title="TensorFlow",
            domain=TechnologyDomain.AI_ML,
        )
        await TechnologyFactory.create(
            db=db_session,
            project_id=project.id,
            title="PyTorch",
            domain=TechnologyDomain.AI_ML,
        )
        await TechnologyFactory.create(
            db=db_session,
            project_id=project.id,
            title="Docker",
            domain=TechnologyDomain.INFRASTRUCTURE,
        )

        # Filter by AI_ML domain
        response = await api_client.get(f"/technologies/?project_id={project.id}&domain=ai-ml")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all(item["domain"] == "ai-ml" for item in data["items"])

    async def test_filter_technologies_by_status(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering technologies by status"""
        project = await ProjectFactory.create(db_session)

        # Create technologies with different statuses
        await TechnologyFactory.create(
            db=db_session,
            project_id=project.id,
            title="Tech1",
            status=TechnologyStatus.DISCOVERY,
        )
        await TechnologyFactory.create(
            db=db_session,
            project_id=project.id,
            title="Tech2",
            status=TechnologyStatus.IMPLEMENTATION,
        )
        await TechnologyFactory.create(
            db=db_session,
            project_id=project.id,
            title="Tech3",
            status=TechnologyStatus.IMPLEMENTATION,
        )

        # Filter by IMPLEMENTATION status
        response = await api_client.get(
            f"/technologies/?project_id={project.id}&status=implementation"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all(item["status"] == "implementation" for item in data["items"])

    async def test_create_technology_validation_error(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """Test technology creation with invalid data"""
        project = await ProjectFactory.create(db_session)

        # Invalid data (relevance_score > 100)
        invalid_data = {
            "title": "InvalidTech",
            "relevance_score": 150,  # Invalid: must be <= 100
        }

        response = await api_client.post(
            f"/technologies/?project_id={project.id}", json=invalid_data
        )

        assert response.status_code == 422  # Validation error

    async def test_get_nonexistent_technology(self, api_client: AsyncClient):
        """Test getting a technology that doesn't exist"""
        response = await api_client.get("/technologies/99999")

        assert response.status_code == 404
