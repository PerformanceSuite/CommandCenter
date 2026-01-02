"""
NATS-to-WebSocket Bridge for real-time graph event forwarding.

This module bridges NATS events published by the graph service to WebSocket
subscribers, enabling real-time updates for connected clients.

NATS Subject Pattern: graph.{entity}.{event_type}
WebSocket Topic Pattern: {entity}:{event_type}:{project_id}

Examples:
    graph.node.created -> entity:created:{project_id}
    graph.node.updated -> entity:updated:{project_id}
    graph.edge.created -> edge:created:{project_id}
    graph.invalidated  -> graph:invalidated:{project_id}
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from app.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)


class NATSBridge:
    """Bridge NATS events to WebSocket subscriptions.

    Converts NATS subjects to WebSocket topics and forwards messages
    to subscribed clients. Supports multi-tenant isolation via project_id
    in the message payload.

    NATS subjects map to WebSocket topics as follows:
        graph.node.created  -> entity:created:{project_id}
        graph.node.updated  -> entity:updated:{project_id}
        graph.node.deleted  -> entity:deleted:{project_id}
        graph.edge.created  -> edge:created:{project_id}
        graph.edge.deleted  -> edge:deleted:{project_id}
        graph.invalidated   -> graph:invalidated:{project_id}

    Attributes:
        manager: The WebSocket ConnectionManager for broadcasting messages.

    Example:
        >>> bridge = NATSBridge(manager)
        >>> await bridge.handle_nats_message(
        ...     "graph.node.updated",
        ...     {"project_id": 123, "node_type": "symbol", "node_id": "symbol:456"}
        ... )
    """

    # Map NATS subjects to WebSocket topic base names
    NATS_TO_WS_TOPIC_MAP: Dict[str, str] = {
        "graph.node.created": "entity:created",
        "graph.node.updated": "entity:updated",
        "graph.node.deleted": "entity:deleted",
        "graph.edge.created": "edge:created",
        "graph.edge.deleted": "edge:deleted",
        "graph.invalidated": "graph:invalidated",
    }

    def __init__(self, manager: "ConnectionManager") -> None:
        """Initialize the NATS bridge.

        Args:
            manager: The WebSocket ConnectionManager instance to use
                for broadcasting messages to subscribers.
        """
        self.manager = manager

    async def handle_nats_message(self, subject: str, data: Dict[str, Any]) -> None:
        """Handle incoming NATS message and forward to WebSocket subscribers.

        Converts the NATS subject to a WebSocket topic based on the mapping,
        extracts the project_id from the payload for multi-tenant isolation,
        and broadcasts the message to all subscribed clients.

        Args:
            subject: NATS subject (e.g., "graph.node.updated")
            data: Message payload containing event data and project_id
        """
        ws_topic = self._nats_subject_to_ws_topic(subject, data)
        if ws_topic:
            await self.manager.broadcast_to_topic(
                ws_topic,
                {
                    "type": "event",
                    "topic": ws_topic,
                    "data": data,
                },
            )
            logger.debug(f"Forwarded NATS {subject} -> WS {ws_topic}")
        else:
            logger.warning(f"No WS mapping for NATS subject: {subject}")

    def _nats_subject_to_ws_topic(self, subject: str, data: Dict[str, Any]) -> Optional[str]:
        """Convert NATS subject to WebSocket topic.

        The topic includes the project_id from the message payload for
        multi-tenant isolation. If no project_id is present, the topic
        is returned without a project qualifier.

        Args:
            subject: NATS subject like "graph.node.updated"
            data: Message payload containing project_id

        Returns:
            WebSocket topic like "entity:updated:123" or None if no mapping
        """
        ws_base = self.NATS_TO_WS_TOPIC_MAP.get(subject)

        if not ws_base:
            return None

        # Extract project_id from payload for multi-tenant isolation
        project_id = data.get("project_id")

        if project_id is not None:
            return f"{ws_base}:{project_id}"

        # Return base topic if no project_id (global events)
        return ws_base
