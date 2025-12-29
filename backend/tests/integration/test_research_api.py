"""
Integration tests for Research Tasks API endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils.factories import ProjectFactory, TechnologyFactory

from app.models.research_task import ResearchTask


@pytest.mark.integration
class TestResearchAPI:
    """Test Research Task API endpoints"""

    async def test_create_research_task(self, api_client: AsyncClient, db_session: AsyncSession):
        """Test creating a research task"""
        project = await ProjectFactory.create(db_session)
        tech = await TechnologyFactory.create(db=db_session, project_id=project.id)

        task_data = {
            "title": "Research FastAPI best practices",
            "description": "Investigate patterns for building scalable FastAPI applications",
            "status": "pending",
            "technology_id": tech.id,
        }

        response = await api_client.post(
            f"/research-tasks/?project_id={project.id}", json=task_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Research FastAPI best practices"
        assert data["status"] == "pending"
        assert data["technology_id"] == tech.id
        assert "id" in data

    async def test_list_research_tasks(self, api_client: AsyncClient, db_session: AsyncSession):
        """Test listing research tasks"""
        project = await ProjectFactory.create(db_session)

        # Create research tasks directly in DB
        task1 = ResearchTask(
            project_id=project.id,
            title="Task 1",
            description="Description 1",
            status="pending",
        )
        task2 = ResearchTask(
            project_id=project.id,
            title="Task 2",
            description="Description 2",
            status="in_progress",
        )
        db_session.add(task1)
        db_session.add(task2)
        await db_session.commit()

        # List tasks
        response = await api_client.get(f"/research-tasks/?project_id={project.id}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_get_research_task_by_id(self, api_client: AsyncClient, db_session: AsyncSession):
        """Test getting a specific research task"""
        project = await ProjectFactory.create(db_session)

        task = ResearchTask(
            project_id=project.id,
            title="Specific Task",
            description="Task description",
            status="pending",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Get task
        response = await api_client.get(f"/research-tasks/{task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task.id
        assert data["title"] == "Specific Task"
        assert data["status"] == "pending"

    async def test_update_research_task_status(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """Test updating research task status"""
        project = await ProjectFactory.create(db_session)

        task = ResearchTask(
            project_id=project.id,
            title="Task to Update",
            description="Description",
            status="pending",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Update status
        update_data = {"status": "completed"}

        response = await api_client.patch(f"/research-tasks/{task.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["title"] == "Task to Update"  # Unchanged

    async def test_delete_research_task(self, api_client: AsyncClient, db_session: AsyncSession):
        """Test deleting a research task"""
        project = await ProjectFactory.create(db_session)

        task = ResearchTask(
            project_id=project.id,
            title="Task to Delete",
            description="Will be deleted",
            status="pending",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Delete task
        response = await api_client.delete(f"/research-tasks/{task.id}")

        assert response.status_code == 204

        # Verify deletion
        response = await api_client.get(f"/research-tasks/{task.id}")
        assert response.status_code == 404

    async def test_filter_research_tasks_by_status(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering research tasks by status"""
        project = await ProjectFactory.create(db_session)

        # Create tasks with different statuses
        task1 = ResearchTask(
            project_id=project.id,
            title="Pending Task 1",
            description="Desc",
            status="pending",
        )
        task2 = ResearchTask(
            project_id=project.id,
            title="Pending Task 2",
            description="Desc",
            status="pending",
        )
        task3 = ResearchTask(
            project_id=project.id,
            title="Completed Task",
            description="Desc",
            status="completed",
        )
        db_session.add_all([task1, task2, task3])
        await db_session.commit()

        # Filter by pending status
        response = await api_client.get(f"/research-tasks/?project_id={project.id}&status=pending")

        assert response.status_code == 200
        data = response.json()
        assert len([t for t in data if t["status"] == "pending"]) >= 2

    async def test_filter_research_tasks_by_technology(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """Test filtering research tasks by technology"""
        project = await ProjectFactory.create(db_session)
        tech = await TechnologyFactory.create(db=db_session, project_id=project.id)

        # Create tasks with and without technology
        task_with_tech = ResearchTask(
            project_id=project.id,
            title="Task with Technology",
            description="Has technology assigned",
            status="pending",
            technology_id=tech.id,
        )
        task_without_tech = ResearchTask(
            project_id=project.id,
            title="Task without Technology",
            description="No technology assigned",
            status="pending",
        )
        db_session.add_all([task_with_tech, task_without_tech])
        await db_session.commit()

        # Filter by technology
        response = await api_client.get(
            f"/research-tasks/?project_id={project.id}&technology_id={tech.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len([t for t in data if t.get("technology_id") == tech.id]) >= 1

    async def test_create_research_task_validation(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """Test research task creation validation"""
        project = await ProjectFactory.create(db_session)

        # Missing required fields
        invalid_data = {
            "description": "Missing title",
        }

        response = await api_client.post(
            f"/research-tasks/?project_id={project.id}", json=invalid_data
        )

        assert response.status_code == 422  # Validation error

    async def test_get_nonexistent_research_task(self, api_client: AsyncClient):
        """Test getting a task that doesn't exist"""
        response = await api_client.get("/research-tasks/99999")

        assert response.status_code == 404
