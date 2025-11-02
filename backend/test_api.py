"""
Basic API tests for Command Center backend
Run with: pytest test_api.py
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_repositories():
    """Test listing repositories"""
    response = client.get("/api/v1/repositories/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_technologies():
    """Test listing technologies"""
    response = client.get("/api/v1/technologies/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_stats():
    """Test dashboard stats endpoint"""
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_repositories" in data
    assert "total_technologies" in data
