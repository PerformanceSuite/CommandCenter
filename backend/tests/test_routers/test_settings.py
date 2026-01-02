# backend/tests/test_routers/test_settings.py
"""Tests for settings router endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status


@pytest.fixture
def mock_settings_service():
    """Mock SettingsService for testing."""
    with patch("app.routers.settings.SettingsService") as mock:
        service = mock.return_value
        yield service


class TestAgentConfigEndpoints:
    @pytest.mark.asyncio
    async def test_list_agents_empty(self, api_client, mock_settings_service):
        """Test listing agents when none exist."""
        mock_settings_service.list_agent_configs = AsyncMock(return_value=[])

        response = await api_client.get("/settings/agents")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"agents": []}

    @pytest.mark.asyncio
    async def test_seed_defaults(self, api_client, mock_settings_service):
        """Test seeding default agent configurations."""
        mock_settings_service.seed_defaults = AsyncMock(return_value=5)
        mock_settings_service.list_agent_configs = AsyncMock(
            return_value=[
                {"role": "analyst", "provider_alias": "claude"},
                {"role": "researcher", "provider_alias": "claude"},
                {"role": "strategist", "provider_alias": "claude"},
                {"role": "critic", "provider_alias": "claude"},
                {"role": "chairman", "provider_alias": "claude"},
            ]
        )

        response = await api_client.post("/settings/seed")

        assert response.status_code == status.HTTP_200_OK
        assert "Seeded" in response.json()["message"]

        # After seeding, agents should be populated
        response = await api_client.get("/settings/agents")
        assert response.status_code == status.HTTP_200_OK
        agents = response.json()["agents"]
        assert len(agents) == 5

    @pytest.mark.asyncio
    async def test_set_agent_provider(self, api_client, mock_settings_service):
        """Test setting an agent's provider."""
        mock_settings_service.set_agent_provider = AsyncMock(
            return_value={"role": "analyst", "provider_alias": "gpt"}
        )

        response = await api_client.put(
            "/settings/agents/analyst",
            json={"provider_alias": "gpt"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "analyst"
        assert response.json()["provider_alias"] == "gpt"

    @pytest.mark.asyncio
    async def test_set_agent_provider_invalid(self, api_client, mock_settings_service):
        """Test setting agent with non-existent provider."""
        mock_settings_service.set_agent_provider = AsyncMock(
            side_effect=ValueError("Provider 'nonexistent' not found")
        )

        response = await api_client.put(
            "/settings/agents/analyst",
            json={"provider_alias": "nonexistent"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found" in response.json()["detail"]
