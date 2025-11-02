"""
CommandCenter Resource Provider for MCP.

Exposes CommandCenter data (projects, technologies, research tasks, repositories)
as MCP resources for AI assistants to read and understand.
"""

import json
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.mcp.providers.base import Resource, ResourceContent, ResourceProvider
from app.mcp.utils import ResourceNotFoundError
from app.models import (
    Project,
    Technology,
    ResearchTask,
    Repository,
    Schedule,
    Job,
)


logger = logging.getLogger(__name__)


class CommandCenterResourceProvider(ResourceProvider):
    """
    Resource provider for CommandCenter data.

    Exposes:
    - Projects list and individual project details
    - Technologies list and individual technology details
    - Research tasks list and individual task details
    - Repositories list and individual repository details
    - Schedules list
    - Jobs list and status
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize CommandCenter resource provider.

        Args:
            db: Database session for accessing CommandCenter data
        """
        super().__init__("commandcenter")
        self.db = db

    async def list_resources(self) -> List[Resource]:
        """
        List all available CommandCenter resources.

        Returns:
            List of Resource objects representing available data
        """
        resources = [
            # Project resources
            Resource(
                uri="commandcenter://projects",
                name="All Projects",
                description="Complete list of all projects in CommandCenter",
                mime_type="application/json",
            ),
            Resource(
                uri="commandcenter://projects/{id}",
                name="Project Details",
                description="Detailed information about a specific project (use project ID)",
                mime_type="application/json",
            ),
            # Technology resources
            Resource(
                uri="commandcenter://technologies",
                name="All Technologies",
                description="Complete technology radar - all tracked technologies",
                mime_type="application/json",
            ),
            Resource(
                uri="commandcenter://technologies/{id}",
                name="Technology Details",
                description="Detailed information about a specific technology (use technology ID)",
                mime_type="application/json",
            ),
            # Research task resources
            Resource(
                uri="commandcenter://research/tasks",
                name="All Research Tasks",
                description="Complete list of research tasks",
                mime_type="application/json",
            ),
            Resource(
                uri="commandcenter://research/tasks/{id}",
                name="Research Task Details",
                description="Detailed information about a specific research task (use task ID)",
                mime_type="application/json",
            ),
            # Repository resources
            Resource(
                uri="commandcenter://repositories",
                name="All Repositories",
                description="Complete list of tracked GitHub repositories",
                mime_type="application/json",
            ),
            Resource(
                uri="commandcenter://repositories/{id}",
                name="Repository Details",
                description="Detailed information about a specific repository (use repository ID)",
                mime_type="application/json",
            ),
            # Schedule resources
            Resource(
                uri="commandcenter://schedules",
                name="All Schedules",
                description="Complete list of automated schedules",
                mime_type="application/json",
            ),
            Resource(
                uri="commandcenter://schedules/active",
                name="Active Schedules",
                description="List of currently active (enabled) schedules",
                mime_type="application/json",
            ),
            # Job resources
            Resource(
                uri="commandcenter://jobs",
                name="All Jobs",
                description="Complete list of async jobs",
                mime_type="application/json",
            ),
            Resource(
                uri="commandcenter://jobs/active",
                name="Active Jobs",
                description="List of currently running or pending jobs",
                mime_type="application/json",
            ),
            Resource(
                uri="commandcenter://jobs/{id}",
                name="Job Details",
                description="Detailed information about a specific job (use job ID)",
                mime_type="application/json",
            ),
            # Summary/overview resources
            Resource(
                uri="commandcenter://overview",
                name="System Overview",
                description="High-level overview of CommandCenter system status",
                mime_type="application/json",
            ),
        ]

        return resources

    async def read_resource(self, uri: str) -> ResourceContent:
        """
        Read specific resource by URI.

        Args:
            uri: Resource URI (e.g., "commandcenter://projects")

        Returns:
            ResourceContent with the requested data

        Raises:
            ResourceNotFoundError: If resource URI doesn't exist or ID not found
        """
        # Parse URI
        if not uri.startswith("commandcenter://"):
            raise ResourceNotFoundError(uri)

        path = uri.replace("commandcenter://", "")

        # Route to appropriate handler
        if path == "projects":
            return await self._read_projects()
        elif path.startswith("projects/"):
            project_id = int(path.split("/")[1])
            return await self._read_project(project_id)

        elif path == "technologies":
            return await self._read_technologies()
        elif path.startswith("technologies/"):
            tech_id = int(path.split("/")[1])
            return await self._read_technology(tech_id)

        elif path == "research/tasks":
            return await self._read_research_tasks()
        elif path.startswith("research/tasks/"):
            task_id = int(path.split("/")[2])
            return await self._read_research_task(task_id)

        elif path == "repositories":
            return await self._read_repositories()
        elif path.startswith("repositories/"):
            repo_id = int(path.split("/")[1])
            return await self._read_repository(repo_id)

        elif path == "schedules":
            return await self._read_schedules()
        elif path == "schedules/active":
            return await self._read_active_schedules()

        elif path == "jobs":
            return await self._read_jobs()
        elif path == "jobs/active":
            return await self._read_active_jobs()
        elif path.startswith("jobs/"):
            job_id = int(path.split("/")[1])
            return await self._read_job(job_id)

        elif path == "overview":
            return await self._read_overview()

        else:
            raise ResourceNotFoundError(uri)

    # Project resource handlers
    async def _read_projects(self) -> ResourceContent:
        """Read all projects."""
        result = await self.db.execute(select(Project))
        projects = result.scalars().all()

        data = [
            p.to_dict()
            if hasattr(p, "to_dict")
            else {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ]

        return ResourceContent(
            uri="commandcenter://projects",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    async def _read_project(self, project_id: int) -> ResourceContent:
        """Read specific project details."""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise ResourceNotFoundError(f"commandcenter://projects/{project_id}")

        data = (
            project.to_dict()
            if hasattr(project, "to_dict")
            else {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat() if project.created_at else None,
            }
        )

        return ResourceContent(
            uri=f"commandcenter://projects/{project_id}",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    # Technology resource handlers
    async def _read_technologies(self) -> ResourceContent:
        """Read all technologies."""
        result = await self.db.execute(select(Technology))
        technologies = result.scalars().all()

        data = [
            t.to_dict()
            if hasattr(t, "to_dict")
            else {
                "id": t.id,
                "title": t.title,
                "domain": t.domain,
                "vendor": t.vendor,
                "status": t.status,
                "relevance": t.relevance,
                "description": t.description,
            }
            for t in technologies
        ]

        return ResourceContent(
            uri="commandcenter://technologies",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    async def _read_technology(self, tech_id: int) -> ResourceContent:
        """Read specific technology details."""
        result = await self.db.execute(select(Technology).where(Technology.id == tech_id))
        technology = result.scalar_one_or_none()

        if not technology:
            raise ResourceNotFoundError(f"commandcenter://technologies/{tech_id}")

        data = (
            technology.to_dict()
            if hasattr(technology, "to_dict")
            else {
                "id": technology.id,
                "title": technology.title,
                "domain": technology.domain,
                "vendor": technology.vendor,
                "status": technology.status,
                "relevance": technology.relevance,
                "description": technology.description,
            }
        )

        return ResourceContent(
            uri=f"commandcenter://technologies/{tech_id}",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    # Research task resource handlers
    async def _read_research_tasks(self) -> ResourceContent:
        """Read all research tasks."""
        result = await self.db.execute(select(ResearchTask))
        tasks = result.scalars().all()

        data = [
            t.to_dict()
            if hasattr(t, "to_dict")
            else {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
            }
            for t in tasks
        ]

        return ResourceContent(
            uri="commandcenter://research/tasks",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    async def _read_research_task(self, task_id: int) -> ResourceContent:
        """Read specific research task details."""
        result = await self.db.execute(select(ResearchTask).where(ResearchTask.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise ResourceNotFoundError(f"commandcenter://research/tasks/{task_id}")

        data = (
            task.to_dict()
            if hasattr(task, "to_dict")
            else {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
            }
        )

        return ResourceContent(
            uri=f"commandcenter://research/tasks/{task_id}",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    # Repository resource handlers
    async def _read_repositories(self) -> ResourceContent:
        """Read all repositories."""
        result = await self.db.execute(select(Repository))
        repositories = result.scalars().all()

        data = [
            r.to_dict()
            if hasattr(r, "to_dict")
            else {
                "id": r.id,
                "name": r.name,
                "owner": r.owner,
                "url": r.url if hasattr(r, "url") else None,
            }
            for r in repositories
        ]

        return ResourceContent(
            uri="commandcenter://repositories",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    async def _read_repository(self, repo_id: int) -> ResourceContent:
        """Read specific repository details."""
        result = await self.db.execute(select(Repository).where(Repository.id == repo_id))
        repository = result.scalar_one_or_none()

        if not repository:
            raise ResourceNotFoundError(f"commandcenter://repositories/{repo_id}")

        data = (
            repository.to_dict()
            if hasattr(repository, "to_dict")
            else {
                "id": repository.id,
                "name": repository.name,
                "owner": repository.owner,
                "url": repository.url if hasattr(repository, "url") else None,
            }
        )

        return ResourceContent(
            uri=f"commandcenter://repositories/{repo_id}",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    # Schedule resource handlers
    async def _read_schedules(self) -> ResourceContent:
        """Read all schedules."""
        result = await self.db.execute(select(Schedule))
        schedules = result.scalars().all()

        data = [s.to_dict() for s in schedules]

        return ResourceContent(
            uri="commandcenter://schedules",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    async def _read_active_schedules(self) -> ResourceContent:
        """Read only active (enabled) schedules."""
        result = await self.db.execute(select(Schedule).where(Schedule.enabled is True))
        schedules = result.scalars().all()

        data = [s.to_dict() for s in schedules]

        return ResourceContent(
            uri="commandcenter://schedules/active",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    # Job resource handlers
    async def _read_jobs(self) -> ResourceContent:
        """Read all jobs."""
        result = await self.db.execute(select(Job))
        jobs = result.scalars().all()

        data = [
            j.to_dict()
            if hasattr(j, "to_dict")
            else {
                "id": j.id,
                "job_type": j.job_type,
                "status": j.status,
                "progress": j.progress,
            }
            for j in jobs
        ]

        return ResourceContent(
            uri="commandcenter://jobs",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    async def _read_active_jobs(self) -> ResourceContent:
        """Read only active (running/pending) jobs."""
        result = await self.db.execute(select(Job).where(Job.status.in_(["pending", "running"])))
        jobs = result.scalars().all()

        data = [
            j.to_dict()
            if hasattr(j, "to_dict")
            else {
                "id": j.id,
                "job_type": j.job_type,
                "status": j.status,
                "progress": j.progress,
            }
            for j in jobs
        ]

        return ResourceContent(
            uri="commandcenter://jobs/active",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    async def _read_job(self, job_id: int) -> ResourceContent:
        """Read specific job details."""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if not job:
            raise ResourceNotFoundError(f"commandcenter://jobs/{job_id}")

        data = (
            job.to_dict()
            if hasattr(job, "to_dict")
            else {
                "id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "progress": job.progress,
            }
        )

        return ResourceContent(
            uri=f"commandcenter://jobs/{job_id}",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )

    # Overview resource handler
    async def _read_overview(self) -> ResourceContent:
        """Read system overview with counts and status."""
        from sqlalchemy import func

        # Get counts
        projects_count = (await self.db.execute(select(func.count(Project.id)))).scalar()
        technologies_count = (await self.db.execute(select(func.count(Technology.id)))).scalar()
        tasks_count = (await self.db.execute(select(func.count(ResearchTask.id)))).scalar()
        repositories_count = (await self.db.execute(select(func.count(Repository.id)))).scalar()
        schedules_count = (await self.db.execute(select(func.count(Schedule.id)))).scalar()
        active_schedules_count = (
            await self.db.execute(select(func.count(Schedule.id)).where(Schedule.enabled is True))
        ).scalar()
        jobs_count = (await self.db.execute(select(func.count(Job.id)))).scalar()
        active_jobs_count = (
            await self.db.execute(
                select(func.count(Job.id)).where(Job.status.in_(["pending", "running"]))
            )
        ).scalar()

        data = {
            "system": "CommandCenter",
            "version": "1.0.0",
            "counts": {
                "projects": projects_count,
                "technologies": technologies_count,
                "research_tasks": tasks_count,
                "repositories": repositories_count,
                "schedules": {
                    "total": schedules_count,
                    "active": active_schedules_count,
                },
                "jobs": {
                    "total": jobs_count,
                    "active": active_jobs_count,
                },
            },
        }

        return ResourceContent(
            uri="commandcenter://overview",
            mime_type="application/json",
            text=json.dumps(data, indent=2),
        )
