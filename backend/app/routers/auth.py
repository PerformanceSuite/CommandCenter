"""
Authentication endpoints for user login, registration, and token management
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.user import User
from app.auth import (
    UserLogin,
    UserCreate,
    UserResponse,
    Token,
    RefreshTokenRequest,
    verify_password,
    get_password_hash,
    create_token_pair,
    decode_token,
    get_current_active_user,
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Rate limiter for auth endpoints
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register(
    request: Request, user_data: UserCreate, db: AsyncSession = Depends(get_db)
) -> User:
    """
    Register a new user account

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user object

    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_superuser=False,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request, user_credentials: UserLogin, db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Login with email and password to get JWT tokens

    Args:
        user_credentials: Login credentials
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == user_credentials.email))
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create token pair
    tokens = create_token_pair(user.id, user.email)

    return tokens


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request, refresh_request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Refresh access token using refresh token

    Args:
        refresh_request: Refresh token request
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Decode refresh token
    payload = decode_token(refresh_request.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token type
    token_type = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user exists and is active
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new token pair
    tokens = create_token_pair(user.id, user.email)

    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Get current authenticated user information

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return current_user


@router.post("/logout")
async def logout() -> dict:
    """
    Logout endpoint (client should discard tokens)

    Returns:
        Success message
    """
    # In a stateless JWT system, logout is handled client-side
    # by discarding the tokens. This endpoint is for completeness.
    # For more security, implement token blacklisting with Redis.
    return {"message": "Successfully logged out"}
