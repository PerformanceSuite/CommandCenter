"""
Tests for Git Command Security

Tests for CWE-78 (OS Command Injection) fixes
"""

import pytest
from pathlib import Path
import tempfile
import os

from app.services.git_security import GitCommandSanitizer


class TestBranchNameSanitization:
    """Test suite for branch name sanitization"""

    def test_valid_branch_names(self):
        """Test valid branch name sanitization"""
        valid_branches = [
            "feature/test",
            "bugfix/issue-123",
            "release/v1.0.0",
            "main",
            "develop",
            "feature_test",
            "fix-bug",
            "123-numeric-start",
        ]

        for branch in valid_branches:
            result = GitCommandSanitizer.sanitize_branch_name(branch)
            assert result == branch

    def test_reject_command_injection(self):
        """Test command injection rejection"""
        malicious_branches = [
            "test; rm -rf /",
            "test && rm -rf /",
            "test | cat /etc/passwd",
            "test; cat /etc/passwd #",
            "test`whoami`",
            "test$(whoami)",
            "test > /etc/passwd",
        ]

        for branch in malicious_branches:
            with pytest.raises(ValueError, match="(Dangerous pattern|Invalid branch name)"):
                GitCommandSanitizer.sanitize_branch_name(branch)

    def test_reject_invalid_patterns(self):
        """Test rejection of invalid branch patterns"""
        invalid_branches = [
            "-starts-with-hyphen",
            ".starts-with-dot",
            "contains..double-dots",
            "ends-with.lock",
            "contains//double-slash",
            "contains spaces",
            "contains@special",
            "contains#hash",
        ]

        for branch in invalid_branches:
            with pytest.raises(ValueError):
                GitCommandSanitizer.sanitize_branch_name(branch)

    def test_empty_branch_name(self):
        """Test empty branch name rejection"""
        with pytest.raises(ValueError, match="Branch name cannot be empty"):
            GitCommandSanitizer.sanitize_branch_name("")

    def test_reserved_branch_names(self):
        """Test reserved branch name rejection"""
        reserved = ["HEAD", "master", "main"]

        for name in reserved:
            with pytest.raises(ValueError, match="reserved"):
                GitCommandSanitizer.sanitize_branch_name(name)

    def test_branch_name_too_long(self):
        """Test overly long branch name rejection"""
        long_branch = "a" * 256
        with pytest.raises(ValueError, match="too long"):
            GitCommandSanitizer.sanitize_branch_name(long_branch)

    def test_branch_with_prefix_allowed(self):
        """Test that prefixed reserved names are allowed"""
        # feature/main should be allowed (not bare 'main')
        result = GitCommandSanitizer.sanitize_branch_name("feature/main")
        assert result == "feature/main"


class TestCommitMessageSanitization:
    """Test suite for commit message sanitization"""

    def test_valid_commit_messages(self):
        """Test valid commit message sanitization"""
        valid_messages = [
            "Fix bug in authentication",
            "Add new feature: user dashboard",
            "Update dependencies to latest versions",
            "Refactor: improve code structure",
            "docs: Update README with examples",
            "Multi-line commit\n\nWith detailed description",
        ]

        for message in valid_messages:
            result = GitCommandSanitizer.sanitize_commit_message(message)
            assert result == message.strip()

    def test_reject_dangerous_patterns(self):
        """Test dangerous pattern rejection in commit messages"""
        dangerous_messages = [
            "Fix bug; rm -rf /",
            "Update && malicious command",
            "Feature | cat /etc/passwd",
            "Fix `whoami`",
            "Update $(dangerous)",
        ]

        for message in dangerous_messages:
            with pytest.raises(ValueError, match="Dangerous pattern"):
                GitCommandSanitizer.sanitize_commit_message(message)

    def test_empty_commit_message(self):
        """Test empty commit message rejection"""
        with pytest.raises(ValueError, match="Commit message cannot be empty"):
            GitCommandSanitizer.sanitize_commit_message("")

    def test_commit_message_too_long(self):
        """Test overly long commit message rejection"""
        long_message = "a" * 5001
        with pytest.raises(ValueError, match="too long"):
            GitCommandSanitizer.sanitize_commit_message(long_message)

    def test_whitespace_trimming(self):
        """Test that whitespace is trimmed"""
        message = "  Fix bug  \n"
        result = GitCommandSanitizer.sanitize_commit_message(message)
        assert result == "Fix bug"


class TestFilePathSanitization:
    """Test suite for file path sanitization"""

    def test_valid_relative_path(self):
        """Test valid relative path sanitization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            result = GitCommandSanitizer.sanitize_file_path("subdir/file.txt", base)

            # Should be within base directory
            assert result.is_relative_to(base)
            assert str(result).startswith(str(base))

    def test_prevent_path_traversal(self):
        """Test path traversal prevention"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            traversal_attempts = [
                "../../etc/passwd",
                "../../../root/.ssh/id_rsa",
                "subdir/../../etc/passwd",
                "./../etc/passwd",
            ]

            for path in traversal_attempts:
                with pytest.raises(ValueError, match="Path traversal detected"):
                    GitCommandSanitizer.sanitize_file_path(path, base)

    def test_absolute_path_outside_base(self):
        """Test absolute path outside base directory rejection"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            with pytest.raises(ValueError, match="Path traversal detected"):
                GitCommandSanitizer.sanitize_file_path("/etc/passwd", base)

    def test_absolute_path_inside_base(self):
        """Test absolute path inside base directory is allowed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            safe_path = base / "safe" / "file.txt"

            result = GitCommandSanitizer.sanitize_file_path(str(safe_path), base)
            assert result == safe_path.resolve()

    def test_empty_path(self):
        """Test empty path rejection"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            with pytest.raises(ValueError, match="File path cannot be empty"):
                GitCommandSanitizer.sanitize_file_path("", base)


class TestTagNameSanitization:
    """Test suite for tag name sanitization"""

    def test_valid_tag_names(self):
        """Test valid tag name sanitization"""
        valid_tags = [
            "v1.0.0",
            "release-1.2.3",
            "beta_2",
            "rc1",
        ]

        for tag in valid_tags:
            result = GitCommandSanitizer.sanitize_tag_name(tag)
            assert result == tag

    def test_reject_invalid_tag_names(self):
        """Test invalid tag name rejection"""
        invalid_tags = [
            "-starts-with-hyphen",
            ".starts-with-dot",
            "contains..dots",
            "has spaces",
            "has/slash",
        ]

        for tag in invalid_tags:
            with pytest.raises(ValueError):
                GitCommandSanitizer.sanitize_tag_name(tag)


class TestSafeGitCommand:
    """Test suite for safe git command building"""

    def test_build_safe_command(self):
        """Test safe git command building"""
        args = ['checkout', '-b', 'feature/test']
        result = GitCommandSanitizer.build_safe_git_command(args)

        assert result == ['git', 'checkout', '-b', 'feature/test']

    def test_empty_args(self):
        """Test empty arguments rejection"""
        with pytest.raises(ValueError, match="cannot be empty"):
            GitCommandSanitizer.build_safe_git_command([])

    def test_non_string_args(self):
        """Test non-string arguments rejection"""
        with pytest.raises(ValueError, match="must be strings"):
            GitCommandSanitizer.build_safe_git_command(['checkout', 123])


class TestRemoteURLValidation:
    """Test suite for remote URL validation"""

    def test_valid_https_url(self):
        """Test valid HTTPS URL"""
        url = "https://github.com/user/repo.git"
        result = GitCommandSanitizer.validate_remote_url(url)
        assert result == url

    def test_valid_ssh_url(self):
        """Test valid SSH URL"""
        url = "git@github.com:user/repo.git"
        result = GitCommandSanitizer.validate_remote_url(url)
        assert result == url

    def test_invalid_protocol(self):
        """Test invalid protocol rejection"""
        url = "file:///etc/passwd"
        with pytest.raises(ValueError, match="Invalid remote URL protocol"):
            GitCommandSanitizer.validate_remote_url(url)

    def test_dangerous_patterns_in_url(self):
        """Test dangerous patterns in URL rejection"""
        dangerous_urls = [
            "https://example.com/repo.git; rm -rf /",
            "git@example.com:user/repo.git && malicious",
        ]

        for url in dangerous_urls:
            with pytest.raises(ValueError, match="Dangerous pattern"):
                GitCommandSanitizer.validate_remote_url(url)

    def test_empty_url(self):
        """Test empty URL rejection"""
        with pytest.raises(ValueError, match="Remote URL cannot be empty"):
            GitCommandSanitizer.validate_remote_url("")


class TestIntegration:
    """Integration tests for git security"""

    def test_full_workflow_protection(self):
        """Test complete git workflow with security"""
        # Sanitize branch name
        branch = GitCommandSanitizer.sanitize_branch_name("feature/test-123")
        assert branch == "feature/test-123"

        # Sanitize commit message
        message = GitCommandSanitizer.sanitize_commit_message("Add new feature")
        assert message == "Add new feature"

        # Build safe command
        cmd = GitCommandSanitizer.build_safe_git_command(['checkout', '-b', branch])
        assert cmd == ['git', 'checkout', '-b', 'feature/test-123']

        # This command can be safely executed with subprocess.run(cmd, shell=False)

    def test_attack_prevention(self):
        """Test that common attacks are prevented"""
        # Command injection attempts
        with pytest.raises(ValueError):
            GitCommandSanitizer.sanitize_branch_name("feature; rm -rf /")

        # Path traversal attempts
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError):
                GitCommandSanitizer.sanitize_file_path("../../etc/passwd", Path(tmpdir))

        # Dangerous commit messages
        with pytest.raises(ValueError):
            GitCommandSanitizer.sanitize_commit_message("Fix && malicious")
