"""
Unit tests for Repository Pydantic schemas
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.repository import (
    RepositoryCreate,
    RepositoryUpdate,
    RepositoryInDB,
    RepositoryResponse,
    RepositorySyncRequest,
    RepositorySyncResponse
)


@pytest.mark.unit
class TestRepositorySchemas:
    """Test Repository Pydantic schemas"""

    def test_repository_create_valid(self):
        """Test creating valid repository schema"""
        data = {
            "owner": "testowner",
            "name": "testrepo",
            "description": "Test repository",
            "is_private": False
        }
        schema = RepositoryCreate(**data)

        assert schema.owner == "testowner"
        assert schema.name == "testrepo"
        assert schema.description == "Test repository"
        assert schema.is_private is False

    def test_repository_create_invalid_owner(self):
        """Test repository creation with invalid owner name"""
        data = {
            "owner": "-invalid-owner",  # Starts with dash
            "name": "testrepo"
        }

        with pytest.raises(ValidationError) as exc_info:
            RepositoryCreate(**data)

        assert "Invalid GitHub name format" in str(exc_info.value)

    def test_repository_create_invalid_name(self):
        """Test repository creation with invalid repo name"""
        data = {
            "owner": "testowner",
            "name": "invalid-repo-"  # Ends with dash
        }

        with pytest.raises(ValidationError) as exc_info:
            RepositoryCreate(**data)

        assert "Invalid GitHub name format" in str(exc_info.value)

    def test_repository_create_with_valid_token(self):
        """Test repository creation with valid GitHub token"""
        data = {
            "owner": "testowner",
            "name": "testrepo",
            "access_token": "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        }
        schema = RepositoryCreate(**data)

        assert schema.access_token == "ghp_1234567890abcdefghijklmnopqrstuvwxyz"

    def test_repository_create_with_invalid_token(self):
        """Test repository creation with invalid token format"""
        data = {
            "owner": "testowner",
            "name": "testrepo",
            "access_token": "invalid_token"
        }

        with pytest.raises(ValidationError) as exc_info:
            RepositoryCreate(**data)

        assert "Invalid GitHub token format" in str(exc_info.value)

    def test_repository_update_partial(self):
        """Test repository update with partial data"""
        data = {
            "description": "Updated description"
        }
        schema = RepositoryUpdate(**data)

        assert schema.description == "Updated description"
        assert schema.access_token is None
        assert schema.is_private is None

    def test_repository_update_all_fields(self):
        """Test repository update with all fields"""
        data = {
            "description": "Updated description",
            "access_token": "ghp_newtoken1234567890abcdefghijklmnopqr",
            "is_private": True,
            "metadata_": {"custom": "data"}
        }
        schema = RepositoryUpdate(**data)

        assert schema.description == "Updated description"
        assert schema.access_token is not None
        assert schema.is_private is True
        assert schema.metadata_ == {"custom": "data"}

    def test_repository_in_db(self):
        """Test RepositoryInDB schema"""
        data = {
            "id": 1,
            "owner": "testowner",
            "name": "testrepo",
            "full_name": "testowner/testrepo",
            "default_branch": "main",
            "is_private": False,
            "stars": 100,
            "forks": 10,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        schema = RepositoryInDB(**data)

        assert schema.id == 1
        assert schema.owner == "testowner"
        assert schema.full_name == "testowner/testrepo"
        assert schema.stars == 100

    def test_repository_sync_request_defaults(self):
        """Test RepositorySyncRequest default values"""
        schema = RepositorySyncRequest()

        assert schema.force is False

    def test_repository_sync_request_force(self):
        """Test RepositorySyncRequest with force=True"""
        schema = RepositorySyncRequest(force=True)

        assert schema.force is True

    def test_repository_sync_response(self):
        """Test RepositorySyncResponse schema"""
        sync_time = datetime.utcnow()
        data = {
            "repository_id": 1,
            "synced": True,
            "last_commit_sha": "abc123",
            "last_commit_message": "Test commit",
            "last_synced_at": sync_time,
            "changes_detected": True
        }
        schema = RepositorySyncResponse(**data)

        assert schema.repository_id == 1
        assert schema.synced is True
        assert schema.last_commit_sha == "abc123"
        assert schema.changes_detected is True

    def test_repository_response_from_db_model(self):
        """Test RepositoryResponse creation from ORM model"""
        # Simulate ORM model data
        data = {
            "id": 1,
            "owner": "testowner",
            "name": "testrepo",
            "full_name": "testowner/testrepo",
            "default_branch": "main",
            "is_private": False,
            "stars": 100,
            "forks": 10,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # RepositoryResponse inherits from RepositoryInDB
        schema = RepositoryResponse(**data)

        assert schema.id == 1
        assert schema.full_name == "testowner/testrepo"
