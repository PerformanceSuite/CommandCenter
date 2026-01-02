"""Comprehensive tests for CommandCenter Tool Provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp.providers.base import Tool, ToolResult
from app.mcp.providers.commandcenter_tools import CommandCenterToolProvider
from app.mcp.utils import InvalidParamsError, ToolNotFoundError
from app.models import Job, ResearchTask, Schedule


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def tool_provider(mock_db_session):
    """Create tool provider with mock session."""
    return CommandCenterToolProvider(mock_db_session)


class TestToolProviderInitialization:
    """Tests for provider initialization."""

    def test_provider_creation(self, tool_provider):
        """Test creating tool provider."""
        assert tool_provider.name == "commandcenter_tools"
        assert tool_provider.db is not None
        assert tool_provider.job_service is not None
        assert tool_provider.schedule_service is not None

    @pytest.mark.asyncio
    async def test_provider_initialize(self, tool_provider):
        """Test provider initialization."""
        await tool_provider.initialize()
        assert tool_provider.is_initialized

    @pytest.mark.asyncio
    async def test_provider_shutdown(self, tool_provider):
        """Test provider shutdown."""
        await tool_provider.initialize()
        await tool_provider.shutdown()
        assert not tool_provider.is_initialized


class TestListTools:
    """Tests for listing available tools."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_10_tools(self, tool_provider):
        """Test that list_tools returns all 10 tool types."""
        tools = await tool_provider.list_tools()

        assert len(tools) == 10
        assert all(isinstance(t, Tool) for t in tools)

    @pytest.mark.asyncio
    async def test_list_tools_research_task_tools(self, tool_provider):
        """Test research task tools."""
        tools = await tool_provider.list_tools()

        research_tools = [t for t in tools if "research" in t.name]
        assert len(research_tools) == 2

        tool_names = [t.name for t in research_tools]
        assert "create_research_task" in tool_names
        assert "update_research_task" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_technology_tools(self, tool_provider):
        """Test technology tools."""
        tools = await tool_provider.list_tools()

        tech_tools = [t for t in tools if "technology" in t.name]
        assert len(tech_tools) == 1
        assert tech_tools[0].name == "add_technology"

    @pytest.mark.asyncio
    async def test_list_tools_schedule_tools(self, tool_provider):
        """Test schedule tools."""
        tools = await tool_provider.list_tools()

        schedule_tools = [t for t in tools if "schedule" in t.name]
        assert len(schedule_tools) == 4

        tool_names = [t.name for t in schedule_tools]
        assert "create_schedule" in tool_names
        assert "execute_schedule" in tool_names
        assert "enable_schedule" in tool_names
        assert "disable_schedule" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_job_tools(self, tool_provider):
        """Test job tools."""
        tools = await tool_provider.list_tools()

        job_tools = [t for t in tools if "job" in t.name]
        assert len(job_tools) == 3

        tool_names = [t.name for t in job_tools]
        assert "create_job" in tool_names
        assert "get_job_status" in tool_names
        assert "cancel_job" in tool_names

    @pytest.mark.asyncio
    async def test_all_tools_have_required_fields(self, tool_provider):
        """Test all tools have name, description, and parameters."""
        tools = await tool_provider.list_tools()

        for tool in tools:
            assert tool.name
            assert tool.description
            assert tool.parameters is not None
            assert tool.returns


class TestResearchTaskTools:
    """Tests for research task tools."""

    @pytest.mark.asyncio
    async def test_create_research_task_success(self, tool_provider, mock_db_session):
        """Test successfully creating a research task."""
        # Mock task creation
        mock_task = MagicMock(spec=ResearchTask)
        mock_task.id = 1
        mock_task.title = "Test Task"
        mock_task.status = "todo"
        mock_task.priority = "high"

        mock_db_session.add = AsyncMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Execute tool
        arguments = {
            "project_id": 1,
            "title": "Test Task",
            "description": "Test Description",
            "priority": "high",
            "status": "todo",
        }

        # Create a mock task that will be returned when ResearchTask is instantiated
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.title = "Test Task"
        mock_task.status = "todo"
        mock_task.priority = "high"

        with patch("app.mcp.providers.commandcenter_tools.ResearchTask", return_value=mock_task):
            tool_provider.db.add = MagicMock()  # add is sync in SQLAlchemy
            tool_provider.db.commit = AsyncMock()
            tool_provider.db.refresh = AsyncMock()

            result = await tool_provider.call_tool("create_research_task", arguments)

        assert result.success is True
        assert "task_id" in result.result
        assert result.result["title"] == "Test Task"

    @pytest.mark.asyncio
    async def test_create_research_task_missing_project_id(self, tool_provider):
        """Test creating task without project_id fails."""
        arguments = {
            "title": "Test Task",
        }

        with pytest.raises(InvalidParamsError):
            await tool_provider.call_tool("create_research_task", arguments)

    @pytest.mark.asyncio
    async def test_create_research_task_missing_title(self, tool_provider):
        """Test creating task without title fails."""
        arguments = {
            "project_id": 1,
        }

        with pytest.raises(InvalidParamsError):
            await tool_provider.call_tool("create_research_task", arguments)

    @pytest.mark.asyncio
    async def test_create_research_task_with_defaults(self, tool_provider):
        """Test creating task with default values."""
        arguments = {
            "project_id": 1,
            "title": "Minimal Task",
        }

        # Create a mock task with default values
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.title = "Minimal Task"
        mock_task.status = "todo"
        mock_task.priority = "medium"

        with patch("app.mcp.providers.commandcenter_tools.ResearchTask", return_value=mock_task):
            tool_provider.db.add = MagicMock()
            tool_provider.db.commit = AsyncMock()
            tool_provider.db.refresh = AsyncMock()

            result = await tool_provider.call_tool("create_research_task", arguments)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_update_research_task_success(self, tool_provider, mock_db_session):
        """Test successfully updating a research task."""
        # Mock existing task
        mock_task = MagicMock(spec=ResearchTask)
        mock_task.id = 1
        mock_task.title = "Updated Task"
        mock_task.status = "in_progress"
        mock_task.priority = "high"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Execute tool
        arguments = {
            "task_id": 1,
            "title": "Updated Task",
            "status": "in_progress",
        }

        result = await tool_provider.call_tool("update_research_task", arguments)

        assert result.success is True
        assert result.result["task_id"] == 1
        assert "updated successfully" in result.result["message"].lower()

    @pytest.mark.asyncio
    async def test_update_research_task_not_found(self, tool_provider, mock_db_session):
        """Test updating non-existent task."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        arguments = {
            "task_id": 999,
            "title": "Updated Task",
        }

        result = await tool_provider.call_tool("update_research_task", arguments)

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_update_research_task_missing_task_id(self, tool_provider):
        """Test updating task without task_id fails."""
        arguments = {
            "title": "Updated Task",
        }

        with pytest.raises(InvalidParamsError):
            await tool_provider.call_tool("update_research_task", arguments)


class TestTechnologyTools:
    """Tests for technology tools."""

    @pytest.mark.asyncio
    async def test_add_technology_success(self, tool_provider):
        """Test successfully adding a technology."""
        arguments = {
            "project_id": 1,
            "title": "Docker",
            "domain": "Infrastructure",
            "vendor": "Docker Inc",
            "description": "Container platform",
            "status": "adopt",
        }

        # Create a mock technology
        mock_tech = MagicMock()
        mock_tech.id = 1
        mock_tech.title = "Docker"
        mock_tech.domain = "Infrastructure"
        mock_tech.status = "adopt"

        with patch("app.mcp.providers.commandcenter_tools.Technology", return_value=mock_tech):
            tool_provider.db.add = MagicMock()
            tool_provider.db.commit = AsyncMock()
            tool_provider.db.refresh = AsyncMock()

            result = await tool_provider.call_tool("add_technology", arguments)

        assert result.success is True
        assert "technology_id" in result.result

    @pytest.mark.asyncio
    async def test_add_technology_missing_required_fields(self, tool_provider):
        """Test adding technology without required fields."""
        # Missing domain
        arguments = {
            "project_id": 1,
            "title": "Docker",
        }

        with pytest.raises(InvalidParamsError):
            await tool_provider.call_tool("add_technology", arguments)

    @pytest.mark.asyncio
    async def test_add_technology_with_defaults(self, tool_provider):
        """Test adding technology with default status."""
        arguments = {
            "project_id": 1,
            "title": "New Tech",
            "domain": "Backend",
        }

        # Create a mock technology with default status
        mock_tech = MagicMock()
        mock_tech.id = 1
        mock_tech.title = "New Tech"
        mock_tech.domain = "Backend"
        mock_tech.status = "assess"  # default status

        with patch("app.mcp.providers.commandcenter_tools.Technology", return_value=mock_tech):
            tool_provider.db.add = MagicMock()
            tool_provider.db.commit = AsyncMock()
            tool_provider.db.refresh = AsyncMock()

            result = await tool_provider.call_tool("add_technology", arguments)

        assert result.success is True


class TestScheduleTools:
    """Tests for schedule tools."""

    @pytest.mark.asyncio
    async def test_create_schedule_success(self, tool_provider):
        """Test successfully creating a schedule."""
        mock_schedule = MagicMock(spec=Schedule)
        mock_schedule.id = 1
        mock_schedule.name = "Weekly Analysis"
        mock_schedule.frequency = "weekly"
        mock_schedule.enabled = True
        mock_schedule.next_run_at = None

        tool_provider.schedule_service.create_schedule = AsyncMock(return_value=mock_schedule)

        arguments = {
            "project_id": 1,
            "name": "Weekly Analysis",
            "task_type": "repository_analysis",
            "frequency": "weekly",
        }

        result = await tool_provider.call_tool("create_schedule", arguments)

        assert result.success is True
        assert result.result["schedule_id"] == 1
        assert result.result["name"] == "Weekly Analysis"

    @pytest.mark.asyncio
    async def test_create_schedule_with_cron(self, tool_provider):
        """Test creating schedule with cron expression."""
        mock_schedule = MagicMock(spec=Schedule)
        mock_schedule.id = 1
        mock_schedule.name = "Custom Schedule"
        mock_schedule.frequency = "cron"
        mock_schedule.enabled = True
        mock_schedule.next_run_at = None

        tool_provider.schedule_service.create_schedule = AsyncMock(return_value=mock_schedule)

        arguments = {
            "project_id": 1,
            "name": "Custom Schedule",
            "task_type": "analysis",
            "frequency": "cron",
            "cron_expression": "0 */2 * * *",
        }

        result = await tool_provider.call_tool("create_schedule", arguments)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_create_schedule_missing_required_fields(self, tool_provider):
        """Test creating schedule without required fields."""
        arguments = {
            "project_id": 1,
            "name": "Test Schedule",
        }

        with pytest.raises(InvalidParamsError):
            await tool_provider.call_tool("create_schedule", arguments)

    @pytest.mark.asyncio
    async def test_execute_schedule_success(self, tool_provider):
        """Test successfully executing a schedule."""
        mock_job = MagicMock(spec=Job)
        mock_job.id = 5

        tool_provider.schedule_service.execute_schedule = AsyncMock(return_value=mock_job)

        arguments = {
            "schedule_id": 1,
        }

        result = await tool_provider.call_tool("execute_schedule", arguments)

        assert result.success is True
        assert result.result["job_id"] == 5
        assert result.result["schedule_id"] == 1

    @pytest.mark.asyncio
    async def test_execute_schedule_with_force(self, tool_provider):
        """Test executing schedule with force flag."""
        mock_job = MagicMock(spec=Job)
        mock_job.id = 5

        tool_provider.schedule_service.execute_schedule = AsyncMock(return_value=mock_job)

        arguments = {
            "schedule_id": 1,
            "force": True,
        }

        result = await tool_provider.call_tool("execute_schedule", arguments)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_schedule_missing_id(self, tool_provider):
        """Test executing schedule without schedule_id."""
        arguments = {}

        with pytest.raises(InvalidParamsError):
            await tool_provider.call_tool("execute_schedule", arguments)

    @pytest.mark.asyncio
    async def test_enable_schedule_success(self, tool_provider):
        """Test successfully enabling a schedule."""
        mock_schedule = MagicMock(spec=Schedule)
        mock_schedule.id = 1
        mock_schedule.name = "Test Schedule"
        mock_schedule.enabled = True

        tool_provider.schedule_service.update_schedule = AsyncMock(return_value=mock_schedule)

        arguments = {
            "schedule_id": 1,
        }

        result = await tool_provider.call_tool("enable_schedule", arguments)

        assert result.success is True
        assert result.result["enabled"] is True

    @pytest.mark.asyncio
    async def test_disable_schedule_success(self, tool_provider):
        """Test successfully disabling a schedule."""
        mock_schedule = MagicMock(spec=Schedule)
        mock_schedule.id = 1
        mock_schedule.name = "Test Schedule"
        mock_schedule.enabled = False

        tool_provider.schedule_service.update_schedule = AsyncMock(return_value=mock_schedule)

        arguments = {
            "schedule_id": 1,
        }

        result = await tool_provider.call_tool("disable_schedule", arguments)

        assert result.success is True
        assert result.result["enabled"] is False


class TestJobTools:
    """Tests for job tools."""

    @pytest.mark.asyncio
    async def test_create_job_success(self, tool_provider):
        """Test successfully creating a job."""
        mock_job = MagicMock(spec=Job)
        mock_job.id = 1
        mock_job.job_type = "analysis"
        mock_job.status = "pending"

        tool_provider.job_service.create_job = AsyncMock(return_value=mock_job)

        arguments = {
            "project_id": 1,
            "job_type": "analysis",
            "parameters": {"depth": "full"},
        }

        result = await tool_provider.call_tool("create_job", arguments)

        assert result.success is True
        assert result.result["job_id"] == 1
        assert result.result["job_type"] == "analysis"

    @pytest.mark.asyncio
    async def test_create_job_with_dispatch(self, tool_provider):
        """Test creating job with automatic dispatch."""
        mock_job = MagicMock(spec=Job)
        mock_job.id = 1
        mock_job.job_type = "analysis"
        mock_job.status = "running"

        tool_provider.job_service.create_job = AsyncMock(return_value=mock_job)
        tool_provider.job_service.dispatch_job = AsyncMock()

        arguments = {
            "project_id": 1,
            "job_type": "analysis",
            "dispatch": True,
        }

        result = await tool_provider.call_tool("create_job", arguments)

        assert result.success is True
        assert "dispatched" in result.result["message"].lower()
        tool_provider.job_service.dispatch_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_job_missing_required_fields(self, tool_provider):
        """Test creating job without required fields."""
        arguments = {
            "project_id": 1,
        }

        with pytest.raises(InvalidParamsError):
            await tool_provider.call_tool("create_job", arguments)

    @pytest.mark.asyncio
    async def test_get_job_status_success(self, tool_provider):
        """Test successfully getting job status."""
        mock_job = MagicMock(spec=Job)
        mock_job.id = 1
        mock_job.job_type = "analysis"
        mock_job.status = "running"
        mock_job.progress = 50
        mock_job.current_step = "processing"
        mock_job.result = None
        mock_job.error = None

        tool_provider.job_service.get_job = AsyncMock(return_value=mock_job)

        arguments = {
            "job_id": 1,
        }

        result = await tool_provider.call_tool("get_job_status", arguments)

        assert result.success is True
        assert result.result["job_id"] == 1
        assert result.result["status"] == "running"
        assert result.result["progress"] == 50

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, tool_provider):
        """Test getting status of non-existent job."""
        tool_provider.job_service.get_job = AsyncMock(return_value=None)

        arguments = {
            "job_id": 999,
        }

        result = await tool_provider.call_tool("get_job_status", arguments)

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_get_job_status_missing_id(self, tool_provider):
        """Test getting job status without job_id."""
        arguments = {}

        with pytest.raises(InvalidParamsError):
            await tool_provider.call_tool("get_job_status", arguments)

    @pytest.mark.asyncio
    async def test_cancel_job_success(self, tool_provider):
        """Test successfully cancelling a job."""
        mock_job = MagicMock(spec=Job)
        mock_job.id = 1
        mock_job.status = "cancelled"

        tool_provider.job_service.cancel_job = AsyncMock(return_value=mock_job)

        arguments = {
            "job_id": 1,
        }

        result = await tool_provider.call_tool("cancel_job", arguments)

        assert result.success is True
        assert result.result["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_job_missing_id(self, tool_provider):
        """Test cancelling job without job_id."""
        arguments = {}

        with pytest.raises(InvalidParamsError):
            await tool_provider.call_tool("cancel_job", arguments)


class TestInvalidTools:
    """Tests for invalid tool calls."""

    @pytest.mark.asyncio
    async def test_call_nonexistent_tool(self, tool_provider):
        """Test calling non-existent tool."""
        with pytest.raises(ToolNotFoundError):
            await tool_provider.call_tool("nonexistent_tool", {})

    @pytest.mark.asyncio
    async def test_call_tool_with_exception(self, tool_provider):
        """Test tool execution with unexpected exception."""
        arguments = {
            "project_id": 1,
            "title": "Test Task",
        }

        # Mock database to raise exception
        tool_provider.db.add = AsyncMock(side_effect=Exception("Database error"))

        result = await tool_provider.call_tool("create_research_task", arguments)

        assert result.success is False
        assert "Tool execution failed" in result.error


class TestToolParameterValidation:
    """Tests for tool parameter validation."""

    @pytest.mark.asyncio
    async def test_tool_parameters_types(self, tool_provider):
        """Test that all tool parameters have proper types."""
        tools = await tool_provider.list_tools()

        for tool in tools:
            for param in tool.parameters:
                assert param.name
                assert param.type in ["string", "integer", "boolean", "object"]
                assert isinstance(param.required, bool)

    @pytest.mark.asyncio
    async def test_tool_parameters_defaults(self, tool_provider):
        """Test tools have appropriate default values."""
        tools = await tool_provider.list_tools()

        # Check specific tools with known defaults
        create_task_tool = next(t for t in tools if t.name == "create_research_task")
        priority_param = next(p for p in create_task_tool.parameters if p.name == "priority")
        assert priority_param.default == "medium"

        status_param = next(p for p in create_task_tool.parameters if p.name == "status")
        assert status_param.default == "todo"


class TestToolResultFormat:
    """Tests for tool result formatting."""

    @pytest.mark.asyncio
    async def test_success_result_format(self, tool_provider):
        """Test successful tool result has correct format."""
        mock_schedule = MagicMock(spec=Schedule)
        mock_schedule.id = 1
        mock_schedule.name = "Test"
        mock_schedule.frequency = "daily"
        mock_schedule.enabled = True
        mock_schedule.next_run_at = None

        tool_provider.schedule_service.create_schedule = AsyncMock(return_value=mock_schedule)

        result = await tool_provider.call_tool(
            "create_schedule",
            {
                "project_id": 1,
                "name": "Test",
                "task_type": "analysis",
                "frequency": "daily",
            },
        )

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.result is not None
        assert result.error is None
        assert "message" in result.result

    @pytest.mark.asyncio
    async def test_error_result_format(self, tool_provider):
        """Test error tool result has correct format."""
        tool_provider.job_service.get_job = AsyncMock(return_value=None)

        result = await tool_provider.call_tool("get_job_status", {"job_id": 999})

        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None
        assert result.result is None
