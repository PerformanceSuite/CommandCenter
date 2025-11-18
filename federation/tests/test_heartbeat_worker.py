"""
Integration tests for NATS heartbeat worker.

Tests the complete heartbeat flow:
- NATS message publishing from hub
- Worker receiving and processing messages
- Pydantic validation of message format
- Database catalog updates
- Metrics tracking
- Stale project detection
"""
import pytest
import asyncio
import json
from datetime import datetime, timezone
from freezegun import freeze_time
from nats.aio.client import Client as NATS
from app.workers.heartbeat_worker import HeartbeatWorker
from app.services.catalog_service import CatalogService
from app.models.project import ProjectStatus
from app.config import settings


@pytest.mark.asyncio
async def test_heartbeat_worker_receives_valid_message(db_session, nats_server):
    """Test worker receives and processes valid heartbeat message."""
    # Setup: Register project in catalog
    service = CatalogService(db_session)
    await service.register_project(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:3000",
        mesh_namespace="hub.commandcenter",
        tags=["python"]
    )

    # Start heartbeat worker
    worker = HeartbeatWorker()
    await worker.start()

    try:
        # Publish heartbeat message from "hub"
        publisher = NATS()
        await publisher.connect(settings.NATS_URL)

        heartbeat_msg = {
            "project_slug": "commandcenter",
            "mesh_namespace": "hub.commandcenter",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hub_url": "http://localhost:3000"
        }

        await publisher.publish(
            "hub.presence.commandcenter",
            json.dumps(heartbeat_msg).encode()
        )
        await publisher.flush()

        # Wait for worker to process message
        await asyncio.sleep(0.5)

        # Verify: Project should be marked ONLINE
        project = await service.get_project("commandcenter")
        assert project.status == ProjectStatus.ONLINE
        assert project.last_heartbeat_at is not None

        await publisher.close()

    finally:
        await worker.stop()


@pytest.mark.asyncio
async def test_heartbeat_worker_rejects_invalid_json(db_session, nats_server):
    """Test worker handles invalid JSON gracefully."""
    service = CatalogService(db_session)
    await service.register_project(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:3000",
        mesh_namespace="hub.commandcenter",
        tags=[]
    )

    worker = HeartbeatWorker()
    await worker.start()

    try:
        publisher = NATS()
        await publisher.connect(settings.NATS_URL)

        # Send invalid JSON
        await publisher.publish(
            "hub.presence.commandcenter",
            b"invalid-json-{{"
        )
        await publisher.flush()
        await asyncio.sleep(0.5)

        # Verify: Project should still be OFFLINE (heartbeat rejected)
        project = await service.get_project("commandcenter")
        assert project.status == ProjectStatus.OFFLINE

        await publisher.close()

    finally:
        await worker.stop()


@pytest.mark.asyncio
async def test_heartbeat_worker_rejects_invalid_schema(db_session, nats_server):
    """Test worker validates heartbeat schema with Pydantic."""
    service = CatalogService(db_session)
    await service.register_project(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:3000",
        mesh_namespace="hub.commandcenter",
        tags=[]
    )

    worker = HeartbeatWorker()
    await worker.start()

    try:
        publisher = NATS()
        await publisher.connect(settings.NATS_URL)

        # Send message with missing required field (project_slug)
        invalid_msg = {
            "mesh_namespace": "hub.commandcenter",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await publisher.publish(
            "hub.presence.commandcenter",
            json.dumps(invalid_msg).encode()
        )
        await publisher.flush()
        await asyncio.sleep(0.5)

        # Verify: Project should still be OFFLINE
        project = await service.get_project("commandcenter")
        assert project.status == ProjectStatus.OFFLINE

        await publisher.close()

    finally:
        await worker.stop()


@pytest.mark.asyncio
async def test_heartbeat_worker_handles_unknown_project(db_session, nats_server):
    """Test worker handles heartbeat for project not in catalog."""
    worker = HeartbeatWorker()
    await worker.start()

    try:
        publisher = NATS()
        await publisher.connect(settings.NATS_URL)

        # Send heartbeat for unregistered project
        heartbeat_msg = {
            "project_slug": "unknown-project",
            "mesh_namespace": "hub.unknown-project",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hub_url": "http://localhost:3000"
        }

        await publisher.publish(
            "hub.presence.unknown-project",
            json.dumps(heartbeat_msg).encode()
        )
        await publisher.flush()
        await asyncio.sleep(0.5)

        # Verify: No exception thrown, worker continues running
        assert worker.running is True

        await publisher.close()

    finally:
        await worker.stop()


@pytest.mark.asyncio
async def test_heartbeat_worker_validates_namespace_matches_slug(db_session, nats_server):
    """Test Pydantic validator ensures mesh_namespace matches project_slug."""
    service = CatalogService(db_session)
    await service.register_project(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:3000",
        mesh_namespace="hub.commandcenter",
        tags=[]
    )

    worker = HeartbeatWorker()
    await worker.start()

    try:
        publisher = NATS()
        await publisher.connect(settings.NATS_URL)

        # Send heartbeat with mismatched namespace
        invalid_msg = {
            "project_slug": "commandcenter",
            "mesh_namespace": "hub.different-project",  # Mismatch!
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hub_url": "http://localhost:3000"
        }

        await publisher.publish(
            "hub.presence.commandcenter",
            json.dumps(invalid_msg).encode()
        )
        await publisher.flush()
        await asyncio.sleep(0.5)

        # Verify: Validation should fail, project stays OFFLINE
        project = await service.get_project("commandcenter")
        assert project.status == ProjectStatus.OFFLINE

        await publisher.close()

    finally:
        await worker.stop()


@pytest.mark.asyncio
async def test_stale_checker_marks_projects_offline(db_session, nats_server):
    """Test stale checker marks projects offline after threshold."""
    service = CatalogService(db_session)
    await service.register_project(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:3000",
        mesh_namespace="hub.commandcenter",
        tags=[]
    )

    worker = HeartbeatWorker()
    await worker.start()

    try:
        publisher = NATS()
        await publisher.connect(settings.NATS_URL)

        # Send heartbeat to mark project online
        with freeze_time("2025-01-01 12:00:00"):
            heartbeat_msg = {
                "project_slug": "commandcenter",
                "mesh_namespace": "hub.commandcenter",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hub_url": "http://localhost:3000"
            }

            await publisher.publish(
                "hub.presence.commandcenter",
                json.dumps(heartbeat_msg).encode()
            )
            await publisher.flush()
            await asyncio.sleep(0.5)

            project = await service.get_project("commandcenter")
            assert project.status == ProjectStatus.ONLINE

        # Fast-forward time past stale threshold (90s)
        with freeze_time("2025-01-01 12:02:00"):
            # Manually trigger stale checker
            stale_count = await service.mark_stale_projects(
                settings.HEARTBEAT_STALE_THRESHOLD_SECONDS
            )

            assert stale_count == 1

            # Verify project is now OFFLINE
            project = await service.get_project("commandcenter")
            assert project.status == ProjectStatus.OFFLINE

        await publisher.close()

    finally:
        await worker.stop()


@pytest.mark.asyncio
async def test_heartbeat_worker_multiple_projects(db_session, nats_server):
    """Test worker handles heartbeats from multiple projects."""
    service = CatalogService(db_session)

    # Register 3 projects
    for i in range(1, 4):
        await service.register_project(
            slug=f"project{i}",
            name=f"Project {i}",
            hub_url=f"http://localhost:300{i}",
            mesh_namespace=f"hub.project{i}",
            tags=[]
        )

    worker = HeartbeatWorker()
    await worker.start()

    try:
        publisher = NATS()
        await publisher.connect(settings.NATS_URL)

        # Send heartbeat for project1 and project3 (not project2)
        for slug in ["project1", "project3"]:
            heartbeat_msg = {
                "project_slug": slug,
                "mesh_namespace": f"hub.{slug}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hub_url": f"http://localhost:300{slug[-1]}"
            }

            await publisher.publish(
                f"hub.presence.{slug}",
                json.dumps(heartbeat_msg).encode()
            )

        await publisher.flush()
        await asyncio.sleep(0.5)

        # Verify: project1 and project3 ONLINE, project2 OFFLINE
        online_projects = await service.get_projects(status_filter=ProjectStatus.ONLINE)
        offline_projects = await service.get_projects(status_filter=ProjectStatus.OFFLINE)

        assert len(online_projects) == 2
        assert len(offline_projects) == 1

        online_slugs = {p.slug for p in online_projects}
        assert online_slugs == {"project1", "project3"}

        offline_slugs = {p.slug for p in offline_projects}
        assert offline_slugs == {"project2"}

        await publisher.close()

    finally:
        await worker.stop()


@pytest.mark.asyncio
async def test_heartbeat_worker_normalizes_project_slug(db_session, nats_server):
    """Test worker normalizes project_slug to lowercase."""
    service = CatalogService(db_session)
    await service.register_project(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:3000",
        mesh_namespace="hub.commandcenter",
        tags=[]
    )

    worker = HeartbeatWorker()
    await worker.start()

    try:
        publisher = NATS()
        await publisher.connect(settings.NATS_URL)

        # Send heartbeat with uppercase slug
        heartbeat_msg = {
            "project_slug": "CommandCenter",  # Uppercase
            "mesh_namespace": "hub.commandcenter",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hub_url": "http://localhost:3000"
        }

        await publisher.publish(
            "hub.presence.commandcenter",
            json.dumps(heartbeat_msg).encode()
        )
        await publisher.flush()
        await asyncio.sleep(0.5)

        # Verify: Project should be marked ONLINE (slug normalized)
        project = await service.get_project("commandcenter")
        assert project.status == ProjectStatus.ONLINE

        await publisher.close()

    finally:
        await worker.stop()
