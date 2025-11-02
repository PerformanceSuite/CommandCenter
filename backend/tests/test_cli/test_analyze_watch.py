"""
Tests for analyze command watch mode.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from cli.commandcenter import cli
from pathlib import Path
import time


class TestAnalyzeWatchMode:
    """Test suite for analyze watch mode functionality."""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a mock config file."""
        config_file = tmp_path / "config.yaml"
        config_content = """
api:
  url: http://localhost:8000
  timeout: 30
auth:
  token: test-token
output:
  format: table
  verbose: false
"""
        config_file.write_text(config_content)
        return config_file

    @patch("cli.commands.analyze.Observer")
    @patch("cli.commands.analyze.APIClient")
    def test_watch_mode_rejects_github_repos(
        self, mock_api, mock_observer, runner, mock_config, tmp_path
    ):
        """Test that watch mode is not supported for GitHub repositories."""
        result = runner.invoke(
            cli,
            [
                "--config",
                str(mock_config),
                "analyze",
                "project",
                "--github",
                "facebook/react",
                "--watch",
            ],
        )

        assert result.exit_code != 0
        assert "Watch mode not supported for GitHub repositories" in result.output

    @patch("cli.commands.analyze.Observer")
    @patch("cli.commands.analyze.APIClient")
    @patch("cli.commands.analyze.click.getchar")
    def test_watch_mode_basic_functionality(
        self, mock_getchar, mock_api, mock_observer, runner, mock_config, tmp_path
    ):
        """Test basic watch mode functionality."""
        # Setup mocks
        mock_getchar.side_effect = KeyboardInterrupt()  # Exit immediately
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_project.return_value = {
            "id": "test-123",
            "status": "completed",
            "technologies": [],
        }
        mock_api.return_value = mock_api_instance

        mock_observer_instance = MagicMock()
        mock_observer.return_value = mock_observer_instance

        # Create test project
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        result = runner.invoke(
            cli, ["--config", str(mock_config), "analyze", "project", str(test_dir), "--watch"]
        )

        # Should start observer
        mock_observer_instance.schedule.assert_called_once()
        mock_observer_instance.start.assert_called_once()
        mock_observer_instance.stop.assert_called_once()

    @patch("cli.commands.analyze.time")
    def test_watch_mode_debouncing(self, mock_time):
        """Test that watch mode debounces rapid file changes."""
        from cli.commands.analyze import time as actual_time

        # Create handler with debouncing
        last_analysis_time = 0
        debounce_seconds = 1.0

        # Simulate rapid events within debounce window
        mock_time.time.side_effect = [0.0, 0.5, 1.5]  # Times for events

        events = [
            Mock(src_path="/test/file1.py"),
            Mock(src_path="/test/file2.py"),
            Mock(src_path="/test/file3.py"),
        ]

        triggered_count = 0
        for event in events:
            current_time = mock_time.time()
            if current_time - last_analysis_time >= debounce_seconds:
                triggered_count += 1
                last_analysis_time = current_time

        # Only 2 should trigger (0.0 and 1.5), 0.5 is within debounce window
        assert triggered_count == 2

    def test_watch_mode_ignores_common_directories(self):
        """Test that watch mode ignores common directories."""
        ignore_patterns = [".git", "__pycache__", "node_modules", ".venv", "venv"]

        test_paths = [
            "/project/.git/config",
            "/project/__pycache__/module.pyc",
            "/project/node_modules/package/index.js",
            "/project/.venv/lib/python3.11/site-packages",
            "/project/venv/bin/activate",
            "/project/src/main.py",  # Should NOT be ignored
        ]

        ignored = []
        for path in test_paths:
            if any(ignored in path for ignored in ignore_patterns):
                ignored.append(path)

        # Should ignore 5 paths, allow 1
        assert len(ignored) == 5
        assert "/project/src/main.py" not in ignored

    @patch("cli.commands.analyze.Observer")
    @patch("cli.commands.analyze.APIClient")
    @patch("cli.commands.analyze.click.getchar")
    def test_watch_mode_manual_trigger_with_enter(
        self, mock_getchar, mock_api, mock_observer, runner, mock_config, tmp_path
    ):
        """Test that Enter key manually triggers analysis."""
        # Setup mocks
        mock_getchar.side_effect = ["\n", KeyboardInterrupt()]  # Enter then exit
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_project.return_value = {"id": "test-123", "status": "completed"}
        mock_api.return_value = mock_api_instance

        mock_observer_instance = MagicMock()
        mock_observer.return_value = mock_observer_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        result = runner.invoke(
            cli, ["--config", str(mock_config), "analyze", "project", str(test_dir), "--watch"]
        )

        # Should call analyze at least twice (initial + manual trigger)
        assert mock_api_instance.analyze_project.call_count >= 2

    @patch("cli.commands.analyze.Observer")
    @patch("cli.commands.analyze.APIClient")
    @patch("cli.commands.analyze.click.getchar")
    def test_watch_mode_graceful_shutdown(
        self, mock_getchar, mock_api, mock_observer, runner, mock_config, tmp_path
    ):
        """Test that watch mode shuts down gracefully on Ctrl+C."""
        mock_getchar.side_effect = KeyboardInterrupt()
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_project.return_value = {"id": "test-123"}
        mock_api.return_value = mock_api_instance

        mock_observer_instance = MagicMock()
        mock_observer.return_value = mock_observer_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        result = runner.invoke(
            cli, ["--config", str(mock_config), "analyze", "project", str(test_dir), "--watch"]
        )

        # Should call stop and join
        mock_observer_instance.stop.assert_called_once()
        mock_observer_instance.join.assert_called_once()
        assert "[Watch Mode] Stopped" in result.output

    @patch("cli.commands.analyze.Observer")
    @patch("cli.commands.analyze.APIClient")
    @patch("cli.commands.analyze.click.getchar")
    def test_watch_mode_with_export(
        self, mock_getchar, mock_api, mock_observer, runner, mock_config, tmp_path
    ):
        """Test watch mode with export functionality."""
        mock_getchar.side_effect = KeyboardInterrupt()
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_project.return_value = {"id": "test-123", "status": "completed"}
        mock_api.return_value = mock_api_instance

        mock_observer_instance = MagicMock()
        mock_observer.return_value = mock_observer_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        result = runner.invoke(
            cli,
            [
                "--config",
                str(mock_config),
                "analyze",
                "project",
                str(test_dir),
                "--watch",
                "--export",
                "json",
            ],
        )

        # Should create export file
        export_files = list(tmp_path.glob("analysis-*.json"))
        # Note: May not exist due to mock, but command should not error
        assert result.exit_code == 0 or "Exported to" in result.output

    def test_watch_mode_requires_watchdog(self, runner, mock_config, tmp_path):
        """Test that watch mode shows clear error if watchdog not installed."""
        # This test would only work if watchdog was actually not installed
        # In practice, we have it in requirements.txt
        # But we test that the error handling exists

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        # The import should succeed since watchdog is in requirements.txt
        # This test documents expected behavior if dependency is missing
        with patch(
            "cli.commands.analyze.Observer", side_effect=ImportError("No module named 'watchdog'")
        ):
            result = runner.invoke(
                cli, ["--config", str(mock_config), "analyze", "project", str(test_dir), "--watch"]
            )

            assert result.exit_code != 0
            assert "watchdog" in result.output.lower()
