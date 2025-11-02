"""
MCP Authentication and Authorization module.

Provides authentication validation and rate limiting for MCP sessions.
"""

import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from aiolimiter import AsyncLimiter


class MCPAuthenticator:
    """
    Handles MCP session authentication and authorization.

    Validates API tokens and manages session security.
    """

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize authenticator.

        Args:
            secret_key: Secret key for token validation (generated if not provided)
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self._valid_tokens: Dict[str, dict] = {}  # token -> {user_id, expires_at}

    def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        """
        Generate authentication token.

        Args:
            user_id: User identifier
            expires_in: Token expiration in seconds

        Returns:
            Authentication token
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        self._valid_tokens[token] = {
            "user_id": user_id,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
        }

        return token

    async def validate_token(self, token: Optional[str]) -> Optional[str]:
        """
        Validate authentication token.

        Args:
            token: Authentication token

        Returns:
            User ID if valid, None otherwise
        """
        if not token or token not in self._valid_tokens:
            return None

        token_info = self._valid_tokens[token]

        # Check expiration
        if datetime.utcnow() > token_info["expires_at"]:
            del self._valid_tokens[token]
            return None

        return token_info["user_id"]

    def revoke_token(self, token: str) -> bool:
        """
        Revoke authentication token.

        Args:
            token: Token to revoke

        Returns:
            True if revoked, False if not found
        """
        if token in self._valid_tokens:
            del self._valid_tokens[token]
            return True
        return False


class MCPRateLimiter:
    """
    Rate limiting for MCP requests.

    Implements per-session and global rate limits.
    """

    def __init__(self, requests_per_minute: int = 100, global_requests_per_minute: int = 1000):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Per-session rate limit
            global_requests_per_minute: Global rate limit
        """
        self._session_limiters: Dict[str, AsyncLimiter] = {}
        self._global_limiter = AsyncLimiter(global_requests_per_minute, 60)
        self._requests_per_minute = requests_per_minute

    def get_session_limiter(self, session_id: str) -> AsyncLimiter:
        """
        Get rate limiter for session.

        Args:
            session_id: Session identifier

        Returns:
            AsyncLimiter instance
        """
        if session_id not in self._session_limiters:
            self._session_limiters[session_id] = AsyncLimiter(self._requests_per_minute, 60)
        return self._session_limiters[session_id]

    async def check_rate_limit(self, session_id: str) -> bool:
        """
        Check if request is within rate limits.

        Args:
            session_id: Session identifier

        Returns:
            True if within limits, False otherwise
        """
        # Check global limit
        if not self._global_limiter.has_capacity():
            return False

        # Check session limit
        session_limiter = self.get_session_limiter(session_id)
        if not session_limiter.has_capacity():
            return False

        return True

    async def acquire(self, session_id: str):
        """
        Acquire rate limit slot (blocks if necessary).

        Args:
            session_id: Session identifier
        """
        async with self._global_limiter:
            session_limiter = self.get_session_limiter(session_id)
            async with session_limiter:
                pass

    def cleanup_session(self, session_id: str):
        """
        Remove session rate limiter.

        Args:
            session_id: Session identifier
        """
        if session_id in self._session_limiters:
            del self._session_limiters[session_id]
