"""
Orchestration service - Start/stop CommandCenter instances via Dagger SDK
"""

import logging
import secrets
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Project
from app.models.service import Service, ServiceType, HealthMethod, HealthStatus
from app.dagger_modules.commandcenter import CommandCenterStack, CommandCenterConfig
from app.events.service import EventService
from app.config import get_nats_url

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

            # Start Dagger stack - manage lifecycle manually to keep stack alive
            stack = CommandCenterStack(config)
            await stack.__aenter__()
            try:
                result = await stack.start()
                self._active_stacks[project_id] = stack
                # Keep stack alive - don't call __aexit__ yet
            except Exception as e:
                await stack.__aexit__(type(e), e, e.__traceback__)
                raise

            # Update status
            project.status = "running"
            project.last_started = datetime.now(timezone.utc)
            await self.db.commit()

            # Register services for health monitoring
            await self._register_services(project)

            # Emit project.started event
            try:
                event_service = EventService(nats_url=get_nats_url(), db_session=self.db)
                await event_service.connect()
                await event_service.publish(
                    subject=f"hub.{event_service.hub_id}.project.started",
                    payload={
                        "project_id": project.id,
                        "project_name": project.name,
                        "backend_port": project.backend_port,
                        "frontend_port": project.frontend_port,
                    }
                )
                await event_service.disconnect()
            except Exception as e:
                logger.warning(f"Failed to publish project.started event: {e}")

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
                await stack.__aexit__(None, None, None)  # Properly close stack
                del self._active_stacks[project_id]

            project.status = "stopped"
            project.last_stopped = datetime.now(timezone.utc)
            await self.db.commit()

            # Unregister services from health monitoring
            await self._unregister_services(project)

            # Emit project.stopped event
            try:
                event_service = EventService(nats_url=get_nats_url(), db_session=self.db)
                await event_service.connect()
                await event_service.publish(
                    subject=f"hub.{event_service.hub_id}.project.stopped",
                    payload={
                        "project_id": project.id,
                        "project_name": project.name,
                    }
                )
                await event_service.disconnect()
            except Exception as e:
                logger.warning(f"Failed to publish project.stopped event: {e}")

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

    async def get_project_logs(
        self,
        project_id: int,
        service_name: str,
        tail: int = 100
    ) -> str:
        """
        Retrieve logs from a project's service container.

        Args:
            project_id: Project ID
            service_name: Service name to get logs from
            tail: Number of lines to retrieve

        Returns:
            Log string

        Raises:
            RuntimeError: If stack not running or logs unavailable
        """
        if project_id not in self._active_stacks:
            raise RuntimeError(f"Project {project_id} is not running")

        stack = self._active_stacks[project_id]
        return await stack.get_logs(service_name, tail)

    async def _get_project(self, project_id: int) -> Project:
        """Get project or raise error"""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        return project

    async def _register_services(self, project: Project):
        """Register services for health monitoring.

        Args:
            project: Project that was just started
        """
        logger.info(f"Registering services for project {project.name}")

        # Define services to register
        services_config = [
            {
                "name": "postgres",
                "service_type": ServiceType.DATABASE,
                "health_method": HealthMethod.POSTGRES,
                "health_url": f"localhost:{project.postgres_port}",
                "port": project.postgres_port,
                "health_interval": 30,
                "health_timeout": 5,
                "health_threshold": 500,
                "is_required": True,
            },
            {
                "name": "redis",
                "service_type": ServiceType.CACHE,
                "health_method": HealthMethod.REDIS,
                "health_url": f"localhost:{project.redis_port}",
                "port": project.redis_port,
                "health_interval": 30,
                "health_timeout": 5,
                "health_threshold": 100,
                "is_required": True,
            },
            {
                "name": "backend",
                "service_type": ServiceType.API,
                "health_method": HealthMethod.HTTP,
                "health_url": f"http://localhost:{project.backend_port}/health",
                "port": project.backend_port,
                "health_interval": 15,
                "health_timeout": 10,
                "health_threshold": 1000,
                "is_required": True,
                "external_url": f"http://localhost:{project.backend_port}",
            },
            {
                "name": "frontend",
                "service_type": ServiceType.WEB,
                "health_method": HealthMethod.HTTP,
                "health_url": f"http://localhost:{project.frontend_port}/",
                "port": project.frontend_port,
                "health_interval": 30,
                "health_timeout": 10,
                "health_threshold": 2000,
                "is_required": True,
                "external_url": f"http://localhost:{project.frontend_port}",
            },
        ]

        # Check if we have a NATS service running (port 4222)
        if self._check_port_available(4222)[0] == False:  # Port is in use (NATS is running)
            services_config.append({
                "name": "nats",
                "service_type": ServiceType.QUEUE,
                "health_method": HealthMethod.HTTP,
                "health_url": "http://localhost:8222/healthz",
                "port": 4222,
                "health_interval": 30,
                "health_timeout": 5,
                "health_threshold": 100,
                "is_required": False,
            })

        # Delete existing services for this project (if any)
        from sqlalchemy import delete
        await self.db.execute(
            delete(Service).where(Service.project_id == project.id)
        )

        # Create service records
        for config in services_config:
            service = Service(
                project_id=project.id,
                name=config["name"],
                service_type=config["service_type"],
                health_method=config["health_method"],
                health_url=config["health_url"],
                port=config["port"],
                health_interval=config.get("health_interval", 30),
                health_timeout=config.get("health_timeout", 5),
                health_threshold=config.get("health_threshold", 1000),
                health_retries=config.get("health_retries", 3),
                is_required=config.get("is_required", True),
                alerts_enabled=True,
                health_status=HealthStatus.UNKNOWN,
                external_url=config.get("external_url"),
                started_at=datetime.now(timezone.utc),
            )
            self.db.add(service)

        await self.db.commit()
        logger.info(f"Registered {len(services_config)} services for project {project.name}")

    async def _unregister_services(self, project: Project):
        """Remove service registrations when project stops.

        Args:
            project: Project that was stopped
        """
        logger.info(f"Unregistering services for project {project.name}")

        # Delete all services for this project
        result = await self.db.execute(
            select(Service).where(Service.project_id == project.id)
        )
        services = result.scalars().all()

        for service in services:
            await self.db.delete(service)

        await self.db.commit()
        logger.info(f"Unregistered {len(services)} services for project {project.name}")
