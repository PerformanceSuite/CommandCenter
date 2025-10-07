"""
Tests for MCP Authentication Manager

Tests for CWE-306 (Missing Authentication) fixes
"""

import pytest
from datetime import datetime, timedelta
import time

from app.mcp.auth import MCPAuthManager


class TestMCPAuthManager:
    """Test suite for MCP authentication manager"""

    def test_generate_token(self):
        """Test MCP token generation"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")
        token, expires_at = auth.generate_session_token("test-client")

        # Token should be URL-safe base64 (43 chars for 32 bytes)
        assert len(token) == 43
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in token)

        # Expiration should be in the future
        assert expires_at > datetime.utcnow()
        assert expires_at < datetime.utcnow() + timedelta(hours=25)

    def test_validate_token(self):
        """Test MCP token validation"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")
        token, _ = auth.generate_session_token("test-client")

        # Validate token
        valid, client_id = auth.validate_token(token)
        assert valid is True
        assert client_id == "test-client"

    def test_validate_invalid_token(self):
        """Test invalid token rejection"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")

        # Non-existent token
        valid, client_id = auth.validate_token("invalid-token-does-not-exist")
        assert valid is False
        assert client_id is None

    def test_validate_empty_token(self):
        """Test empty token rejection"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")

        valid, client_id = auth.validate_token("")
        assert valid is False
        assert client_id is None

    def test_expired_token(self):
        """Test expired token rejection"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")

        # Generate token with very short TTL
        token, _ = auth.generate_session_token("test-client", ttl_hours=1/3600)  # 1 second

        # Wait for expiration
        time.sleep(2)

        # Token should be invalid
        valid, client_id = auth.validate_token(token)
        assert valid is False
        assert client_id is None

    def test_revoke_token(self):
        """Test token revocation"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")
        token, _ = auth.generate_session_token("test-client")

        # Token should be valid
        valid, _ = auth.validate_token(token)
        assert valid is True

        # Revoke token
        revoked = auth.revoke_token(token)
        assert revoked is True

        # Token should now be invalid
        valid, _ = auth.validate_token(token)
        assert valid is False

    def test_revoke_nonexistent_token(self):
        """Test revoking token that doesn't exist"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")

        revoked = auth.revoke_token("nonexistent-token")
        assert revoked is False

    def test_revoke_all_client_tokens(self):
        """Test revoking all tokens for a client"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")

        # Create multiple tokens for same client
        token1, _ = auth.generate_session_token("client1")
        token2, _ = auth.generate_session_token("client1")
        token3, _ = auth.generate_session_token("client2")

        # Revoke all tokens for client1
        count = auth.revoke_all_client_tokens("client1")
        assert count == 2

        # client1 tokens should be invalid
        valid, _ = auth.validate_token(token1)
        assert valid is False
        valid, _ = auth.validate_token(token2)
        assert valid is False

        # client2 token should still be valid
        valid, _ = auth.validate_token(token3)
        assert valid is True

    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")

        # Create some valid and expired tokens
        token1, _ = auth.generate_session_token("client1", ttl_hours=24)
        token2, _ = auth.generate_session_token("client2", ttl_hours=1/3600)  # 1 second

        # Wait for one to expire
        time.sleep(2)

        # Cleanup
        count = auth.cleanup_expired_tokens()
        assert count == 1

        # Valid token should still work
        valid, _ = auth.validate_token(token1)
        assert valid is True

    def test_get_active_sessions_count(self):
        """Test active sessions count"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")

        # Initially no sessions
        assert auth.get_active_sessions_count() == 0

        # Create some sessions
        auth.generate_session_token("client1")
        auth.generate_session_token("client2")
        assert auth.get_active_sessions_count() == 2

    def test_custom_ttl(self):
        """Test custom TTL hours"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")

        # 48-hour token
        token, expires_at = auth.generate_session_token("test-client", ttl_hours=48)

        expected_expiry = datetime.utcnow() + timedelta(hours=48)
        assert abs((expires_at - expected_expiry).total_seconds()) < 5

    def test_invalid_client_id(self):
        """Test empty client ID rejection"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")

        with pytest.raises(ValueError, match="Client ID cannot be empty"):
            auth.generate_session_token("")

    def test_invalid_ttl(self):
        """Test invalid TTL rejection"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")

        # Zero TTL
        with pytest.raises(ValueError, match="TTL must be between"):
            auth.generate_session_token("client", ttl_hours=0)

        # Negative TTL
        with pytest.raises(ValueError, match="TTL must be between"):
            auth.generate_session_token("client", ttl_hours=-1)

        # Too long TTL (> 30 days)
        with pytest.raises(ValueError, match="TTL must be between"):
            auth.generate_session_token("client", ttl_hours=721)

    def test_weak_secret_key(self):
        """Test weak secret key rejection"""
        with pytest.raises(ValueError, match="Secret key must be at least"):
            MCPAuthManager("short")

    def test_token_uniqueness(self):
        """Test that generated tokens are unique"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")

        tokens = set()
        for _ in range(100):
            token, _ = auth.generate_session_token("test-client")
            tokens.add(token)

        # All tokens should be unique
        assert len(tokens) == 100

    def test_client_id_preservation(self):
        """Test that client ID is preserved correctly"""
        auth = MCPAuthManager("test-secret-key-minimum-16-chars")

        test_clients = [
            "user123:project456",
            "admin@example.com:prod-system",
            "special-chars_./test",
        ]

        for client_id in test_clients:
            token, _ = auth.generate_session_token(client_id)
            valid, retrieved_id = auth.validate_token(token)

            assert valid is True
            assert retrieved_id == client_id
