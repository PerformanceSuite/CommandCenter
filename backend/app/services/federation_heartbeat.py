import asyncio
import json
import logging
import os
from datetime import datetime, timezone

from app.nats_client import get_nats_client

logger = logging.getLogger(__name__)


class FederationHeartbeat:
    """Publishes heartbeat to federation service via NATS."""

    def __init__(self):
        self.project_slug = os.getenv("PROJECT_SLUG", "commandcenter")
        self.hub_url = os.getenv("HUB_URL", "http://localhost:8000")
        self.mesh_namespace = f"hub.{self.project_slug}"
        self.interval = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
        self.running = False

    async def publish_heartbeat(self):
        """Publish single heartbeat to NATS."""
        nats = await get_nats_client()

        if not nats:
            logger.warning("NATS client not available, skipping heartbeat")
            return

        payload = {
            "project_slug": self.project_slug,
            "hub_url": self.hub_url,
            "mesh_namespace": self.mesh_namespace,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "0.9.0",
        }

        subject = f"hub.presence.{self.project_slug}"
        await nats.publish(subject, json.dumps(payload).encode())
        logger.debug(f"Published heartbeat to {subject}")

    async def start_heartbeat_loop(self):
        """Start periodic heartbeat publishing."""
        self.running = True
        logger.info(f"Starting heartbeat loop (every {self.interval}s)")

        while self.running:
            try:
                await self.publish_heartbeat()
            except Exception as e:
                logger.error(f"Failed to publish heartbeat: {e}")

            await asyncio.sleep(self.interval)

    def stop(self):
        """Stop heartbeat loop."""
        self.running = False
        logger.info("Stopped heartbeat loop")
