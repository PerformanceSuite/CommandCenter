"""
WebSocket Connection Manager for real-time graph updates.

This module provides the infrastructure for managing WebSocket connections
and topic-based subscriptions for the graph service. Clients can subscribe
to specific topics and receive real-time updates when graph entities change.

Topics follow the pattern: entity:<event_type>:<optional_id>
Examples:
- entity:created - All entity creation events
- entity:updated:proj123 - Updates for a specific entity
- entity:deleted - All deletion events
"""

from typing import Dict, Set
from uuid import uuid4

from fastapi import WebSocket


class ConnectionManager:
    """Manage WebSocket connections and topic subscriptions.

    This class handles:
    - Connection lifecycle (connect/disconnect)
    - Topic-based subscriptions
    - Broadcasting messages to subscribers

    Thread Safety:
        This implementation is not thread-safe. For production use with
        multiple workers, consider using Redis pub/sub for cross-process
        message distribution.
    """

    def __init__(self):
        """Initialize the connection manager."""
        # Map session_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Map session_id -> set of subscribed topics
        self.subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket) -> str:
        """Accept a WebSocket connection and return a session ID.

        Args:
            websocket: The WebSocket connection to accept.

        Returns:
            A unique session ID for this connection.
        """
        await websocket.accept()
        session_id = str(uuid4())
        self.active_connections[session_id] = websocket
        self.subscriptions[session_id] = set()
        await websocket.send_json({"type": "connected", "session_id": session_id})
        return session_id

    def disconnect(self, session_id: str) -> None:
        """Remove a connection and its subscriptions.

        Args:
            session_id: The session ID to disconnect.
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.subscriptions:
            del self.subscriptions[session_id]

    async def subscribe(self, session_id: str, topic: str, websocket: WebSocket) -> None:
        """Subscribe a session to a topic.

        Args:
            session_id: The session ID to subscribe.
            topic: The topic to subscribe to.
            websocket: The WebSocket connection to send confirmation.
        """
        if session_id in self.subscriptions:
            self.subscriptions[session_id].add(topic)
            await websocket.send_json({"type": "subscribed", "topic": topic})

    async def unsubscribe(self, session_id: str, topic: str, websocket: WebSocket) -> None:
        """Unsubscribe a session from a topic.

        Args:
            session_id: The session ID to unsubscribe.
            topic: The topic to unsubscribe from.
            websocket: The WebSocket connection to send confirmation.
        """
        if session_id in self.subscriptions:
            self.subscriptions[session_id].discard(topic)
            await websocket.send_json({"type": "unsubscribed", "topic": topic})

    async def broadcast_to_topic(self, topic: str, message: dict) -> None:
        """Send a message to all sessions subscribed to a topic.

        Args:
            topic: The topic to broadcast to.
            message: The message to send (will be JSON serialized).
        """
        disconnected_sessions = []

        for session_id, topics in self.subscriptions.items():
            if topic in topics:
                websocket = self.active_connections.get(session_id)
                if websocket:
                    try:
                        await websocket.send_json(message)
                    except Exception:
                        # Connection might be closed, mark for cleanup
                        disconnected_sessions.append(session_id)

        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            self.disconnect(session_id)

    def get_subscriptions(self, session_id: str) -> Set[str]:
        """Get all topics a session is subscribed to.

        Args:
            session_id: The session ID to query.

        Returns:
            Set of topic names, or empty set if session not found.
        """
        return self.subscriptions.get(session_id, set())

    def get_subscriber_count(self, topic: str) -> int:
        """Get the number of sessions subscribed to a topic.

        Args:
            topic: The topic to query.

        Returns:
            Number of subscribed sessions.
        """
        count = 0
        for topics in self.subscriptions.values():
            if topic in topics:
                count += 1
        return count


# Singleton instance for application-wide use
manager = ConnectionManager()
