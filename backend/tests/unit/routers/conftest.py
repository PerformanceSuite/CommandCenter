"""Pytest configuration for router unit tests - isolated from parent conftest."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app - synchronous fixture."""
    return TestClient(app)
