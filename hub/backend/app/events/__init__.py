"""Event system for Hub backend.

This module provides event sourcing, NATS integration, event replay,
and bidirectional NATS bridge capabilities for the CommandCenter Hub.
"""
from app.events.service import EventService
from app.events.bridge import NATSBridge, RoutingRule

__all__ = ["EventService", "NATSBridge", "RoutingRule"]
