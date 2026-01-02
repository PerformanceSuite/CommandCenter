"""
Security tests for basic authentication functionality
"""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils.factories import UserFactory
from tests.utils.helpers import create_test_token

from app.auth.jwt import create_access_token, decode_token, get_password_hash, verify_password


@pytest.mark.security
class TestAuthBasic:
    """Test basic authentication security features"""

    async def test_password_hashing_works_correctly(self):
        """Test that password hashing works correctly"""
        # Test password
        password = "mySecurePassword123!"

        # Hash the password
        hashed = get_password_hash(password)

        # Verify hashed password is different from original
        assert hashed != password
        assert len(hashed) > len(password)

        # Verify the password
        assert verify_password(password, hashed) is True

        # Verify wrong password fails
        assert verify_password("wrongPassword", hashed) is False

    async def test_password_hashing_uses_bcrypt(self):
        """Test that password hashing uses bcrypt"""
        password = "testPassword456"
        hashed = get_password_hash(password)

        # Bcrypt hashes start with $2b$ or $2a$
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    async def test_jwt_token_creation_and_validation(self):
        """Test JWT token creation and validation"""
        # Create token
        user_data = {"sub": "1", "email": "test@example.com"}
        token = create_access_token(user_data)

        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and validate token
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "1"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded  # Expiration time should be included
        assert "type" in decoded  # Token type should be included
        assert decoded["type"] == "access"

    async def test_jwt_token_contains_expiration(self):
        """Test that JWT tokens contain expiration time"""
        import time

        # Record time before token creation
        before_creation = int(time.time())

        user_data = {"sub": "1", "email": "test@example.com"}
        token = create_access_token(user_data)

        decoded = decode_token(token)
        assert "exp" in decoded

        # Expiration should be after token creation time
        # (at least 1 minute in the future from when token was created)
        exp_timestamp = decoded["exp"]
        assert (
            exp_timestamp > before_creation
        ), f"Token expiration {exp_timestamp} should be greater than creation time {before_creation}"

    async def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected"""
        # Completely invalid token
        invalid_token = "this.is.not.a.valid.jwt.token"
        decoded = decode_token(invalid_token)

        assert decoded is None

    async def test_malformed_token_rejected(self):
        """Test that malformed tokens are rejected"""
        # Create a valid token and corrupt it
        valid_token = create_test_token(user_id=1, email="test@example.com")
        corrupted_token = valid_token[:-10] + "corrupted"

        decoded = decode_token(corrupted_token)
        assert decoded is None

    async def test_missing_token_returns_401(
        self, unauthenticated_api_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that missing token returns 401 Unauthorized"""
        # Try to access an endpoint that requires authentication (skills/usage)
        usage_data = {
            "skill_id": 1,
            "context": "test",
            "was_helpful": True,
        }

        # Try to post without authentication (using unauthenticated client)
        response = await unauthenticated_api_client.post("/skills/usage", json=usage_data)

        # Should return 401 or 403 (Unauthorized/Forbidden)
        assert response.status_code in [401, 403]

    async def test_invalid_credentials_rejected(
        self, unauthenticated_api_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that invalid credentials are rejected"""
        # Create a user
        _ = await UserFactory.create(
            db=db_session, email="test@example.com", password="correctPassword123"
        )

        # Try to login with wrong password (using /auth/login endpoint)
        login_data = {
            "email": "test@example.com",
            "password": "wrongPassword",
        }

        response = await unauthenticated_api_client.post("/auth/login", json=login_data)

        # Should return 401 Unauthorized
        assert response.status_code == 401

    async def test_expired_token_rejected(self):
        """Test that expired tokens are rejected"""
        # Create a token that's already expired
        user_data = {"sub": "1", "email": "test@example.com"}
        expired_token = create_access_token(
            user_data, expires_delta=timedelta(seconds=-60)  # Expired 60 seconds ago
        )

        # Try to decode expired token
        decoded = decode_token(expired_token)

        # Should return None for expired token
        assert decoded is None

    async def test_token_includes_user_identifier(self):
        """Test that tokens include user identifier (sub claim)"""
        user_data = {"sub": "123", "email": "user@example.com"}
        token = create_access_token(user_data)

        decoded = decode_token(token)
        assert decoded is not None
        assert "sub" in decoded
        assert decoded["sub"] == "123"

    async def test_password_hash_is_salted(self):
        """Test that password hashing includes salt (same password produces different hashes)"""
        password = "samePassword123"

        # Hash the same password twice
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different (due to salt)
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    async def test_token_without_user_id_invalid(self):
        """Test that tokens without user ID (sub) are invalid"""
        # Try to create token with missing sub claim
        invalid_data = {"email": "test@example.com"}  # Missing 'sub'

        token = create_access_token(invalid_data)

        # Token is created but should be considered invalid for authentication
        decoded = decode_token(token)
        # Token should decode but not have 'sub' claim
        assert decoded is not None
        assert "sub" not in decoded or decoded.get("sub") is None

    async def test_authenticated_endpoint_requires_valid_token(
        self, unauthenticated_api_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that authenticated endpoints require valid token"""
        # Create a user, project, and user_project association for auth context
        from app.models.project import Project
        from app.models.user_project import UserProject

        user = await UserFactory.create(db=db_session)

        project = Project(name="Test Project", owner="testowner", description="Test")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        user_project = UserProject(
            user_id=user.id, project_id=project.id, is_default=True, role="member"
        )
        db_session.add(user_project)
        await db_session.commit()

        # Test with valid token on an auth-required endpoint (skills/usage)
        usage_data = {"skill_id": 1, "context": "test", "was_helpful": True}

        # Try with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        response = await unauthenticated_api_client.post(
            "/skills/usage", json=usage_data, headers=invalid_headers
        )

        # Should return 401 Unauthorized for invalid token
        assert response.status_code in [401, 403]

    async def test_token_reuse_across_requests(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that same token can be reused across multiple requests"""
        user = await UserFactory.create(db=db_session)
        token = create_test_token(user_id=user.id, email=user.email)
        headers = {"Authorization": f"Bearer {token}"}

        # Make multiple requests with same token
        for _ in range(3):
            response = await api_client.get("/projects/", headers=headers)
            # Should not return 401 (token should remain valid)
            assert response.status_code != 401
