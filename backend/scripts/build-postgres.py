#!/usr/bin/env python3
"""Build custom Postgres image with pgvector using Dagger."""
import asyncio
import sys
from pathlib import Path

# Add backend to path so we can import dagger_modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dagger_modules.postgres import PostgresStack, PostgresConfig


async def main():
    """Build and export Postgres image with pgvector."""
    print("Building custom Postgres image with pgvector...")

    config = PostgresConfig(
        db_name="commandcenter",
        db_password="postgres",  # Will be overridden by .env
        postgres_version="16",
        pgvector_version="v0.7.0"
    )

    async with PostgresStack(config) as stack:
        print("Building container...")
        container = await stack.build_postgres()

        print("Exporting to Docker...")
        # Export as tar for local Docker import
        await container.export("./postgres-pgvector.tar")

        print("✅ Postgres image built and exported to postgres-pgvector.tar")
        print("\nTo use:")
        print("  docker load < postgres-pgvector.tar")
        print("  docker-compose up -d postgres")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Build failed: {e}", file=sys.stderr)
        sys.exit(1)
