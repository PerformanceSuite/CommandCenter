"""Event system for Hub backend.

This module provides event sourcing, NATS integration, and event replay
capabilities for the CommandCenter Hub.
"""
from app.events.service import EventService

__all__ = ["EventService"]
