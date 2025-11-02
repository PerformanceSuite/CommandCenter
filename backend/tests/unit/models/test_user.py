"""
Unit tests for User model
"""

from datetime import datetime

import pytest
from sqlalchemy import select
from tests.utils import create_test_user

from app.models.user import User
from app.utils.crypto import hash_password, verify_password


@pytest.mark.unit
@pytest.mark.db
class TestUserModel:
    """Test User database model"""

    async def test_create_user(self, db_session):
        """Test creating a user"""
        user = await create_test_user(db_session)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_superuser is False
        assert isinstance(user.created_at, datetime)

    async def test_password_hashing_works_correctly(self, db_session):
        """Password is hashed and can be verified"""
        password = "TestPass123"
        hashed = hash_password(password)

        user = User(email="test@gmail.com", hashed_password=hashed)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.hashed_password != password
        assert verify_password(password, user.hashed_password)
        assert not verify_password("WrongPass", user.hashed_password)

    async def test_user_email_validation(self, db_session):
        """User model validates email format"""
        # Invalid email should raise error
        with pytest.raises(ValueError, match="Invalid email address"):
            user = User(email="not-an-email", hashed_password=hash_password("password"))
            db_session.add(user)
            await db_session.commit()

    async def test_user_email_normalization(self, db_session):
        """User email is normalized"""
        user = await create_test_user(db_session, email="Test.User@Example.COM")

        # Email should be normalized to lowercase
        assert user.email == "test.user@example.com"

    async def test_user_unique_email(self, db_session):
        """Test that user email must be unique"""
        await create_test_user(db_session, email="unique@example.com")

        # Attempting to create another user with same email should fail
        with pytest.raises(Exception):
            await create_test_user(db_session, email="unique@example.com")

    async def test_user_default_values(self, db_session):
        """Test user default values"""
        user = User(email="newuser@example.com", hashed_password=hash_password("password"))
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.is_active is True
        assert user.is_superuser is False
        assert user.full_name is None
        assert user.last_login is None
        assert user.created_at is not None
        assert user.updated_at is not None

    async def test_user_with_full_profile(self, db_session):
        """Test user with all fields populated"""
        user = await create_test_user(
            db_session,
            email="full@example.com",
            full_name="John Doe",
            is_active=True,
            is_superuser=True,
        )

        assert user.email == "full@example.com"
        assert user.full_name == "John Doe"
        assert user.is_active is True
        assert user.is_superuser is True

    async def test_user_can_be_deactivated(self, db_session):
        """Test deactivating a user"""
        user = await create_test_user(db_session)
        assert user.is_active is True

        # Deactivate user
        user.is_active = False
        await db_session.commit()
        await db_session.refresh(user)
        assert user.is_active is False

    async def test_user_last_login_tracking(self, db_session):
        """Test updating last login timestamp"""
        user = await create_test_user(db_session)
        assert user.last_login is None

        # Update last login
        login_time = datetime.utcnow()
        user.last_login = login_time
        await db_session.commit()
        await db_session.refresh(user)

        assert user.last_login is not None
        assert abs((user.last_login - login_time).total_seconds()) < 1

    async def test_user_repr(self, db_session):
        """Test user string representation"""
        user = await create_test_user(db_session)
        repr_str = repr(user)

        assert "User" in repr_str
        assert str(user.id) in repr_str
        assert user.email in repr_str
