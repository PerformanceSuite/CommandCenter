from dagger import dag, function, object_type, Container, Service
from typing import Optional


@object_type
class FederationStack:
    """Dagger module for Federation service orchestration."""

    @function
    async def build_service(self) -> Container:
        """Build federation service container with curl for health checks."""
        return (
            dag.container()
            .from_("python:3.11-slim")
            .with_workdir("/app")
            # Install curl for health checks
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y", "curl"])
            .with_exec(["rm", "-rf", "/var/lib/apt/lists/*"])
            .with_file(
                "/app/requirements.txt",
                dag.host().directory("federation").file("requirements.txt")
            )
            .with_exec(["pip", "install", "--no-cache-dir", "-r", "requirements.txt"])
            .with_directory("/app", dag.host().directory("federation"))
            .with_exposed_port(8001)
        )

    @function
    async def serve(
        self,
        db_url: str,
        nats_url: str = "nats://nats:4222",
        port: int = 8001
    ) -> Service:
        """
        Run federation service as Dagger service with health check validation.

        Args:
            db_url: PostgreSQL connection string for commandcenter_fed
            nats_url: NATS connection URL
            port: Service port (default 8001)

        Returns:
            Running federation service with validated health check
        """
        container = await self.build_service()

        # Build service container with environment
        service_container = (
            container
            .with_env_variable("DATABASE_URL", db_url)
            .with_env_variable("NATS_URL", nats_url)
            .with_env_variable("LOG_LEVEL", "info")
            .with_exec([
                "uvicorn", "app.main:app",
                "--host", "0.0.0.0",
                f"--port", str(port)
            ])
        )

        # Convert to service and validate health check
        service = service_container.as_service()

        # Wait for service to be ready by checking health endpoint
        # This validates the service started successfully before returning
        health_check = await (
            service_container
            .with_service_binding("federation", service)
            .with_exec([
                "curl",
                "-f",
                "-s",
                "--retry", "10",
                "--retry-delay", "1",
                "--retry-all-errors",
                f"http://federation:{port}/health"
            ])
            .stdout()
        )

        # If we got here, health check passed
        return service

    @function
    async def run_migrations(self, db_url: str) -> str:
        """
        Run Alembic migrations for federation database.

        Args:
            db_url: PostgreSQL connection string for commandcenter_fed

        Returns:
            Migration output
        """
        container = await self.build_service()

        # Convert asyncpg URL to psycopg2 for Alembic
        sync_db_url = db_url.replace("+asyncpg", "")

        return await (
            container
            .with_env_variable("DATABASE_URL", sync_db_url)
            .with_exec(["alembic", "upgrade", "head"])
            .stdout()
        )

    @function
    async def test(self, db_url: str) -> str:
        """
        Run federation service tests.

        Args:
            db_url: Test database connection string

        Returns:
            Test output
        """
        container = await self.build_service()

        return await (
            container
            .with_env_variable("DATABASE_URL", db_url)
            .with_exec(["pytest", "tests/", "-v", "--tb=short"])
            .stdout()
        )
