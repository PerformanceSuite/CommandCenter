"""
CommandCenter Stack Definition using Dagger SDK

This module defines the complete CommandCenter infrastructure stack
as code using Dagger's Python SDK. No docker-compose.yml needed.
"""

import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

import dagger

from .retry import retry_with_backoff

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """Resource limits for CommandCenter containers"""
    postgres_cpu: float = 1.0
    postgres_memory_mb: int = 2048
    redis_cpu: float = 0.5
    redis_memory_mb: int = 512
    backend_cpu: float = 1.0
    backend_memory_mb: int = 1024
    frontend_cpu: float = 0.5
    frontend_memory_mb: int = 512


@dataclass
class CommandCenterConfig:
    """Configuration for a CommandCenter instance"""
    project_name: str
    project_path: str
    backend_port: int
    frontend_port: int
    postgres_port: int
    redis_port: int
    db_password: str
    secret_key: str
    resource_limits: ResourceLimits = None

    def __post_init__(self):
        """Set defaults after initialization"""
        if self.resource_limits is None:
            self.resource_limits = ResourceLimits()


class CommandCenterStack:
    """Defines and manages CommandCenter container stack using Dagger"""

    VALID_SERVICES = ["postgres", "redis", "backend", "frontend"]

    # User IDs for non-root execution
    POSTGRES_USER_ID = 999
    REDIS_USER_ID = 999
    APP_USER_ID = 1000

    def __init__(self, config: CommandCenterConfig):
        self.config = config
        self._connection: Optional[dagger.Connection] = None
        self.client = None  # Will be set to Client in __aenter__
        self._service_containers: dict[str, dagger.Container] = {}  # Track containers

    async def __aenter__(self):
        """Initialize Dagger client"""
        self._connection = dagger.Connection(dagger.Config())
        self.client = await self._connection.__aenter__()  # Get Client from Connection
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Dagger client"""
        if self._connection:
            await self._connection.__aexit__(exc_type, exc_val, exc_tb)

    async def build_postgres(self) -> dagger.Container:
        """Build PostgreSQL container with resource limits and security"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        limits = self.config.resource_limits

        return (
            self.client.container()
            .from_("postgres:15-alpine")
            .with_user(str(self.POSTGRES_USER_ID))  # Run as non-root
            .with_env_variable("POSTGRES_USER", "commandcenter")
            .with_env_variable("POSTGRES_PASSWORD", self.config.db_password)
            .with_env_variable("POSTGRES_DB", "commandcenter")
            .with_exposed_port(5432)
            .with_resource_limit("cpu", str(limits.postgres_cpu))
            .with_resource_limit("memory", f"{limits.postgres_memory_mb}m")
        )

    async def build_redis(self) -> dagger.Container:
        """Build Redis container with resource limits and security"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        limits = self.config.resource_limits

        return (
            self.client.container()
            .from_("redis:7-alpine")
            .with_user(str(self.REDIS_USER_ID))  # Run as non-root
            .with_exposed_port(6379)
            .with_resource_limit("cpu", str(limits.redis_cpu))
            .with_resource_limit("memory", f"{limits.redis_memory_mb}m")
        )

    async def build_backend(self, postgres_host: str, redis_host: str) -> dagger.Container:
        """Build CommandCenter backend container with resource limits and security"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        limits = self.config.resource_limits

        # Mount project directory as read-only volume
        project_dir = self.client.host().directory(self.config.project_path)

        return (
            self.client.container()
            .from_("python:3.11-slim")
            .with_user(str(self.APP_USER_ID))  # Run as non-root
            # Install CommandCenter backend dependencies
            .with_exec(["pip", "install", "fastapi", "uvicorn[standard]",
                       "sqlalchemy", "asyncpg", "redis", "langchain",
                       "langchain-community", "chromadb", "sentence-transformers"])
            # Mount project directory
            .with_mounted_directory("/workspace", project_dir)
            .with_workdir("/workspace")
            # Set environment variables
            .with_env_variable("DATABASE_URL",
                             f"postgresql://commandcenter:{self.config.db_password}@{postgres_host}:5432/commandcenter")
            .with_env_variable("REDIS_URL", f"redis://{redis_host}:6379")
            .with_env_variable("SECRET_KEY", self.config.secret_key)
            .with_env_variable("PROJECT_NAME", self.config.project_name)
            # Run backend
            .with_exec(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
            .with_exposed_port(8000)
            .with_resource_limit("cpu", str(limits.backend_cpu))
            .with_resource_limit("memory", f"{limits.backend_memory_mb}m")
        )

    async def build_frontend(self, backend_url: str) -> dagger.Container:
        """Build CommandCenter frontend container with resource limits and security"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        limits = self.config.resource_limits

        return (
            self.client.container()
            .from_("node:18-alpine")
            .with_user(str(self.APP_USER_ID))  # Run as non-root
            # Install CommandCenter frontend dependencies
            .with_exec(["npm", "install", "-g", "vite", "react", "react-dom"])
            # Set environment variables
            .with_env_variable("VITE_API_BASE_URL", backend_url)
            .with_env_variable("VITE_PROJECT_NAME", self.config.project_name)
            # Run frontend dev server
            .with_exec(["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"])
            .with_exposed_port(3000)
            .with_resource_limit("cpu", str(limits.frontend_cpu))
            .with_resource_limit("memory", f"{limits.frontend_memory_mb}m")
        )

    @retry_with_backoff(max_attempts=3, initial_delay=2.0)
    async def start(self) -> dict:
        """Start all CommandCenter containers"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        try:
            logger.info(f"Starting CommandCenter stack for project: {self.config.project_name}")

            # Build containers
            postgres = await self.build_postgres()
            redis = await self.build_redis()
            backend = await self.build_backend("postgres", "redis")
            frontend = await self.build_frontend(f"http://backend:{self.config.backend_port}")

            # Store in registry for later access (logs, health checks)
            self._service_containers["postgres"] = postgres
            self._service_containers["redis"] = redis
            self._service_containers["backend"] = backend
            self._service_containers["frontend"] = frontend

            # Start as services
            postgres_svc = postgres.as_service()
            redis_svc = redis.as_service()
            backend_svc = backend.as_service()
            frontend_svc = frontend.as_service()

            logger.info(f"CommandCenter stack started successfully for {self.config.project_name}")

            return {
                "success": True,
                "message": "Stack started successfully",
                "services": {
                    "postgres": {"port": self.config.postgres_port},
                    "redis": {"port": self.config.redis_port},
                    "backend": {"port": self.config.backend_port},
                    "frontend": {"port": self.config.frontend_port},
                }
            }

        except Exception as e:
            logger.error(f"Failed to start CommandCenter stack: {e}")
            raise

    async def get_logs(
        self,
        service_name: str,
        tail: int = 100,
        follow: bool = False
    ) -> str:
        """
        Retrieve logs from a specific service container.

        Args:
            service_name: Name of service (postgres, redis, backend, frontend)
            tail: Number of lines to retrieve from end of logs
            follow: If True, stream logs continuously (not implemented yet)

        Returns:
            String containing log lines

        Raises:
            ValueError: If service_name is invalid
        """
        if service_name not in self.VALID_SERVICES:
            raise ValueError(f"Invalid service name: {service_name}. "
                           f"Must be one of {self.VALID_SERVICES}")

        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        # Get the container for this service
        container = await self._get_service_container(service_name)

        # Retrieve stdout logs
        logs = await container.stdout()

        # Apply tail limit if specified
        if tail:
            log_lines = logs.split('\n')
            logs = '\n'.join(log_lines[-tail:])

        return logs

    async def _get_service_container(self, service_name: str) -> dagger.Container:
        """Get container for a service from registry"""
        if service_name not in self._service_containers:
            raise RuntimeError(f"Service {service_name} not found in registry. "
                             f"Has start() been called?")
        return self._service_containers[service_name]

    @retry_with_backoff(max_attempts=2, initial_delay=1.0)
    async def check_postgres_health(self) -> dict:
        """
        Check PostgreSQL health using pg_isready.

        Returns:
            Dict with health status
        """
        try:
            container = self._service_containers.get("postgres")
            if not container:
                return {"healthy": False, "service": "postgres", "error": "Container not found"}

            # Execute pg_isready command
            result = await container.with_exec([
                "pg_isready", "-U", "commandcenter"
            ]).stdout()

            healthy = "accepting connections" in result
            return {
                "healthy": healthy,
                "service": "postgres",
                "message": result.strip()
            }
        except Exception as e:
            return {
                "healthy": False,
                "service": "postgres",
                "error": str(e)
            }

    @retry_with_backoff(max_attempts=2, initial_delay=1.0)
    async def check_redis_health(self) -> dict:
        """
        Check Redis health using redis-cli ping.

        Returns:
            Dict with health status
        """
        try:
            container = self._service_containers.get("redis")
            if not container:
                return {"healthy": False, "service": "redis", "error": "Container not found"}

            # Execute redis-cli ping
            result = await container.with_exec([
                "redis-cli", "ping"
            ]).stdout()

            healthy = "PONG" in result
            return {
                "healthy": healthy,
                "service": "redis",
                "message": result.strip()
            }
        except Exception as e:
            return {
                "healthy": False,
                "service": "redis",
                "error": str(e)
            }

    @retry_with_backoff(max_attempts=2, initial_delay=1.0)
    async def check_backend_health(self) -> dict:
        """
        Check backend health via HTTP /health endpoint.

        Returns:
            Dict with health status
        """
        try:
            container = self._service_containers.get("backend")
            if not container:
                return {"healthy": False, "service": "backend", "error": "Container not found"}

            # Execute curl to health endpoint
            result = await container.with_exec([
                "curl", "-f", "http://localhost:8000/health"
            ]).stdout()

            healthy = "ok" in result.lower() or "healthy" in result.lower()
            return {
                "healthy": healthy,
                "service": "backend",
                "message": result.strip()
            }
        except Exception as e:
            return {
                "healthy": False,
                "service": "backend",
                "error": str(e)
            }

    @retry_with_backoff(max_attempts=2, initial_delay=1.0)
    async def check_frontend_health(self) -> dict:
        """
        Check frontend health via HTTP request to root.

        Returns:
            Dict with health status
        """
        try:
            container = self._service_containers.get("frontend")
            if not container:
                return {"healthy": False, "service": "frontend", "error": "Container not found"}

            # Execute curl to root path
            result = await container.with_exec([
                "curl", "-f", "http://localhost:3000/"
            ]).stdout()

            # If curl succeeds (exit 0), consider healthy
            healthy = len(result) > 0
            return {
                "healthy": healthy,
                "service": "frontend",
                "message": "HTTP 200 OK" if healthy else "No response"
            }
        except Exception as e:
            return {
                "healthy": False,
                "service": "frontend",
                "error": str(e)
            }

    async def health_status(self) -> dict:
        """
        Get aggregated health status for all services.

        Returns:
            Dict with overall health and per-service status
        """
        services = {}

        services["postgres"] = await self.check_postgres_health()
        services["redis"] = await self.check_redis_health()
        services["backend"] = await self.check_backend_health()
        services["frontend"] = await self.check_frontend_health()

        overall_healthy = all(svc["healthy"] for svc in services.values())

        return {
            "overall_healthy": overall_healthy,
            "services": services,
            "timestamp": str(datetime.now())
        }

    @retry_with_backoff(max_attempts=3, initial_delay=2.0)
    async def restart_service(self, service_name: str) -> dict:
        """
        Restart a specific service container.

        Args:
            service_name: Name of service to restart (postgres, redis, backend, frontend)

        Returns:
            Dict with restart status

        Raises:
            ValueError: If service_name is invalid
            RuntimeError: If service not found in registry
        """
        if service_name not in self.VALID_SERVICES:
            raise ValueError(f"Invalid service name: {service_name}. "
                           f"Must be one of {self.VALID_SERVICES}")

        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        # Verify service exists in registry
        if service_name not in self._service_containers:
            raise RuntimeError(f"Service {service_name} not found in registry. "
                             f"Has start() been called?")

        logger.info(f"Restarting service: {service_name}")

        # Rebuild the container based on service type
        if service_name == "postgres":
            new_container = await self.build_postgres()
        elif service_name == "redis":
            new_container = await self.build_redis()
        elif service_name == "backend":
            # Backend needs postgres and redis hostnames
            new_container = await self.build_backend("postgres", "redis")
        elif service_name == "frontend":
            # Frontend needs backend URL
            new_container = await self.build_frontend(f"http://backend:{self.config.backend_port}")
        else:
            raise ValueError(f"Unhandled service: {service_name}")

        # Update registry with new container
        self._service_containers[service_name] = new_container

        # Start as service
        _ = new_container.as_service()

        logger.info(f"Service {service_name} restarted successfully")

        return {
            "success": True,
            "service": service_name,
            "message": f"Service {service_name} restarted successfully"
        }

    async def stop(self) -> dict:
        """Stop all CommandCenter containers"""
        # Dagger containers are ephemeral and automatically cleaned up
        logger.info(f"Stopping CommandCenter stack for project: {self.config.project_name}")
        return {
            "success": True,
            "message": "Stack stopped successfully"
        }

    async def status(self) -> dict:
        """Get status of CommandCenter containers"""
        # For now, return placeholder - we'll implement proper health checks
        return {
            "status": "running",
            "health": "healthy",
            "containers": []
        }
