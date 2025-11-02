"""
Base classes for external integrations.

Provides common functionality for OAuth, webhooks, rate limiting, and error handling.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.integration import Integration, IntegrationStatus
from app.utils.crypto import encrypt_value, decrypt_value


logger = logging.getLogger(__name__)


class IntegrationError(Exception):
    """Base exception for integration errors."""



class IntegrationAuthError(IntegrationError):
    """Authentication/authorization error."""



class IntegrationRateLimitError(IntegrationError):
    """Rate limit exceeded."""



class BaseIntegration(ABC):
    """
    Base class for external integrations.

    Provides common functionality:
    - OAuth token management with encryption
    - Webhook signature verification
    - Rate limit handling
    - Error tracking and health monitoring
    - Retry logic with exponential backoff
    """

    def __init__(
        self,
        integration_id: int,
        db: AsyncSession,
        integration_type: str,
    ):
        """
        Initialize integration.

        Args:
            integration_id: Database ID of integration record
            db: Database session
            integration_type: Type identifier (github, custom_webhook, etc.)
        """
        self.integration_id = integration_id
        self.db = db
        self.integration_type = integration_type
        self._integration: Optional[Integration] = None
        self._logger = logger.getChild(self.__class__.__name__)

    async def load(self) -> Integration:
        """
        Load integration from database.

        Returns:
            Integration model

        Raises:
            IntegrationError: If integration not found
        """
        if self._integration:
            return self._integration

        result = await self.db.execute(
            select(Integration).where(Integration.id == self.integration_id)
        )
        integration = result.scalar_one_or_none()

        if not integration:
            raise IntegrationError(f"Integration {self.integration_id} not found")

        if integration.integration_type != self.integration_type:
            raise IntegrationError(
                f"Integration type mismatch: expected {self.integration_type}, "
                f"got {integration.integration_type}"
            )

        self._integration = integration
        return integration

    async def get_access_token(self) -> str:
        """
        Get decrypted access token.

        Returns:
            Decrypted access token

        Raises:
            IntegrationAuthError: If token not available or expired
        """
        integration = await self.load()

        if not integration.access_token_encrypted:
            raise IntegrationAuthError("No access token configured")

        if integration.is_token_expired:
            if integration.refresh_token_encrypted:
                # Try to refresh
                await self.refresh_token()
                integration = await self.load()
            else:
                raise IntegrationAuthError("Access token expired and no refresh token available")

        try:
            return decrypt_value(integration.access_token_encrypted)
        except Exception as e:
            raise IntegrationAuthError(f"Failed to decrypt access token: {e}")

    async def set_access_token(
        self,
        access_token: str,
        expires_in: Optional[int] = None,
        refresh_token: Optional[str] = None,
    ) -> None:
        """
        Store encrypted access token.

        Args:
            access_token: Access token to encrypt and store
            expires_in: Token lifetime in seconds
            refresh_token: Optional refresh token
        """
        integration = await self.load()

        integration.access_token_encrypted = encrypt_value(access_token)

        if expires_in:
            integration.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        if refresh_token:
            integration.refresh_token_encrypted = encrypt_value(refresh_token)

        integration.token_refreshed_at = datetime.utcnow()
        integration.status = IntegrationStatus.ACTIVE

        await self.db.commit()
        await self.db.refresh(integration)
        self._integration = integration

    async def refresh_token(self) -> str:
        """
        Refresh expired access token.

        Returns:
            New access token

        Raises:
            IntegrationAuthError: If refresh fails
        """
        # Override in subclasses that support token refresh
        raise IntegrationAuthError(f"{self.integration_type} does not support token refresh")

    async def record_success(self) -> None:
        """Record successful operation."""
        integration = await self.load()
        integration.success_count += 1
        integration.error_count = 0  # Reset consecutive error count
        integration.last_sync_at = datetime.utcnow()
        integration.last_error = None

        await self.db.commit()

    async def record_error(self, error: str) -> None:
        """
        Record failed operation.

        Args:
            error: Error message
        """
        integration = await self.load()
        integration.error_count += 1
        integration.last_error = error[:500]  # Truncate
        integration.last_error_at = datetime.utcnow()

        # Disable if too many consecutive failures
        if integration.error_count >= 5:
            integration.status = IntegrationStatus.ERROR
            integration.enabled = False
            self._logger.error(
                f"Integration {self.integration_id} disabled after {integration.error_count} consecutive errors"
            )

        await self.db.commit()

    async def check_health(self) -> Dict[str, Any]:
        """
        Check integration health.

        Returns:
            Health status dictionary
        """
        integration = await self.load()

        return {
            "integration_id": integration.id,
            "integration_type": integration.integration_type,
            "status": integration.status,
            "enabled": integration.enabled,
            "is_healthy": integration.is_healthy,
            "is_token_expired": integration.is_token_expired,
            "needs_refresh": integration.needs_refresh,
            "error_count": integration.error_count,
            "success_count": integration.success_count,
            "success_rate": integration.success_rate,
            "last_sync_at": (
                integration.last_sync_at.isoformat() if integration.last_sync_at else None
            ),
            "last_error": integration.last_error,
        }

    async def update_rate_limit(self, remaining: int, reset_at: datetime) -> None:
        """
        Update rate limit information.

        Args:
            remaining: Number of requests remaining
            reset_at: When rate limit resets
        """
        integration = await self.load()
        integration.rate_limit_remaining = remaining
        integration.rate_limit_reset_at = reset_at
        await self.db.commit()

    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """
        Verify webhook signature (HMAC-SHA256).

        Args:
            payload: Raw webhook payload
            signature: Signature from webhook header
            secret: Webhook secret

        Returns:
            True if signature is valid
        """
        import hmac
        import hashlib

        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        return hmac.compare_digest(signature, expected)

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test if integration is working.

        Returns:
            True if connection successful

        Raises:
            IntegrationError: If connection fails
        """

    @abstractmethod
    async def get_display_name(self) -> str:
        """
        Get human-readable display name.

        Returns:
            Display name (e.g., "GitHub: username/repo")
        """


class WebhookIntegration(BaseIntegration):
    """
    Base class for integrations that receive webhooks.

    Provides webhook validation and event processing.
    """

    @abstractmethod
    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming webhook event.

        Args:
            event_type: Type of event (push, pull_request, etc.)
            payload: Webhook payload

        Returns:
            Processing result

        Raises:
            IntegrationError: If processing fails
        """

    @abstractmethod
    def get_webhook_secret(self) -> str:
        """
        Get webhook secret for signature verification.

        Returns:
            Webhook secret
        """


class OAuthIntegration(BaseIntegration):
    """
    Base class for OAuth-based integrations.

    Provides OAuth flow helpers.
    """

    @abstractmethod
    def get_oauth_authorize_url(self, state: str, redirect_uri: str) -> str:
        """
        Get OAuth authorization URL.

        Args:
            state: State parameter for CSRF protection
            redirect_uri: OAuth redirect URI

        Returns:
            Authorization URL
        """

    @abstractmethod
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code
            redirect_uri: OAuth redirect URI

        Returns:
            Token response with access_token, expires_in, etc.

        Raises:
            IntegrationAuthError: If exchange fails
        """
