"""
CommandCenter Tool Provider for MCP.

Exposes CommandCenter actions (create tasks, analyze repos, manage schedules, execute jobs)
as MCP tools that AI assistants can call to perform operations.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp.providers.base import Tool, ToolParameter, ToolProvider, ToolResult
from app.mcp.utils import ToolNotFoundError, InvalidParamsError
from app.services.job_service import JobService
from app.services.schedule_service import ScheduleService
from app.models import ResearchTask, Technology, Repository, Project, Schedule


logger = logging.getLogger(__name__)


class CommandCenterToolProvider(ToolProvider):
    """
    Tool provider for CommandCenter operations.

    Exposes tools for:
    - Research task management (create, update, list)
    - Technology tracking (add, update)
    - Repository management (add, sync)
    - Schedule management (create, execute, enable/disable)
    - Job management (create, dispatch, get status)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize CommandCenter tool provider.

        Args:
            db: Database session for operations
        """
        super().__init__("commandcenter_tools")
        self.db = db
        self.job_service = JobService(db)
        self.schedule_service = ScheduleService(db)

    async def list_tools(self) -> List[Tool]:
        """
        List all available CommandCenter tools.

        Returns:
            List of Tool objects
        """
        tools = [
            # Research task tools
            Tool(
                name="create_research_task",
                description="Create a new research task",
                parameters=[
                    ToolParameter(
                        name="project_id",
                        type="integer",
                        description="Project ID",
                        required=True,
                    ),
                    ToolParameter(
                        name="title",
                        type="string",
                        description="Task title",
                        required=True,
                    ),
                    ToolParameter(
                        name="description",
                        type="string",
                        description="Task description",
                        required=False,
                    ),
                    ToolParameter(
                        name="priority",
                        type="string",
                        description="Priority (low, medium, high)",
                        required=False,
                        default="medium",
                    ),
                    ToolParameter(
                        name="status",
                        type="string",
                        description="Status (todo, in_progress, done)",
                        required=False,
                        default="todo",
                    ),
                ],
                returns="Created research task with ID",
            ),
            Tool(
                name="update_research_task",
                description="Update an existing research task",
                parameters=[
                    ToolParameter(
                        name="task_id",
                        type="integer",
                        description="Task ID to update",
                        required=True,
                    ),
                    ToolParameter(
                        name="title",
                        type="string",
                        description="New title",
                        required=False,
                    ),
                    ToolParameter(
                        name="description",
                        type="string",
                        description="New description",
                        required=False,
                    ),
                    ToolParameter(
                        name="status",
                        type="string",
                        description="New status",
                        required=False,
                    ),
                    ToolParameter(
                        name="priority",
                        type="string",
                        description="New priority",
                        required=False,
                    ),
                ],
                returns="Updated task details",
            ),

            # Technology tools
            Tool(
                name="add_technology",
                description="Add a new technology to the radar",
                parameters=[
                    ToolParameter(
                        name="project_id",
                        type="integer",
                        description="Project ID",
                        required=True,
                    ),
                    ToolParameter(
                        name="title",
                        type="string",
                        description="Technology title",
                        required=True,
                    ),
                    ToolParameter(
                        name="domain",
                        type="string",
                        description="Technology domain",
                        required=True,
                    ),
                    ToolParameter(
                        name="vendor",
                        type="string",
                        description="Vendor/provider",
                        required=False,
                    ),
                    ToolParameter(
                        name="description",
                        type="string",
                        description="Technology description",
                        required=False,
                    ),
                    ToolParameter(
                        name="status",
                        type="string",
                        description="Status (adopt, trial, assess, hold)",
                        required=False,
                        default="assess",
                    ),
                ],
                returns="Created technology with ID",
            ),

            # Schedule tools
            Tool(
                name="create_schedule",
                description="Create a new automated schedule",
                parameters=[
                    ToolParameter(
                        name="project_id",
                        type="integer",
                        description="Project ID",
                        required=True,
                    ),
                    ToolParameter(
                        name="name",
                        type="string",
                        description="Schedule name",
                        required=True,
                    ),
                    ToolParameter(
                        name="task_type",
                        type="string",
                        description="Task type to execute",
                        required=True,
                    ),
                    ToolParameter(
                        name="frequency",
                        type="string",
                        description="Frequency (once, hourly, daily, weekly, monthly, cron)",
                        required=True,
                    ),
                    ToolParameter(
                        name="cron_expression",
                        type="string",
                        description="Cron expression (required if frequency=cron)",
                        required=False,
                    ),
                    ToolParameter(
                        name="description",
                        type="string",
                        description="Schedule description",
                        required=False,
                    ),
                    ToolParameter(
                        name="enabled",
                        type="boolean",
                        description="Whether schedule is enabled",
                        required=False,
                        default=True,
                    ),
                ],
                returns="Created schedule with ID and next run time",
            ),
            Tool(
                name="execute_schedule",
                description="Execute a schedule immediately",
                parameters=[
                    ToolParameter(
                        name="schedule_id",
                        type="integer",
                        description="Schedule ID to execute",
                        required=True,
                    ),
                    ToolParameter(
                        name="force",
                        type="boolean",
                        description="Force execution even if disabled",
                        required=False,
                        default=False,
                    ),
                ],
                returns="Created job ID and execution status",
            ),
            Tool(
                name="enable_schedule",
                description="Enable a disabled schedule",
                parameters=[
                    ToolParameter(
                        name="schedule_id",
                        type="integer",
                        description="Schedule ID to enable",
                        required=True,
                    ),
                ],
                returns="Updated schedule status",
            ),
            Tool(
                name="disable_schedule",
                description="Disable an active schedule",
                parameters=[
                    ToolParameter(
                        name="schedule_id",
                        type="integer",
                        description="Schedule ID to disable",
                        required=True,
                    ),
                ],
                returns="Updated schedule status",
            ),

            # Job tools
            Tool(
                name="create_job",
                description="Create a new async job",
                parameters=[
                    ToolParameter(
                        name="project_id",
                        type="integer",
                        description="Project ID",
                        required=True,
                    ),
                    ToolParameter(
                        name="job_type",
                        type="string",
                        description="Job type (analysis, export, batch_analysis, etc.)",
                        required=True,
                    ),
                    ToolParameter(
                        name="parameters",
                        type="object",
                        description="Job-specific parameters",
                        required=False,
                    ),
                    ToolParameter(
                        name="dispatch",
                        type="boolean",
                        description="Automatically dispatch job after creation",
                        required=False,
                        default=False,
                    ),
                ],
                returns="Created job ID and status",
            ),
            Tool(
                name="get_job_status",
                description="Get status of a running or completed job",
                parameters=[
                    ToolParameter(
                        name="job_id",
                        type="integer",
                        description="Job ID",
                        required=True,
                    ),
                ],
                returns="Job status, progress, and results",
            ),
            Tool(
                name="cancel_job",
                description="Cancel a running or pending job",
                parameters=[
                    ToolParameter(
                        name="job_id",
                        type="integer",
                        description="Job ID to cancel",
                        required=True,
                    ),
                ],
                returns="Cancellation status",
            ),
        ]

        return tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute tool with given arguments.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            ToolResult with execution result

        Raises:
            ToolNotFoundError: If tool doesn't exist
            InvalidParamsError: If arguments are invalid
        """
        try:
            # Route to appropriate handler
            if name == "create_research_task":
                return await self._create_research_task(arguments)
            elif name == "update_research_task":
                return await self._update_research_task(arguments)
            elif name == "add_technology":
                return await self._add_technology(arguments)
            elif name == "create_schedule":
                return await self._create_schedule(arguments)
            elif name == "execute_schedule":
                return await self._execute_schedule(arguments)
            elif name == "enable_schedule":
                return await self._enable_schedule(arguments)
            elif name == "disable_schedule":
                return await self._disable_schedule(arguments)
            elif name == "create_job":
                return await self._create_job(arguments)
            elif name == "get_job_status":
                return await self._get_job_status(arguments)
            elif name == "cancel_job":
                return await self._cancel_job(arguments)
            else:
                raise ToolNotFoundError(name)

        except ToolNotFoundError:
            raise
        except InvalidParamsError:
            raise
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}",
            )

    # Research task tool handlers
    async def _create_research_task(self, arguments: Dict[str, Any]) -> ToolResult:
        """Create a new research task."""
        if "project_id" not in arguments or "title" not in arguments:
            raise InvalidParamsError("project_id and title are required")

        task = ResearchTask(
            project_id=arguments["project_id"],
            title=arguments["title"],
            description=arguments.get("description"),
            priority=arguments.get("priority", "medium"),
            status=arguments.get("status", "todo"),
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        return ToolResult(
            success=True,
            result={
                "task_id": task.id,
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "message": f"Research task '{task.title}' created successfully",
            },
        )

    async def _update_research_task(self, arguments: Dict[str, Any]) -> ToolResult:
        """Update an existing research task."""
        if "task_id" not in arguments:
            raise InvalidParamsError("task_id is required")

        from sqlalchemy import select
        result = await self.db.execute(
            select(ResearchTask).where(ResearchTask.id == arguments["task_id"])
        )
        task = result.scalar_one_or_none()

        if not task:
            return ToolResult(
                success=False,
                error=f"Task {arguments['task_id']} not found",
            )

        # Update fields
        if "title" in arguments:
            task.title = arguments["title"]
        if "description" in arguments:
            task.description = arguments["description"]
        if "status" in arguments:
            task.status = arguments["status"]
        if "priority" in arguments:
            task.priority = arguments["priority"]

        await self.db.commit()
        await self.db.refresh(task)

        return ToolResult(
            success=True,
            result={
                "task_id": task.id,
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "message": f"Task {task.id} updated successfully",
            },
        )

    # Technology tool handlers
    async def _add_technology(self, arguments: Dict[str, Any]) -> ToolResult:
        """Add a new technology to the radar."""
        required = ["project_id", "title", "domain"]
        if not all(k in arguments for k in required):
            raise InvalidParamsError(f"Required parameters: {', '.join(required)}")

        technology = Technology(
            project_id=arguments["project_id"],
            title=arguments["title"],
            domain=arguments["domain"],
            vendor=arguments.get("vendor"),
            description=arguments.get("description"),
            status=arguments.get("status", "assess"),
        )

        self.db.add(technology)
        await self.db.commit()
        await self.db.refresh(technology)

        return ToolResult(
            success=True,
            result={
                "technology_id": technology.id,
                "title": technology.title,
                "domain": technology.domain,
                "status": technology.status,
                "message": f"Technology '{technology.title}' added successfully",
            },
        )

    # Schedule tool handlers
    async def _create_schedule(self, arguments: Dict[str, Any]) -> ToolResult:
        """Create a new schedule."""
        required = ["project_id", "name", "task_type", "frequency"]
        if not all(k in arguments for k in required):
            raise InvalidParamsError(f"Required parameters: {', '.join(required)}")

        schedule = await self.schedule_service.create_schedule(
            project_id=arguments["project_id"],
            name=arguments["name"],
            task_type=arguments["task_type"],
            frequency=arguments["frequency"],
            cron_expression=arguments.get("cron_expression"),
            description=arguments.get("description"),
            enabled=arguments.get("enabled", True),
        )

        return ToolResult(
            success=True,
            result={
                "schedule_id": schedule.id,
                "name": schedule.name,
                "frequency": schedule.frequency,
                "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
                "enabled": schedule.enabled,
                "message": f"Schedule '{schedule.name}' created successfully",
            },
        )

    async def _execute_schedule(self, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a schedule immediately."""
        if "schedule_id" not in arguments:
            raise InvalidParamsError("schedule_id is required")

        job = await self.schedule_service.execute_schedule(arguments["schedule_id"])

        return ToolResult(
            success=True,
            result={
                "schedule_id": arguments["schedule_id"],
                "job_id": job.id,
                "message": f"Schedule executed, job {job.id} created",
            },
        )

    async def _enable_schedule(self, arguments: Dict[str, Any]) -> ToolResult:
        """Enable a schedule."""
        if "schedule_id" not in arguments:
            raise InvalidParamsError("schedule_id is required")

        schedule = await self.schedule_service.update_schedule(
            schedule_id=arguments["schedule_id"],
            enabled=True,
        )

        return ToolResult(
            success=True,
            result={
                "schedule_id": schedule.id,
                "name": schedule.name,
                "enabled": schedule.enabled,
                "message": f"Schedule '{schedule.name}' enabled",
            },
        )

    async def _disable_schedule(self, arguments: Dict[str, Any]) -> ToolResult:
        """Disable a schedule."""
        if "schedule_id" not in arguments:
            raise InvalidParamsError("schedule_id is required")

        schedule = await self.schedule_service.update_schedule(
            schedule_id=arguments["schedule_id"],
            enabled=False,
        )

        return ToolResult(
            success=True,
            result={
                "schedule_id": schedule.id,
                "name": schedule.name,
                "enabled": schedule.enabled,
                "message": f"Schedule '{schedule.name}' disabled",
            },
        )

    # Job tool handlers
    async def _create_job(self, arguments: Dict[str, Any]) -> ToolResult:
        """Create a new job."""
        required = ["project_id", "job_type"]
        if not all(k in arguments for k in required):
            raise InvalidParamsError(f"Required parameters: {', '.join(required)}")

        job = await self.job_service.create_job(
            project_id=arguments["project_id"],
            job_type=arguments["job_type"],
            parameters=arguments.get("parameters", {}),
        )

        # Optionally dispatch immediately
        if arguments.get("dispatch", False):
            await self.job_service.dispatch_job(job.id)

        return ToolResult(
            success=True,
            result={
                "job_id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "message": f"Job {job.id} created" + (" and dispatched" if arguments.get("dispatch") else ""),
            },
        )

    async def _get_job_status(self, arguments: Dict[str, Any]) -> ToolResult:
        """Get job status."""
        if "job_id" not in arguments:
            raise InvalidParamsError("job_id is required")

        job = await self.job_service.get_job(arguments["job_id"])

        if not job:
            return ToolResult(
                success=False,
                error=f"Job {arguments['job_id']} not found",
            )

        return ToolResult(
            success=True,
            result={
                "job_id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "progress": job.progress,
                "current_step": job.current_step,
                "result": job.result,
                "error": job.error,
            },
        )

    async def _cancel_job(self, arguments: Dict[str, Any]) -> ToolResult:
        """Cancel a job."""
        if "job_id" not in arguments:
            raise InvalidParamsError("job_id is required")

        job = await self.job_service.cancel_job(arguments["job_id"])

        return ToolResult(
            success=True,
            result={
                "job_id": job.id,
                "status": job.status,
                "message": f"Job {job.id} cancelled",
            },
        )
