"""
Authentication module for JWT-based authentication
"""

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    verify_password,
    get_password_hash,
)
from app.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    require_auth,
)
from app.auth.schemas import (
    Token,
    TokenData,
    UserLogin,
    UserCreate,
    UserResponse,
    RefreshTokenRequest,
)

__all__ = [
    # JWT utilities
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "decode_token",
    "verify_password",
    "get_password_hash",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser",
    "require_auth",
    # Schemas
    "Token",
    "TokenData",
    "UserLogin",
    "UserCreate",
    "UserResponse",
    "RefreshTokenRequest",
]
