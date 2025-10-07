"""
MCP Authentication Router

API endpoints for MCP token generation and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.mcp import (
    MCPTokenRequest,
    MCPTokenResponse,
    MCPTokenValidationRequest,
    MCPTokenValidationResponse,
)
from app.mcp.auth import MCPAuthManager
from app.config import settings
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/mcp", tags=["MCP Authentication"])

# Global MCP auth manager instance
auth_manager = MCPAuthManager(settings.SECRET_KEY)


@router.post("/tokens", response_model=MCPTokenResponse)
async def create_mcp_token(
    request: MCPTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MCPTokenResponse:
    """
    Generate MCP authentication token for client

    Requires authentication. Creates a session token that MCP clients
    must include in requests to prevent unauthorized access.

    Security:
    - Fixes CWE-306 (Missing Authentication)
    - 32-byte secure random tokens
    - Time-limited sessions (configurable TTL)
    - Bound to authenticated user + project
    """
    try:
        # Generate unique client ID
        client_id = f"{current_user.id}:{request.project_id}"

        # Generate token
        token, expires_at = auth_manager.generate_session_token(
            client_id=client_id, ttl_hours=request.ttl_hours
        )

        return MCPTokenResponse(
            token=token, expires_at=expires_at, client_id=client_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/tokens/validate", response_model=MCPTokenValidationResponse)
async def validate_mcp_token(
    request: MCPTokenValidationRequest,
) -> MCPTokenValidationResponse:
    """
    Validate MCP authentication token

    Public endpoint for MCP servers to validate tokens.
    Does not require authentication (validates the provided token).
    """
    valid, client_id = auth_manager.validate_token(request.token)

    if valid:
        return MCPTokenValidationResponse(
            valid=True,
            client_id=client_id,
            message="Token is valid",
        )
    else:
        return MCPTokenValidationResponse(
            valid=False,
            client_id=None,
            message="Token is invalid or expired",
        )


@router.delete("/tokens/{token}")
async def revoke_mcp_token(
    token: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Revoke MCP authentication token

    Requires authentication. Only the user who created the token
    can revoke it.
    """
    # Validate token exists and belongs to this user
    valid, client_id = auth_manager.validate_token(token)

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found or already expired",
        )

    # Check ownership
    if not client_id.startswith(f"{current_user.id}:"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke token belonging to another user",
        )

    # Revoke token
    auth_manager.revoke_token(token)

    return {"message": "Token revoked successfully"}


@router.post("/tokens/cleanup")
async def cleanup_expired_tokens(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Clean up expired tokens

    Requires authentication. Admin maintenance endpoint.
    """
    count = auth_manager.cleanup_expired_tokens()

    return {"message": f"Cleaned up {count} expired tokens"}


@router.get("/stats")
async def get_mcp_stats(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get MCP authentication statistics

    Requires authentication.
    """
    return {
        "active_sessions": auth_manager.get_active_sessions_count(),
    }
