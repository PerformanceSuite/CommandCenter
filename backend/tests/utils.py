"""
Test utilities and helper functions
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository
from app.models.technology import Technology
from app.models.research_task import ResearchTask
from app.models.knowledge_entry import KnowledgeEntry
from app.models.user import User
from app.models.project import Project
from app.utils.crypto import hash_password


async def create_test_repository(db: AsyncSession, **kwargs) -> Repository:
    """
    Create a test repository in the database

    Args:
        db: Database session
        **kwargs: Repository attributes to override

    Returns:
        Created repository
    """
    defaults = {
        "owner": "testowner",
        "name": "testrepo",
        "full_name": "testowner/testrepo",
        "description": "Test repository",
        "url": "https://github.com/testowner/testrepo",
        "clone_url": "https://github.com/testowner/testrepo.git",
        "default_branch": "main",
        "is_private": False,
        "github_id": 12345,
        "stars": 100,
        "forks": 10,
        "language": "Python",
    }
    defaults.update(kwargs)

    repository = Repository(**defaults)
    db.add(repository)
    await db.commit()
    await db.refresh(repository)
    return repository


async def create_test_technology(db: AsyncSession, **kwargs) -> Technology:
    """
    Create a test technology in the database

    Args:
        db: Database session
        **kwargs: Technology attributes to override

    Returns:
        Created technology
    """
    defaults = {
        "name": "Python",
        "category": "language",
        "ring": "adopt",
        "description": "A high-level programming language",
        "moved": 0,
    }
    defaults.update(kwargs)

    technology = Technology(**defaults)
    db.add(technology)
    await db.commit()
    await db.refresh(technology)
    return technology


async def create_test_research_task(db: AsyncSession, project_id: int, **kwargs) -> ResearchTask:
    """
    Create a test research task in the database

    Args:
        db: Database session
        project_id: ID of associated project
        **kwargs: Research task attributes to override

    Returns:
        Created research task
    """
    from app.models.research_task import TaskStatus

    defaults = {
        "title": "Test Research Task",
        "description": "A test research task",
        "status": TaskStatus.PENDING,
        "project_id": project_id,
    }
    defaults.update(kwargs)

    task = ResearchTask(**defaults)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def create_test_knowledge_entry(
    db: AsyncSession, repository_id: int, **kwargs
) -> KnowledgeEntry:
    """
    Create a test knowledge entry in the database

    Args:
        db: Database session
        repository_id: ID of associated repository
        **kwargs: Knowledge entry attributes to override

    Returns:
        Created knowledge entry
    """
    defaults = {
        "title": "Test Knowledge Entry",
        "content": "Test content for knowledge entry",
        "category": "documentation",
        "repository_id": repository_id,
        "file_path": "/test/path/file.md",
    }
    defaults.update(kwargs)

    entry = KnowledgeEntry(**defaults)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


class MockGitHubRepo:
    """Mock GitHub repository object for testing"""

    def __init__(self, **kwargs):
        self.owner = type("Owner", (), {"login": kwargs.get("owner", "testowner")})()
        self.name = kwargs.get("name", "testrepo")
        self.full_name = kwargs.get("full_name", "testowner/testrepo")
        self.description = kwargs.get("description", "Test repository")
        self.html_url = kwargs.get("html_url", "https://github.com/testowner/testrepo")
        self.clone_url = kwargs.get("clone_url", "https://github.com/testowner/testrepo.git")
        self.default_branch = kwargs.get("default_branch", "main")
        self.private = kwargs.get("private", False)
        self.id = kwargs.get("id", 12345)
        self.stargazers_count = kwargs.get("stars", 100)
        self.forks_count = kwargs.get("forks", 10)
        self.language = kwargs.get("language", "Python")
        self.created_at = kwargs.get("created_at", datetime.utcnow())
        self.updated_at = kwargs.get("updated_at", datetime.utcnow())

    def get_topics(self):
        return ["python", "testing"]


class MockGitHubCommit:
    """Mock GitHub commit object for testing"""

    def __init__(self, **kwargs):
        self.sha = kwargs.get("sha", "abc123")
        self.commit = type(
            "Commit",
            (),
            {
                "message": kwargs.get("message", "Test commit"),
                "author": type(
                    "Author",
                    (),
                    {
                        "name": kwargs.get("author", "Test Author"),
                        "date": kwargs.get("date", datetime.utcnow()),
                    },
                )(),
            },
        )()


def create_mock_github_service():
    """Create a mock GitHub service for testing"""

    class MockGitHub:
        def get_repo(self, full_name: str):
            return MockGitHubRepo(full_name=full_name)

        def get_user(self, username: Optional[str] = None):
            class MockUser:
                def get_repos(self):
                    return [MockGitHubRepo()]

            return MockUser()

        def search_repositories(self, query: str):
            return [MockGitHubRepo()]

    return MockGitHub()


async def create_test_user(db: AsyncSession, **kwargs) -> User:
    """
    Create a test user in the database

    Args:
        db: Database session
        **kwargs: User attributes to override

    Returns:
        Created user
    """
    defaults = {
        "email": "test@example.com",
        "hashed_password": hash_password("TestPassword123"),
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
    }
    defaults.update(kwargs)

    user = User(**defaults)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_test_project(db: AsyncSession, **kwargs) -> Project:
    """
    Create a test project in the database

    Args:
        db: Database session
        **kwargs: Project attributes to override

    Returns:
        Created project
    """
    defaults = {
        "name": "Test Project",
        "owner": "testowner",
        "description": "A test project for unit testing",
    }
    defaults.update(kwargs)

    project = Project(**defaults)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project
