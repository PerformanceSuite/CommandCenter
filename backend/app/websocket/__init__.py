"""
WebSocket package for real-time graph updates.

This package provides the infrastructure for managing WebSocket connections
and topic-based subscriptions for the graph service.

Usage:
    from app.websocket import manager, ConnectionManager, NATSBridge

    # Subscribe to a topic
    await manager.subscribe(session_id, "entity:updated:proj123", websocket)

    # Broadcast to subscribers
    await manager.broadcast_to_topic("entity:updated:proj123", {"data": "..."})

    # Bridge NATS events to WebSocket
    bridge = NATSBridge(manager)
    await bridge.handle_nats_message("graph.node.updated", {"project_id": 123, ...})
"""

from .manager import ConnectionManager, manager
from .nats_bridge import NATSBridge

__all__ = ["ConnectionManager", "manager", "NATSBridge"]
