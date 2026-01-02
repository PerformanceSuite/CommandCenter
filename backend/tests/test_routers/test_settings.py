# backend/tests/test_routers/test_settings.py
"""Tests for settings router endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status


class MockAgentConfig:
    """Mock agent config object."""

    def __init__(self, role: str, provider: str, model_id: str):
        self.role = role
        self.provider = provider
        self.model_id = model_id


class MockModelInfo:
    """Mock model info for get_cached_models."""

    def __init__(self, model_id: str):
        self.id = model_id
        self.name = model_id
        self.cost_input = 0.01
        self.cost_output = 0.03
        self.api_key_env = "ANTHROPIC_API_KEY"


@pytest.fixture
def mock_settings_service():
    """Mock SettingsService for testing."""
    with patch("app.services.settings_service.SettingsService") as mock_cls:
        service = MagicMock()
        mock_cls.return_value = service
        yield service


@pytest.fixture
def mock_sync_session():
    """Mock get_sync_session to return a mock session."""
    with patch("app.routers.settings.get_sync_session") as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def mock_cached_models():
    """Mock get_cached_models for provider validation."""
    with patch("libs.llm_gateway.providers.get_cached_models") as mock:
        mock.return_value = {
            "anthropic": [
                MockModelInfo("claude-3-5-sonnet-20241022"),
                MockModelInfo("claude-3-opus-20240229"),
            ],
            "openai": [
                MockModelInfo("gpt-4o"),
                MockModelInfo("gpt-4-turbo"),
            ],
        }
        yield mock


class TestAgentConfigEndpoints:
    @pytest.mark.asyncio
    async def test_list_agents_empty(self, api_client, mock_settings_service, mock_sync_session):
        """Test listing agents when none exist."""
        mock_settings_service.list_agent_configs.return_value = []

        response = await api_client.get("/settings/agents")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"agents": []}

    @pytest.mark.asyncio
    async def test_seed_defaults(self, api_client, mock_settings_service, mock_sync_session):
        """Test seeding default agent configurations."""
        mock_settings_service.seed_defaults.return_value = None

        response = await api_client.post("/settings/seed")

        assert response.status_code == status.HTTP_200_OK
        assert "Seeded" in response.json()["message"]
        mock_settings_service.seed_defaults.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_agent_provider(
        self, api_client, mock_settings_service, mock_sync_session, mock_cached_models
    ):
        """Test setting an agent's provider and model."""
        mock_settings_service.set_agent_model.return_value = MockAgentConfig(
            role="analyst",
            provider="anthropic",
            model_id="claude-3-5-sonnet-20241022",
        )

        response = await api_client.put(
            "/settings/agents/analyst",
            json={"provider": "anthropic", "model_id": "claude-3-5-sonnet-20241022"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "analyst"
        assert data["provider"] == "anthropic"
        assert data["model_id"] == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_set_agent_provider_invalid(
        self, api_client, mock_settings_service, mock_sync_session, mock_cached_models
    ):
        """Test setting agent with non-existent provider."""
        response = await api_client.put(
            "/settings/agents/analyst",
            json={"provider": "nonexistent", "model_id": "some-model"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_set_agent_invalid_model(
        self, api_client, mock_settings_service, mock_sync_session, mock_cached_models
    ):
        """Test setting agent with invalid model for provider."""
        response = await api_client.put(
            "/settings/agents/analyst",
            json={"provider": "anthropic", "model_id": "invalid-model"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_agents_with_data(
        self, api_client, mock_settings_service, mock_sync_session
    ):
        """Test listing agents with existing configurations."""
        mock_settings_service.list_agent_configs.return_value = [
            MockAgentConfig("analyst", "anthropic", "claude-3-5-sonnet-20241022"),
            MockAgentConfig("researcher", "openai", "gpt-4o"),
        ]

        response = await api_client.get("/settings/agents")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["agents"]) == 2
        assert data["agents"][0]["role"] == "analyst"
        assert data["agents"][1]["role"] == "researcher"
