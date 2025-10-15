"""
Orchestration service - Start/stop CommandCenter instances via docker-compose
"""

import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime

import yaml
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Project

logger = logging.getLogger(__name__)


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

            # Create a temporary compose file with absolute host paths
            # Read and validate docker-compose.yml
            with open(compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)

            if not isinstance(compose_config, dict):
                raise ValueError(f"Invalid docker-compose.yml: expected dict, got {type(compose_config)}")

            # Replace relative volume paths with absolute host paths
            # Only convert relative bind mounts (./path), not named volumes
            volumes_converted = 0
            for service_name, service_config in compose_config.get('services', {}).items():
                if 'volumes' in service_config:
                    new_volumes = []
                    for volume in service_config['volumes']:
                        if isinstance(volume, str) and ':' in volume:
                            source, target_part = volume.split(':', 1)
                            # Only convert relative bind mounts, skip named volumes and absolute paths
                            if source.startswith('./'):
                                source = os.path.join(host_cc_path, source[2:])
                                volumes_converted += 1
                                logger.debug(f"Converted relative volume path for {service_name}: {volume} -> {source}:{target_part}")
                                new_volumes.append(f"{source}:{target_part}")
                            else:
                                # Keep named volumes, absolute paths, and other formats as-is
                                new_volumes.append(volume)
                        else:
                            # Keep dict-format volumes and other types as-is
                            new_volumes.append(volume)
                    service_config['volumes'] = new_volumes

            logger.info(f"Converted {volumes_converted} relative volume paths to absolute paths")

            # Write temporary compose file with secure permissions
            temp_compose_path = None
            try:
                temp_compose = tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.yml',
                    delete=False,
                    dir=project.cc_path,
                    prefix='.compose-',
                    encoding='utf-8'
                )
                yaml.dump(compose_config, temp_compose, default_flow_style=False)
                temp_compose_path = temp_compose.name
                temp_compose.close()

                # Set secure permissions (owner read/write only)
                os.chmod(temp_compose_path, 0o600)

                # Set environment for docker-compose
                env = os.environ.copy()

                # Run docker-compose with temporary file
                env_file = os.path.join(project.cc_path, ".env.docker")
                result = subprocess.run(
                    ["docker-compose", "-f", temp_compose_path, "--env-file", env_file, "up", "-d"] + self.ESSENTIAL_SERVICES,
                    cwd=project.cc_path,
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minute timeout
                    env=env,
                )

            finally:
                # Clean up temporary file
                if temp_compose_path and os.path.exists(temp_compose_path):
                    try:
                        os.unlink(temp_compose_path)
                        logger.debug(f"Cleaned up temporary compose file: {temp_compose_path}")
                    except OSError as e:
                        logger.warning(f"Failed to cleanup temp compose file {temp_compose_path}: {e}")

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

            # Run docker-compose down with explicit file path
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "down"],
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
                ["docker-compose", "-f", compose_file, "ps", "--format", "json"],
                cwd=project.cc_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Parse container status
            containers = []
            if result.returncode == 0 and result.stdout:
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
                ["docker-compose", "-f", compose_file, "logs", "--tail", str(tail)],
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
