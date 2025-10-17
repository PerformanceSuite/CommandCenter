"""
Orchestration service - Start/stop CommandCenter instances via Dagger SDK
"""

import logging
import secrets
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Project
from app.dagger_modules.commandcenter import CommandCenterStack, CommandCenterConfig

logger = logging.getLogger(__name__)


class OrchestrationService:
    """Service for orchestrating Dagger-based CommandCenter stacks"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._active_stacks: dict[int, CommandCenterStack] = {}

    def _check_port_available(self, port: int) -> tuple[bool, str]:
        """Check if a port is available (same as before)"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    return False, f"Port {port} is already in use"
                return True, ""
        except Exception as e:
            logger.warning(f"Error checking port {port}: {e}")
            return True, ""

    async def start_project(self, project_id: int) -> dict:
        """Start CommandCenter instance using Dagger"""
        project = await self._get_project(project_id)

        if project.status == "running":
            return {
                "success": True,
                "message": "Project is already running",
                "project_id": project_id,
                "status": "running",
            }

        # Check for port conflicts
        ports_to_check = [
            ("Frontend", project.frontend_port),
            ("Backend", project.backend_port),
            ("PostgreSQL", project.postgres_port),
            ("Redis", project.redis_port),
        ]

        port_conflicts = []
        for service_name, port in ports_to_check:
            is_available, error = self._check_port_available(port)
            if not is_available:
                port_conflicts.append(f"{service_name} port {port}")

        if port_conflicts:
            error_msg = (
                f"Cannot start project: The following ports are already in use: "
                f"{', '.join(port_conflicts)}"
            )
            raise RuntimeError(error_msg)

        # Update status
        project.status = "starting"
        await self.db.commit()

        try:
            # Create Dagger configuration
            config = CommandCenterConfig(
                project_name=project.name,
                project_path=project.path,  # Direct path to project folder
                backend_port=project.backend_port,
                frontend_port=project.frontend_port,
                postgres_port=project.postgres_port,
                redis_port=project.redis_port,
                db_password=secrets.token_urlsafe(32),
                secret_key=secrets.token_hex(32),
            )

            # Start Dagger stack
            async with CommandCenterStack(config) as stack:
                result = await stack.start()
                self._active_stacks[project_id] = stack

            # Update status
            project.status = "running"
            project.last_started = datetime.now(timezone.utc)
            await self.db.commit()

            return {
                "success": True,
                "message": "Project started successfully via Dagger",
                "project_id": project_id,
                "status": "running",
            }

        except Exception as e:
            project.status = "error"
            await self.db.commit()
            raise RuntimeError(f"Failed to start project with Dagger: {str(e)}")

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

        project.status = "stopping"
        await self.db.commit()

        try:
            # Stop Dagger stack
            if project_id in self._active_stacks:
                stack = self._active_stacks[project_id]
                await stack.stop()
                del self._active_stacks[project_id]

            project.status = "stopped"
            project.last_stopped = datetime.now(timezone.utc)
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
        await self.stop_project(project_id)
        return await self.start_project(project_id)

    async def get_project_status(self, project_id: int) -> dict:
        """Get real-time status from Dagger"""
        project = await self._get_project(project_id)

        try:
            if project_id in self._active_stacks:
                stack = self._active_stacks[project_id]
                return await stack.status()
            else:
                return {
                    "project_id": project_id,
                    "status": "stopped",
                    "health": "stopped",
                }
        except Exception as e:
            return {
                "project_id": project_id,
                "status": "unknown",
                "health": "unknown",
                "error": str(e),
            }

    async def get_logs(self, project_id: int, tail: int = 100) -> dict:
        """Get container logs (to be implemented with Dagger)"""
        # Placeholder for now
        return {
            "project_id": project_id,
            "logs": "Dagger log retrieval not yet implemented",
            "errors": "",
        }

    async def _get_project(self, project_id: int) -> Project:
        """Get project or raise error"""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        return project
