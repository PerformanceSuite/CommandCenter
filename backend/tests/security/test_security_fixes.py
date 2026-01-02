"""
Security validation tests for critical fixes applied in Session 33.

Tests the 5 immediate-priority security fixes:
1. Session fixation prevention (MCP)
2. Error message sanitization
3. Path traversal protection
4. CLI setup.py
5. Secure token storage
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from cli.config import Config

# Test imports - grouped here to satisfy E402
from app.mcp.connection import MCPConnectionManager, MCPSession
from app.mcp.protocol import MCPProtocolHandler
from app.routers.projects import validate_project_path


class TestSessionFixationPrevention:
    """Test that session IDs are always generated server-side."""

    def test_session_id_always_generated_server_side(self):
        """Session ID should always be generated, never client-provided."""
        # Create session without providing session_id
        session1 = MCPSession(client_info={"name": "test"})

        # Session ID should be a valid UUID
        assert session1.session_id is not None
        assert len(session1.session_id) == 36  # UUID format
        assert "-" in session1.session_id

        # Create another session
        session2 = MCPSession(client_info={"name": "test"})

        # Session IDs should be different (unique)
        assert session1.session_id != session2.session_id

    def test_session_id_parameter_removed(self):
        """MCPSession.__init__ should not accept session_id parameter."""
        # This should raise TypeError if session_id parameter exists
        with pytest.raises(TypeError):
            MCPSession(session_id="attacker-controlled-id", client_info={})

    @pytest.mark.asyncio
    async def test_connection_manager_generates_unique_sessions(self):
        """Connection manager should create unique sessions."""
        manager = MCPConnectionManager(max_connections=10)

        # Create multiple sessions
        session1 = await manager.create_session({"client": "1"})
        session2 = await manager.create_session({"client": "2"})
        session3 = await manager.create_session({"client": "3"})

        # All session IDs should be unique
        session_ids = {session1.session_id, session2.session_id, session3.session_id}
        assert len(session_ids) == 3  # No duplicates


# Test 2: Error Message Sanitization
class TestErrorMessageSanitization:
    """Test that exception details are not leaked to clients."""

    @pytest.mark.asyncio
    async def test_internal_error_sanitized(self):
        """Internal errors should not leak exception messages to clients."""
        handler = MCPProtocolHandler()

        # Create an exception with sensitive information
        sensitive_exception = ValueError(
            "Database connection failed: user=admin password=secret123 host=internal-db.company.com"
        )

        # Handle the exception
        response = await handler.handle_exception(sensitive_exception, request_id=1)

        # Response should be an error response
        assert response.error is not None
        assert response.error.code == -32603  # Internal error

        # Error message should be generic
        assert response.error.message == "Internal server error"
        assert "password" not in response.error.message
        assert "secret123" not in response.error.message
        assert "admin" not in response.error.message

        # Error data should only contain error type, not message
        assert response.error.data is not None
        assert response.error.data.get("type") == "ValueError"
        # Should NOT contain the sensitive message
        assert "password" not in str(response.error.data)

    @pytest.mark.asyncio
    async def test_multiple_error_types_sanitized(self):
        """Different exception types should all be sanitized."""
        handler = MCPProtocolHandler()

        # Test various exception types
        exceptions = [
            RuntimeError("Internal API key: sk-1234567890abcdef"),
            ConnectionError("Failed to connect to 192.168.1.100:5432"),
            PermissionError("/etc/passwd access denied for user john"),
        ]

        for exc in exceptions:
            response = await handler.handle_exception(exc, request_id=1)

            # All should return generic message
            assert response.error.message == "Internal server error"
            # Only type should be in data
            assert response.error.data.get("type") == type(exc).__name__


# Test 3: Path Traversal Protection
class TestPathTraversalProtection:
    """Test that path traversal attacks are prevented."""

    def test_path_outside_allowed_dirs_rejected(self):
        """Paths outside allowed directories should be rejected."""
        # Try to access /etc/passwd
        with pytest.raises(ValueError) as exc_info:
            validate_project_path("/etc/passwd")

        assert "not within allowed analysis directories" in str(exc_info.value).lower()

    def test_path_traversal_with_dotdot_rejected(self):
        """Path traversal with ../ should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file structure
            allowed_dir = Path(tmpdir) / "allowed"
            allowed_dir.mkdir()
            secret_file = Path(tmpdir) / "secret.txt"
            secret_file.write_text("sensitive data")

            # Try to traverse up from allowed dir
            traversal_path = str(allowed_dir / ".." / "secret.txt")

            with pytest.raises(ValueError) as exc_info:
                validate_project_path(traversal_path)

            # Should be rejected
            assert "not within allowed" in str(exc_info.value).lower()

    def test_symlink_escape_rejected(self):
        """Symlinks that escape allowed directories should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            allowed_dir = Path(tmpdir) / "allowed"
            allowed_dir.mkdir()

            # Create symlink to /etc
            symlink_path = allowed_dir / "link"
            try:
                symlink_path.symlink_to("/etc")
            except OSError:
                pytest.skip("Cannot create symlinks on this system")

            # Try to access through symlink
            with pytest.raises(ValueError):
                validate_project_path(str(symlink_path))

    def test_nonexistent_path_rejected(self):
        """Non-existent paths should be rejected."""
        fake_path = "/tmp/nonexistent-path-12345678"

        with pytest.raises(ValueError) as exc_info:
            validate_project_path(fake_path)

        assert "does not exist" in str(exc_info.value).lower()

    def test_valid_path_accepted(self):
        """Valid paths within allowed directories should be accepted."""
        # This test depends on allowed directories being configured
        # We'll test with /tmp which is typically allowed in dev
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch ALLOWED_ANALYSIS_DIRS for this test
            from app.routers import projects

            original_dirs = projects.ALLOWED_ANALYSIS_DIRS
            tmpdir_path = Path(tmpdir).resolve()

            try:
                # Set the allowed dir to the resolved temp directory
                projects.ALLOWED_ANALYSIS_DIRS = [tmpdir_path]

                # Create a valid project directory
                project_dir = tmpdir_path / "my-project"
                project_dir.mkdir()

                # Should not raise
                validated_path = validate_project_path(str(project_dir))
                assert validated_path == project_dir.resolve()

            finally:
                projects.ALLOWED_ANALYSIS_DIRS = original_dirs


# Test 4: CLI Setup.py Installation
class TestCLISetup:
    """Test that CLI setup.py is properly configured."""

    def test_setup_py_exists(self):
        """setup.py file should exist."""
        setup_path = Path(__file__).parent.parent.parent / "setup.py"
        assert setup_path.exists(), "setup.py not found in backend/"

    def test_setup_py_has_entry_point(self):
        """setup.py should define console_scripts entry point."""
        setup_path = Path(__file__).parent.parent.parent / "setup.py"
        setup_content = setup_path.read_text()

        # Check for entry_points definition
        assert "entry_points" in setup_content
        assert "console_scripts" in setup_content
        assert "commandcenter=cli.commandcenter:cli" in setup_content

    def test_setup_py_includes_keyring_dependency(self):
        """setup.py should include keyring for secure token storage."""
        setup_path = Path(__file__).parent.parent.parent / "setup.py"
        setup_content = setup_path.read_text()

        # Check for keyring in install_requires
        assert "keyring" in setup_content
        assert "install_requires" in setup_content


# Test 5: Secure Token Storage
class TestSecureTokenStorage:
    """Test that tokens are stored securely in system keyring."""

    @patch("keyring.set_password")
    @patch("keyring.get_password")
    @patch("keyring.delete_password")
    def test_token_saved_to_keyring(self, mock_delete, mock_get, mock_set):
        """Tokens should be saved to system keyring, not config file."""
        config = Config()
        test_token = "test-api-token-12345"

        # Save token
        config.save_token(test_token)

        # Should call keyring.set_password
        mock_set.assert_called_once_with("commandcenter", "api_token", test_token)

    @patch("keyring.get_password", return_value="stored-token")
    def test_token_loaded_from_keyring(self, mock_get):
        """Tokens should be loaded from system keyring."""
        config = Config()

        # Load token
        token = config.load_token()

        # Should call keyring.get_password
        mock_get.assert_called_once_with("commandcenter", "api_token")
        assert token == "stored-token"

    @patch("keyring.delete_password")
    def test_token_deleted_from_keyring(self, mock_delete):
        """Tokens should be deleted from system keyring."""
        config = Config()

        # Delete token
        config.delete_token()

        # Should call keyring.delete_password
        mock_delete.assert_called_once_with("commandcenter", "api_token")

    @patch("keyring.get_password", return_value=None)
    def test_has_token_returns_false_when_no_token(self, mock_get):
        """has_token() should return False when no token exists."""
        config = Config()

        assert config.has_token() is False

    @patch("keyring.get_password", return_value="some-token")
    def test_has_token_returns_true_when_token_exists(self, mock_get):
        """has_token() should return True when token exists."""
        config = Config()

        assert config.has_token() is True

    def test_token_not_in_config_file(self):
        """Tokens should NOT be saved to config YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            config = Config()
            config.save(config_path)

            # Read config file
            config_content = config_path.read_text()

            # Token should not be in config file
            assert "token" not in config_content.lower()
            # AuthConfig should be present but empty (no token field)
            assert "auth:" in config_content


# Test 6: Integration Test - All Fixes Together
class TestSecurityIntegration:
    """Integration tests combining multiple security fixes."""

    @pytest.mark.asyncio
    async def test_mcp_session_creation_secure_end_to_end(self):
        """Test complete MCP session creation flow is secure."""
        manager = MCPConnectionManager()

        # Create session
        session = await manager.create_session({"client": "test"})

        # Session ID should be server-generated
        assert session.session_id is not None
        assert len(session.session_id) == 36

        # Simulate an error in the session
        protocol_handler = MCPProtocolHandler()
        sensitive_error = RuntimeError(f"Session {session.session_id} failed: internal details")

        error_response = await protocol_handler.handle_exception(sensitive_error)

        # Error should be sanitized
        assert error_response.error.message == "Internal server error"
        assert session.session_id not in error_response.error.message

    def test_project_analysis_security_end_to_end(self):
        """Test that project analysis is secure against path traversal."""
        # Attempt to analyze /etc/passwd
        with pytest.raises(ValueError) as exc_info:
            validate_project_path("/etc/passwd")

        # Should be blocked
        assert "not within allowed" in str(exc_info.value).lower()

        # Attempt path traversal
        with pytest.raises(ValueError):
            validate_project_path("../../etc/passwd")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
