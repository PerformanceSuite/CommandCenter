"""Tests for CLI entry point."""
import pytest
from click.testing import CliRunner
from app.cli.__main__ import cli


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


def test_cli_version(runner):
    """Test CLI version command."""
    result = runner.invoke(cli, ['--version'])

    assert result.exit_code == 0
    assert 'version' in result.output.lower()


def test_cli_help(runner):
    """Test CLI help command."""
    result = runner.invoke(cli, ['--help'])

    assert result.exit_code == 0
    assert 'Usage:' in result.output
    assert 'Hub Event CLI' in result.output


def test_cli_no_command_shows_help(runner):
    """Test CLI with no command shows help."""
    result = runner.invoke(cli, [])

    # Should show help by default
    assert 'Usage:' in result.output
