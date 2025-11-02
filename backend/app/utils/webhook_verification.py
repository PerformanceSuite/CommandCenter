"""
GitHub webhook signature verification utilities
"""

import hashlib
import hmac
from typing import Optional

from fastapi import Header, HTTPException, status


def verify_github_signature(
    payload_body: bytes, secret: str, signature_header: Optional[str] = None
) -> bool:
    """
    Verify GitHub webhook signature

    Args:
        payload_body: Raw request body bytes
        secret: Webhook secret
        signature_header: X-Hub-Signature-256 header value

    Returns:
        True if signature is valid

    Raises:
        HTTPException: If signature is invalid or missing
    """
    if not signature_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Hub-Signature-256 header is missing",
        )

    # GitHub sends signature in format: sha256=<hash>
    if not signature_header.startswith("sha256="):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature format"
        )

    # Extract the hash from the header
    expected_signature = signature_header[7:]  # Remove 'sha256=' prefix

    # Compute HMAC-SHA256
    mac = hmac.new(secret.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256)
    computed_signature = mac.hexdigest()

    # Compare signatures using constant-time comparison
    if not hmac.compare_digest(computed_signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
        )

    return True


async def get_webhook_signature(
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256")
) -> Optional[str]:
    """Dependency to extract webhook signature from headers"""
    return x_hub_signature_256


async def get_webhook_event_type(
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event")
) -> Optional[str]:
    """Dependency to extract GitHub event type from headers"""
    return x_github_event


async def get_webhook_delivery_id(
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery")
) -> Optional[str]:
    """Dependency to extract GitHub delivery ID from headers"""
    return x_github_delivery
