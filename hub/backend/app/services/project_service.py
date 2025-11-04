"""
Project service - Business logic for project management
"""

import os
import re
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate, ProjectStats
from app.services.port_service import PortService
from app.events.service import EventService
from app.config import get_nats_url

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing CommandCenter projects"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.port_service = PortService(db)

    async def list_projects(self) -> List[Project]:
        """
        List all projects

        Note: Excludes projects with status='creating' to prevent race condition
        where partially created projects appear before setup completes.
        See: Issue #44
        """
        result = await self.db.execute(
            select(Project).where(Project.status != "creating")
        )
        return list(result.scalars().all())

    async def get_stats(self) -> ProjectStats:
        """
        Get project statistics

        Note: Excludes projects with status='creating' from total count
        to match list_projects() behavior (Issue #44)
        """
        result = await self.db.execute(
            select(
                func.count(Project.id).label("total"),
                func.sum(case((Project.status == "running", 1), else_=0)).label("running"),
                func.sum(case((Project.status == "stopped", 1), else_=0)).label("stopped"),
                func.sum(case((Project.status == "error", 1), else_=0)).label("errors"),
            ).where(Project.status != "creating")
        )
        row = result.one()
        return ProjectStats(
            total_projects=row.total or 0,
            running=int(row.running or 0),
            stopped=int(row.stopped or 0),
            errors=int(row.errors or 0),
        )

    async def get_project(self, project_id: int) -> Optional[Project]:
        """Get project by ID"""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def get_project_by_slug(self, slug: str) -> Optional[Project]:
        """Get project by slug"""
        result = await self.db.execute(select(Project).where(Project.slug == slug))
        return result.scalar_one_or_none()

    async def create_project(self, project_data: ProjectCreate) -> Project:
        """
        Create new CommandCenter project

        Steps:
        1. Generate slug from name
        2. Allocate ports
        3. Create database entry

        Note: Projects now just need a path - no CommandCenter cloning needed.
        Dagger will mount the project path and orchestrate containers directly.
        """
        # Generate slug
        slug = self._generate_slug(project_data.name)

        # Check if slug exists
        existing = await self.get_project_by_slug(slug)
        if existing:
            raise ValueError(f"Project with name '{project_data.name}' already exists")

        # Validate path exists
        if not os.path.exists(project_data.path):
            raise ValueError(f"Path does not exist: {project_data.path}")

        # Allocate ports
        ports = await self.port_service.allocate_ports()

        # Create project record - ready to use immediately (no setup needed)
        # Dagger will mount the project path and orchestrate containers directly
        project = Project(
            name=project_data.name,
            slug=slug,
            path=project_data.path,
            backend_port=ports.backend,
            frontend_port=ports.frontend,
            postgres_port=ports.postgres,
            redis_port=ports.redis,
            status="stopped",
            health="unknown",
            is_configured=True,  # Always configured - Dagger handles everything
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        # Emit project.created event
        try:
            event_service = EventService(nats_url=get_nats_url(), db_session=self.db)
            await event_service.connect()
            await event_service.publish(
                subject=f"hub.{event_service.hub_id}.project.created",
                payload={
                    "project_id": project.id,
                    "project_name": project.name,
                    "project_slug": project.slug,
                    "project_path": project.path,
                    "backend_port": project.backend_port,
                    "frontend_port": project.frontend_port,
                }
            )
            await event_service.disconnect()
        except Exception as e:
            logger.warning(f"Failed to publish project.created event: {e}")

        return project

    async def update_project(
        self, project_id: int, project_data: ProjectUpdate
    ) -> Optional[Project]:
        """Update project"""
        project = await self.get_project(project_id)
        if not project:
            return None

        # Update fields
        if project_data.name is not None:
            project.name = project_data.name
            project.slug = self._generate_slug(project_data.name)

        if project_data.status is not None:
            project.status = project_data.status

        if project_data.health is not None:
            project.health = project_data.health

        if project_data.repo_count is not None:
            project.repo_count = project_data.repo_count

        if project_data.tech_count is not None:
            project.tech_count = project_data.tech_count

        if project_data.task_count is not None:
            project.task_count = project_data.task_count

        await self.db.commit()
        await self.db.refresh(project)

        return project

    async def delete_project(self, project_id: int, delete_files: bool = False) -> bool:
        """
        Delete project

        Args:
            project_id: Project ID to delete
            delete_files: If True, also stop the running project (if any)
        """
        project = await self.get_project(project_id)
        if not project:
            return False

        # Stop project if running (via Dagger)
        if delete_files and project.status == "running":
            try:
                # Import here to avoid circular dependency
                from app.services.orchestration_service import OrchestrationService

                orchestration_service = OrchestrationService(self.db)
                await orchestration_service.stop_project(project_id)
            except Exception as e:
                logger.warning(f"Failed to stop project {project.name} during deletion: {e}")

        # Emit project.deleted event
        try:
            event_service = EventService(nats_url=get_nats_url(), db_session=self.db)
            await event_service.connect()
            await event_service.publish(
                subject=f"hub.{event_service.hub_id}.project.deleted",
                payload={
                    "project_id": project.id,
                    "project_name": project.name,
                    "project_slug": project.slug,
                    "deleted_files": delete_files,
                }
            )
            await event_service.disconnect()
        except Exception as e:
            logger.warning(f"Failed to publish project.deleted event: {e}")

        # Delete from database
        await self.db.delete(project)
        await self.db.commit()

        return True

    def _generate_slug(self, name: str) -> str:
        """Generate URL-safe slug from project name"""
        # Convert to lowercase
        slug = name.lower()
        # Replace spaces and special chars with hyphens
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        # Remove leading/trailing hyphens
        slug = slug.strip("-")
        return slug
