"""Comprehensive tests for CommandCenter Resource Provider."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp.providers.base import Resource
from app.mcp.providers.commandcenter_resources import CommandCenterResourceProvider
from app.mcp.utils import ResourceNotFoundError
from app.models import Job, Schedule


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def resource_provider(mock_db_session):
    """Create resource provider with mock session."""
    return CommandCenterResourceProvider(mock_db_session)


class TestResourceProviderInitialization:
    """Tests for provider initialization."""

    def test_provider_creation(self, resource_provider):
        """Test creating resource provider."""
        assert resource_provider.name == "commandcenter"
        assert resource_provider.db is not None

    @pytest.mark.asyncio
    async def test_provider_initialize(self, resource_provider):
        """Test provider initialization."""
        await resource_provider.initialize()
        assert resource_provider.is_initialized

    @pytest.mark.asyncio
    async def test_provider_shutdown(self, resource_provider):
        """Test provider shutdown."""
        await resource_provider.initialize()
        await resource_provider.shutdown()
        assert not resource_provider.is_initialized


class TestListResources:
    """Tests for listing available resources."""

    @pytest.mark.asyncio
    async def test_list_resources_returns_all_14_types(self, resource_provider):
        """Test that list_resources returns all 14 resource types."""
        resources = await resource_provider.list_resources()

        assert len(resources) == 14
        assert all(isinstance(r, Resource) for r in resources)

    @pytest.mark.asyncio
    async def test_list_resources_project_types(self, resource_provider):
        """Test project resource types."""
        resources = await resource_provider.list_resources()

        project_resources = [r for r in resources if "projects" in r.uri]
        assert len(project_resources) == 2

        uris = [r.uri for r in project_resources]
        assert "commandcenter://projects" in uris
        assert "commandcenter://projects/{id}" in uris

    @pytest.mark.asyncio
    async def test_list_resources_technology_types(self, resource_provider):
        """Test technology resource types."""
        resources = await resource_provider.list_resources()

        tech_resources = [r for r in resources if "technologies" in r.uri]
        assert len(tech_resources) == 2

        uris = [r.uri for r in tech_resources]
        assert "commandcenter://technologies" in uris
        assert "commandcenter://technologies/{id}" in uris

    @pytest.mark.asyncio
    async def test_list_resources_research_task_types(self, resource_provider):
        """Test research task resource types."""
        resources = await resource_provider.list_resources()

        research_resources = [r for r in resources if "research" in r.uri]
        assert len(research_resources) == 2

        uris = [r.uri for r in research_resources]
        assert "commandcenter://research/tasks" in uris
        assert "commandcenter://research/tasks/{id}" in uris

    @pytest.mark.asyncio
    async def test_list_resources_repository_types(self, resource_provider):
        """Test repository resource types."""
        resources = await resource_provider.list_resources()

        repo_resources = [r for r in resources if "repositories" in r.uri]
        assert len(repo_resources) == 2

        uris = [r.uri for r in repo_resources]
        assert "commandcenter://repositories" in uris
        assert "commandcenter://repositories/{id}" in uris

    @pytest.mark.asyncio
    async def test_list_resources_schedule_types(self, resource_provider):
        """Test schedule resource types."""
        resources = await resource_provider.list_resources()

        schedule_resources = [r for r in resources if "schedules" in r.uri]
        assert len(schedule_resources) == 2

        uris = [r.uri for r in schedule_resources]
        assert "commandcenter://schedules" in uris
        assert "commandcenter://schedules/active" in uris

    @pytest.mark.asyncio
    async def test_list_resources_job_types(self, resource_provider):
        """Test job resource types."""
        resources = await resource_provider.list_resources()

        job_resources = [r for r in resources if "jobs" in r.uri]
        assert len(job_resources) == 3

        uris = [r.uri for r in job_resources]
        assert "commandcenter://jobs" in uris
        assert "commandcenter://jobs/active" in uris
        assert "commandcenter://jobs/{id}" in uris

    @pytest.mark.asyncio
    async def test_list_resources_overview(self, resource_provider):
        """Test overview resource."""
        resources = await resource_provider.list_resources()

        overview_resources = [r for r in resources if "overview" in r.uri]
        assert len(overview_resources) == 1
        assert overview_resources[0].uri == "commandcenter://overview"

    @pytest.mark.asyncio
    async def test_list_resources_mime_types(self, resource_provider):
        """Test all resources have correct MIME type."""
        resources = await resource_provider.list_resources()

        for resource in resources:
            assert resource.mime_type == "application/json"


class TestReadProjectResources:
    """Tests for reading project resources."""

    @pytest.mark.asyncio
    async def test_read_all_projects(self, resource_provider, mock_db_session):
        """Test reading all projects."""
        # Mock projects (no spec= so to_dict can be mocked)
        project1 = MagicMock()
        project1.id = 1
        project1.name = "Project 1"
        project1.description = "Description 1"
        project1.created_at = None
        project1.to_dict.return_value = {
            "id": 1,
            "name": "Project 1",
            "description": "Description 1",
        }

        project2 = MagicMock()
        project2.id = 2
        project2.name = "Project 2"
        project2.description = "Description 2"
        project2.created_at = None
        project2.to_dict.return_value = {
            "id": 2,
            "name": "Project 2",
            "description": "Description 2",
        }

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [project1, project2]
        mock_db_session.execute.return_value = mock_result

        # Test
        content = await resource_provider.read_resource("commandcenter://projects")

        assert content.uri == "commandcenter://projects"
        assert content.mime_type == "application/json"

        data = json.loads(content.text)
        assert len(data) == 2
        assert data[0]["name"] == "Project 1"
        assert data[1]["name"] == "Project 2"

    @pytest.mark.asyncio
    async def test_read_single_project(self, resource_provider, mock_db_session):
        """Test reading single project by ID."""
        # Mock project (no spec= so to_dict can be mocked)
        project = MagicMock()
        project.id = 1
        project.name = "Test Project"
        project.description = "Test Description"
        project.created_at = None
        project.to_dict.return_value = {
            "id": 1,
            "name": "Test Project",
            "description": "Test Description",
        }

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = project
        mock_db_session.execute.return_value = mock_result

        # Test
        content = await resource_provider.read_resource("commandcenter://projects/1")

        assert content.uri == "commandcenter://projects/1"
        data = json.loads(content.text)
        assert data["id"] == 1
        assert data["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_read_nonexistent_project(self, resource_provider, mock_db_session):
        """Test reading non-existent project raises error."""
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Test
        with pytest.raises(ResourceNotFoundError):
            await resource_provider.read_resource("commandcenter://projects/999")


class TestReadTechnologyResources:
    """Tests for reading technology resources."""

    @pytest.mark.asyncio
    async def test_read_all_technologies(self, resource_provider, mock_db_session):
        """Test reading all technologies."""
        # Mock technologies (no spec= so to_dict can be mocked)
        tech1 = MagicMock()
        tech1.to_dict.return_value = {
            "id": 1,
            "title": "Docker",
            "domain": "Infrastructure",
            "status": "adopt",
        }

        tech2 = MagicMock()
        tech2.to_dict.return_value = {
            "id": 2,
            "title": "Kubernetes",
            "domain": "Infrastructure",
            "status": "trial",
        }

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [tech1, tech2]
        mock_db_session.execute.return_value = mock_result

        # Test
        content = await resource_provider.read_resource("commandcenter://technologies")

        data = json.loads(content.text)
        assert len(data) == 2
        assert data[0]["title"] == "Docker"
        assert data[1]["title"] == "Kubernetes"

    @pytest.mark.asyncio
    async def test_read_single_technology(self, resource_provider, mock_db_session):
        """Test reading single technology by ID."""
        tech = MagicMock()
        tech.to_dict.return_value = {
            "id": 1,
            "title": "FastAPI",
            "domain": "Backend",
            "status": "adopt",
            "relevance": "high",
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = tech
        mock_db_session.execute.return_value = mock_result

        # Test
        content = await resource_provider.read_resource("commandcenter://technologies/1")

        data = json.loads(content.text)
        assert data["title"] == "FastAPI"
        assert data["domain"] == "Backend"


class TestReadResearchTaskResources:
    """Tests for reading research task resources."""

    @pytest.mark.asyncio
    async def test_read_all_research_tasks(self, resource_provider, mock_db_session):
        """Test reading all research tasks."""
        task1 = MagicMock()
        task1.to_dict.return_value = {
            "id": 1,
            "title": "Evaluate Kubernetes",
            "status": "in_progress",
            "priority": "high",
        }

        task2 = MagicMock()
        task2.to_dict.return_value = {
            "id": 2,
            "title": "Test Docker Compose",
            "status": "done",
            "priority": "medium",
        }

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [task1, task2]
        mock_db_session.execute.return_value = mock_result

        # Test
        content = await resource_provider.read_resource("commandcenter://research/tasks")

        data = json.loads(content.text)
        assert len(data) == 2
        assert data[0]["title"] == "Evaluate Kubernetes"
        assert data[1]["status"] == "done"


class TestReadScheduleResources:
    """Tests for reading schedule resources."""

    @pytest.mark.asyncio
    async def test_read_all_schedules(self, resource_provider, mock_db_session):
        """Test reading all schedules."""
        schedule1 = MagicMock(spec=Schedule)
        schedule1.to_dict.return_value = {"id": 1, "name": "Weekly Analysis", "enabled": True}

        schedule2 = MagicMock(spec=Schedule)
        schedule2.to_dict.return_value = {"id": 2, "name": "Daily Sync", "enabled": False}

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [schedule1, schedule2]
        mock_db_session.execute.return_value = mock_result

        # Test
        content = await resource_provider.read_resource("commandcenter://schedules")

        data = json.loads(content.text)
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_read_active_schedules_only(self, resource_provider, mock_db_session):
        """Test reading only active (enabled) schedules."""
        schedule1 = MagicMock(spec=Schedule)
        schedule1.to_dict.return_value = {"id": 1, "name": "Active Schedule", "enabled": True}

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [schedule1]
        mock_db_session.execute.return_value = mock_result

        # Test
        content = await resource_provider.read_resource("commandcenter://schedules/active")

        data = json.loads(content.text)
        assert len(data) == 1
        assert data[0]["enabled"] is True


class TestReadJobResources:
    """Tests for reading job resources."""

    @pytest.mark.asyncio
    async def test_read_all_jobs(self, resource_provider, mock_db_session):
        """Test reading all jobs."""
        job1 = MagicMock(spec=Job)
        job1.to_dict.return_value = {"id": 1, "job_type": "analysis", "status": "completed"}

        job2 = MagicMock(spec=Job)
        job2.to_dict.return_value = {"id": 2, "job_type": "export", "status": "running"}

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [job1, job2]
        mock_db_session.execute.return_value = mock_result

        # Test
        content = await resource_provider.read_resource("commandcenter://jobs")

        data = json.loads(content.text)
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_read_active_jobs_only(self, resource_provider, mock_db_session):
        """Test reading only active (running/pending) jobs."""
        job = MagicMock(spec=Job)
        job.to_dict.return_value = {
            "id": 1,
            "job_type": "analysis",
            "status": "running",
            "progress": 50,
        }

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [job]
        mock_db_session.execute.return_value = mock_result

        # Test
        content = await resource_provider.read_resource("commandcenter://jobs/active")

        data = json.loads(content.text)
        assert len(data) == 1
        assert data[0]["status"] == "running"

    @pytest.mark.asyncio
    async def test_read_single_job(self, resource_provider, mock_db_session):
        """Test reading single job by ID."""
        job = MagicMock(spec=Job)
        job.to_dict.return_value = {
            "id": 5,
            "job_type": "batch_analysis",
            "status": "completed",
            "progress": 100,
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = job
        mock_db_session.execute.return_value = mock_result

        # Test
        content = await resource_provider.read_resource("commandcenter://jobs/5")

        data = json.loads(content.text)
        assert data["id"] == 5
        assert data["progress"] == 100


class TestReadOverview:
    """Tests for reading system overview."""

    @pytest.mark.asyncio
    async def test_read_overview(self, resource_provider, mock_db_session):
        """Test reading system overview with counts."""

        # Mock count queries
        def mock_execute(query):
            mock_result = MagicMock()
            mock_result.scalar.return_value = 5  # Mock count
            return mock_result

        mock_db_session.execute.side_effect = mock_execute

        # Test
        content = await resource_provider.read_resource("commandcenter://overview")

        data = json.loads(content.text)
        assert data["system"] == "CommandCenter"
        assert data["version"] == "1.0.0"
        assert "counts" in data
        assert data["counts"]["projects"] == 5
        assert data["counts"]["technologies"] == 5
        assert "schedules" in data["counts"]
        assert "jobs" in data["counts"]


class TestInvalidResources:
    """Tests for invalid resource URIs."""

    @pytest.mark.asyncio
    async def test_invalid_uri_scheme(self, resource_provider):
        """Test reading resource with invalid URI scheme."""
        with pytest.raises(ResourceNotFoundError):
            await resource_provider.read_resource("invalid://projects")

    @pytest.mark.asyncio
    async def test_nonexistent_resource_type(self, resource_provider):
        """Test reading non-existent resource type."""
        with pytest.raises(ResourceNotFoundError):
            await resource_provider.read_resource("commandcenter://nonexistent")

    @pytest.mark.asyncio
    async def test_invalid_id_format(self, resource_provider, mock_db_session):
        """Test reading resource with invalid ID format."""
        with pytest.raises(ValueError):
            await resource_provider.read_resource("commandcenter://projects/invalid_id")


class TestResourceContentFormat:
    """Tests for resource content formatting."""

    @pytest.mark.asyncio
    async def test_content_is_valid_json(self, resource_provider, mock_db_session):
        """Test that all resource content is valid JSON."""
        project = MagicMock()
        project.to_dict.return_value = {"id": 1, "name": "Test"}

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [project]
        mock_db_session.execute.return_value = mock_result

        content = await resource_provider.read_resource("commandcenter://projects")

        # Should not raise exception
        data = json.loads(content.text)
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_content_is_formatted_with_indentation(self, resource_provider, mock_db_session):
        """Test that JSON content is formatted with proper indentation."""
        project = MagicMock()
        project.to_dict.return_value = {"id": 1, "name": "Test"}

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [project]
        mock_db_session.execute.return_value = mock_result

        content = await resource_provider.read_resource("commandcenter://projects")

        # Check for indentation (2 spaces)
        assert "  " in content.text
