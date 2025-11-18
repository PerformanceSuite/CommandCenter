"""
NATS Client for CommandCenter Backend (Phase 7)

Provides simple NATS connectivity for event-driven architecture.
Uses similar pattern to Hub's NATSBridge but simplified for single-tenant backend.
"""

import json
import logging
from typing import Callable, Optional
from uuid import UUID

import nats
from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)


class NATSClient:
    """Simple NATS client for CommandCenter backend.

    Handles:
    - Publishing events to NATS subjects
    - Subscribing to NATS events with async handlers
    - Connection lifecycle management

    Subject Namespace:
        graph.indexed.{project_id}        # Code indexing completion
        graph.symbol.added                # New symbol indexed
        graph.task.created                # Task created
        graph.updated.{project_id}        # Any graph mutation
        audit.requested.{kind}            # Audit request
        audit.result.{kind}               # Audit result
    """

    def __init__(self, nats_url: str):
        """Initialize NATS client.

        Args:
            nats_url: NATS server URL (e.g., 'nats://localhost:4222')
        """
        self.nats_url = nats_url
        self.nc: Optional[NATS] = None
        self._subscriptions: list = []

    async def connect(self) -> None:
        """Connect to NATS server."""
        try:
            self.nc = await nats.connect(self.nats_url)
            logger.info(f"NATSClient connected to {self.nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from NATS server and cleanup subscriptions."""
        # Unsubscribe from all active subscriptions
        for sub in self._subscriptions:
            try:
                await sub.unsubscribe()
            except Exception as e:
                logger.warning(f"Error unsubscribing: {e}")

        self._subscriptions.clear()

        if self.nc:
            await self.nc.close()
            logger.info("NATSClient disconnected")

    async def publish(
        self, subject: str, payload: dict, correlation_id: Optional[UUID] = None
    ) -> None:
        """Publish event to NATS.

        Args:
            subject: NATS subject (e.g., 'audit.requested.codeReview')
            payload: Event data as dictionary
            correlation_id: Optional request correlation UUID

        Raises:
            RuntimeError: If not connected to NATS
        """
        if not self.nc:
            raise RuntimeError("Not connected to NATS. Call connect() first.")

        # Build message
        message = json.dumps(
            {
                "payload": payload,
                "correlation_id": str(correlation_id) if correlation_id else None,
            }
        )

        # Add correlation header if provided
        headers = {}
        if correlation_id:
            headers["Correlation-ID"] = str(correlation_id)

        # Publish to NATS
        try:
            await self.nc.publish(subject, message.encode(), headers=headers)
            logger.debug(f"Published to NATS: {subject}")
        except Exception as e:
            logger.error(f"Failed to publish to NATS subject {subject}: {e}")
            raise

    async def subscribe(self, subject_filter: str, handler: Callable) -> None:
        """Subscribe to NATS events with async handler.

        Args:
            subject_filter: NATS subject pattern (supports wildcards: *, >)
            handler: Async function called with (subject, data) on each message

        Raises:
            RuntimeError: If not connected to NATS

        Example:
            async def handle_audit_results(subject: str, data: dict):
                print(f"Audit result: {subject} -> {data}")

            await nats_client.subscribe("audit.result.*", handle_audit_results)
        """
        if not self.nc:
            raise RuntimeError("Not connected to NATS. Call connect() first.")

        async def message_handler(msg):
            try:
                data = json.loads(msg.data.decode())

                # Call handler with subject and payload
                await handler(msg.subject, data.get("payload", data))

                logger.debug(f"Handled NATS event: {msg.subject}")
            except Exception as e:
                logger.error(f"Error in NATS message handler for {msg.subject}: {e}")

        # Subscribe to NATS
        sub = await self.nc.subscribe(subject_filter, cb=message_handler)
        self._subscriptions.append(sub)
        logger.info(f"Subscribed to NATS pattern: {subject_filter}")


# Global NATS client instance (initialized on startup)
nats_client: Optional[NATSClient] = None


async def get_nats_client() -> Optional[NATSClient]:
    """Get global NATS client instance.

    Returns:
        NATSClient if connected, None otherwise
    """
    return nats_client


async def init_nats_client(nats_url: str) -> NATSClient:
    """Initialize and connect global NATS client.

    Args:
        nats_url: NATS server URL

    Returns:
        Connected NATSClient instance
    """
    global nats_client
    nats_client = NATSClient(nats_url)
    await nats_client.connect()
    return nats_client


async def shutdown_nats_client() -> None:
    """Shutdown global NATS client."""
    global nats_client
    if nats_client:
        await nats_client.disconnect()
        nats_client = None
