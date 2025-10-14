"""
Project service - Business logic for project management
"""

import os
import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate
from app.services.port_service import PortService
from app.services.setup_service import SetupService


class ProjectService:
    """Service for managing CommandCenter projects"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.port_service = PortService(db)
        self.setup_service = SetupService()

    async def list_projects(self) -> List[Project]:
        """List all projects"""
        result = await self.db.execute(select(Project))
        return list(result.scalars().all())

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
        4. Clone CommandCenter (async via SetupService)
        5. Generate .env file
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

        # Determine CC path
        cc_path = os.path.join(project_data.path, "commandcenter")

        # Create project record
        project = Project(
            name=project_data.name,
            slug=slug,
            path=project_data.path,
            cc_path=cc_path,
            compose_project_name=f"{slug}-commandcenter",
            backend_port=ports.backend,
            frontend_port=ports.frontend,
            postgres_port=ports.postgres,
            redis_port=ports.redis,
            status="stopped",
            health="unknown",
            is_configured=False,
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        # Trigger async setup (clone CC, configure .env)
        # This happens in the background
        await self.setup_service.setup_commandcenter(project)

        # Update is_configured flag
        project.is_configured = True
        await self.db.commit()
        await self.db.refresh(project)

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

    async def delete_project(self, project_id: int) -> bool:
        """Delete project (does not delete files)"""
        project = await self.get_project(project_id)
        if not project:
            return False

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
