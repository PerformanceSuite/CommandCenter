"""Unit tests for router validation and middleware."""
import pytest

from app.models.technology import TechnologyDomain, TechnologyStatus


@pytest.mark.unit
@pytest.mark.asyncio
class TestRequestValidation:
    """Test request validation for API endpoints"""

    async def test_request_validation_rejects_invalid_input(self, client):
        """Request validation rejects invalid input."""
        # Invalid request: empty title
        response = await client.post(
            "/api/v1/technologies",
            json={
                "title": "",
                "domain": TechnologyDomain.AI_ML.value,
            },
        )

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422
        assert "detail" in response.json()
        # Check validation error mentions title field
        error_detail = response.json()["detail"]
        assert any("title" in str(err.get("loc", [])) for err in error_detail)

    async def test_response_serialization_format(self, client):
        """Responses are properly serialized."""
        # Create valid technology
        response = await client.post(
            "/api/v1/technologies",
            json={
                "title": "Python",
                "domain": TechnologyDomain.AI_ML.value,
                "status": TechnologyStatus.RESEARCH.value,
                "description": "A high-level programming language",
            },
        )

        # Should return 201 Created
        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["title"] == "Python"
        assert data["domain"] == TechnologyDomain.AI_ML.value
        assert data["status"] == TechnologyStatus.RESEARCH.value
        assert isinstance(data["id"], int)

    async def test_error_response_formatting(self, client):
        """Error responses follow standard format."""
        # Trigger 404 error by requesting non-existent technology
        response = await client.get("/api/v1/technologies/99999")

        assert response.status_code == 404
        error = response.json()

        # Standard FastAPI error format
        assert "detail" in error
        # Detail should be a string or list
        assert isinstance(error["detail"], (str, list))
