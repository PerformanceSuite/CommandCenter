# backend/tests/test_services/test_settings_service.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services.settings_service import SettingsService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def service(db_session):
    return SettingsService(db_session)


class TestProviderCRUD:
    def test_create_provider(self, service):
        provider = service.create_provider(
            alias="claude",
            model_id="anthropic/claude-sonnet-4",
            cost_input=3.0,
            cost_output=15.0,
        )
        assert provider.alias == "claude"
        assert provider.is_active is True

    def test_list_providers(self, service):
        service.create_provider(alias="a", model_id="model-a")
        service.create_provider(alias="b", model_id="model-b")

        providers = service.list_providers()
        assert len(providers) == 2

    def test_get_provider(self, service):
        service.create_provider(alias="gpt", model_id="openai/gpt-4o")

        provider = service.get_provider("gpt")
        assert provider is not None
        assert provider.model_id == "openai/gpt-4o"

    def test_update_provider(self, service):
        service.create_provider(alias="test", model_id="old-model")

        updated = service.update_provider("test", model_id="new-model")
        assert updated.model_id == "new-model"

    def test_delete_provider(self, service):
        service.create_provider(alias="delete-me", model_id="model")

        success = service.delete_provider("delete-me")
        assert success is True
        assert service.get_provider("delete-me") is None

    def test_set_api_key_encrypts(self, service, monkeypatch, tmp_path):
        # Use temp key path
        key_path = tmp_path / "secret.key"
        monkeypatch.setenv("COMMANDCENTER_KEY_PATH", str(key_path))

        service.create_provider(alias="secure", model_id="model")
        service.set_provider_api_key("secure", "sk-secret-key-123")

        provider = service.get_provider("secure")
        assert provider.api_key_encrypted is not None
        assert provider.api_key_encrypted != "sk-secret-key-123"


class TestAgentConfig:
    def test_get_agent_config(self, service):
        service.create_provider(alias="gemini", model_id="gemini/flash")
        service.set_agent_model("analyst", "google", "gemini/flash")

        config = service.get_agent_config("analyst")
        assert config.provider == "google"
        assert config.model_id == "gemini/flash"

    def test_list_agent_configs(self, service):
        service.create_provider(alias="p1", model_id="m1")
        service.set_agent_model("analyst", "provider1", "m1")
        service.set_agent_model("critic", "provider1", "m1")

        configs = service.list_agent_configs()
        assert len(configs) == 2


class TestSeeding:
    def test_seed_defaults_when_empty(self, service, monkeypatch, tmp_path):
        # Use temp key path
        key_path = tmp_path / "secret.key"
        monkeypatch.setenv("COMMANDCENTER_KEY_PATH", str(key_path))

        service.seed_defaults()

        providers = service.list_providers()
        assert len(providers) >= 4  # At least claude, gemini, gpt, gpt-mini

        configs = service.list_agent_configs()
        assert len(configs) == 5  # analyst, researcher, strategist, critic, chairman
