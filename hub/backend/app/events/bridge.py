"""NATS Bridge for bidirectional event routing.

The NATSBridge provides:
- Auto-publish internal events to NATS subjects
- Subscribe to external NATS events and route to internal handlers
- Subject namespace routing (hub.<hub_id>.* vs hub.global.*)
- Event filtering and routing rules
"""
import json
import logging
from typing import Optional, Callable, Dict, List
from uuid import UUID

import nats
from nats.js import JetStreamContext
from nats.aio.client import Client as NATS

from app.config import get_hub_id

logger = logging.getLogger(__name__)


class RoutingRule:
    """Routing rule for event filtering and transformation.

    Attributes:
        subject_pattern: NATS subject pattern (supports wildcards: *, >)
        handler: Async function to call when event matches
        enabled: Whether rule is active
        description: Human-readable rule description
    """

    def __init__(
        self,
        subject_pattern: str,
        handler: Callable,
        enabled: bool = True,
        description: Optional[str] = None
    ):
        self.subject_pattern = subject_pattern
        self.handler = handler
        self.enabled = enabled
        self.description = description or f"Route {subject_pattern}"

    def matches(self, subject: str) -> bool:
        """Check if subject matches this rule's pattern.

        Args:
            subject: NATS subject to check

        Returns:
            True if subject matches pattern
        """
        if not self.enabled:
            return False

        # Convert NATS wildcards to simple matching
        # * matches single segment
        # > matches remaining segments

        if '>' in self.subject_pattern:
            prefix = self.subject_pattern.split('>')[0]
            return subject.startswith(prefix)

        if '*' in self.subject_pattern:
            parts = self.subject_pattern.split('.')
            subject_parts = subject.split('.')

            if len(parts) != len(subject_parts):
                return False

            for pattern_part, subject_part in zip(parts, subject_parts):
                if pattern_part != '*' and pattern_part != subject_part:
                    return False

            return True

        # Exact match
        return self.subject_pattern == subject


class NATSBridge:
    """Bidirectional bridge between internal events and NATS.

    The bridge handles:
    - Publishing internal events to NATS subjects
    - Subscribing to external NATS events
    - Routing events based on subject patterns
    - Event filtering and transformation

    Subject Namespace:
        hub.<hub_id>.<domain>.<action>     # Local events
        hub.global.<domain>.<action>        # Cross-hub events

    Examples:
        hub.local-hub.project.created
        hub.local-hub.audit.security.completed
        hub.global.presence.announced
    """

    def __init__(self, nats_url: str, hub_id: Optional[str] = None):
        """Initialize NATS Bridge.

        Args:
            nats_url: NATS server URL (e.g., 'nats://localhost:4222')
            hub_id: Unique Hub identifier (defaults to config)
        """
        self.nats_url = nats_url
        self.hub_id = hub_id or get_hub_id()

        self.nc: Optional[NATS] = None
        self.js: Optional[JetStreamContext] = None

        # Routing rules
        self._rules: List[RoutingRule] = []
        self._subscriptions: List = []

    async def connect(self) -> None:
        """Connect to NATS server and initialize JetStream."""
        try:
            self.nc = await nats.connect(self.nats_url)
            self.js = self.nc.jetstream()
            logger.info(f"NATSBridge connected to {self.nats_url} (hub_id={self.hub_id})")
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
            logger.info("NATSBridge disconnected")

    async def publish_internal_to_nats(
        self,
        subject: str,
        payload: dict,
        correlation_id: Optional[UUID] = None
    ) -> None:
        """Publish internal event to NATS.

        Automatically prefixes subject with hub.<hub_id> if not already present.

        Args:
            subject: Event subject (domain.action format)
            payload: Event data as dictionary
            correlation_id: Request correlation UUID

        Example:
            await bridge.publish_internal_to_nats(
                subject="project.created",
                payload={"project_id": "123", "name": "MyProject"}
            )
            # Publishes to: hub.local-hub.project.created
        """
        if not self.nc:
            raise RuntimeError("Not connected to NATS. Call connect() first.")

        # Auto-prefix with hub ID if not present
        if not subject.startswith("hub."):
            subject = f"hub.{self.hub_id}.{subject}"

        # Build message
        message = json.dumps({
            "payload": payload,
            "correlation_id": str(correlation_id) if correlation_id else None,
            "hub_id": self.hub_id
        })

        # Add correlation header if provided
        headers = {}
        if correlation_id:
            headers["Correlation-ID"] = str(correlation_id)

        # Publish to NATS
        try:
            await self.nc.publish(subject, message.encode(), headers=headers)
            logger.debug(f"Published to NATS: {subject}")
        except Exception as e:
            logger.error(f"Failed to publish to NATS: {e}")
            raise

    async def subscribe_nats_to_internal(
        self,
        subject_filter: str,
        handler: Callable[[str, dict], None]
    ) -> None:
        """Subscribe to external NATS events and route to internal handler.

        Args:
            subject_filter: NATS subject pattern (supports wildcards: *, >)
            handler: Async function called with (subject, data) on each message

        Example:
            async def handle_global_events(subject: str, data: dict):
                print(f"Global event: {subject} -> {data}")

            await bridge.subscribe_nats_to_internal(
                "hub.global.>",
                handle_global_events
            )
        """
        if not self.nc:
            raise RuntimeError("Not connected to NATS. Call connect() first.")

        async def message_handler(msg):
            try:
                data = json.loads(msg.data.decode())

                # Extract correlation ID from headers if present
                correlation_id = None
                if hasattr(msg, 'headers') and msg.headers:
                    correlation_id = msg.headers.get("Correlation-ID")

                # Call internal handler
                await handler(msg.subject, data)

                logger.debug(f"Routed NATS event to internal handler: {msg.subject}")
            except Exception as e:
                logger.error(f"Error in NATS message handler for {msg.subject}: {e}")

        # Subscribe to NATS
        sub = await self.nc.subscribe(subject_filter, cb=message_handler)
        self._subscriptions.append(sub)
        logger.info(f"Subscribed to NATS pattern: {subject_filter}")

    def add_routing_rule(
        self,
        subject_pattern: str,
        handler: Callable,
        enabled: bool = True,
        description: Optional[str] = None
    ) -> RoutingRule:
        """Add event routing rule.

        Args:
            subject_pattern: NATS subject pattern (supports wildcards)
            handler: Async function to call when event matches
            enabled: Whether rule is active
            description: Human-readable rule description

        Returns:
            Created RoutingRule instance

        Example:
            async def log_project_events(subject: str, data: dict):
                logger.info(f"Project event: {subject}")

            bridge.add_routing_rule(
                "hub.*.project.*",
                log_project_events,
                description="Log all project events"
            )
        """
        rule = RoutingRule(
            subject_pattern=subject_pattern,
            handler=handler,
            enabled=enabled,
            description=description
        )
        self._rules.append(rule)
        logger.info(f"Added routing rule: {rule.description}")
        return rule

    def remove_routing_rule(self, rule: RoutingRule) -> None:
        """Remove routing rule.

        Args:
            rule: RoutingRule instance to remove
        """
        if rule in self._rules:
            self._rules.remove(rule)
            logger.info(f"Removed routing rule: {rule.description}")

    async def route_event(self, subject: str, data: dict) -> int:
        """Route event to matching handlers.

        Args:
            subject: NATS subject
            data: Event data

        Returns:
            Number of handlers that matched and were called
        """
        matched = 0

        for rule in self._rules:
            if rule.matches(subject):
                try:
                    await rule.handler(subject, data)
                    matched += 1
                except Exception as e:
                    logger.error(f"Error in routing handler for {subject}: {e}")

        if matched == 0:
            logger.debug(f"No routing rules matched for subject: {subject}")

        return matched

    def get_routing_rules(self) -> List[Dict]:
        """Get all routing rules.

        Returns:
            List of rule dictionaries with pattern, enabled, description
        """
        return [
            {
                "subject_pattern": rule.subject_pattern,
                "enabled": rule.enabled,
                "description": rule.description
            }
            for rule in self._rules
        ]
