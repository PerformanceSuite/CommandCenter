"""Tests for JSON-RPC endpoint."""
import pytest
from uuid import uuid4
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
class TestJSONRPC:
    """Tests for JSON-RPC 2.0 endpoint."""

    async def test_rpc_bus_publish(self, async_client: AsyncClient):
        """Test bus.publish RPC method."""
        response = await async_client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "bus.publish",
                "params": {
                    "topic": "hub.test.rpc.publish",
                    "payload": {"test": "data", "value": 123}
                }
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        assert data["result"]["published"] is True
        assert data["result"]["subject"] == "hub.test.rpc.publish"
        assert "correlation_id" in data["result"]

    async def test_rpc_bus_publish_with_correlation_id(self, async_client: AsyncClient):
        """Test bus.publish with explicit correlation ID."""
        correlation_id = str(uuid4())

        response = await async_client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "bus.publish",
                "params": {
                    "topic": "hub.test.rpc.correlation",
                    "payload": {"test": "correlation"},
                    "correlation_id": correlation_id
                }
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["result"]["correlation_id"] == correlation_id

    async def test_rpc_bus_subscribe(self, async_client: AsyncClient):
        """Test bus.subscribe RPC method."""
        # First publish some events
        for i in range(3):
            await async_client.post(
                "/api/events",
                json={
                    "subject": f"hub.test.rpc.subscribe.event{i}",
                    "payload": {"index": i}
                }
            )

        # Query events via RPC
        response = await async_client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "bus.subscribe",
                "params": {
                    "subject": "hub.test.rpc.subscribe.>",
                    "limit": 10
                }
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["jsonrpc"] == "2.0"
        assert "result" in data
        assert data["result"]["count"] >= 3
        assert len(data["result"]["events"]) >= 3

    async def test_rpc_hub_info(self, async_client: AsyncClient):
        """Test hub.info RPC method."""
        response = await async_client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "hub.info",
                "params": {}
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["jsonrpc"] == "2.0"
        assert "result" in data
        assert "hub_id" in data["result"]
        assert "version" in data["result"]
        assert "status" in data["result"]

    async def test_rpc_hub_health(self, async_client: AsyncClient):
        """Test hub.health RPC method."""
        response = await async_client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "hub.health",
                "params": {}
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["jsonrpc"] == "2.0"
        assert "result" in data
        assert "status" in data["result"]
        assert "services" in data["result"]

    async def test_rpc_method_not_found(self, async_client: AsyncClient):
        """Test calling non-existent RPC method."""
        response = await async_client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 6,
                "method": "nonexistent.method",
                "params": {}
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 6
        assert "error" in data
        assert data["error"]["code"] == -32601  # METHOD_NOT_FOUND
        assert "available_methods" in data["error"]["data"]

    async def test_rpc_invalid_params(self, async_client: AsyncClient):
        """Test RPC call with invalid parameters."""
        response = await async_client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 7,
                "method": "bus.publish",
                "params": {
                    # Missing required "payload" param
                    "topic": "hub.test.invalid"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "error" in data
        assert data["error"]["code"] == -32602  # INVALID_PARAMS

    async def test_rpc_invalid_jsonrpc_version(self, async_client: AsyncClient):
        """Test RPC call with invalid JSON-RPC version."""
        response = await async_client.post(
            "/rpc",
            json={
                "jsonrpc": "1.0",  # Wrong version
                "id": 8,
                "method": "hub.info",
                "params": {}
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "error" in data
        assert data["error"]["code"] == -32600  # INVALID_REQUEST

    async def test_rpc_no_id(self, async_client: AsyncClient):
        """Test RPC notification (no id field)."""
        response = await async_client.post(
            "/rpc",
            json={
                "jsonrpc": "2.0",
                "method": "hub.info"
                # No "id" field = notification
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Response should still have result but id will be None
        assert data["jsonrpc"] == "2.0"
        assert data["id"] is None
        assert "result" in data

    async def test_list_methods(self, async_client: AsyncClient):
        """Test /rpc/methods helper endpoint."""
        response = await async_client.get("/rpc/methods")

        assert response.status_code == 200
        data = response.json()

        assert "methods" in data
        assert len(data["methods"]) >= 4

        method_names = [m["name"] for m in data["methods"]]
        assert "bus.publish" in method_names
        assert "bus.subscribe" in method_names
        assert "hub.info" in method_names
        assert "hub.health" in method_names

    async def test_rpc_batch_not_supported(self, async_client: AsyncClient):
        """Test that batch requests are not supported (yet)."""
        # JSON-RPC 2.0 supports batch requests (array of request objects)
        # We don't implement this yet, so it should fail gracefully
        response = await async_client.post(
            "/rpc",
            json=[
                {"jsonrpc": "2.0", "id": 1, "method": "hub.info"},
                {"jsonrpc": "2.0", "id": 2, "method": "hub.health"}
            ]
        )

        # FastAPI will reject this as it doesn't match the JSONRPCRequest schema
        assert response.status_code == 422  # Unprocessable Entity
