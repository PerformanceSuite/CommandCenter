# backend/tests/test_routers/test_settings.py
"""Tests for settings router endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app


@pytest.fixture
def client(monkeypatch, tmp_path):
    # Use temp key path for encryption
    key_path = tmp_path / "secret.key"
    monkeypatch.setenv("COMMANDCENTER_KEY_PATH", str(key_path))

    # Create in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Override the sync session factory
    def override_get_sync_session():
        return TestingSessionLocal()

    # Monkey-patch the module's get_sync_session
    import app.routers.settings as settings_module

    original_func = settings_module.get_sync_session
    settings_module.get_sync_session = override_get_sync_session

    with TestClient(app) as c:
        yield c

    # Restore original
    settings_module.get_sync_session = original_func


class TestAgentConfigEndpoints:
    def test_list_agents_empty(self, client):
        response = client.get("/api/v1/settings/agents")
        assert response.status_code == 200
        assert response.json() == {"agents": []}

    def test_seed_defaults(self, client):
        response = client.post("/api/v1/settings/seed")
        assert response.status_code == 200
        assert "Seeded" in response.json()["message"]

        # After seeding, agents should be populated
        response = client.get("/api/v1/settings/agents")
        assert response.status_code == 200
        agents = response.json()["agents"]
        assert len(agents) == 5  # analyst, researcher, strategist, critic, chairman

    def test_set_agent_provider(self, client):
        # Seed first
        client.post("/api/v1/settings/seed")

        # Update an agent's provider
        response = client.put(
            "/api/v1/settings/agents/analyst",
            json={"provider_alias": "gpt"},
        )
        assert response.status_code == 200
        assert response.json()["role"] == "analyst"
        assert response.json()["provider_alias"] == "gpt"

    def test_set_agent_provider_invalid(self, client):
        # Try to set with non-existent provider
        response = client.put(
            "/api/v1/settings/agents/analyst",
            json={"provider_alias": "nonexistent"},
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]
