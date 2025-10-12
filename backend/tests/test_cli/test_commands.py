"""
Tests for CLI commands using CliRunner.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
from unittest.mock import patch, Mock
from cli.commandcenter import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config():
    """Create a temporary config file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        yield config_path


def test_cli_version(runner):
    """Test version command."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_help(runner):
    """Test help output."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "CommandCenter CLI" in result.output
    assert "analyze" in result.output
    assert "agents" in result.output
    assert "search" in result.output
    assert "config" in result.output


# Config commands tests
def test_config_init(runner):
    """Test config init command."""
    with runner.isolated_filesystem():
        config_path = Path("test_config.yaml")

        with patch("cli.config.Config.get_default_config_path", return_value=config_path):
            with patch("cli.commands.config_cmd.Config.get_default_config_path", return_value=config_path):
                result = runner.invoke(cli, ["config", "init", "--force"])

                assert result.exit_code == 0
                assert "initialized" in result.output.lower()


def test_config_init_exists_no_force(runner, temp_config):
    """Test config init fails if file exists without force."""
    temp_config.write_text("existing: config")

    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        result = runner.invoke(cli, ["config", "init"])

        assert result.exit_code == 1
        assert "already exists" in result.output.lower()


def test_config_init_force(runner, temp_config):
    """Test config init with force flag."""
    temp_config.write_text("existing: config")

    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        result = runner.invoke(cli, ["config", "init", "--force"])

        assert result.exit_code == 0


def test_config_get(runner, temp_config):
    """Test config get command."""
    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        runner.invoke(cli, ["config", "init"])
        result = runner.invoke(cli, ["config", "get", "api.url"])

        assert result.exit_code == 0
        assert "http://localhost:8000" in result.output


def test_config_set(runner, temp_config):
    """Test config set command."""
    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        runner.invoke(cli, ["config", "init"])
        result = runner.invoke(cli, ["config", "set", "api.url", "http://example.com"])

        assert result.exit_code == 0
        assert "http://example.com" in result.output

        # Verify it was saved
        result = runner.invoke(cli, ["config", "get", "api.url"])
        assert "http://example.com" in result.output


def test_config_list(runner, temp_config):
    """Test config list command."""
    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        runner.invoke(cli, ["config", "init"])
        result = runner.invoke(cli, ["config", "list"])

        assert result.exit_code == 0
        assert "api.url" in result.output
        assert "auth.token" in result.output


def test_config_path(runner, temp_config):
    """Test config path command."""
    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        result = runner.invoke(cli, ["config", "path"])

        assert result.exit_code == 0
        assert str(temp_config) in result.output


# Analyze commands tests
@patch("cli.commands.analyze.APIClient")
def test_analyze_project(mock_api_client, runner, temp_config):
    """Test analyze project command."""
    mock_api = Mock()
    mock_api.analyze_project.return_value = {
        "id": "123",
        "project_path": "/test/path",
        "technologies": [],
        "dependencies": [],
        "research_gaps": [],
    }
    mock_api_client.return_value.__enter__.return_value = mock_api

    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        runner.invoke(cli, ["config", "init"])
        result = runner.invoke(cli, ["analyze", "project", "."])

        assert result.exit_code == 0
        mock_api.analyze_project.assert_called_once()


@patch("cli.commands.analyze.APIClient")
def test_analyze_github(mock_api_client, runner, temp_config):
    """Test analyze GitHub repository."""
    mock_api = Mock()
    mock_api.analyze_github_repo.return_value = {
        "id": "456",
        "project_path": "facebook/react",
        "technologies": [],
    }
    mock_api_client.return_value.__enter__.return_value = mock_api

    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        runner.invoke(cli, ["config", "init"])
        result = runner.invoke(
            cli, ["analyze", "project", ".", "--github", "facebook/react"]
        )

        assert result.exit_code == 0
        mock_api.analyze_github_repo.assert_called_once()


@patch("cli.commands.analyze.APIClient")
def test_analyze_with_export(mock_api_client, runner, temp_config):
    """Test analyze with export option."""
    mock_api = Mock()
    mock_api.analyze_project.return_value = {
        "id": "789",
        "technologies": [],
    }
    mock_api_client.return_value.__enter__.return_value = mock_api

    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        with runner.isolated_filesystem():
            runner.invoke(cli, ["config", "init"])
            result = runner.invoke(cli, ["analyze", "project", ".", "--export", "json"])

            assert result.exit_code == 0
            assert Path("analysis-789.json").exists()


@patch("cli.commands.analyze.APIClient")
def test_analyze_stats(mock_api_client, runner, temp_config):
    """Test analyze stats command."""
    mock_api = Mock()
    mock_api.get_analysis_statistics.return_value = {
        "total_analyses": 10,
        "projects_scanned": 5,
    }
    mock_api_client.return_value.__enter__.return_value = mock_api

    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        runner.invoke(cli, ["config", "init"])
        result = runner.invoke(cli, ["analyze", "stats"])

        assert result.exit_code == 0
        mock_api.get_analysis_statistics.assert_called_once()


# Search commands tests
@patch("cli.commands.search.APIClient")
def test_search_query(mock_api_client, runner, temp_config):
    """Test search command."""
    mock_api = Mock()
    mock_api.search_knowledge.return_value = {
        "query": "test",
        "matches": [],
    }
    mock_api_client.return_value.__enter__.return_value = mock_api

    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        runner.invoke(cli, ["config", "init"])
        result = runner.invoke(cli, ["search", "test query"])

        assert result.exit_code == 0
        mock_api.search_knowledge.assert_called_once()


# Agents commands tests
@patch("cli.commands.agents.APIClient")
def test_agents_launch_no_watch(mock_api_client, runner, temp_config):
    """Test agents launch command without watching."""
    mock_api = Mock()
    mock_api.launch_agents.return_value = {
        "id": "orch-123",
        "status": "running",
    }
    mock_api_client.return_value.__enter__.return_value = mock_api

    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        runner.invoke(cli, ["config", "init"])
        result = runner.invoke(cli, ["agents", "launch", "--no-watch"])

        assert result.exit_code == 0
        assert "orch-123" in result.output
        mock_api.launch_agents.assert_called_once()


@patch("cli.commands.agents.APIClient")
def test_agents_status_list(mock_api_client, runner, temp_config):
    """Test agents status command listing orchestrations."""
    mock_api = Mock()
    mock_api.list_orchestrations.return_value = [
        {"id": "orch-1", "status": "completed"},
        {"id": "orch-2", "status": "running"},
    ]
    mock_api_client.return_value.__enter__.return_value = mock_api

    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        runner.invoke(cli, ["config", "init"])
        result = runner.invoke(cli, ["agents", "status"])

        assert result.exit_code == 0
        mock_api.list_orchestrations.assert_called_once()


@patch("cli.commands.agents.APIClient")
def test_agents_stop(mock_api_client, runner, temp_config):
    """Test agents stop command."""
    mock_api = Mock()
    mock_api.stop_orchestration.return_value = {"status": "stopped"}
    mock_api_client.return_value.__enter__.return_value = mock_api

    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        runner.invoke(cli, ["config", "init"])
        result = runner.invoke(cli, ["agents", "stop", "orch-123"])

        assert result.exit_code == 0
        mock_api.stop_orchestration.assert_called_once_with("orch-123")


@patch("cli.commands.agents.APIClient")
def test_agents_logs(mock_api_client, runner, temp_config):
    """Test agents logs command."""
    mock_api = Mock()
    mock_api.get_agent_logs.return_value = [
        {"timestamp": "2025-01-01", "level": "INFO", "message": "Test"}
    ]
    mock_api_client.return_value.__enter__.return_value = mock_api

    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        runner.invoke(cli, ["config", "init"])
        result = runner.invoke(cli, ["agents", "logs", "agent-123"])

        assert result.exit_code == 0
        mock_api.get_agent_logs.assert_called_once()


@patch("cli.commands.agents.APIClient")
def test_agents_retry(mock_api_client, runner, temp_config):
    """Test agents retry command."""
    mock_api = Mock()
    mock_api.retry_agent.return_value = {"status": "retrying"}
    mock_api_client.return_value.__enter__.return_value = mock_api

    with patch("cli.config.Config.get_default_config_path", return_value=temp_config):
        runner.invoke(cli, ["config", "init"])
        result = runner.invoke(cli, ["agents", "retry", "agent-123"])

        assert result.exit_code == 0
        mock_api.retry_agent.assert_called_once_with("agent-123")
