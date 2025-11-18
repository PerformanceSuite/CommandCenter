"""Federation Service for Hub discovery and metrics publishing.

The FederationService manages:
- Presence heartbeats (5s interval)
- Hub discovery via NATS
- Metrics publishing (30s interval)
- Stale Hub pruning (60s interval)
"""
import asyncio
import logging
import socket
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_hub_id, get_hub_name, get_hub_version, get_project_slug, get_mesh_namespace
from app.events.bridge import NATSBridge
from app.models.hub_registry import HubRegistry
from app.models.project import Project

logger = logging.getLogger(__name__)


class FederationService:
    """Manages Hub federation: presence heartbeats, discovery, and metrics.

    The service runs three background tasks:
    1. Heartbeat: Publishes presence every 5s to hub.global.presence
    2. Metrics: Publishes metrics every 30s to hub.global.metrics.<hub_id>
    3. Pruning: Removes stale Hubs every 60s (timeout: 30s)

    Attributes:
        db_session: Async SQLAlchemy session for database operations
        nats_bridge: NATS Bridge for pub/sub operations
        hub_id: Unique Hub identifier
        hub_name: Human-readable Hub name
        version: Hub software version
        start_time: Timestamp when service started
    """

    def __init__(
        self,
        db_session: AsyncSession,
        nats_bridge: NATSBridge
    ):
        """Initialize FederationService.

        Args:
            db_session: Async SQLAlchemy session
            nats_bridge: NATS Bridge for messaging
        """
        self.db_session = db_session
        self.nats_bridge = nats_bridge
        self.hub_id = get_hub_id()
        self.hub_name = get_hub_name()
        self.version = get_hub_version()
        self.project_slug = get_project_slug()
        self.mesh_namespace = get_mesh_namespace()
        self.start_time = datetime.utcnow()

        # Background task handles
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._pruning_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start federation services.

        Subscribes to global presence announcements and starts background tasks:
        - Heartbeat publisher (5s)
        - Metrics publisher (30s)
        - Stale Hub pruner (60s)
        """
        logger.info(f"Starting Federation Service - Hub ID: {self.hub_id}")

        # Subscribe to presence announcements from other Hubs
        await self.nats_bridge.subscribe_nats_to_internal(
            subject="hub.global.presence",
            handler=self._handle_presence_announcement
        )

        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._metrics_task = asyncio.create_task(self._metrics_loop())
        self._pruning_task = asyncio.create_task(self._pruning_loop())

        logger.info("✅ Federation Service started")

    async def stop(self):
        """Stop federation services and cancel background tasks."""
        logger.info("Stopping Federation Service...")

        # Cancel background tasks
        tasks = [
            self._heartbeat_task,
            self._metrics_task,
            self._pruning_task
        ]

        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info("✅ Federation Service stopped")

    # ========================================================================
    # HEARTBEAT & PRESENCE
    # ========================================================================

    async def _heartbeat_loop(self):
        """Publish presence heartbeat every 5 seconds."""
        while True:
            try:
                await self._publish_presence()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                logger.info("Heartbeat loop cancelled")
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Continue despite errors

    async def _publish_presence(self):
        """Publish presence announcement to NATS.

        Publishes to two subjects:
        1. hub.global.presence - For Hub-to-Hub discovery
        2. hub.presence.<project_slug> - For federation catalog heartbeats
        """
        # Hub-to-Hub presence (existing format)
        hub_payload = {
            "hub_id": self.hub_id,
            "name": self.hub_name,
            "version": self.version,
            "hostname": socket.gethostname(),
            "project_path": str(Path.cwd().resolve()),
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.nats_bridge.publish_internal_to_nats(
            topic="hub.global.presence",
            payload=hub_payload
        )

        # Federation catalog heartbeat (new format for Phase 9)
        # Matches federation/app/schemas/heartbeat.py HeartbeatMessage schema
        catalog_payload = {
            "project_slug": self.project_slug,
            "mesh_namespace": self.mesh_namespace,
            "timestamp": datetime.utcnow().isoformat(),
            "hub_url": f"http://localhost:9001"  # TODO: Make configurable
        }

        await self.nats_bridge.publish_internal_to_nats(
            topic=f"hub.presence.{self.project_slug}",
            payload=catalog_payload
        )

        logger.debug(f"Published presence: {self.hub_id} (catalog: {self.project_slug})")

    async def _handle_presence_announcement(self, event_data: Dict[str, Any]):
        """Handle presence announcement from another Hub.

        Args:
            event_data: Event payload containing Hub metadata
        """
        hub_id = event_data.get("hub_id")

        # Don't register self
        if hub_id == self.hub_id:
            logger.debug("Ignoring self-announcement")
            return

        logger.info(f"Discovered Hub: {hub_id} ({event_data.get('name')})")

        # Upsert Hub registry entry
        from sqlalchemy import select

        stmt = select(HubRegistry).filter_by(id=hub_id)
        result = await self.db_session.execute(stmt)
        hub_entry = result.scalar_one_or_none()

        if hub_entry:
            # Update existing entry
            hub_entry.last_seen = datetime.utcnow()
            hub_entry.name = event_data.get("name")
            hub_entry.version = event_data.get("version")
            hub_entry.hostname = event_data.get("hostname")
            hub_entry.project_path = event_data.get("project_path")
        else:
            # Create new entry
            hub_entry = HubRegistry(
                id=hub_id,
                name=event_data.get("name", "Unknown Hub"),
                version=event_data.get("version", "Unknown"),
                hostname=event_data.get("hostname"),
                project_path=event_data.get("project_path"),
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
            self.db_session.add(hub_entry)

        await self.db_session.commit()
        logger.debug(f"Registered Hub: {hub_id}")

    # ========================================================================
    # METRICS PUBLISHING
    # ========================================================================

    async def _metrics_loop(self):
        """Publish metrics every 30 seconds."""
        while True:
            try:
                await self._publish_metrics()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                logger.info("Metrics loop cancelled")
                break
            except Exception as e:
                logger.error(f"Metrics error: {e}", exc_info=True)
                await asyncio.sleep(30)  # Continue despite errors

    async def _publish_metrics(self):
        """Publish minimal metrics to NATS.

        Publishes to: hub.global.metrics.<hub_id>
        Metrics include: project_count, service_count, uptime_seconds
        """
        # Calculate uptime
        uptime_seconds = int((datetime.utcnow() - self.start_time).total_seconds())

        # Get basic counts
        from sqlalchemy import select, func

        # Count projects
        stmt = select(func.count()).select_from(Project)
        result = await self.db_session.execute(stmt)
        project_count = result.scalar() or 0

        # Service count would require querying orchestration state
        # For Phase 5, we'll set it to 0 (can be enhanced in Phase 6)
        service_count = 0

        payload = {
            "hub_id": self.hub_id,
            "project_count": project_count,
            "service_count": service_count,
            "uptime_seconds": uptime_seconds,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Publish to hub-specific metrics subject
        await self.nats_bridge.publish_internal_to_nats(
            topic=f"hub.global.metrics.{self.hub_id}",
            payload=payload
        )

        logger.debug(f"Published metrics: projects={project_count}, uptime={uptime_seconds}s")

    # ========================================================================
    # STALE HUB PRUNING
    # ========================================================================

    async def _pruning_loop(self):
        """Prune stale Hubs every 60 seconds."""
        while True:
            try:
                await self._prune_stale_hubs()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                logger.info("Pruning loop cancelled")
                break
            except Exception as e:
                logger.error(f"Pruning error: {e}", exc_info=True)
                await asyncio.sleep(60)  # Continue despite errors

    async def _prune_stale_hubs(self):
        """Remove Hubs not seen in last 30 seconds.

        Stale threshold: 30 seconds (6x heartbeat interval for safety)
        """
        stale_threshold = datetime.utcnow() - timedelta(seconds=30)

        from sqlalchemy import delete

        stmt = delete(HubRegistry).where(HubRegistry.last_seen < stale_threshold)
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()

        deleted_count = result.rowcount

        if deleted_count > 0:
            logger.info(f"Pruned {deleted_count} stale Hub(s)")
        else:
            logger.debug("No stale Hubs to prune")
