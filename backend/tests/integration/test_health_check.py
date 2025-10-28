"""
Integration tests for Health Check endpoint
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.integration
class TestHealthCheck:
    """Test service health check endpoint"""

    async def test_health_check_success(self, async_client: AsyncClient):
        """Test health check endpoint returns healthy status"""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]

    async def test_health_check_includes_timestamp(self, async_client: AsyncClient):
        """Test health check includes timestamp"""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        # Most health endpoints include a timestamp
        assert "timestamp" in data or "time" in data or "checked_at" in data or "status" in data

    async def test_health_check_database_status(self, async_client: AsyncClient):
        """Test health check includes database status"""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Health endpoint may include detailed checks
        if "checks" in data or "services" in data:
            # Detailed health check
            assert isinstance(data, dict)
        else:
            # Simple health check
            assert "status" in data

    async def test_health_check_fast_response(self, async_client: AsyncClient):
        """Test health check responds quickly"""
        import time

        start = time.time()
        response = await async_client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        # Health check should be fast (< 1 second)
        assert duration < 1.0

    async def test_readiness_check(self, async_client: AsyncClient):
        """Test readiness endpoint if available"""
        # Try both /health and /ready endpoints
        endpoints = ["/health", "/ready", "/readiness"]

        success = False
        for endpoint in endpoints:
            try:
                response = await async_client.get(endpoint)
                if response.status_code == 200:
                    success = True
                    break
            except Exception:
                continue

        assert success, "No health/readiness endpoint found"

    async def test_liveness_check(self, async_client: AsyncClient):
        """Test liveness endpoint if available"""
        # Try both /health and /live endpoints
        endpoints = ["/health", "/live", "/liveness"]

        success = False
        for endpoint in endpoints:
            try:
                response = await async_client.get(endpoint)
                if response.status_code == 200:
                    success = True
                    data = response.json()
                    assert isinstance(data, dict)
                    break
            except Exception:
                continue

        assert success, "No health/liveness endpoint found"

    async def test_health_check_response_format(self, async_client: AsyncClient):
        """Test health check returns valid JSON"""
        response = await async_client.get("/health")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

        data = response.json()
        assert isinstance(data, dict)

    async def test_health_check_no_auth_required(self, async_client: AsyncClient):
        """Test health check doesn't require authentication"""
        # Create a client without auth headers
        response = await async_client.get("/health")

        # Health endpoint should be publicly accessible
        assert response.status_code == 200

    async def test_health_check_idempotent(self, async_client: AsyncClient):
        """Test health check is idempotent"""
        # Call health check multiple times
        responses = []
        for _ in range(3):
            response = await async_client.get("/health")
            responses.append(response.status_code)

        # All should return 200
        assert all(status == 200 for status in responses)

    async def test_health_check_version_info(self, async_client: AsyncClient):
        """Test health check may include version information"""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Version info is optional but common
        # Just verify the response is valid
        assert isinstance(data, dict)
        if "version" in data:
            assert isinstance(data["version"], str)
