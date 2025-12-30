# backend/tests/test_models/test_settings.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.settings import AgentConfig, Provider


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_provider(db_session):
    """Can create a provider with all fields."""
    provider = Provider(
        alias="claude",
        model_id="anthropic/claude-sonnet-4-20250514",
        cost_input=3.0,
        cost_output=15.0,
    )
    db_session.add(provider)
    db_session.commit()

    result = db_session.query(Provider).filter_by(alias="claude").first()
    assert result is not None
    assert result.model_id == "anthropic/claude-sonnet-4-20250514"
    assert result.is_active is True


def test_provider_alias_unique(db_session):
    """Provider alias must be unique."""
    p1 = Provider(alias="gpt", model_id="openai/gpt-4o")
    p2 = Provider(alias="gpt", model_id="openai/gpt-4o-mini")

    db_session.add(p1)
    db_session.commit()

    db_session.add(p2)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_create_agent_config(db_session):
    """Can create agent config linked to provider."""
    provider = Provider(alias="gemini", model_id="gemini/gemini-2.5-flash")
    db_session.add(provider)
    db_session.commit()

    config = AgentConfig(role="analyst", provider_alias="gemini")
    db_session.add(config)
    db_session.commit()

    result = db_session.query(AgentConfig).filter_by(role="analyst").first()
    assert result.provider_alias == "gemini"
