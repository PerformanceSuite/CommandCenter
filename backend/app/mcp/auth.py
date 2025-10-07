"""
MCP Authentication Manager

Provides session-based authentication for MCP stdio servers to prevent
unauthorized access (fixes CWE-306: Missing Authentication).

Security Features:
- 32-byte secure random session tokens
- Time-limited sessions (default 24 hours)
- Token validation and revocation
- Client identity tracking
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple


class MCPAuthManager:
    """Authentication manager for MCP stdio servers"""

    def __init__(self, secret_key: str):
        """
        Initialize MCP authentication manager

        Args:
            secret_key: Secret key for additional token validation
        """
        if not secret_key or len(secret_key) < 16:
            raise ValueError("Secret key must be at least 16 characters")

        self.secret_key = secret_key
        self.session_tokens: Dict[str, dict] = {}

    def generate_session_token(
        self, client_id: str, ttl_hours: int = 24
    ) -> Tuple[str, datetime]:
        """
        Generate time-limited session token for MCP client

        Args:
            client_id: Unique identifier for the client (e.g., "user_id:project_id")
            ttl_hours: Time to live in hours (default: 24)

        Returns:
            Tuple of (token, expires_at)

        Raises:
            ValueError: If client_id is empty or ttl_hours is invalid
        """
        if not client_id:
            raise ValueError("Client ID cannot be empty")

        if ttl_hours <= 0 or ttl_hours > 720:  # Max 30 days
            raise ValueError("TTL must be between 1 and 720 hours")

        # Generate cryptographically secure random token
        token = secrets.token_urlsafe(32)  # 43 characters base64-encoded
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        self.session_tokens[token] = {
            "client_id": client_id,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
        }

        return token, expires_at

    def validate_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate MCP session token

        Args:
            token: Session token to validate

        Returns:
            Tuple of (is_valid, client_id)
            - is_valid: True if token is valid and not expired
            - client_id: Client identifier if valid, None otherwise
        """
        if not token:
            return False, None

        if token not in self.session_tokens:
            return False, None

        session = self.session_tokens[token]

        # Check expiration
        if datetime.utcnow() > session["expires_at"]:
            # Clean up expired token
            del self.session_tokens[token]
            return False, None

        return True, session["client_id"]

    def revoke_token(self, token: str) -> bool:
        """
        Revoke MCP session token

        Args:
            token: Session token to revoke

        Returns:
            True if token was revoked, False if token didn't exist
        """
        if token in self.session_tokens:
            del self.session_tokens[token]
            return True
        return False

    def revoke_all_client_tokens(self, client_id: str) -> int:
        """
        Revoke all tokens for a specific client

        Args:
            client_id: Client identifier

        Returns:
            Number of tokens revoked
        """
        tokens_to_revoke = [
            token
            for token, session in self.session_tokens.items()
            if session["client_id"] == client_id
        ]

        for token in tokens_to_revoke:
            del self.session_tokens[token]

        return len(tokens_to_revoke)

    def cleanup_expired_tokens(self) -> int:
        """
        Remove all expired tokens from storage

        Returns:
            Number of tokens cleaned up
        """
        now = datetime.utcnow()
        expired_tokens = [
            token
            for token, session in self.session_tokens.items()
            if now > session["expires_at"]
        ]

        for token in expired_tokens:
            del self.session_tokens[token]

        return len(expired_tokens)

    def get_active_sessions_count(self) -> int:
        """
        Get count of active (non-expired) sessions

        Returns:
            Number of active sessions
        """
        now = datetime.utcnow()
        return sum(
            1
            for session in self.session_tokens.values()
            if now <= session["expires_at"]
        )
