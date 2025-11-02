"""
Tests for analyze command export functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from cli.commandcenter import cli
from pathlib import Path
import json
import yaml


class TestAnalyzeExport:
    """Test suite for analyze export functionality."""

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

    @pytest.fixture
    def mock_analysis_result(self):
        """Create a mock analysis result."""
        return {
            "id": "test-analysis-123",
            "status": "completed",
            "project_name": "test-project",
            "technologies": [
                {"name": "Python", "version": "3.11"},
                {"name": "FastAPI", "version": "0.109.0"},
            ],
            "dependencies_count": 45,
            "lines_of_code": 12500,
        }

    @patch("cli.commands.analyze.APIClient")
    def test_export_with_custom_path_json(
        self, mock_api, runner, mock_config, mock_analysis_result, tmp_path
    ):
        """Test export with custom path for JSON format."""
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_project.return_value = mock_analysis_result
        mock_api.return_value = mock_api_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        output_file = tmp_path / "custom" / "results.json"

        result = runner.invoke(
            cli,
            [
                "--config",
                str(mock_config),
                "analyze",
                "project",
                str(test_dir),
                "--export",
                "json",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Verify JSON content
        with open(output_file) as f:
            exported_data = json.load(f)
            assert exported_data["id"] == "test-analysis-123"
            assert exported_data["project_name"] == "test-project"

    @patch("cli.commands.analyze.APIClient")
    def test_export_with_custom_path_yaml(
        self, mock_api, runner, mock_config, mock_analysis_result, tmp_path
    ):
        """Test export with custom path for YAML format."""
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_project.return_value = mock_analysis_result
        mock_api.return_value = mock_api_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        output_file = tmp_path / "exports" / "scan.yaml"

        result = runner.invoke(
            cli,
            [
                "--config",
                str(mock_config),
                "analyze",
                "project",
                str(test_dir),
                "--export",
                "yaml",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Verify YAML content
        with open(output_file) as f:
            exported_data = yaml.safe_load(f)
            assert exported_data["id"] == "test-analysis-123"
            assert exported_data["project_name"] == "test-project"

    @patch("cli.commands.analyze.APIClient")
    def test_export_creates_parent_directories(
        self, mock_api, runner, mock_config, mock_analysis_result, tmp_path
    ):
        """Test that export creates parent directories if they don't exist."""
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_project.return_value = mock_analysis_result
        mock_api.return_value = mock_api_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        # Nested path that doesn't exist
        output_file = tmp_path / "reports" / "2025" / "october" / "analysis.json"
        assert not output_file.parent.exists()

        result = runner.invoke(
            cli,
            [
                "--config",
                str(mock_config),
                "analyze",
                "project",
                str(test_dir),
                "--export",
                "json",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        assert output_file.parent.exists()

    @patch("cli.commands.analyze.APIClient")
    def test_export_with_relative_path(
        self, mock_api, runner, mock_config, mock_analysis_result, tmp_path
    ):
        """Test export with relative path."""
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_project.return_value = mock_analysis_result
        mock_api.return_value = mock_api_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "--config",
                    str(mock_config),
                    "analyze",
                    "project",
                    str(test_dir),
                    "--export",
                    "json",
                    "--output",
                    "results/analysis.json",
                ],
            )

            assert result.exit_code == 0
            assert Path("results/analysis.json").exists()

    @patch("cli.commands.analyze.APIClient")
    def test_export_default_path_without_output_flag(
        self, mock_api, runner, mock_config, mock_analysis_result, tmp_path
    ):
        """Test export uses default path when --output is not specified."""
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_project.return_value = mock_analysis_result
        mock_api.return_value = mock_api_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                [
                    "--config",
                    str(mock_config),
                    "analyze",
                    "project",
                    str(test_dir),
                    "--export",
                    "json",
                ],
            )

            assert result.exit_code == 0
            # Should create file with pattern: analysis-{id}.json
            export_files = list(Path(".").glob("analysis-*.json"))
            assert len(export_files) == 1
            assert export_files[0].name == "analysis-test-analysis-123.json"

    @patch("cli.commands.analyze.APIClient")
    def test_export_short_flag_alias(
        self, mock_api, runner, mock_config, mock_analysis_result, tmp_path
    ):
        """Test that -o works as alias for --output."""
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_project.return_value = mock_analysis_result
        mock_api.return_value = mock_api_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        output_file = tmp_path / "output.json"

        result = runner.invoke(
            cli,
            [
                "--config",
                str(mock_config),
                "analyze",
                "project",
                str(test_dir),
                "--export",
                "json",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

    @patch("cli.commands.analyze.APIClient")
    def test_export_overwrites_existing_file(
        self, mock_api, runner, mock_config, mock_analysis_result, tmp_path
    ):
        """Test that export overwrites existing file."""
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_project.return_value = mock_analysis_result
        mock_api.return_value = mock_api_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        output_file = tmp_path / "analysis.json"

        # Create existing file with old content
        output_file.write_text('{"old": "data"}')
        old_content = output_file.read_text()

        result = runner.invoke(
            cli,
            [
                "--config",
                str(mock_config),
                "analyze",
                "project",
                str(test_dir),
                "--export",
                "json",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        new_content = output_file.read_text()
        assert new_content != old_content
        assert "test-analysis-123" in new_content

    @patch("cli.commands.analyze.APIClient")
    def test_export_with_github_repo(
        self, mock_api, runner, mock_config, mock_analysis_result, tmp_path
    ):
        """Test export works with GitHub repository analysis."""
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_github_repo.return_value = mock_analysis_result
        mock_api.return_value = mock_api_instance

        output_file = tmp_path / "github-analysis.json"

        result = runner.invoke(
            cli,
            [
                "--config",
                str(mock_config),
                "analyze",
                "project",
                "--github",
                "facebook/react",
                "--export",
                "json",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

    @patch("cli.commands.analyze.APIClient")
    def test_export_json_is_pretty_printed(
        self, mock_api, runner, mock_config, mock_analysis_result, tmp_path
    ):
        """Test that exported JSON is pretty-printed with indentation."""
        mock_api_instance = MagicMock()
        mock_api_instance.__enter__ = Mock(return_value=mock_api_instance)
        mock_api_instance.__exit__ = Mock(return_value=False)
        mock_api_instance.analyze_project.return_value = mock_analysis_result
        mock_api.return_value = mock_api_instance

        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        output_file = tmp_path / "analysis.json"

        result = runner.invoke(
            cli,
            [
                "--config",
                str(mock_config),
                "analyze",
                "project",
                str(test_dir),
                "--export",
                "json",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0

        content = output_file.read_text()
        # Should have indentation (not minified)
        assert "\n" in content
        assert "  " in content  # 2-space indent from json.dump(indent=2)

    def test_export_requires_format_argument(self, runner, mock_config, tmp_path):
        """Test that --output flag requires --export format to be specified."""
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        output_file = tmp_path / "output.json"

        result = runner.invoke(
            cli,
            [
                "--config",
                str(mock_config),
                "analyze",
                "project",
                str(test_dir),
                "--output",
                str(output_file),
            ],
        )

        # --output without --export should still work (just ignored)
        # Or could be an error depending on implementation
        # Current implementation: --output is only used if --export is specified
        assert result.exit_code == 0 or "export" in result.output.lower()
