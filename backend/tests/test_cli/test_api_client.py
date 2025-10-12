"""
Tests for API client.
"""

import pytest
import httpx
from unittest.mock import Mock, patch
from cli.api_client import APIClient, APIError


@pytest.fixture
def mock_client():
    """Create a mock HTTP client."""
    with patch("cli.api_client.httpx.Client") as mock:
        yield mock


def test_api_client_init():
    """Test API client initialization."""
    client = APIClient("http://localhost:8000", "test-token", 30)

    assert client.base_url == "http://localhost:8000"
    assert client.token == "test-token"
    assert client.timeout == 30


def test_api_client_strips_trailing_slash():
    """Test base URL trailing slash is stripped."""
    client = APIClient("http://localhost:8000/", "token")

    assert client.base_url == "http://localhost:8000"


def test_get_headers_without_token():
    """Test headers without authentication token."""
    client = APIClient("http://localhost:8000")
    headers = client._get_headers()

    assert "Content-Type" in headers
    assert "Authorization" not in headers


def test_get_headers_with_token():
    """Test headers with authentication token."""
    client = APIClient("http://localhost:8000", "test-token")
    headers = client._get_headers()

    assert "Content-Type" in headers
    assert headers["Authorization"] == "Bearer test-token"


def test_handle_response_success():
    """Test handling successful response."""
    client = APIClient("http://localhost:8000")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    mock_response.content = b'{"status": "ok"}'

    result = client._handle_response(mock_response)
    assert result == {"status": "ok"}


def test_handle_response_error():
    """Test handling error response."""
    client = APIClient("http://localhost:8000")

    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"detail": "Not found"}
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not found", request=Mock(), response=mock_response
    )

    with pytest.raises(APIError) as exc_info:
        client._handle_response(mock_response)

    assert "Not found" in str(exc_info.value.message)
    assert exc_info.value.status_code == 404


def test_analyze_project(mock_client):
    """Test analyzing a project."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "123", "technologies": []}
    mock_response.content = b'{"id": "123"}'

    mock_client.return_value.post.return_value = mock_response

    client = APIClient("http://localhost:8000")
    result = client.analyze_project("/path/to/project")

    assert result["id"] == "123"
    mock_client.return_value.post.assert_called_once()


def test_search_knowledge(mock_client):
    """Test searching knowledge base."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"query": "test", "matches": []}
    mock_response.content = b'{"query": "test"}'

    mock_client.return_value.get.return_value = mock_response

    client = APIClient("http://localhost:8000")
    result = client.search_knowledge("test query")

    assert result["query"] == "test"
    mock_client.return_value.get.assert_called_once()


def test_health_check(mock_client):
    """Test health check."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "healthy"}
    mock_response.content = b'{"status": "healthy"}'

    mock_client.return_value.get.return_value = mock_response

    client = APIClient("http://localhost:8000")
    result = client.health_check()

    assert result["status"] == "healthy"


def test_context_manager():
    """Test API client as context manager."""
    with APIClient("http://localhost:8000") as client:
        assert isinstance(client, APIClient)
