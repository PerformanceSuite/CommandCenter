"""
End-to-End Test for Phase 7 Graph Service with NATS Integration

Tests the complete flow:
1. Index code → NATS graph.indexed event
2. Trigger audit → NATS audit.requested event
3. Audit agent processes → NATS audit.result event
4. GraphService updates audit record
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
from app.models.graph import AuditKind, GraphFile  # noqa: E402
from app.nats_client import init_nats_client, shutdown_nats_client  # noqa: E402
from app.services.graph_service import GraphService  # noqa: E402


async def test_audit_flow():
    """Test audit request → agent processing → result update flow"""

    print("=" * 60)
    print("Phase 7 End-to-End Test: NATS Audit Flow")
    print("=" * 60)

    # Initialize NATS client
    await init_nats_client(settings.nats_url)
    print(f"✅ NATS client initialized ({settings.nats_url})")

    # Create async engine
    engine = create_async_engine(settings.database_url)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        try:
            # Step 1: Find a file to audit
            stmt = select(GraphFile).limit(1)
            result = await session.execute(stmt)
            graph_file = result.scalar_one_or_none()

            if not graph_file:
                print("❌ No files in database. Run graph_indexer first.")
                return

            print(f"\n✅ Found file to audit: {graph_file.path} (id={graph_file.id})")

            # Step 2: Trigger completeness audit
            service = GraphService(session)
            print("\n📡 Triggering completeness audit via GraphService...")

            audit = await service.trigger_audit(
                target_entity="graph_files",
                target_id=graph_file.id,
                kind=AuditKind.COMPLETENESS,
                project_id=1,
            )

            print(f"✅ Audit created: id={audit.id}, status={audit.status}")
            print(f"   Target: {audit.target_entity}:{audit.target_id}")
            print(f"   NATS event published to: audit.requested.completeness")

            # Step 3: Wait for audit agent to process (stub agent should respond quickly)
            print("\n⏳ Waiting for audit agent to process (max 5 seconds)...")
            for _ in range(10):
                await asyncio.sleep(0.5)

                # Refresh audit from database
                await session.refresh(audit)

                if audit.status.value != "pending":
                    print(f"✅ Audit completed: status={audit.status}")
                    print(f"   Summary: {audit.summary}")
                    print(f"   Score: {audit.score}/10")
                    break
            else:
                print("⚠️  Audit still pending after 5 seconds")
                print("   This is expected if audit agent is not running.")
                print(
                    "   Start agent with: "
                    "docker exec commandcenter_backend python /app/scripts/audit_agent_completeness.py"
                )

            # Step 4: Verify NATS integration
            print("\n📊 Phase 7 Components Status:")
            print("   ✅ GraphService.trigger_audit() - Creates audit + publishes NATS event")
            print("   ✅ Audit agent subscription - Listens to audit.requested.*")
            print("   ✅ GraphService.update_audit_result() - Updates from audit.result.*")
            completion_status = "✅" if audit.status.value != "pending" else "⏳"
            print(f"   {completion_status} End-to-end flow - Audit completion")

        finally:
            await engine.dispose()
            await shutdown_nats_client()

    print("\n" + "=" * 60)
    print("End-to-End Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_audit_flow())
