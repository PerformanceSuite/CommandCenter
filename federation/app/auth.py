"""
API Key authentication for Federation Service

Provides simple API key authentication for federation endpoints.
API keys are configured via FEDERATION_API_KEYS environment variable.
"""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key from X-API-Key header.

    Args:
        api_key: API key from request header

    Returns:
        API key if valid

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key:
        logger.warning("API key missing from request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Check if API key is valid
    if not settings.FEDERATION_API_KEYS or api_key not in settings.api_keys_set:
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    logger.debug(f"API key validated: {api_key[:8]}...")
    return api_key
