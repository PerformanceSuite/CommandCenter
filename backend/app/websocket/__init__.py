"""
WebSocket package for real-time graph updates.

This package provides the infrastructure for managing WebSocket connections
and topic-based subscriptions for the graph service.

Usage:
    from app.websocket import manager, ConnectionManager

    # Subscribe to a topic
    await manager.subscribe(session_id, "entity:updated:proj123", websocket)

    # Broadcast to subscribers
    await manager.broadcast_to_topic("entity:updated:proj123", {"data": "..."})
"""

from .manager import ConnectionManager, manager

__all__ = ["ConnectionManager", "manager"]
