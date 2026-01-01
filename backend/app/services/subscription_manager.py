"""Subscription Manager for SSE connections.

Sprint 4: Real-time Subscriptions (Task 6)

Tracks active SSE connections and provides metrics for monitoring.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about an active SSE connection."""

    connection_id: str
    project_id: int
    subjects: list[str]
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    events_sent: int = 0
    last_event_at: Optional[datetime] = None


@dataclass
class SubscriptionMetrics:
    """Aggregated subscription metrics."""

    active_connections: int = 0
    total_connections: int = 0  # All-time count
    total_events_sent: int = 0
    connections_by_project: Dict[int, int] = field(default_factory=dict)


class SubscriptionManager:
    """Manages SSE subscriptions and tracks metrics.

    Thread-safe singleton for tracking all active SSE connections
    across the application.

    Usage:
        manager = get_subscription_manager()

        # On connection
        conn_id = await manager.register(project_id=1, subjects=["graph.*"])

        # On event sent
        await manager.record_event(conn_id)

        # On disconnect
        await manager.unregister(conn_id)

        # Get metrics
        metrics = manager.get_metrics()
    """

    _instance: Optional["SubscriptionManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._connections: Dict[str, ConnectionInfo] = {}
        self._metrics = SubscriptionMetrics()
        self._initialized = True

        logger.info("SubscriptionManager initialized")

    async def register(
        self,
        project_id: int,
        subjects: list[str],
        connection_id: Optional[str] = None,
    ) -> str:
        """Register a new SSE connection.

        Args:
            project_id: Project ID for this connection
            subjects: NATS subject patterns subscribed to
            connection_id: Optional explicit ID (auto-generated if not provided)

        Returns:
            Connection ID for tracking
        """
        conn_id = connection_id or str(uuid.uuid4())

        self._connections[conn_id] = ConnectionInfo(
            connection_id=conn_id,
            project_id=project_id,
            subjects=subjects,
        )

        self._metrics.active_connections += 1
        self._metrics.total_connections += 1

        # Track by project
        self._metrics.connections_by_project[project_id] = (
            self._metrics.connections_by_project.get(project_id, 0) + 1
        )

        logger.info(
            f"SSE connection registered: {conn_id} (project={project_id}, "
            f"active={self._metrics.active_connections})"
        )

        return conn_id

    async def unregister(self, connection_id: str) -> bool:
        """Unregister an SSE connection.

        Args:
            connection_id: Connection ID to unregister

        Returns:
            True if connection was found and removed
        """
        if connection_id not in self._connections:
            return False

        conn_info = self._connections.pop(connection_id)
        self._metrics.active_connections -= 1

        # Update project count
        project_id = conn_info.project_id
        if project_id in self._metrics.connections_by_project:
            self._metrics.connections_by_project[project_id] -= 1
            if self._metrics.connections_by_project[project_id] <= 0:
                del self._metrics.connections_by_project[project_id]

        logger.info(
            f"SSE connection unregistered: {connection_id} "
            f"(project={project_id}, events_sent={conn_info.events_sent}, "
            f"active={self._metrics.active_connections})"
        )

        return True

    async def record_event(self, connection_id: str) -> bool:
        """Record that an event was sent on a connection.

        Args:
            connection_id: Connection ID

        Returns:
            True if connection was found and updated
        """
        if connection_id not in self._connections:
            return False

        conn_info = self._connections[connection_id]
        conn_info.events_sent += 1
        conn_info.last_event_at = datetime.now(timezone.utc)
        self._metrics.total_events_sent += 1

        return True

    def get_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get information about a specific connection."""
        return self._connections.get(connection_id)

    def get_connections_for_project(self, project_id: int) -> list[ConnectionInfo]:
        """Get all connections for a specific project."""
        return [c for c in self._connections.values() if c.project_id == project_id]

    def get_metrics(self) -> SubscriptionMetrics:
        """Get aggregated subscription metrics."""
        return self._metrics

    def get_detailed_metrics(self) -> dict:
        """Get detailed metrics including per-connection info."""
        connections = []
        for conn in self._connections.values():
            duration = datetime.now(timezone.utc) - conn.connected_at
            connections.append(
                {
                    "connection_id": conn.connection_id,
                    "project_id": conn.project_id,
                    "subjects": conn.subjects,
                    "connected_at": conn.connected_at.isoformat(),
                    "duration_seconds": duration.total_seconds(),
                    "events_sent": conn.events_sent,
                    "last_event_at": (
                        conn.last_event_at.isoformat() if conn.last_event_at else None
                    ),
                }
            )

        return {
            "active_connections": self._metrics.active_connections,
            "total_connections": self._metrics.total_connections,
            "total_events_sent": self._metrics.total_events_sent,
            "connections_by_project": dict(self._metrics.connections_by_project),
            "connections": connections,
        }


# Global singleton instance
_subscription_manager: Optional[SubscriptionManager] = None


def get_subscription_manager() -> SubscriptionManager:
    """Get the global SubscriptionManager instance."""
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = SubscriptionManager()
    return _subscription_manager
