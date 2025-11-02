"""Dagger module for building custom Postgres with pgvector."""
from dataclasses import dataclass
from typing import Optional

import dagger


@dataclass
class PostgresConfig:
    """Configuration for custom Postgres with pgvector."""

    db_name: str = "commandcenter"
    db_password: str = "changeme"
    postgres_version: str = "16"
    pgvector_version: str = "v0.7.0"


class PostgresStack:
    """Dagger stack for custom Postgres with pgvector extension."""

    def __init__(self, config: PostgresConfig):
        """Initialize Postgres stack.

        Args:
            config: PostgresConfig instance
        """
        self.config = config
        self._connection: Optional[dagger.Connection] = None
        self.client = None

    async def __aenter__(self):
        """Initialize Dagger client (async context manager entry)."""
        self._connection = dagger.Connection(dagger.Config())
        self.client = await self._connection.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Dagger client (async context manager exit)."""
        if self._connection:
            await self._connection.__aexit__(exc_type, exc_val, exc_tb)

    async def build_postgres(self) -> dagger.Container:
        """Build Postgres container with pgvector extension.

        Returns:
            Dagger container with Postgres + pgvector
        """
        if not self.client:
            raise RuntimeError("Dagger client not initialized. Use async with context manager.")

        return (
            self.client.container()
            .from_(f"postgres:{self.config.postgres_version}")
            # Install build dependencies
            .with_exec(["apt-get", "update"])
            .with_exec(
                [
                    "apt-get",
                    "install",
                    "-y",
                    "build-essential",
                    f"postgresql-server-dev-{self.config.postgres_version}",
                    "git",
                ]
            )
            # Install pgvector
            .with_exec(
                [
                    "git",
                    "clone",
                    "--branch",
                    self.config.pgvector_version,
                    "https://github.com/pgvector/pgvector.git",
                    "/tmp/pgvector",
                ]
            )
            .with_workdir("/tmp/pgvector")
            .with_exec(["make"])
            .with_exec(["make", "install"])
            # Configure Postgres
            .with_env_variable("POSTGRES_DB", self.config.db_name)
            .with_env_variable("POSTGRES_PASSWORD", self.config.db_password)
            .with_exposed_port(5432)
        )
