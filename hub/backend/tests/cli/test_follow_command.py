"""Tests for follow command."""
import pytest
from click.testing import CliRunner
from app.cli.__main__ import cli


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


def test_follow_command_exists(runner):
    """Test follow command is registered."""
    result = runner.invoke(cli, ['follow', '--help'])

    assert result.exit_code == 0
    assert 'Usage:' in result.output
    assert 'follow' in result.output.lower()


def test_follow_options_exist(runner):
    """Test follow command has expected options."""
    result = runner.invoke(cli, ['follow', '--help'])

    assert result.exit_code == 0
    assert '--subject' in result.output
    assert '--format' in result.output
