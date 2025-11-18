"""
Create test graph data for Phase 7 testing

Populates the database with sample repos, files, symbols, and relationships.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.config import settings  # noqa: E402
from app.models.graph import DependencyType, GraphDependency, GraphFile, GraphRepo  # noqa: E402
from app.models.graph import GraphService as GraphServiceModel  # noqa: E402
from app.models.graph import (  # noqa: E402
    GraphSpecItem,
    GraphSymbol,
    GraphTask,
    HealthStatus,
    ServiceType,
    SpecItemSource,
    SpecItemStatus,
    SymbolKind,
    TaskKind,
)
from app.models.project import Project  # noqa: E402


async def create_test_data():
    """Create test graph data"""

    # Create async engine
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Ensure project 1 exists
            stmt = select(Project).filter(Project.id == 1)
            result = await session.execute(stmt)
            project = result.scalar_one_or_none()

            if not project:
                project = Project(
                    id=1, name="Test Project", description="Test project for Phase 7 graph testing"
                )
                session.add(project)
                await session.commit()
                print("✅ Created test project")

            # Create test repository
            repo = GraphRepo(
                project_id=1,
                provider="github",
                owner="testorg",
                name="testproject",
                full_name="testorg/testproject",
                default_branch="main",
            )
            session.add(repo)
            await session.flush()
            print(f"✅ Created repository: {repo.full_name}")

            # Create test files
            file1 = GraphFile(
                repo_id=repo.id,
                path="src/main.py",
                lang="python",
                hash="abc123",
                size=1500,
                lines=50,
            )
            file2 = GraphFile(
                repo_id=repo.id,
                path="src/utils.py",
                lang="python",
                hash="def456",
                size=800,
                lines=30,
            )
            session.add_all([file1, file2])
            await session.flush()
            print("✅ Created 2 files")

            # Create test symbols
            symbol1 = GraphSymbol(
                file_id=file1.id,
                kind=SymbolKind.FUNCTION,
                name="main",
                qualified_name="src.main.main",
                signature="def main() -> None",
                range_start=10,
                range_end=25,
                exports=True,
            )
            symbol2 = GraphSymbol(
                file_id=file1.id,
                kind=SymbolKind.CLASS,
                name="Application",
                qualified_name="src.main.Application",
                signature="class Application",
                range_start=30,
                range_end=45,
                exports=True,
            )
            symbol3 = GraphSymbol(
                file_id=file2.id,
                kind=SymbolKind.FUNCTION,
                name="helper",
                qualified_name="src.utils.helper",
                signature="def helper(x: int) -> str",
                range_start=5,
                range_end=15,
                exports=True,
            )
            session.add_all([symbol1, symbol2, symbol3])
            await session.flush()
            print("✅ Created 3 symbols")

            # Create test dependencies
            dep1 = GraphDependency(
                from_symbol_id=symbol1.id,
                to_symbol_id=symbol3.id,
                type=DependencyType.CALL,
                weight=1.0,
            )
            dep2 = GraphDependency(
                from_symbol_id=symbol2.id,
                to_symbol_id=symbol3.id,
                type=DependencyType.USES,
                weight=0.8,
            )
            session.add_all([dep1, dep2])
            await session.flush()
            print("✅ Created 2 dependencies")

            # Create test service
            service = GraphServiceModel(
                project_id=1,
                repo_id=repo.id,
                name="test-api",
                type=ServiceType.API,
                endpoint="http://localhost:8000",
                health_url="http://localhost:8000/health",
                status=HealthStatus.UP,
            )
            session.add(service)
            await session.flush()
            print(f"✅ Created service: {service.name}")

            # Create test spec item (TODO comment)
            spec = GraphSpecItem(
                project_id=1,
                source=SpecItemSource.FILE,
                ref="src/main.py:42",
                title="TODO: Add rate limiting",
                description="Implement rate limiting for API endpoints",
                priority=5,
                status=SpecItemStatus.PLANNED,
            )
            session.add(spec)
            await session.flush()
            print(f"✅ Created spec item: {spec.title}")

            # Create test task
            task = GraphTask(
                project_id=1,
                spec_item_id=spec.id,
                title="Implement rate limiting middleware",
                description="Add rate limiting using Redis",
                kind=TaskKind.FEATURE,
                status=SpecItemStatus.PLANNED,
                labels=["backend", "security"],
            )
            session.add(task)
            await session.flush()
            print(f"✅ Created task: {task.title}")

            await session.commit()
            print("\n🎉 Test graph data created successfully!")
            print("\nSummary:")
            print("  - 1 repository (testorg/testproject)")
            print("  - 2 files (main.py, utils.py)")
            print("  - 3 symbols (main, Application, helper)")
            print("  - 2 dependencies (function calls)")
            print("  - 1 service (test-api)")
            print("  - 1 spec item (TODO)")
            print("  - 1 task (rate limiting)")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating test data: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_data())
