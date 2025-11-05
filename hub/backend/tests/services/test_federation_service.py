"""Tests for FederationService - Hub discovery and metrics publishing."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.services.federation_service import FederationService
from app.models import Base
from app.models.hub_registry import HubRegistry
from app.models.project import Project


@pytest_asyncio.fixture
async def db_session():
    """Create test database session with federation tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def mock_nats_bridge():
    """Create mock NATS Bridge."""
    bridge = AsyncMock()
    bridge.publish_internal_to_nats = AsyncMock()
    bridge.subscribe_nats_to_internal = AsyncMock()
    return bridge


@pytest.mark.asyncio
class TestFederationService:
    """Test suite for FederationService."""

    async def test_service_initialization(self, db_session, mock_nats_bridge):
        """Test FederationService initializes with correct attributes."""
        service = FederationService(db_session=db_session, nats_bridge=mock_nats_bridge)

        assert service.db_session == db_session
        assert service.nats_bridge == mock_nats_bridge
        assert service.hub_id.startswith("hub-")
        assert service.hub_name is not None
        assert service.version is not None
        assert service.start_time is not None

    async def test_start_subscribes_to_presence(self, db_session, mock_nats_bridge):
        """Test start() subscribes to hub.global.presence."""
        service = FederationService(db_session=db_session, nats_bridge=mock_nats_bridge)

        await service.start()

        # Verify subscription
        mock_nats_bridge.subscribe_nats_to_internal.assert_called_once()
        call_args = mock_nats_bridge.subscribe_nats_to_internal.call_args
        assert call_args[1]["subject"] == "hub.global.presence"
        assert callable(call_args[1]["handler"])

        # Cleanup
        await service.stop()

    async def test_publish_presence(self, db_session, mock_nats_bridge):
        """Test _publish_presence() publishes correct payload."""
        service = FederationService(db_session=db_session, nats_bridge=mock_nats_bridge)

        await service._publish_presence()

        # Verify NATS publish called
        mock_nats_bridge.publish_internal_to_nats.assert_called_once()
        call_args = mock_nats_bridge.publish_internal_to_nats.call_args
        assert call_args[1]["topic"] == "hub.global.presence"

        payload = call_args[1]["payload"]
        assert payload["hub_id"] == service.hub_id
        assert payload["name"] == service.hub_name
        assert payload["version"] == service.version
        assert "hostname" in payload
        assert "project_path" in payload
        assert "timestamp" in payload

    async def test_handle_presence_creates_new_hub(self, db_session, mock_nats_bridge):
        """Test _handle_presence_announcement() creates new Hub entry."""
        service = FederationService(db_session=db_session, nats_bridge=mock_nats_bridge)

        event_data = {
            "hub_id": "hub-other123",
            "name": "Other Hub",
            "version": "1.0.0",
            "hostname": "other-machine",
            "project_path": "/path/to/project"
        }

        await service._handle_presence_announcement(event_data)

        # Verify Hub registered
        from sqlalchemy import select
        stmt = select(HubRegistry).filter_by(id="hub-other123")
        result = await db_session.execute(stmt)
        hub = result.scalar_one_or_none()

        assert hub is not None
        assert hub.id == "hub-other123"
        assert hub.name == "Other Hub"
        assert hub.version == "1.0.0"
        assert hub.hostname == "other-machine"
        assert hub.project_path == "/path/to/project"
        assert hub.first_seen is not None
        assert hub.last_seen is not None

    async def test_handle_presence_updates_existing_hub(self, db_session, mock_nats_bridge):
        """Test _handle_presence_announcement() updates existing Hub."""
        service = FederationService(db_session=db_session, nats_bridge=mock_nats_bridge)

        # Create existing Hub
        existing_hub = HubRegistry(
            id="hub-existing",
            name="Old Name",
            version="0.9.0",
            first_seen=datetime.utcnow() - timedelta(hours=1),
            last_seen=datetime.utcnow() - timedelta(minutes=10)
        )
        db_session.add(existing_hub)
        await db_session.commit()

        old_last_seen = existing_hub.last_seen

        # Handle presence update
        event_data = {
            "hub_id": "hub-existing",
            "name": "Updated Name",
            "version": "1.0.0",
            "hostname": "new-hostname",
            "project_path": "/new/path"
        }

        await service._handle_presence_announcement(event_data)

        # Verify Hub updated
        from sqlalchemy import select
        stmt = select(HubRegistry).filter_by(id="hub-existing")
        result = await db_session.execute(stmt)
        hub = result.scalar_one_or_none()

        assert hub is not None
        assert hub.name == "Updated Name"
        assert hub.version == "1.0.0"
        assert hub.hostname == "new-hostname"
        assert hub.project_path == "/new/path"
        assert hub.last_seen > old_last_seen

    async def test_handle_presence_ignores_self(self, db_session, mock_nats_bridge):
        """Test _handle_presence_announcement() ignores self-announcements."""
        service = FederationService(db_session=db_session, nats_bridge=mock_nats_bridge)

        event_data = {
            "hub_id": service.hub_id,  # Same as this Hub
            "name": "Self Hub",
            "version": "1.0.0"
        }

        await service._handle_presence_announcement(event_data)

        # Verify no Hub registered
        from sqlalchemy import select
        stmt = select(HubRegistry).filter_by(id=service.hub_id)
        result = await db_session.execute(stmt)
        hub = result.scalar_one_or_none()

        assert hub is None

    async def test_publish_metrics(self, db_session, mock_nats_bridge):
        """Test _publish_metrics() publishes correct metrics."""
        service = FederationService(db_session=db_session, nats_bridge=mock_nats_bridge)

        # Create test projects
        project1 = Project(
            name="Project 1",
            slug="project-1",
            path="/path/to/project1",
            backend_port=8000,
            frontend_port=3000,
            postgres_port=5432,
            redis_port=6379
        )
        project2 = Project(
            name="Project 2",
            slug="project-2",
            path="/path/to/project2",
            backend_port=8001,
            frontend_port=3001,
            postgres_port=5433,
            redis_port=6380
        )
        db_session.add(project1)
        db_session.add(project2)
        await db_session.commit()

        await service._publish_metrics()

        # Verify NATS publish called
        mock_nats_bridge.publish_internal_to_nats.assert_called_once()
        call_args = mock_nats_bridge.publish_internal_to_nats.call_args
        assert call_args[1]["topic"] == f"hub.global.metrics.{service.hub_id}"

        payload = call_args[1]["payload"]
        assert payload["hub_id"] == service.hub_id
        assert payload["project_count"] == 2
        assert payload["service_count"] == 0  # Phase 5 doesn't count services yet
        assert payload["uptime_seconds"] >= 0
        assert "timestamp" in payload

    async def test_prune_stale_hubs(self, db_session, mock_nats_bridge):
        """Test _prune_stale_hubs() removes old Hubs."""
        service = FederationService(db_session=db_session, nats_bridge=mock_nats_bridge)

        # Create stale Hub (last seen 60s ago)
        stale_hub = HubRegistry(
            id="hub-stale",
            name="Stale Hub",
            version="1.0.0",
            first_seen=datetime.utcnow() - timedelta(minutes=5),
            last_seen=datetime.utcnow() - timedelta(seconds=60)
        )
        db_session.add(stale_hub)

        # Create active Hub (last seen 10s ago)
        active_hub = HubRegistry(
            id="hub-active",
            name="Active Hub",
            version="1.0.0",
            first_seen=datetime.utcnow() - timedelta(minutes=1),
            last_seen=datetime.utcnow() - timedelta(seconds=10)
        )
        db_session.add(active_hub)
        await db_session.commit()

        await service._prune_stale_hubs()

        # Verify stale Hub pruned, active Hub remains
        from sqlalchemy import select
        stmt_stale = select(HubRegistry).filter_by(id="hub-stale")
        stmt_active = select(HubRegistry).filter_by(id="hub-active")

        result_stale = await db_session.execute(stmt_stale)
        result_active = await db_session.execute(stmt_active)

        assert result_stale.scalar_one_or_none() is None
        assert result_active.scalar_one_or_none() is not None

    async def test_prune_handles_empty_registry(self, db_session, mock_nats_bridge):
        """Test _prune_stale_hubs() handles empty registry gracefully."""
        service = FederationService(db_session=db_session, nats_bridge=mock_nats_bridge)

        # Should not raise exception
        await service._prune_stale_hubs()

    async def test_stop_cancels_tasks(self, db_session, mock_nats_bridge):
        """Test stop() cancels background tasks."""
        service = FederationService(db_session=db_session, nats_bridge=mock_nats_bridge)

        await service.start()

        # Verify tasks started
        assert service._heartbeat_task is not None
        assert service._metrics_task is not None
        assert service._pruning_task is not None

        await service.stop()

        # Verify tasks cancelled
        assert service._heartbeat_task.cancelled()
        assert service._metrics_task.cancelled()
        assert service._pruning_task.cancelled()


@pytest.mark.asyncio
class TestHubIDGeneration:
    """Test Hub ID generation function."""

    def test_hub_id_format(self):
        """Test Hub ID has correct format."""
        from app.config import generate_hub_id

        hub_id = generate_hub_id()
        assert hub_id.startswith("hub-")
        assert len(hub_id) == 16  # "hub-" + 12 chars

    def test_hub_id_stability(self):
        """Test Hub ID is stable across calls."""
        from app.config import generate_hub_id

        id1 = generate_hub_id()
        id2 = generate_hub_id()
        assert id1 == id2

    @patch('app.config.socket.gethostname')
    @patch('app.config.Path.cwd')
    def test_hub_id_changes_with_context(self, mock_cwd, mock_hostname):
        """Test Hub ID changes when machine or path changes."""
        from app.config import generate_hub_id

        # First context
        mock_hostname.return_value = "machine1"
        mock_cwd.return_value.resolve.return_value = "/path/to/project1"
        id1 = generate_hub_id()

        # Second context (different machine)
        mock_hostname.return_value = "machine2"
        mock_cwd.return_value.resolve.return_value = "/path/to/project1"
        id2 = generate_hub_id()

        assert id1 != id2

        # Third context (different path)
        mock_hostname.return_value = "machine1"
        mock_cwd.return_value.resolve.return_value = "/path/to/project2"
        id3 = generate_hub_id()

        assert id1 != id3
