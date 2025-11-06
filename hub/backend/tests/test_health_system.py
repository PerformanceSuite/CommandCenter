"""Test script for Phase 6: Health & Service Discovery system."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.service import Service, HealthStatus, ServiceType, HealthMethod
from app.models.project import Project
from app.services.health_service import HealthService
from app.database import Base


async def test_health_system():
    """Test the health system components."""
    print("🧪 Testing Phase 6: Health & Service Discovery System")
    print("=" * 60)

    # Create test database (isolated from main database)
    test_db_path = "/tmp/test_health.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    engine = create_async_engine(f"sqlite+aiosqlite:///{test_db_path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        # Create a test project
        print("\n1️⃣ Creating test project...")
        test_project = Project(
            name="test-project",
            slug="test-project",
            path="/tmp/test-project",
            backend_port=8010,
            frontend_port=3010,
            postgres_port=5442,
            redis_port=6389,
            status="running",
            health="unknown"
        )
        db.add(test_project)
        await db.commit()
        await db.refresh(test_project)
        print(f"   ✅ Created project: {test_project.name} (ID: {test_project.id})")

        # Create test services
        print("\n2️⃣ Creating test services...")
        services = [
            Service(
                project_id=test_project.id,
                name="backend",
                service_type=ServiceType.API,
                health_method=HealthMethod.HTTP,
                health_url="http://localhost:8000/health",  # Main hub backend
                port=8000,
                health_interval=30,
                health_timeout=5,
                health_threshold=1000,
                is_required=True,
                health_status=HealthStatus.UNKNOWN
            ),
            Service(
                project_id=test_project.id,
                name="test-tcp",
                service_type=ServiceType.DATABASE,
                health_method=HealthMethod.TCP,
                health_url="localhost:8000",  # Test TCP on hub backend port
                port=8000,
                health_interval=30,
                health_timeout=5,
                health_threshold=100,
                is_required=False,
                health_status=HealthStatus.UNKNOWN
            )
        ]

        for service in services:
            db.add(service)
        await db.commit()
        print(f"   ✅ Created {len(services)} services")

        # Test health checks
        print("\n3️⃣ Testing health checks...")
        health_service = HealthService()

        for service in services:
            print(f"\n   Checking {service.name} ({service.health_method.value})...")
            try:
                health_check = await health_service.check_service_health(service, db)
                await db.commit()

                print(f"   - Status: {health_check.status.value}")
                print(f"   - Latency: {health_check.latency_ms:.2f}ms")
                if health_check.error_message:
                    print(f"   - Error: {health_check.error_message}")
                if health_check.details:
                    print(f"   - Details: {health_check.details}")

            except Exception as e:
                print(f"   ❌ Error checking {service.name}: {e}")

        # Query service health status
        print("\n4️⃣ Querying service health status...")
        result = await db.execute(
            select(Service).where(Service.project_id == test_project.id)
        )
        updated_services = result.scalars().all()

        print("\n   Service Health Summary:")
        print("   " + "-" * 50)
        for service in updated_services:
            status_icon = "🟢" if service.health_status == HealthStatus.UP else \
                         "🟡" if service.health_status == HealthStatus.DEGRADED else \
                         "🔴" if service.health_status == HealthStatus.DOWN else "⚪"
            print(f"   {status_icon} {service.name:15} {service.health_status.value:10} "
                  f"Latency: {service.average_latency or 0:.2f}ms")

        # Test uptime calculation
        print("\n5️⃣ Testing uptime calculation...")
        for service in updated_services:
            if service.total_checks > 0:
                uptime = await health_service.calculate_uptime(
                    service.id, hours=1, db=db
                )
                print(f"   {service.name}: {uptime:.1f}% uptime")

    # Cleanup
    await engine.dispose()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    print("\n" + "=" * 60)
    print("✅ Health system test completed successfully!")


async def test_health_transitions():
    """Test health status transitions."""
    print("\n🔄 Testing Health Status Transitions")
    print("=" * 60)

    health_service = HealthService()

    # Test transition detection
    transitions = [
        (HealthStatus.UNKNOWN, HealthStatus.UP, "unknown_to_up"),
        (HealthStatus.UP, HealthStatus.DEGRADED, "up_to_degraded"),
        (HealthStatus.UP, HealthStatus.DOWN, "up_to_down"),
        (HealthStatus.DEGRADED, HealthStatus.UP, "degraded_to_up"),
        (HealthStatus.DEGRADED, HealthStatus.DOWN, "degraded_to_down"),
        (HealthStatus.DOWN, HealthStatus.UP, "down_to_up"),
    ]

    print("\nTesting status transitions:")
    for old, new, expected in transitions:
        transition = health_service._get_transition(old, new)
        result = "✅" if transition and transition.value == expected else "❌"
        print(f"   {result} {old.value:8} -> {new.value:8} = {expected}")

    print("\n✅ Transition test completed!")


if __name__ == "__main__":
    print("\n🚀 Starting Health System Tests\n")
    asyncio.run(test_health_system())
    asyncio.run(test_health_transitions())
    print("\n🎉 All tests completed!\n")
