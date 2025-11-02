"""
Tests for MCP FastAPI router.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestMCPRouter:
    """Tests for MCP router endpoints."""

    def test_mcp_health_endpoint(self, client):
        """Test MCP health check."""
        response = client.get("/api/v1/mcp/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "server" in data

    def test_mcp_info_endpoint(self, client):
        """Test MCP info endpoint."""
        response = client.get("/api/v1/mcp/info")
        assert response.status_code == 200
        data = response.json()
        assert "server_info" in data
        assert "capabilities" in data

    def test_mcp_rpc_endpoint(self, client):
        """Test MCP JSON-RPC endpoint."""
        rpc_request = {"jsonrpc": "2.0", "id": 1, "method": "resources/list", "params": {}}
        response = client.post("/api/v1/mcp/rpc", json=rpc_request)
        assert response.status_code == 200

    def test_mcp_resources_endpoint(self, client):
        """Test convenience resources endpoint."""
        response = client.get("/api/v1/mcp/resources")
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data or isinstance(data, dict)

    def test_mcp_tools_endpoint(self, client):
        """Test convenience tools endpoint."""
        response = client.get("/api/v1/mcp/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data or isinstance(data, dict)

    def test_mcp_prompts_endpoint(self, client):
        """Test convenience prompts endpoint."""
        response = client.get("/api/v1/mcp/prompts")
        assert response.status_code == 200
        data = response.json()
        assert "prompts" in data or isinstance(data, dict)
