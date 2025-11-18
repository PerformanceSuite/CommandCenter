import asyncio
import json
from nats.aio.client import Client as NATS
from typing import Optional
from app.database import get_async_session
from app.services.catalog_service import CatalogService
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class HeartbeatWorker:
    """Worker that subscribes to NATS heartbeats and updates catalog."""

    def __init__(self):
        self.nats: Optional[NATS] = None
        self.running = False
        self.stale_checker_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the heartbeat worker."""
        self.running = True

        # Connect to NATS
        self.nats = NATS()
        await self.nats.connect(settings.NATS_URL)
        logger.info(f"Connected to NATS at {settings.NATS_URL}")

        # Subscribe to all presence subjects
        await self.nats.subscribe("hub.presence.*", cb=self._handle_heartbeat)
        logger.info("Subscribed to hub.presence.* subjects")

        # Start stale checker
        self.stale_checker_task = asyncio.create_task(self._stale_checker_loop())

    async def _handle_heartbeat(self, msg):
        """Handle incoming heartbeat message."""
        try:
            data = json.loads(msg.data.decode())
            project_slug = data.get("project_slug")

            if not project_slug:
                logger.warning(f"Heartbeat missing project_slug: {data}")
                return

            # Update heartbeat in database
            async with get_async_session() as db:
                service = CatalogService(db)
                await service.update_heartbeat(project_slug)
                logger.debug(f"Updated heartbeat for {project_slug}")

        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}", exc_info=True)

    async def _stale_checker_loop(self):
        """Periodically check for stale projects."""
        while self.running:
            try:
                async with get_async_session() as db:
                    service = CatalogService(db)
                    stale_count = await service.mark_stale_projects()
                    if stale_count > 0:
                        logger.info(f"Marked {stale_count} projects as offline")

            except Exception as e:
                logger.error(f"Error in stale checker: {e}", exc_info=True)

            await asyncio.sleep(60)  # Check every 60 seconds

    async def stop(self):
        """Stop the heartbeat worker."""
        self.running = False

        if self.stale_checker_task:
            self.stale_checker_task.cancel()
            try:
                await self.stale_checker_task
            except asyncio.CancelledError:
                pass

        if self.nats:
            await self.nats.close()
            logger.info("Disconnected from NATS")
