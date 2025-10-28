"""Test Postgres Dagger module."""
import pytest


def test_postgres_config_dataclass():
    """Test PostgresConfig dataclass."""
    from dagger_modules.postgres import PostgresConfig

    config = PostgresConfig(
        db_name="test",
        db_password="testpass",
        postgres_version="16",
        pgvector_version="v0.7.0"
    )

    assert config.db_name == "test"
    assert config.db_password == "testpass"
    assert config.postgres_version == "16"
    assert config.pgvector_version == "v0.7.0"


def test_postgres_stack_initialization():
    """Test PostgresStack can be initialized."""
    from dagger_modules.postgres import PostgresStack, PostgresConfig

    config = PostgresConfig()
    stack = PostgresStack(config)

    assert stack.config == config
    assert stack._connection is None
    assert stack.client is None
