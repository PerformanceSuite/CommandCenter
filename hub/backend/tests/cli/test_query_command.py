"""Tests for query command."""
import pytest
from click.testing import CliRunner
from uuid import uuid4

from app.cli.__main__ import cli


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


def test_query_command_exists(runner):
    """Test query command is registered."""
    result = runner.invoke(cli, ['query', '--help'])

    assert result.exit_code == 0
    assert 'Usage:' in result.output


def test_query_with_subject_filter(runner):
    """Test query with subject filter."""
    result = runner.invoke(cli, [
        'query',
        '--subject', 'hub.test.*'
    ])

    # Should succeed (may be empty)
    assert result.exit_code == 0


def test_query_with_since_filter(runner):
    """Test query with time filter."""
    result = runner.invoke(cli, [
        'query',
        '--since', '1h'
    ])

    assert result.exit_code == 0


def test_query_with_correlation_id(runner):
    """Test query with correlation ID."""
    test_id = str(uuid4())

    result = runner.invoke(cli, [
        'query',
        '--correlation-id', test_id
    ])

    assert result.exit_code == 0


def test_query_with_limit(runner):
    """Test query with limit."""
    result = runner.invoke(cli, [
        'query',
        '--limit', '10'
    ])

    assert result.exit_code == 0


def test_query_json_output(runner):
    """Test query with JSON output format."""
    result = runner.invoke(cli, [
        'query',
        '--format', 'json'
    ])

    assert result.exit_code == 0
