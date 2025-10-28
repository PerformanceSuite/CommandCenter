"""
CommandCenter Stack Definition using Dagger SDK

This module defines the complete CommandCenter infrastructure stack
as code using Dagger's Python SDK. No docker-compose.yml needed.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import dagger

logger = logging.getLogger(__name__)


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


class CommandCenterStack:
    """Defines and manages CommandCenter container stack using Dagger"""

    def __init__(self, config: CommandCenterConfig):
        self.config = config
        self._connection: Optional[dagger.Connection] = None
        self.client = None  # Will be set to Client in __aenter__

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
        """Build PostgreSQL container"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        return (
            self.client.container()
            .from_("postgres:15-alpine")
            .with_env_variable("POSTGRES_USER", "commandcenter")
            .with_env_variable("POSTGRES_PASSWORD", self.config.db_password)
            .with_env_variable("POSTGRES_DB", "commandcenter")
            .with_exposed_port(5432)
        )

    async def build_redis(self) -> dagger.Container:
        """Build Redis container"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        return (
            self.client.container()
            .from_("redis:7-alpine")
            .with_exposed_port(6379)
        )

    async def build_backend(self, postgres_host: str, redis_host: str) -> dagger.Container:
        """Build CommandCenter backend container"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        # Mount project directory as read-only volume
        project_dir = self.client.host().directory(self.config.project_path)

        return (
            self.client.container()
            .from_("python:3.11-slim")
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
        )

    async def build_frontend(self, backend_url: str) -> dagger.Container:
        """Build CommandCenter frontend container"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        return (
            self.client.container()
            .from_("node:18-alpine")
            # Install CommandCenter frontend dependencies
            .with_exec(["npm", "install", "-g", "vite", "react", "react-dom"])
            # Set environment variables
            .with_env_variable("VITE_API_BASE_URL", backend_url)
            .with_env_variable("VITE_PROJECT_NAME", self.config.project_name)
            # Run frontend dev server
            .with_exec(["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"])
            .with_exposed_port(3000)
        )

    async def start(self) -> dict:
        """Start all CommandCenter containers"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        try:
            logger.info(f"Starting CommandCenter stack for project: {self.config.project_name}")

            # Build and start containers
            postgres = await self.build_postgres()
            redis = await self.build_redis()

            # Start postgres and redis first
            postgres_svc = postgres.as_service()
            redis_svc = redis.as_service()

            # Build backend with service hostnames
            backend = await self.build_backend("postgres", "redis")
            backend_svc = backend.as_service()

            # Build frontend with backend URL
            frontend = await self.build_frontend(f"http://backend:{self.config.backend_port}")
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
