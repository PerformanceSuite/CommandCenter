"""
Unit tests for Technology Pydantic schemas
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.technology import (
    CostTier,
    IntegrationDifficulty,
    MaturityLevel,
    TechnologyDomain,
    TechnologyStatus,
)
from app.schemas.technology import (
    TechnologyBase,
    TechnologyCreate,
    TechnologyResponse,
    TechnologyUpdate,
)


@pytest.mark.unit
class TestTechnologySchemas:
    """Test Technology Pydantic schema validation"""

    def test_technology_base_valid(self):
        """Test TechnologyBase with valid data"""
        data = {
            "title": "FastAPI",
            "domain": TechnologyDomain.INFRASTRUCTURE,
            "status": TechnologyStatus.EVALUATION,
            "relevance_score": 85,
            "priority": 4,
            "description": "Modern Python web framework",
        }
        schema = TechnologyBase(**data)

        assert schema.title == "FastAPI"
        assert schema.domain == TechnologyDomain.INFRASTRUCTURE
        assert schema.status == TechnologyStatus.EVALUATION
        assert schema.relevance_score == 85
        assert schema.priority == 4
        assert schema.description == "Modern Python web framework"

    def test_technology_base_defaults(self):
        """Test TechnologyBase default values"""
        schema = TechnologyBase(title="TestTech")

        assert schema.title == "TestTech"
        assert schema.domain == TechnologyDomain.OTHER
        assert schema.status == TechnologyStatus.DISCOVERY
        assert schema.relevance_score == 50
        assert schema.priority == 3

    def test_technology_create_validation(self):
        """Test TechnologyCreate schema validation"""
        # Valid creation
        schema = TechnologyCreate(
            title="Django",
            domain=TechnologyDomain.INFRASTRUCTURE,
            description="Python web framework",
        )
        assert schema.title == "Django"

        # Test title length validation
        with pytest.raises(ValidationError) as exc_info:
            TechnologyCreate(title="")  # Empty title should fail

        assert "title" in str(exc_info.value)

    def test_technology_relevance_score_validation(self):
        """Test relevance score must be between 0-100"""
        # Valid scores
        for score in [0, 50, 100]:
            schema = TechnologyCreate(title="Test", relevance_score=score)
            assert schema.relevance_score == score

        # Invalid scores
        with pytest.raises(ValidationError):
            TechnologyCreate(title="Test", relevance_score=-1)

        with pytest.raises(ValidationError):
            TechnologyCreate(title="Test", relevance_score=101)

    def test_technology_priority_validation(self):
        """Test priority must be between 1-5"""
        # Valid priorities
        for priority in [1, 2, 3, 4, 5]:
            schema = TechnologyCreate(title="Test", priority=priority)
            assert schema.priority == priority

        # Invalid priorities
        with pytest.raises(ValidationError):
            TechnologyCreate(title="Test", priority=0)

        with pytest.raises(ValidationError):
            TechnologyCreate(title="Test", priority=6)

    def test_technology_update_partial(self):
        """Test TechnologyUpdate allows partial updates"""
        # Update only title
        schema = TechnologyUpdate(title="Updated Title")
        assert schema.title == "Updated Title"
        assert schema.domain is None
        assert schema.status is None

        # Update multiple fields
        schema = TechnologyUpdate(
            title="Redis",
            status=TechnologyStatus.IMPLEMENTATION,
            priority=5,
        )
        assert schema.title == "Redis"
        assert schema.status == TechnologyStatus.IMPLEMENTATION
        assert schema.priority == 5

    def test_technology_with_enhanced_fields(self):
        """Test Technology Radar v2 enhanced fields"""
        schema = TechnologyCreate(
            title="Kubernetes",
            latency_ms=5.0,
            throughput_qps=50000,
            integration_difficulty=IntegrationDifficulty.COMPLEX,
            integration_time_estimate_days=30,
            maturity_level=MaturityLevel.STABLE,
            stability_score=90,
            cost_tier=CostTier.FREE,
            cost_monthly_usd=0.0,
            github_stars=100000,
        )

        assert schema.latency_ms == 5.0
        assert schema.throughput_qps == 50000
        assert schema.integration_difficulty == IntegrationDifficulty.COMPLEX
        assert schema.integration_time_estimate_days == 30
        assert schema.maturity_level == MaturityLevel.STABLE
        assert schema.stability_score == 90
        assert schema.cost_tier == CostTier.FREE
        assert schema.cost_monthly_usd == 0.0
        assert schema.github_stars == 100000

    def test_technology_negative_values_validation(self):
        """Test that negative values are rejected for numeric fields"""
        # latency_ms cannot be negative
        with pytest.raises(ValidationError):
            TechnologyCreate(title="Test", latency_ms=-1.0)

        # throughput_qps cannot be negative
        with pytest.raises(ValidationError):
            TechnologyCreate(title="Test", throughput_qps=-100)

        # integration_time_estimate_days cannot be negative
        with pytest.raises(ValidationError):
            TechnologyCreate(title="Test", integration_time_estimate_days=-5)

        # stability_score must be 0-100
        with pytest.raises(ValidationError):
            TechnologyCreate(title="Test", stability_score=-1)

        with pytest.raises(ValidationError):
            TechnologyCreate(title="Test", stability_score=101)

        # cost_monthly_usd cannot be negative
        with pytest.raises(ValidationError):
            TechnologyCreate(title="Test", cost_monthly_usd=-50.0)

        # github_stars cannot be negative
        with pytest.raises(ValidationError):
            TechnologyCreate(title="Test", github_stars=-1)

    def test_technology_response_from_model(self):
        """Test TechnologyResponse can be created from model attributes"""
        data = {
            "id": 1,
            "title": "PostgreSQL",
            "vendor": None,
            "domain": TechnologyDomain.INFRASTRUCTURE,
            "status": TechnologyStatus.INTEGRATED,
            "relevance_score": 95,
            "priority": 5,
            "description": "Open source database",
            "notes": None,
            "use_cases": None,
            "documentation_url": "https://postgresql.org/docs",
            "repository_url": None,
            "website_url": "https://postgresql.org",
            "tags": "database,sql,open-source",
            "latency_ms": None,
            "throughput_qps": None,
            "integration_difficulty": None,
            "integration_time_estimate_days": None,
            "maturity_level": MaturityLevel.MATURE,
            "stability_score": 98,
            "cost_tier": CostTier.FREE,
            "cost_monthly_usd": None,
            "dependencies": None,
            "alternatives": None,
            "last_hn_mention": None,
            "hn_score_avg": None,
            "github_stars": None,
            "github_last_commit": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        schema = TechnologyResponse(**data)
        assert schema.id == 1
        assert schema.title == "PostgreSQL"
        assert schema.maturity_level == MaturityLevel.MATURE
        assert schema.stability_score == 98
        assert isinstance(schema.created_at, datetime)
        assert isinstance(schema.updated_at, datetime)

    def test_technology_with_dependencies(self):
        """Test technology with dependency tracking"""
        dependencies = {
            "python": ">=3.8",
            "fastapi": ">=0.100.0",
            "uvicorn": "latest",
        }

        schema = TechnologyCreate(
            title="MyApp", dependencies=dependencies, alternatives="Flask,Django"
        )

        assert schema.dependencies == dependencies
        assert schema.alternatives == "Flask,Django"
