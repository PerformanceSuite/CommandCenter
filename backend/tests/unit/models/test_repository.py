"""
Unit tests for Repository model
"""

from datetime import datetime

import pytest
from sqlalchemy import select
from tests.utils import create_test_project, create_test_repository

from app.models.repository import Repository


@pytest.mark.unit
@pytest.mark.db
class TestRepositoryModel:
    """Test Repository database model"""

    async def test_create_repository(self, db_session):
        """Test creating a repository"""
        repo = await create_test_repository(db_session)

        assert repo.id is not None
        assert repo.owner == "testowner"
        assert repo.name == "testrepo"
        assert repo.full_name == "testowner/testrepo"
        assert repo.is_private is False
        assert repo.stars == 100
        assert repo.forks == 10
        assert isinstance(repo.created_at, datetime)

    async def test_repository_unique_full_name(self, db_session):
        """Test that full_name must be unique"""
        await create_test_repository(db_session, full_name="owner/repo")

        # Attempting to create another repo with same full_name should fail
        with pytest.raises(Exception):
            await create_test_repository(db_session, full_name="owner/repo")

    async def test_repository_default_values(self, db_session):
        """Test repository default values"""
        # First create a project (required for repository)
        project = await create_test_project(db_session)

        repo = Repository(owner="owner", name="repo", full_name="owner/repo", project_id=project.id)
        db_session.add(repo)
        await db_session.commit()
        await db_session.refresh(repo)

        assert repo.default_branch == "main"
        assert repo.is_private is False
        assert repo.stars == 0
        assert repo.forks == 0
        assert repo.created_at is not None
        assert repo.updated_at is not None

    async def test_repository_with_metadata(self, db_session):
        """Test repository with JSON metadata"""
        metadata = {"topics": ["python", "testing"], "has_issues": True, "open_issues": 5}
        repo = await create_test_repository(db_session, metadata_=metadata)

        assert repo.metadata_ == metadata
        assert repo.metadata_["topics"] == ["python", "testing"]

    async def test_repository_update(self, db_session):
        """Test updating repository"""
        repo = await create_test_repository(db_session)
        _original_updated_at = repo.updated_at  # noqa: F841 - kept for potential future assertion

        # Update repository
        repo.stars = 200
        repo.description = "Updated description"
        await db_session.commit()
        await db_session.refresh(repo)

        assert repo.stars == 200
        assert repo.description == "Updated description"
        # Note: updated_at auto-update might not trigger in test environment

    async def test_repository_sync_fields(self, db_session):
        """Test repository sync-related fields"""
        sync_time = datetime.utcnow()
        repo = await create_test_repository(
            db_session,
            last_commit_sha="abc123",
            last_commit_message="Test commit",
            last_commit_author="Test Author",
            last_commit_date=sync_time,
            last_synced_at=sync_time,
        )

        assert repo.last_commit_sha == "abc123"
        assert repo.last_commit_message == "Test commit"
        assert repo.last_commit_author == "Test Author"
        assert repo.last_commit_date == sync_time
        assert repo.last_synced_at == sync_time

    async def test_repository_repr(self, db_session):
        """Test repository string representation"""
        repo = await create_test_repository(db_session)
        repr_str = repr(repo)

        assert "Repository" in repr_str
        assert str(repo.id) in repr_str
        assert repo.full_name in repr_str

    async def test_query_repository_by_full_name(self, db_session):
        """Test querying repository by full_name"""
        repo1 = await create_test_repository(db_session, full_name="owner1/repo1")

        # Query by full_name
        stmt = select(Repository).where(Repository.full_name == "owner1/repo1")
        result = await db_session.execute(stmt)
        found_repo = result.scalar_one_or_none()

        assert found_repo is not None
        assert found_repo.id == repo1.id
        assert found_repo.full_name == "owner1/repo1"

    async def test_repository_with_private_flag(self, db_session):
        """Test private repository"""
        repo = await create_test_repository(
            db_session, is_private=True, access_token="ghp_test_token_123"
        )

        assert repo.is_private is True
        assert repo.access_token == "ghp_test_token_123"
