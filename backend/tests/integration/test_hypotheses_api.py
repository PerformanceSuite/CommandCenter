"""
Integration tests for Hypotheses API endpoints (AI Arena).

Tests the REST API for hypothesis management and validation.
"""

import pytest
from httpx import AsyncClient
from libs.ai_arena.hypothesis.registry import HypothesisRegistry
from libs.ai_arena.hypothesis.schema import (
    Hypothesis,
    HypothesisCategory,
    HypothesisCreate,
    HypothesisEvidence,
    HypothesisStatus,
    ImpactLevel,
    RiskLevel,
    TestabilityLevel,
)

from app.services.hypothesis_service import HypothesisService


@pytest.fixture
def hypothesis_registry():
    """Create a fresh hypothesis registry for each test."""
    from app.services.hypothesis_service import hypothesis_service

    registry = HypothesisRegistry()
    # Reset both the class variable and the singleton's instance variable
    HypothesisService._registry = registry
    hypothesis_service.registry = registry

    yield registry

    # Clean up after test
    registry.clear()


@pytest.fixture
def sample_hypothesis(hypothesis_registry) -> Hypothesis:
    """Create a sample hypothesis for testing."""
    return hypothesis_registry.create(
        HypothesisCreate(
            statement="AI-powered hypothesis validation improves research quality",
            category=HypothesisCategory.TECHNICAL,
            impact=ImpactLevel.HIGH,
            risk=RiskLevel.MEDIUM,
            testability=TestabilityLevel.MEDIUM,
            success_criteria="80% consensus reached in validation",
            context="Testing the AI Arena system",
        )
    )


@pytest.fixture
def sample_hypotheses(hypothesis_registry) -> list[Hypothesis]:
    """Create multiple sample hypotheses for testing."""
    h1 = hypothesis_registry.create(
        HypothesisCreate(
            statement="Market analysis improves pricing decisions",
            category=HypothesisCategory.MARKET,
            impact=ImpactLevel.HIGH,
            risk=RiskLevel.LOW,
            testability=TestabilityLevel.EASY,
            success_criteria="Correlation > 0.7",
        )
    )
    h2 = hypothesis_registry.create(
        HypothesisCreate(
            statement="Customer interviews reveal hidden needs",
            category=HypothesisCategory.CUSTOMER,
            impact=ImpactLevel.MEDIUM,
            risk=RiskLevel.LOW,
            testability=TestabilityLevel.MEDIUM,
            success_criteria="3+ new insights discovered",
        )
    )
    h3 = hypothesis_registry.create(
        HypothesisCreate(
            statement="Premium pricing increases perceived value",
            category=HypothesisCategory.REVENUE,
            impact=ImpactLevel.HIGH,
            risk=RiskLevel.HIGH,
            testability=TestabilityLevel.HARD,
            success_criteria="Willingness to pay increases 20%",
        )
    )
    return [h1, h2, h3]


@pytest.mark.integration
class TestHypothesesListAPI:
    """Test hypothesis listing endpoints."""

    async def test_list_hypotheses_empty(
        self, api_client: AsyncClient, hypothesis_registry: HypothesisRegistry
    ):
        """Test listing hypotheses when registry is empty."""
        response = await api_client.get("/hypotheses/")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 20
        assert data["skip"] == 0

    async def test_list_hypotheses(
        self, api_client: AsyncClient, sample_hypotheses: list[Hypothesis]
    ):
        """Test listing hypotheses with data."""
        response = await api_client.get("/hypotheses/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    async def test_list_hypotheses_filter_by_status(
        self, api_client: AsyncClient, sample_hypotheses: list[Hypothesis], hypothesis_registry
    ):
        """Test filtering hypotheses by status."""
        # Mark one as validated
        hypothesis_registry.update_status(sample_hypotheses[0].id, HypothesisStatus.VALIDATED)

        response = await api_client.get("/hypotheses/?status=validated")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "validated"

    async def test_list_hypotheses_filter_by_category(
        self, api_client: AsyncClient, sample_hypotheses: list[Hypothesis]
    ):
        """Test filtering hypotheses by category."""
        response = await api_client.get("/hypotheses/?category=market")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["category"] == "market"

    async def test_list_hypotheses_pagination(
        self, api_client: AsyncClient, sample_hypotheses: list[Hypothesis]
    ):
        """Test pagination of hypothesis list."""
        response = await api_client.get("/hypotheses/?limit=2&skip=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["limit"] == 2
        assert data["skip"] == 0

        # Get second page
        response = await api_client.get("/hypotheses/?limit=2&skip=2")
        data = response.json()
        assert len(data["items"]) == 1


@pytest.mark.integration
class TestHypothesisDetailAPI:
    """Test hypothesis detail endpoints."""

    async def test_get_hypothesis(self, api_client: AsyncClient, sample_hypothesis: Hypothesis):
        """Test getting a specific hypothesis."""
        response = await api_client.get(f"/hypotheses/{sample_hypothesis.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_hypothesis.id
        assert data["statement"] == sample_hypothesis.statement
        assert data["category"] == sample_hypothesis.category.value
        assert data["status"] == sample_hypothesis.status.value
        assert data["impact"] == "high"
        assert data["risk"] == "medium"
        assert "created_at" in data
        assert "evidence" in data

    async def test_get_hypothesis_not_found(self, api_client: AsyncClient, hypothesis_registry):
        """Test getting a non-existent hypothesis."""
        response = await api_client.get("/hypotheses/nonexistent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_hypothesis_with_evidence(
        self, api_client: AsyncClient, sample_hypothesis: Hypothesis, hypothesis_registry
    ):
        """Test getting hypothesis with evidence."""
        # Add evidence
        evidence = HypothesisEvidence(
            source="Customer interview",
            content="Users prefer automated validation",
            supports=True,
            confidence=85,
            collected_by="researcher_agent",
        )
        hypothesis_registry.add_evidence(sample_hypothesis.id, evidence)

        response = await api_client.get(f"/hypotheses/{sample_hypothesis.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["evidence"]) == 1
        assert data["evidence"][0]["source"] == "Customer interview"
        assert data["evidence"][0]["supports"] is True
        assert data["evidence"][0]["confidence"] == 85


@pytest.mark.integration
class TestHypothesisStatsAPI:
    """Test hypothesis statistics endpoint."""

    async def test_get_stats_empty(self, api_client: AsyncClient, hypothesis_registry):
        """Test statistics with no hypotheses."""
        response = await api_client.get("/hypotheses/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert "by_status" in data
        assert "by_category" in data

    async def test_get_stats_with_data(
        self, api_client: AsyncClient, sample_hypotheses: list[Hypothesis], hypothesis_registry
    ):
        """Test statistics with hypotheses."""
        # Mark one as validated
        hypothesis_registry.update_status(sample_hypotheses[0].id, HypothesisStatus.VALIDATED)

        response = await api_client.get("/hypotheses/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["by_status"]["validated"] == 1
        assert data["by_status"]["untested"] == 2


@pytest.mark.integration
class TestValidationAPI:
    """Test hypothesis validation endpoints."""

    async def test_start_validation(self, api_client: AsyncClient, sample_hypothesis: Hypothesis):
        """Test starting a validation (returns task ID)."""
        response = await api_client.post(
            f"/hypotheses/{sample_hypothesis.id}/validate",
            json={"max_rounds": 2},
        )

        # Validation is async, so we get 202 Accepted
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["hypothesis_id"] == sample_hypothesis.id
        assert data["status"] == "started"

    async def test_start_validation_not_found(self, api_client: AsyncClient, hypothesis_registry):
        """Test starting validation for non-existent hypothesis."""
        response = await api_client.post(
            "/hypotheses/nonexistent-id/validate",
            json={},
        )

        assert response.status_code == 404

    async def test_get_validation_task_not_found(
        self, api_client: AsyncClient, hypothesis_registry
    ):
        """Test getting non-existent validation task."""
        response = await api_client.get("/hypotheses/validation/nonexistent-task")

        assert response.status_code == 404


@pytest.mark.integration
class TestEvidenceExplorerAPI:
    """Test evidence exploration endpoints."""

    async def test_list_evidence_empty(self, api_client: AsyncClient, hypothesis_registry):
        """Test listing evidence when none exists."""
        response = await api_client.get("/hypotheses/evidence/list")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_evidence(
        self, api_client: AsyncClient, sample_hypothesis: Hypothesis, hypothesis_registry
    ):
        """Test listing evidence across hypotheses."""
        # Add evidence
        evidence1 = HypothesisEvidence(
            source="Market research",
            content="Data supports hypothesis",
            supports=True,
            confidence=90,
            collected_by="analyst_agent",
        )
        evidence2 = HypothesisEvidence(
            source="Customer survey",
            content="Mixed results",
            supports=False,
            confidence=60,
            collected_by="researcher_agent",
        )
        hypothesis_registry.add_evidence(sample_hypothesis.id, evidence1)
        hypothesis_registry.add_evidence(sample_hypothesis.id, evidence2)

        response = await api_client.get("/hypotheses/evidence/list")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    async def test_list_evidence_filter_supports(
        self, api_client: AsyncClient, sample_hypothesis: Hypothesis, hypothesis_registry
    ):
        """Test filtering evidence by supports flag."""
        # Add mixed evidence
        evidence1 = HypothesisEvidence(
            source="Test 1",
            content="Supporting",
            supports=True,
            confidence=80,
            collected_by="agent",
        )
        evidence2 = HypothesisEvidence(
            source="Test 2",
            content="Contradicting",
            supports=False,
            confidence=70,
            collected_by="agent",
        )
        hypothesis_registry.add_evidence(sample_hypothesis.id, evidence1)
        hypothesis_registry.add_evidence(sample_hypothesis.id, evidence2)

        response = await api_client.get("/hypotheses/evidence/list?supports=true")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["supports"] is True

    async def test_evidence_stats(
        self, api_client: AsyncClient, sample_hypothesis: Hypothesis, hypothesis_registry
    ):
        """Test evidence statistics endpoint."""
        # Add evidence
        evidence = HypothesisEvidence(
            source="Research study",
            content="Test content",
            supports=True,
            confidence=85,
            collected_by="analyst_agent",
        )
        hypothesis_registry.add_evidence(sample_hypothesis.id, evidence)

        response = await api_client.get("/hypotheses/evidence/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["supporting"] == 1
        assert data["contradicting"] == 0
        assert data["average_confidence"] == 85


@pytest.mark.integration
class TestCostTrackingAPI:
    """Test cost tracking endpoint."""

    async def test_get_cost_stats(self, api_client: AsyncClient, hypothesis_registry):
        """Test getting cost statistics."""
        response = await api_client.get("/hypotheses/costs")

        assert response.status_code == 200
        data = response.json()
        # Should have cost-related fields
        assert "total_cost" in data
        assert "total_tokens" in data
        assert "total_requests" in data
        assert "cost_by_provider" in data
        assert "tokens_by_provider" in data
        assert "requests_by_provider" in data
