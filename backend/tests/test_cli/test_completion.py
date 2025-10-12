"""
Tests for shell completion command.
"""

import pytest
from click.testing import CliRunner
from cli.commands.completion import completion


class TestCompletionCommand:
    """Test suite for completion command."""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()

    def test_bash_completion_generates_script(self, runner):
        """Test that bash completion generates valid script."""
        result = runner.invoke(completion, ["bash"])

        assert result.exit_code == 0
        assert "_commandcenter_completion()" in result.output
        assert "complete -o nosort -F _commandcenter_completion commandcenter" in result.output
        assert "COMP_WORDS" in result.output
        assert "COMP_CWORD" in result.output

    def test_zsh_completion_generates_script(self, runner):
        """Test that zsh completion generates valid script."""
        result = runner.invoke(completion, ["zsh"])

        assert result.exit_code == 0
        assert "#compdef commandcenter" in result.output
        assert "_commandcenter()" in result.output
        assert "compdef _commandcenter commandcenter" in result.output
        assert "COMP_WORDS" in result.output

    def test_fish_completion_generates_script(self, runner):
        """Test that fish completion generates valid script."""
        result = runner.invoke(completion, ["fish"])

        assert result.exit_code == 0
        assert "_commandcenter_completion" in result.output
        assert "complete --no-files --command commandcenter" in result.output
        assert "_COMMANDCENTER_COMPLETE=fish_complete" in result.output

    def test_completion_requires_shell_argument(self, runner):
        """Test that completion command requires shell argument."""
        result = runner.invoke(completion, [])

        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_completion_rejects_invalid_shell(self, runner):
        """Test that completion rejects invalid shell names."""
        result = runner.invoke(completion, ["powershell"])

        assert result.exit_code != 0
        assert "Invalid value" in result.output or "Invalid choice" in result.output

    def test_bash_completion_handles_file_types(self, runner):
        """Test that bash completion script handles file type completions."""
        result = runner.invoke(completion, ["bash"])

        assert result.exit_code == 0
        # Check for file type handling
        assert "file" in result.output
        assert "dir" in result.output
        assert "plain" in result.output

    def test_zsh_completion_handles_file_types(self, runner):
        """Test that zsh completion script handles file type completions."""
        result = runner.invoke(completion, ["zsh"])

        assert result.exit_code == 0
        # Check for file type handling
        assert "_path_files" in result.output
        assert "file" in result.output
        assert "dir" in result.output

    def test_fish_completion_handles_file_types(self, runner):
        """Test that fish completion script handles file type completions."""
        result = runner.invoke(completion, ["fish"])

        assert result.exit_code == 0
        # Check for file type handling
        assert "__fish_complete_directories" in result.output
        assert "__fish_complete_path" in result.output

    def test_bash_completion_script_syntax(self, runner):
        """Test that bash completion script has valid syntax."""
        result = runner.invoke(completion, ["bash"])

        assert result.exit_code == 0
        # Basic bash syntax checks
        assert result.output.count("_commandcenter_completion() {") == 1
        assert "local IFS=" in result.output
        assert "return 0" in result.output

    def test_zsh_completion_script_syntax(self, runner):
        """Test that zsh completion script has valid syntax."""
        result = runner.invoke(completion, ["zsh"])

        assert result.exit_code == 0
        # Basic zsh syntax checks
        assert result.output.count("_commandcenter() {") == 1
        assert "local -a" in result.output

    def test_completion_output_is_executable_script(self, runner):
        """Test that completion output is a valid executable script."""
        for shell in ["bash", "zsh", "fish"]:
            result = runner.invoke(completion, [shell])

            assert result.exit_code == 0
            assert len(result.output) > 100  # Should be substantial script
            assert "\n" in result.output  # Should be multiline
