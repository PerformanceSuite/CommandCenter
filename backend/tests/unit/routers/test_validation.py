"""Unit tests for router validation and middleware."""
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.main import app
from app.models.technology import TechnologyDomain, TechnologyStatus


@pytest.mark.unit
class TestRequestValidation:
    """Test request validation for API endpoints"""

    @pytest.mark.asyncio(enabled=False)
    def test_request_validation_rejects_invalid_input(self, client):
        """Request validation rejects invalid input."""
        # Invalid request: empty title
        response = client.post(
            "/api/v1/technologies",
            json={
                "title": "",
                "domain": TechnologyDomain.BACKEND.value,
            },
        )

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422
        assert "detail" in response.json()
        # Check validation error mentions title field
        error_detail = response.json()["detail"]
        assert any("title" in str(err.get("loc", [])) for err in error_detail)

    @pytest.mark.asyncio(enabled=False)
    def test_response_serialization_format(self, client):
        """Responses are properly serialized."""
        # Create valid technology
        response = client.post(
            "/api/v1/technologies",
            json={
                "title": "Python",
                "domain": TechnologyDomain.BACKEND.value,
                "status": TechnologyStatus.ADOPT.value,
                "description": "A high-level programming language",
            },
        )

        # Should return 201 Created
        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["title"] == "Python"
        assert data["domain"] == TechnologyDomain.BACKEND.value
        assert data["status"] == TechnologyStatus.ADOPT.value
        assert isinstance(data["id"], int)

    @pytest.mark.asyncio(enabled=False)
    def test_error_response_formatting(self, client):
        """Error responses follow standard format."""
        # Trigger 404 error by requesting non-existent technology
        response = client.get("/api/v1/technologies/99999")

        assert response.status_code == 404
        error = response.json()

        # Standard FastAPI error format
        assert "detail" in error
        # Detail should be a string or list
        assert isinstance(error["detail"], (str, list))
