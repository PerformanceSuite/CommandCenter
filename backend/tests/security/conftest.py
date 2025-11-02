"""Security test fixtures."""
from datetime import timedelta

import pytest
from tests.utils.factories import ProjectFactory, UserFactory

from app.auth.jwt import create_access_token


@pytest.fixture
async def user_a(db_session):
    """Create isolated user A with project-a."""
    user = await UserFactory.create(db_session, email="user_a@test.com", project_id="project-a")
    return user


@pytest.fixture
async def user_b(db_session):
    """Create isolated user B with project-b."""
    user = await UserFactory.create(db_session, email="user_b@test.com", project_id="project-b")
    return user


@pytest.fixture
def jwt_token_factory():
    """Factory for creating test JWT tokens.

    Args:
        user_id: User ID to encode in token
        expires_delta: Token expiration time (default: 30 minutes)
        tampered: Whether to tamper with token
        tamper_type: Type of tampering ("signature" or "payload")

    Returns:
        JWT token string
    """

    def _create_token(
        user_id: str,
        expires_delta: timedelta = None,
        tampered: bool = False,
        tamper_type: str = "signature",
    ):
        if expires_delta is None:
            expires_delta = timedelta(minutes=30)

        token = create_access_token(data={"sub": user_id}, expires_delta=expires_delta)

        if tampered:
            parts = token.split(".")
            if tamper_type == "signature":
                # Modify signature (last part)
                parts[2] = parts[2][:-5] + "XXXXX"
            elif tamper_type == "payload":
                # Modify payload (middle part)
                parts[1] = parts[1][:-5] + "XXXXX"
            token = ".".join(parts)

        return token

    return _create_token


@pytest.fixture
def auth_headers_factory(jwt_token_factory):
    """Create authorization headers for user.

    Args:
        user: User object to create token for

    Returns:
        Dictionary with Authorization header
    """

    def _create_headers(user):
        token = jwt_token_factory(user_id=str(user.id))
        return {"Authorization": f"Bearer {token}"}

    return _create_headers
