"""
Project service - Business logic for project management
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate, ProjectStats
from app.services.port_service import PortService
from app.services.setup_service import SetupService
from sqlalchemy import func, case

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing CommandCenter projects"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.port_service = PortService(db)
        self.setup_service = SetupService()

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
        4. Clone CommandCenter (async via SetupService) OR use existing
        5. Generate .env file (only if not using existing)
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

        # Determine CC path
        if project_data.use_existing_cc:
            if not project_data.existing_cc_path:
                raise ValueError("existing_cc_path is required when use_existing_cc=True")

            cc_path = project_data.existing_cc_path

            # Validate existing CC path
            if not os.path.exists(cc_path):
                raise ValueError(f"CommandCenter path does not exist: {cc_path}")

            # Check for docker-compose.yml
            compose_file = os.path.join(cc_path, "docker-compose.yml")
            if not os.path.exists(compose_file):
                raise ValueError(f"No docker-compose.yml found at {cc_path}")
        else:
            cc_path = os.path.join(project_data.path, "commandcenter")

        # Allocate ports (only if not using existing, for display purposes)
        ports = await self.port_service.allocate_ports()

        # If using existing, try to read ports from .env
        if project_data.use_existing_cc:
            env_ports = self._read_ports_from_env(cc_path)
            if env_ports:
                ports = env_ports

        # Create project record with 'creating' status to prevent race condition
        # where frontend polling shows incomplete projects (Issue #44)
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
            status="creating" if not project_data.use_existing_cc else "stopped",
            health="unknown",
            is_configured=project_data.use_existing_cc,  # Already configured if existing
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        # Setup only if not using existing CC
        if not project_data.use_existing_cc:
            try:
                # Trigger async setup (clone CC, configure .env)
                await self.setup_service.setup_commandcenter(project)

                # Update status and is_configured flag after successful setup
                project.status = "stopped"
                project.is_configured = True
                await self.db.commit()
                await self.db.refresh(project)
            except Exception as e:
                # Log the error with full traceback for debugging
                logger.error(
                    f"Project setup failed for '{project.name}' (id={project.id}): {str(e)}",
                    exc_info=True,
                    extra={"project_id": project.id, "project_name": project.name}
                )

                # Mark project as error state if setup fails
                project.status = "error"
                project.health = "unhealthy"
                await self.db.commit()
                await self.db.refresh(project)
                raise

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
            delete_files: If True, also delete the CommandCenter directory and stop containers
        """
        import subprocess
        import shutil

        project = await self.get_project(project_id)
        if not project:
            return False

        # Stop and remove containers if requested
        if delete_files and os.path.exists(project.cc_path):
            try:
                # Stop and remove containers with volumes
                compose_file = os.path.join(project.cc_path, "docker-compose.yml")
                if os.path.exists(compose_file):
                    # Import here to avoid circular dependency
                    from app.services.orchestration_service import OrchestrationService

                    # Get host path for proper volume resolution
                    host_cc_path = OrchestrationService.HOST_PROJECTS_PATH
                    if project.cc_path.startswith("/projects"):
                        host_cc_path = project.cc_path.replace(
                            "/projects",
                            OrchestrationService.HOST_PROJECTS_PATH,
                            1
                        )

                    subprocess.run(
                        ["docker-compose", "-f", compose_file, "down", "-v"],
                        cwd=project.cc_path,
                        capture_output=True,
                        timeout=60,
                    )

                # Delete the directory
                shutil.rmtree(project.cc_path)
            except Exception as e:
                print(f"Warning: Failed to delete files for project {project.name}: {e}")

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

    def _read_ports_from_env(self, cc_path: str) -> Optional["PortSet"]:
        """Read ports from existing .env file"""
        from app.schemas import PortSet

        env_file = os.path.join(cc_path, ".env")
        if not os.path.exists(env_file):
            return None

        try:
            with open(env_file, "r") as f:
                env_content = f.read()

            # Parse port values
            backend_port = None
            frontend_port = None
            postgres_port = None
            redis_port = None

            for line in env_content.split("\n"):
                line = line.strip()
                if line.startswith("BACKEND_PORT="):
                    backend_port = int(line.split("=")[1])
                elif line.startswith("FRONTEND_PORT="):
                    frontend_port = int(line.split("=")[1])
                elif line.startswith("POSTGRES_PORT="):
                    postgres_port = int(line.split("=")[1])
                elif line.startswith("REDIS_PORT="):
                    redis_port = int(line.split("=")[1])

            if all([backend_port, frontend_port, postgres_port, redis_port]):
                return PortSet(
                    backend=backend_port,
                    frontend=frontend_port,
                    postgres=postgres_port,
                    redis=redis_port,
                )

            return None

        except Exception as e:
            print(f"Warning: Failed to read ports from {env_file}: {e}")
            return None
