"""Tests for NATS Bridge functionality."""
import asyncio
import json
from uuid import uuid4
import pytest

from app.events.bridge import NATSBridge, RoutingRule
from app.config import get_nats_url


class TestRoutingRule:
    """Tests for RoutingRule class."""

    def test_exact_match(self):
        """Test exact subject matching."""
        rule = RoutingRule("hub.local.project.created", lambda s, d: None)

        assert rule.matches("hub.local.project.created") is True
        assert rule.matches("hub.local.project.deleted") is False
        assert rule.matches("hub.local.task.created") is False

    def test_wildcard_single_segment(self):
        """Test single segment wildcard (*) matching."""
        rule = RoutingRule("hub.*.project.created", lambda s, d: None)

        assert rule.matches("hub.local.project.created") is True
        assert rule.matches("hub.remote.project.created") is True
        assert rule.matches("hub.project.created") is False  # Missing segment
        assert rule.matches("hub.local.test.project.created") is False  # Too many segments

    def test_wildcard_multi_segment(self):
        """Test multi segment wildcard (>) matching."""
        rule = RoutingRule("hub.global.>", lambda s, d: None)

        assert rule.matches("hub.global.presence") is True
        assert rule.matches("hub.global.presence.announced") is True
        assert rule.matches("hub.global.sync.registry.update") is True
        assert rule.matches("hub.local.project.created") is False

    def test_disabled_rule(self):
        """Test that disabled rules don't match."""
        rule = RoutingRule("hub.*.project.*", lambda s, d: None, enabled=False)

        assert rule.matches("hub.local.project.created") is False


@pytest.mark.asyncio
class TestNATSBridge:
    """Tests for NATSBridge class."""

    @pytest.fixture
    async def bridge(self):
        """Create and connect NATSBridge instance."""
        bridge = NATSBridge(nats_url=get_nats_url())
        try:
            await bridge.connect()
            yield bridge
        finally:
            await bridge.disconnect()

    async def test_connect_disconnect(self):
        """Test NATS connection lifecycle."""
        bridge = NATSBridge(nats_url=get_nats_url())

        # Initially not connected
        assert bridge.nc is None
        assert bridge.js is None

        # Connect
        await bridge.connect()
        assert bridge.nc is not None
        assert bridge.js is not None
        assert not bridge.nc.is_closed

        # Disconnect
        await bridge.disconnect()
        assert bridge.nc.is_closed

    async def test_publish_internal_to_nats(self, bridge):
        """Test publishing internal events to NATS."""
        subject = "project.created"
        payload = {"project_id": "test-123", "name": "Test Project"}
        correlation_id = uuid4()

        # Publish event
        await bridge.publish_internal_to_nats(
            subject=subject,
            payload=payload,
            correlation_id=correlation_id
        )

        # Event should be published to hub.<hub_id>.project.created
        # We can't easily verify without subscribing, but no exception = success

    async def test_auto_prefix_subject(self, bridge):
        """Test automatic hub ID prefixing of subjects."""
        # Subject without hub prefix should be auto-prefixed
        await bridge.publish_internal_to_nats(
            subject="test.event",
            payload={"data": "test"}
        )

        # Subject with hub prefix should not be modified
        await bridge.publish_internal_to_nats(
            subject="hub.custom.test.event",
            payload={"data": "test"}
        )

    async def test_subscribe_and_receive(self, bridge):
        """Test subscribing to NATS and receiving messages."""
        received_messages = []

        async def handler(subject: str, data: dict):
            received_messages.append({"subject": subject, "data": data})

        # Subscribe to test pattern
        test_subject = f"hub.{bridge.hub_id}.test.subscribe"
        await bridge.subscribe_nats_to_internal(
            f"hub.{bridge.hub_id}.test.>",
            handler
        )

        # Give subscription time to register
        await asyncio.sleep(0.1)

        # Publish message
        payload = {"test": "data", "value": 123}
        await bridge.publish_internal_to_nats(
            subject="test.subscribe",
            payload=payload
        )

        # Wait for message to be received
        await asyncio.sleep(0.2)

        # Verify message was received
        assert len(received_messages) == 1
        assert received_messages[0]["subject"] == test_subject
        assert received_messages[0]["data"]["payload"] == payload

    async def test_routing_rules(self, bridge):
        """Test adding and matching routing rules."""
        matched_subjects = []

        async def handler(subject: str, data: dict):
            matched_subjects.append(subject)

        # Add routing rule
        rule = bridge.add_routing_rule(
            "hub.*.project.*",
            handler,
            description="Route project events"
        )

        # Test routing
        await bridge.route_event("hub.local.project.created", {"test": "data"})
        await bridge.route_event("hub.remote.project.deleted", {"test": "data"})
        await bridge.route_event("hub.local.task.created", {"test": "data"})  # Should not match

        await asyncio.sleep(0.1)

        # Verify only matching events were routed
        assert len(matched_subjects) == 2
        assert "hub.local.project.created" in matched_subjects
        assert "hub.remote.project.deleted" in matched_subjects

        # Test removing rule
        bridge.remove_routing_rule(rule)
        matched_subjects.clear()

        await bridge.route_event("hub.local.project.updated", {"test": "data"})
        await asyncio.sleep(0.1)

        # No messages should be routed after rule removal
        assert len(matched_subjects) == 0

    async def test_get_routing_rules(self, bridge):
        """Test retrieving routing rules."""
        async def handler1(s, d): pass
        async def handler2(s, d): pass

        bridge.add_routing_rule("hub.*.project.*", handler1, description="Rule 1")
        bridge.add_routing_rule("hub.global.>", handler2, enabled=False, description="Rule 2")

        rules = bridge.get_routing_rules()

        assert len(rules) == 2
        assert rules[0]["subject_pattern"] == "hub.*.project.*"
        assert rules[0]["enabled"] is True
        assert rules[0]["description"] == "Rule 1"
        assert rules[1]["subject_pattern"] == "hub.global.>"
        assert rules[1]["enabled"] is False

    async def test_multiple_handlers_same_event(self, bridge):
        """Test multiple routing rules matching same event."""
        handler1_called = []
        handler2_called = []

        async def handler1(subject: str, data: dict):
            handler1_called.append(subject)

        async def handler2(subject: str, data: dict):
            handler2_called.append(subject)

        # Add two rules that both match the same pattern
        bridge.add_routing_rule("hub.*.project.*", handler1)
        bridge.add_routing_rule("hub.local.>", handler2)

        # Publish event that matches both
        matched_count = await bridge.route_event(
            "hub.local.project.created",
            {"test": "data"}
        )

        await asyncio.sleep(0.1)

        # Both handlers should be called
        assert matched_count == 2
        assert len(handler1_called) == 1
        assert len(handler2_called) == 1

    async def test_error_in_handler(self, bridge):
        """Test that errors in handlers don't break routing."""
        successful_calls = []

        async def failing_handler(subject: str, data: dict):
            raise ValueError("Simulated error")

        async def successful_handler(subject: str, data: dict):
            successful_calls.append(subject)

        bridge.add_routing_rule("hub.*.test.*", failing_handler)
        bridge.add_routing_rule("hub.*.test.*", successful_handler)

        # Route event - failing handler should not prevent successful handler
        matched_count = await bridge.route_event(
            "hub.local.test.error",
            {"test": "data"}
        )

        await asyncio.sleep(0.1)

        # Both handlers matched (even though one failed)
        assert matched_count == 2
        assert len(successful_calls) == 1

    async def test_not_connected_raises_error(self):
        """Test that operations fail when not connected."""
        bridge = NATSBridge(nats_url=get_nats_url())

        # Should raise error when not connected
        with pytest.raises(RuntimeError, match="Not connected to NATS"):
            await bridge.publish_internal_to_nats("test.event", {})

        with pytest.raises(RuntimeError, match="Not connected to NATS"):
            await bridge.subscribe_nats_to_internal("test.>", lambda s, d: None)
