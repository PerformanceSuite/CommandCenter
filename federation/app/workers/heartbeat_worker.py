import asyncio
import json
import time
from nats.aio.client import Client as NATS
from typing import Optional
from pydantic import ValidationError
from app.database import get_async_session
from app.services.catalog_service import CatalogService
from app.schemas.heartbeat import HeartbeatMessage
from app.config import settings
from app.utils.metrics import (
    track_heartbeat_message,
    track_stale_checker_run,
    track_nats_message,
    update_nats_connection_status,
    update_project_catalog_counts,
    heartbeat_processing_duration,
    stale_checker_duration,
    nats_message_processing_duration,
)
from app.models.project import ProjectStatus
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

        # Update NATS connection status metric
        update_nats_connection_status(True)

        # Subscribe to all presence subjects
        await self.nats.subscribe("hub.presence.*", cb=self._handle_heartbeat)
        logger.info("Subscribed to hub.presence.* subjects")

        # Start stale checker
        self.stale_checker_task = asyncio.create_task(self._stale_checker_loop())

    async def _handle_heartbeat(self, msg):
        """Handle incoming heartbeat message with Pydantic validation."""
        start_time = time.time()
        project_slug = "unknown"

        try:
            # Track NATS message received
            track_nats_message(msg.subject, success=True)

            # Measure NATS message processing time
            with nats_message_processing_duration.labels(subject=msg.subject).time():
                # Parse and validate message with Pydantic
                data = json.loads(msg.data.decode())
                heartbeat = HeartbeatMessage(**data)
                project_slug = heartbeat.project_slug

                # Measure heartbeat processing time
                with heartbeat_processing_duration.labels(project_slug=project_slug).time():
                    # Update heartbeat in database
                    async with get_async_session() as db:
                        service = CatalogService(db)
                        try:
                            await service.update_heartbeat(project_slug)
                            logger.info(f"Updated heartbeat for {project_slug}")
                            track_heartbeat_message(project_slug, success=True)
                        except ValueError as e:
                            # Project not found in catalog - this is expected for new projects
                            logger.warning(
                                f"Heartbeat for unknown project '{project_slug}': {e}. "
                                f"Project must be registered via config/projects.yaml or API first."
                            )
                            track_heartbeat_message(project_slug, success=False, unknown=True)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in heartbeat message: {e}", exc_info=True)
            track_nats_message(msg.subject, success=False)
            track_heartbeat_message(project_slug, success=False)
        except ValidationError as e:
            logger.error(f"Invalid heartbeat message format: {e}", exc_info=True)
            track_nats_message(msg.subject, success=False)
            track_heartbeat_message(project_slug, success=False)
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}", exc_info=True)
            track_nats_message(msg.subject, success=False)
            track_heartbeat_message(project_slug, success=False)

    async def _stale_checker_loop(self):
        """Periodically check for stale projects."""
        logger.info(
            f"Starting stale checker (threshold={settings.HEARTBEAT_STALE_THRESHOLD_SECONDS}s, "
            f"interval={settings.HEARTBEAT_STALE_CHECK_INTERVAL_SECONDS}s)"
        )
        while self.running:
            try:
                # Measure stale checker duration
                with stale_checker_duration.time():
                    async with get_async_session() as db:
                        service = CatalogService(db)
                        stale_count = await service.mark_stale_projects(
                            settings.HEARTBEAT_STALE_THRESHOLD_SECONDS
                        )
                        if stale_count > 0:
                            logger.info(f"Marked {stale_count} projects as offline")

                        # Track stale checker run
                        track_stale_checker_run(success=True, projects_marked_offline=stale_count)

                        # Update project catalog count metrics
                        online_projects = await service.get_projects(status_filter=ProjectStatus.ONLINE)
                        offline_projects = await service.get_projects(status_filter=ProjectStatus.OFFLINE)
                        update_project_catalog_counts(
                            online_count=len(online_projects),
                            offline_count=len(offline_projects)
                        )

            except Exception as e:
                logger.error(f"Error in stale checker: {e}", exc_info=True)
                track_stale_checker_run(success=False)

            await asyncio.sleep(settings.HEARTBEAT_STALE_CHECK_INTERVAL_SECONDS)

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

            # Update NATS connection status metric
            update_nats_connection_status(False)
