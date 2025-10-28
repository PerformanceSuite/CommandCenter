"""
Test data factories for Hub

Provides factory functions for creating test data objects.
"""

from typing import Optional
from app.models import Project
from app.schemas import ProjectCreate, PortSet


class ProjectFactory:
    """Factory for creating test Project instances"""

    @staticmethod
    def create_project_data(
        name: str = "TestProject",
        path: str = "/tmp/test-project",
    ) -> ProjectCreate:
        """Create ProjectCreate schema for testing"""
        return ProjectCreate(name=name, path=path)

    @staticmethod
    def create_project(
        name: str = "TestProject",
        slug: Optional[str] = None,
        path: str = "/tmp/test-project",
        status: str = "stopped",
        backend_port: int = 8010,
        frontend_port: int = 3010,
        postgres_port: int = 5442,
        redis_port: int = 6389,
        health: str = "unknown",
        is_configured: bool = True,
    ) -> Project:
        """Create Project model instance for testing"""
        if slug is None:
            slug = name.lower().replace(" ", "-")

        return Project(
            name=name,
            slug=slug,
            path=path,
            status=status,
            backend_port=backend_port,
            frontend_port=frontend_port,
            postgres_port=postgres_port,
            redis_port=redis_port,
            health=health,
            is_configured=is_configured,
        )


class PortSetFactory:
    """Factory for creating test PortSet instances"""

    @staticmethod
    def create_port_set(
        backend: int = 8010,
        frontend: int = 3010,
        postgres: int = 5442,
        redis: int = 6389,
    ) -> PortSet:
        """Create PortSet for testing"""
        return PortSet(
            backend=backend, frontend=frontend, postgres=postgres, redis=redis
        )


class CommandCenterConfigFactory:
    """Factory for creating test CommandCenter configurations"""

    @staticmethod
    def create_config(
        project_name: str = "TestProject",
        project_path: str = "/tmp/test-project",
        backend_port: int = 8010,
        frontend_port: int = 3010,
        postgres_port: int = 5442,
        redis_port: int = 6389,
        db_password: str = "test_password",
        secret_key: str = "test_secret_key",
    ):
        """Create CommandCenterConfig for testing (returns dict to avoid import issues)"""
        return {
            "project_name": project_name,
            "project_path": project_path,
            "backend_port": backend_port,
            "frontend_port": frontend_port,
            "postgres_port": postgres_port,
            "redis_port": redis_port,
            "db_password": db_password,
            "secret_key": secret_key,
        }
