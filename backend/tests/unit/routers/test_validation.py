"""Unit tests for router validation and middleware."""
import pytest

from app.models.technology import TechnologyDomain


@pytest.mark.unit
class TestRequestValidation:
    """Test request validation for API endpoints.

    These tests focus on Pydantic validation (422 errors) which happens
    before database operations, making them suitable for sync unit tests.
    """

    def test_request_validation_rejects_invalid_input(self, client):
        """Request validation rejects invalid input (empty title)."""
        response = client.post(
            "/api/v1/technologies",
            json={
                "title": "",  # Empty title should fail validation
                "domain": TechnologyDomain.AI_ML.value,
            },
        )

        # Should return 422 Unprocessable Entity for validation error
        assert response.status_code == 422
        assert "detail" in response.json()
        # Check validation error mentions title field
        error_detail = response.json()["detail"]
        assert any("title" in str(err.get("loc", [])) for err in error_detail)

    def test_request_validation_rejects_invalid_domain(self, client):
        """Request validation rejects invalid domain value."""
        response = client.post(
            "/api/v1/technologies",
            json={
                "title": "Valid Title",
                "domain": "invalid_domain_value",  # Invalid domain
            },
        )

        # Should return 422 for invalid enum value
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_request_validation_rejects_missing_required_fields(self, client):
        """Request validation rejects missing required fields."""
        response = client.post(
            "/api/v1/technologies",
            json={
                # Missing title and domain - both required
            },
        )

        # Should return 422 for missing required fields
        assert response.status_code == 422
        assert "detail" in response.json()
        error_detail = response.json()["detail"]
        # Should mention missing fields
        assert len(error_detail) >= 1
