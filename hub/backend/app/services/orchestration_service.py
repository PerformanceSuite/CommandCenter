"""
Orchestration service - Start/stop CommandCenter instances via docker-compose
"""

import os
import subprocess
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Project


class OrchestrationService:
    """Service for orchestrating docker-compose operations"""

    # Path mapping: container path -> host path
    CONTAINER_PROJECTS_PATH = "/projects"
    HOST_PROJECTS_PATH = os.getenv("PROJECTS_ROOT", os.path.expanduser("~/Projects"))

    # Docker Compose service configuration
    # Essential services that must be started for project functionality
    ESSENTIAL_SERVICES = ["backend", "frontend", "postgres", "redis"]
    # Optional services that may conflict with ports or not be required
    # Flower: Port 5555 (Celery monitoring UI)
    # Prometheus: Port 9090 (Metrics collection)
    # Celery worker: Can be started separately if needed
    EXCLUDED_SERVICES = ["flower", "prometheus", "celery"]

    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_host_path(self, container_path: str) -> str:
        """Convert container path to host path for Docker volume mounts"""
        if container_path.startswith(self.CONTAINER_PROJECTS_PATH):
            return container_path.replace(
                self.CONTAINER_PROJECTS_PATH,
                self.HOST_PROJECTS_PATH,
                1
            )
        return container_path

    async def start_project(self, project_id: int) -> dict:
        """Start CommandCenter instance"""
        project = await self._get_project(project_id)

        if project.status == "running":
            return {
                "success": True,
                "message": "Project is already running",
                "project_id": project_id,
                "status": "running",
            }

        # Update status to starting
        project.status = "starting"
        await self.db.commit()

        try:
            # Convert container path to host path for Docker volumes
            host_cc_path = self._get_host_path(project.cc_path)
            compose_file = os.path.join(project.cc_path, "docker-compose.yml")

            # Set environment for docker-compose
            # COMPOSE_PROJECT_DIR tells docker-compose where to resolve relative paths
            env = os.environ.copy()
            env["COMPOSE_PROJECT_DIR"] = host_cc_path

            # Run docker-compose with explicit file path and project directory
            # Use --project-directory to tell docker-compose where to resolve relative volume paths
            # This allows us to use the host path for volume resolution while running from container
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "--project-directory", host_cc_path, "up", "-d"] + self.ESSENTIAL_SERVICES,
                cwd=project.cc_path,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                env=env,
            )

            if result.returncode != 0:
                project.status = "error"
                await self.db.commit()
                raise RuntimeError(f"Failed to start: {result.stderr}")

            # Update status
            project.status = "running"
            project.last_started = datetime.utcnow()
            await self.db.commit()

            return {
                "success": True,
                "message": "Project started successfully",
                "project_id": project_id,
                "status": "running",
            }

        except Exception as e:
            project.status = "error"
            await self.db.commit()
            raise RuntimeError(f"Failed to start project: {str(e)}")

    async def stop_project(self, project_id: int) -> dict:
        """Stop CommandCenter instance"""
        project = await self._get_project(project_id)

        if project.status == "stopped":
            return {
                "success": True,
                "message": "Project is already stopped",
                "project_id": project_id,
                "status": "stopped",
            }

        # Update status
        project.status = "stopping"
        await self.db.commit()

        try:
            # Convert container path to host path for Docker volumes
            host_cc_path = self._get_host_path(project.cc_path)
            compose_file = os.path.join(project.cc_path, "docker-compose.yml")

            # Run docker-compose down with explicit file path and project directory
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "--project-directory", host_cc_path, "down"],
                cwd=project.cc_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                project.status = "error"
                await self.db.commit()
                raise RuntimeError(f"Failed to stop: {result.stderr}")

            # Update status
            project.status = "stopped"
            project.last_stopped = datetime.utcnow()
            await self.db.commit()

            return {
                "success": True,
                "message": "Project stopped successfully",
                "project_id": project_id,
                "status": "stopped",
            }

        except Exception as e:
            project.status = "error"
            await self.db.commit()
            raise RuntimeError(f"Failed to stop project: {str(e)}")

    async def restart_project(self, project_id: int) -> dict:
        """Restart CommandCenter instance"""
        # Stop then start
        await self.stop_project(project_id)
        return await self.start_project(project_id)

    async def get_project_status(self, project_id: int) -> dict:
        """Get real-time status from docker-compose"""
        project = await self._get_project(project_id)

        try:
            # Convert container path to host path for Docker volumes
            host_cc_path = self._get_host_path(project.cc_path)
            compose_file = os.path.join(project.cc_path, "docker-compose.yml")

            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "--project-directory", host_cc_path, "ps", "--format", "json"],
                cwd=project.cc_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Parse container status
            containers = []
            if result.returncode == 0 and result.stdout:
                import json

                for line in result.stdout.strip().split("\n"):
                    if line:
                        containers.append(json.loads(line))

            running_count = sum(1 for c in containers if "running" in c.get("State", "").lower())
            total_count = len(containers)

            # Determine health
            if running_count == 0:
                health = "stopped"
                status = "stopped"
            elif running_count == total_count and total_count > 0:
                health = "healthy"
                status = "running"
            else:
                health = "unhealthy"
                status = "running"

            # Update project if changed
            if project.status != status or project.health != health:
                project.status = status
                project.health = health
                await self.db.commit()

            return {
                "project_id": project_id,
                "status": status,
                "health": health,
                "containers": containers,
                "running_count": running_count,
                "total_count": total_count,
            }

        except Exception as e:
            return {
                "project_id": project_id,
                "status": "unknown",
                "health": "unknown",
                "error": str(e),
            }

    async def get_logs(self, project_id: int, tail: int = 100) -> dict:
        """Get docker-compose logs"""
        project = await self._get_project(project_id)

        try:
            # Convert container path to host path for Docker volumes
            host_cc_path = self._get_host_path(project.cc_path)
            compose_file = os.path.join(project.cc_path, "docker-compose.yml")

            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "--project-directory", host_cc_path, "logs", "--tail", str(tail)],
                cwd=project.cc_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            return {
                "project_id": project_id,
                "logs": result.stdout,
                "errors": result.stderr,
            }

        except Exception as e:
            raise RuntimeError(f"Failed to get logs: {str(e)}")

    async def _get_project(self, project_id: int) -> Project:
        """Get project or raise error"""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        return project
