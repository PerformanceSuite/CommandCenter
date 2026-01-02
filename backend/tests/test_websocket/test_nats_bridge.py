"""
Tests for NATS-to-WebSocket bridge.

Tests the bridge that converts NATS events from the graph service
to WebSocket messages for real-time client updates.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.websocket.nats_bridge import NATSBridge


class TestNATSBridgeForwarding:
    """Tests for NATS message forwarding to WebSocket subscribers."""

    @pytest.mark.asyncio
    async def test_nats_bridge_forwards_messages(self):
        """NATS messages should be forwarded to WebSocket subscribers."""
        mock_manager = MagicMock()
        mock_manager.broadcast_to_topic = AsyncMock()

        bridge = NATSBridge(mock_manager)
        await bridge.handle_nats_message(
            subject="graph.node.updated",
            data={"project_id": 123, "node_type": "symbol", "node_id": "symbol:456"},
        )

        mock_manager.broadcast_to_topic.assert_called_once()
        call_args = mock_manager.broadcast_to_topic.call_args
        assert "entity:updated" in call_args[0][0]  # topic contains entity:updated

    @pytest.mark.asyncio
    async def test_nats_bridge_forwards_with_correct_payload(self):
        """NATS bridge should wrap data in proper WebSocket message format."""
        mock_manager = MagicMock()
        mock_manager.broadcast_to_topic = AsyncMock()

        bridge = NATSBridge(mock_manager)
        test_data = {"project_id": 123, "node_type": "task", "node_id": "task:789"}
        await bridge.handle_nats_message(subject="graph.node.created", data=test_data)

        call_args = mock_manager.broadcast_to_topic.call_args
        message = call_args[0][1]
        assert message["type"] == "event"
        assert "topic" in message
        assert message["data"] == test_data


class TestNATSSubjectMapping:
    """Tests for NATS subject to WebSocket topic mapping."""

    @pytest.mark.asyncio
    async def test_nats_bridge_maps_node_subjects(self):
        """NATS node subjects should map to entity topics."""
        mock_manager = MagicMock()
        mock_manager.broadcast_to_topic = AsyncMock()

        bridge = NATSBridge(mock_manager)

        # Test different node event types
        await bridge.handle_nats_message(
            "graph.node.created", {"project_id": 1, "node_type": "file"}
        )
        await bridge.handle_nats_message(
            "graph.node.updated", {"project_id": 1, "node_type": "symbol"}
        )
        await bridge.handle_nats_message(
            "graph.node.deleted", {"project_id": 1, "node_type": "service"}
        )

        assert mock_manager.broadcast_to_topic.call_count == 3

        # Verify topic mappings
        calls = mock_manager.broadcast_to_topic.call_args_list
        topics = [call[0][0] for call in calls]
        assert "entity:created:1" in topics
        assert "entity:updated:1" in topics
        assert "entity:deleted:1" in topics

    @pytest.mark.asyncio
    async def test_nats_bridge_maps_edge_subjects(self):
        """NATS edge subjects should map to edge topics."""
        mock_manager = MagicMock()
        mock_manager.broadcast_to_topic = AsyncMock()

        bridge = NATSBridge(mock_manager)

        await bridge.handle_nats_message(
            "graph.edge.created", {"project_id": 2, "from_node": "file:1", "to_node": "symbol:2"}
        )
        await bridge.handle_nats_message(
            "graph.edge.deleted", {"project_id": 2, "from_node": "symbol:2", "to_node": "symbol:3"}
        )

        assert mock_manager.broadcast_to_topic.call_count == 2

        calls = mock_manager.broadcast_to_topic.call_args_list
        topics = [call[0][0] for call in calls]
        assert "edge:created:2" in topics
        assert "edge:deleted:2" in topics

    @pytest.mark.asyncio
    async def test_nats_bridge_maps_invalidated_subject(self):
        """NATS graph.invalidated should map to graph:invalidated topic."""
        mock_manager = MagicMock()
        mock_manager.broadcast_to_topic = AsyncMock()

        bridge = NATSBridge(mock_manager)

        await bridge.handle_nats_message(
            "graph.invalidated",
            {"project_id": 3, "reason": "reindex", "affected_types": ["symbol"]},
        )

        mock_manager.broadcast_to_topic.assert_called_once()
        call_args = mock_manager.broadcast_to_topic.call_args
        assert call_args[0][0] == "graph:invalidated:3"

    @pytest.mark.asyncio
    async def test_nats_bridge_ignores_unknown_subjects(self):
        """Unknown NATS subjects should not trigger broadcasts."""
        mock_manager = MagicMock()
        mock_manager.broadcast_to_topic = AsyncMock()

        bridge = NATSBridge(mock_manager)

        await bridge.handle_nats_message("unknown.subject.here", {"some": "data"})

        mock_manager.broadcast_to_topic.assert_not_called()


class TestNATSBridgeProjectIsolation:
    """Tests for project-based topic isolation."""

    @pytest.mark.asyncio
    async def test_nats_bridge_includes_project_in_topic(self):
        """Topics should include project_id for multi-tenant isolation."""
        mock_manager = MagicMock()
        mock_manager.broadcast_to_topic = AsyncMock()

        bridge = NATSBridge(mock_manager)

        # Messages for different projects
        await bridge.handle_nats_message(
            "graph.node.updated", {"project_id": 100, "node_type": "symbol", "node_id": "symbol:1"}
        )
        await bridge.handle_nats_message(
            "graph.node.updated", {"project_id": 200, "node_type": "symbol", "node_id": "symbol:2"}
        )

        calls = mock_manager.broadcast_to_topic.call_args_list
        topics = [call[0][0] for call in calls]
        assert "entity:updated:100" in topics
        assert "entity:updated:200" in topics

    @pytest.mark.asyncio
    async def test_nats_bridge_handles_missing_project_id(self):
        """Messages without project_id should use a default topic."""
        mock_manager = MagicMock()
        mock_manager.broadcast_to_topic = AsyncMock()

        bridge = NATSBridge(mock_manager)

        await bridge.handle_nats_message(
            "graph.node.created", {"node_type": "symbol", "node_id": "symbol:1"}  # No project_id
        )

        # Should still broadcast, but to a topic without project qualifier
        mock_manager.broadcast_to_topic.assert_called_once()
        call_args = mock_manager.broadcast_to_topic.call_args
        topic = call_args[0][0]
        assert topic == "entity:created"  # No project suffix
