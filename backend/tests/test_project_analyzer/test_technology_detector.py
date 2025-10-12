"""
Tests for technology detector
"""
import pytest

from app.services.technology_detector import TechnologyDetector


@pytest.mark.asyncio
async def test_detect_react_from_package_json(sample_package_json):
    """Test React detection from package.json"""
    detector = TechnologyDetector()

    technologies = await detector.detect(sample_package_json)

    # Should detect React, Express
    tech_names = [t.name for t in technologies]
    assert "react" in tech_names
    assert "express" in tech_names

    # Check React details
    react_tech = next(t for t in technologies if t.name == "react")
    assert react_tech.category == "framework"
    assert react_tech.confidence >= 0.9


@pytest.mark.asyncio
async def test_detect_database_from_docker_compose(sample_docker_compose):
    """Test database detection from docker-compose.yml"""
    detector = TechnologyDetector()

    technologies = await detector.detect(sample_docker_compose)

    # Should detect PostgreSQL and Redis
    tech_names = [t.name for t in technologies]
    assert "postgresql" in tech_names
    assert "redis" in tech_names

    # Check PostgreSQL details
    postgres_tech = next(t for t in technologies if t.name == "postgresql")
    assert postgres_tech.category == "database"
    assert postgres_tech.version  # Should extract version from image


@pytest.mark.asyncio
async def test_detect_github_actions(sample_github_actions):
    """Test CI/CD detection from .github/workflows"""
    detector = TechnologyDetector()

    technologies = await detector.detect(sample_github_actions)

    # Should detect GitHub Actions
    tech_names = [t.name for t in technologies]
    assert "github-actions" in tech_names

    gh_actions = next(t for t in technologies if t.name == "github-actions")
    assert gh_actions.category == "ci_cd"
    assert gh_actions.confidence == 1.0


@pytest.mark.asyncio
async def test_detect_multiple_technologies(sample_multi_language_project):
    """Test detection across multiple config files"""
    detector = TechnologyDetector()

    technologies = await detector.detect(sample_multi_language_project)

    # Should detect multiple technologies
    tech_names = [t.name for t in technologies]
    assert "react" in tech_names
    assert "next" in tech_names  # from package.json
    assert "postgresql" in tech_names  # from docker-compose


@pytest.mark.asyncio
async def test_deduplication():
    """Test that duplicate technologies are properly deduplicated"""
    detector = TechnologyDetector()

    from app.schemas.project_analysis import DetectedTechnology

    # Create duplicate technologies with different confidences
    techs = [
        DetectedTechnology(
            name="react",
            category="framework",
            version="18.0.0",
            confidence=0.8,
            file_path="package.json",
        ),
        DetectedTechnology(
            name="react",
            category="framework",
            version="18.2.0",
            confidence=0.95,
            file_path="package-lock.json",
        ),
    ]

    deduplicated = detector._deduplicate(techs)

    # Should keep only one React entry
    assert len(deduplicated) == 1
    # Should keep the higher confidence one
    assert deduplicated[0].confidence == 0.95
