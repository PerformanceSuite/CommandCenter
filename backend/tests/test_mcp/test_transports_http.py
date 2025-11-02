"""
Tests for HTTP transport layer.
"""

import pytest
from fastapi.testclient import TestClient

from app.mcp.config import MCPCapabilities, MCPServerConfig, MCPServerInfo
from app.mcp.server import MCPServer
from app.mcp.transports.http import HTTPTransport, create_http_app


@pytest.fixture
def mcp_server():
    """Create test MCP server."""
    config = MCPServerConfig(
        server_info=MCPServerInfo(
            name="test-mcp-server",
            version="1.0.0",
        ),
        capabilities=MCPCapabilities(
            resources=True,
            tools=True,
            prompts=True,
        ),
    )
    return MCPServer(config)


@pytest.fixture
async def http_transport(mcp_server):
    """Create HTTP transport."""
    transport = HTTPTransport(mcp_server)
    await transport.start()
    yield transport
    await transport.stop()


@pytest.fixture
def http_client(mcp_server):
    """Create test HTTP client."""
    app = create_http_app(mcp_server)
    return TestClient(app)


class TestHTTPTransport:
    """Tests for HTTP transport."""

    def test_health_endpoint(self, http_client):
        """Test health check endpoint."""
        response = http_client.get("/mcp/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "test-mcp-server"
        assert data["version"] == "1.0.0"

    def test_info_endpoint(self, http_client):
        """Test server info endpoint."""
        response = http_client.get("/mcp/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert "server_info" in data
        assert "capabilities" in data
        assert "stats" in data
        assert data["server_info"]["name"] == "test-mcp-server"

    def test_rpc_endpoint_list_resources(self, http_client):
        """Test JSON-RPC request for listing resources."""
        rpc_request = {"jsonrpc": "2.0", "id": 1, "method": "resources/list", "params": {}}
        response = http_client.post("/mcp/v1/rpc", json=rpc_request)
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data

    def test_rpc_endpoint_list_tools(self, http_client):
        """Test JSON-RPC request for listing tools."""
        rpc_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        response = http_client.post("/mcp/v1/rpc", json=rpc_request)
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 2
        assert "result" in data

    def test_rpc_endpoint_list_prompts(self, http_client):
        """Test JSON-RPC request for listing prompts."""
        rpc_request = {"jsonrpc": "2.0", "id": 3, "method": "prompts/list", "params": {}}
        response = http_client.post("/mcp/v1/rpc", json=rpc_request)
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 3
        assert "result" in data

    def test_rpc_endpoint_invalid_json(self, http_client):
        """Test JSON-RPC endpoint with invalid JSON."""
        response = http_client.post("/mcp/v1/rpc", data="invalid json")
        assert response.status_code >= 400

    def test_rpc_endpoint_invalid_method(self, http_client):
        """Test JSON-RPC request with invalid method."""
        rpc_request = {"jsonrpc": "2.0", "id": 4, "method": "invalid/method", "params": {}}
        response = http_client.post("/mcp/v1/rpc", json=rpc_request)
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_transport_lifecycle(self, mcp_server):
        """Test transport start and stop."""
        transport = HTTPTransport(mcp_server)

        # Start
        await transport.start()
        assert transport.is_running()

        # Stop
        await transport.stop()
        assert not transport.is_running()

    @pytest.mark.asyncio
    async def test_transport_double_start(self, http_transport):
        """Test starting transport twice."""
        # Should not raise, just log warning
        await http_transport.start()
        assert http_transport.is_running()

    def test_create_http_app_returns_fastapi(self, mcp_server):
        """Test create_http_app returns FastAPI instance."""
        app = create_http_app(mcp_server)
        from fastapi import FastAPI

        assert isinstance(app, FastAPI)

    def test_rpc_notification_no_response(self, http_client):
        """Test JSON-RPC notification (no id, no response expected)."""
        rpc_notification = {"jsonrpc": "2.0", "method": "notification/test", "params": {}}
        response = http_client.post("/mcp/v1/rpc", json=rpc_notification)
        # Notifications return 204 No Content
        assert response.status_code == 204
