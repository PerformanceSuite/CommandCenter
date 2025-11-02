"""
Tests for authentication endpoints and JWT functionality
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_token_pair, decode_token, get_password_hash, verify_password
from app.models.user import User


class TestPasswordHashing:
    """Test password hashing utilities"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        # Verify correct password
        assert verify_password(password, hashed) is True

        # Verify incorrect password
        assert verify_password("WrongPassword", hashed) is False

    def test_different_hashes(self):
        """Test that same password produces different hashes"""
        password = "SecurePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different (due to salt)
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and validation"""

    def test_create_token_pair(self):
        """Test creating access and refresh tokens"""
        user_id = 1
        email = "test@example.com"

        tokens = create_token_pair(user_id, email)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"

    def test_decode_access_token(self):
        """Test decoding access token"""
        user_id = 1
        email = "test@example.com"

        tokens = create_token_pair(user_id, email)
        payload = decode_token(tokens["access_token"])

        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["email"] == email
        assert payload["type"] == "access"

    def test_decode_refresh_token(self):
        """Test decoding refresh token"""
        user_id = 1
        email = "test@example.com"

        tokens = create_token_pair(user_id, email)
        payload = decode_token(tokens["refresh_token"])

        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["email"] == email
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        """Test decoding invalid token"""
        invalid_token = "invalid.token.here"
        payload = decode_token(invalid_token)

        assert payload is None


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication API endpoints"""

    async def test_register_user(self, client: AsyncClient):
        """Test user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "id" in data
        assert "hashed_password" not in data  # Password should not be returned

    async def test_register_duplicate_email(self, client: AsyncClient, db_session: AsyncSession):
        """Test registering with duplicate email"""
        # Create first user
        user1 = User(
            email="existing@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user1)
        await db_session.commit()

        # Try to register with same email
        user_data = {"email": "existing@example.com", "password": "DifferentPassword123!"}

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful login"""
        # Create user
        password = "SecurePassword123!"
        user = User(
            email="testuser@example.com",
            hashed_password=get_password_hash(password),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Login
        login_data = {"email": "testuser@example.com", "password": password}

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with wrong password"""
        # Create user
        user = User(
            email="testuser@example.com",
            hashed_password=get_password_hash("CorrectPassword123!"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Try to login with wrong password
        login_data = {"email": "testuser@example.com", "password": "WrongPassword123!"}

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_inactive_user(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with inactive user"""
        # Create inactive user
        password = "SecurePassword123!"
        user = User(
            email="inactive@example.com",
            hashed_password=get_password_hash(password),
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()

        # Try to login
        login_data = {"email": "inactive@example.com", "password": password}

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()

    async def test_get_current_user(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting current user information"""
        # Create user
        password = "SecurePassword123!"
        user = User(
            email="testuser@example.com",
            hashed_password=get_password_hash(password),
            full_name="Test User",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Get token
        tokens = create_token_pair(user.id, user.email)

        # Get current user info
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email
        assert data["full_name"] == user.full_name

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token"""
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    async def test_refresh_token(self, client: AsyncClient, db_session: AsyncSession):
        """Test refreshing access token"""
        # Create user
        user = User(
            email="testuser@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Get initial tokens
        tokens = create_token_pair(user.id, user.email)

        # Refresh token
        refresh_data = {"refresh_token": tokens["refresh_token"]}

        response = await client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != tokens["access_token"]  # Should be new token

    async def test_refresh_with_access_token_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that using access token for refresh fails"""
        # Create user
        user = User(
            email="testuser@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Get tokens
        tokens = create_token_pair(user.id, user.email)

        # Try to refresh with access token (should fail)
        refresh_data = {"refresh_token": tokens["access_token"]}  # Using access token instead

        response = await client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 401
        assert "invalid token type" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestTokenEncryption:
    """Test token encryption for repository access tokens"""

    async def test_token_encryption_decryption(self, db_session: AsyncSession):
        """Test that repository tokens are encrypted and decrypted correctly"""
        from app.models.repository import Repository

        # Create repository with access token
        plain_token = "ghp_test_token_123456789"
        repo = Repository(
            owner="testowner",
            name="testrepo",
            full_name="testowner/testrepo",
            access_token=plain_token,
        )

        db_session.add(repo)
        await db_session.commit()
        await db_session.refresh(repo)

        # Verify token is encrypted in database
        assert repo._encrypted_access_token is not None
        assert repo._encrypted_access_token != plain_token

        # Verify token can be decrypted
        assert repo.access_token == plain_token

    async def test_null_token_handling(self, db_session: AsyncSession):
        """Test that null tokens are handled correctly"""
        from app.models.repository import Repository

        # Create repository without access token
        repo = Repository(
            owner="testowner", name="testrepo", full_name="testowner/testrepo", access_token=None
        )

        db_session.add(repo)
        await db_session.commit()
        await db_session.refresh(repo)

        assert repo.access_token is None
        assert repo._encrypted_access_token is None
