"""
Helper functions for testing
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.auth.jwt import create_access_token, create_token_pair
from backend.tests.utils.factories import UserFactory


async def create_user_and_login(
    db: AsyncSession,
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "testpassword123",
    full_name: str = "Test User",
) -> Tuple[Any, Dict[str, str]]:
    """
    Create a user and return user object with authentication headers

    Args:
        db: Database session
        client: HTTP client
        email: User email
        password: User password
        full_name: User full name

    Returns:
        Tuple of (user, headers_dict)
    """
    # Create user
    user = await UserFactory.create(
        db=db, email=email, password=password, full_name=full_name
    )

    # Create token
    tokens = create_token_pair(user.id, user.email)
    access_token = tokens["access_token"]

    # Create headers
    headers = {"Authorization": f"Bearer {access_token}"}

    return user, headers


def create_test_token(
    user_id: int = 1,
    email: str = "test@example.com",
    expires_delta: timedelta = None,
) -> str:
    """
    Create a test JWT token

    Args:
        user_id: User ID to encode
        email: User email
        expires_delta: Optional expiration time delta

    Returns:
        JWT token string
    """
    data = {"sub": str(user_id), "email": email}
    return create_access_token(data, expires_delta=expires_delta)


def generate_mock_github_data(
    owner: str = "testowner",
    repo: str = "testrepo",
    include_commits: bool = True,
) -> Dict[str, Any]:
    """
    Generate mock GitHub API response data

    Args:
        owner: Repository owner
        repo: Repository name
        include_commits: Whether to include commit data

    Returns:
        Mock GitHub data dictionary
    """
    data = {
        "id": 12345,
        "name": repo,
        "full_name": f"{owner}/{repo}",
        "owner": {"login": owner, "id": 67890},
        "description": f"Test repository {repo}",
        "html_url": f"https://github.com/{owner}/{repo}",
        "clone_url": f"https://github.com/{owner}/{repo}.git",
        "default_branch": "main",
        "private": False,
        "language": "Python",
        "stargazers_count": 100,
        "forks_count": 25,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "pushed_at": "2024-01-15T00:00:00Z",
    }

    if include_commits:
        data["commits"] = [
            {
                "sha": "abc123def456",
                "commit": {
                    "message": "Initial commit",
                    "author": {
                        "name": "Test Author",
                        "email": "test@example.com",
                        "date": "2024-01-15T00:00:00Z",
                    },
                },
                "html_url": f"https://github.com/{owner}/{repo}/commit/abc123def456",
            }
        ]

    return data


def generate_mock_rag_response(
    query: str = "test query",
    answer: str = "test answer",
    num_sources: int = 2,
) -> Dict[str, Any]:
    """
    Generate mock RAG service response

    Args:
        query: Query text
        answer: Answer text
        num_sources: Number of source documents

    Returns:
        Mock RAG response dictionary
    """
    sources = []
    for i in range(num_sources):
        sources.append(
            {
                "document_id": f"doc_{i}",
                "content": f"Source content {i}",
                "metadata": {
                    "file_path": f"path/to/file_{i}.py",
                    "line_number": i * 10,
                },
                "score": 0.9 - (i * 0.1),
            }
        )

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "context_used": num_sources,
        "generated_at": datetime.utcnow().isoformat(),
    }


def generate_mock_research_task_data(
    title: str = "Research FastAPI best practices",
    status: str = "pending",
    priority: str = "high",
) -> Dict[str, Any]:
    """
    Generate mock research task data

    Args:
        title: Task title
        status: Task status
        priority: Task priority

    Returns:
        Mock research task dictionary
    """
    return {
        "title": title,
        "description": f"Description for {title}",
        "status": status,
        "priority": priority,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


def generate_mock_technology_data(
    title: str = "Python",
    domain: str = "ai-ml",
    status: str = "discovery",
) -> Dict[str, Any]:
    """
    Generate mock technology data

    Args:
        title: Technology title
        domain: Technology domain
        status: Technology status

    Returns:
        Mock technology dictionary
    """
    return {
        "title": title,
        "domain": domain,
        "status": status,
        "relevance_score": 75,
        "priority": 4,
        "description": f"Mock technology: {title}",
        "repository_url": f"https://github.com/python/{title.lower()}",
        "documentation_url": f"https://docs.{title.lower()}.org",
    }
