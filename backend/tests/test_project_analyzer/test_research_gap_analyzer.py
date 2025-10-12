"""
Tests for research gap analyzer
"""
import pytest

from app.schemas.project_analysis import Dependency, DependencyType
from app.services.research_gap_analyzer import ResearchGapAnalyzer


@pytest.mark.asyncio
async def test_identify_outdated_dependencies():
    """Test identification of outdated dependencies"""
    analyzer = ResearchGapAnalyzer()

    # Create mock dependencies with version gaps
    dependencies = [
        Dependency(
            name="react",
            version="16.0.0",  # Old version
            latest_version="18.2.0",  # Current version
            is_outdated=True,
            type=DependencyType.RUNTIME,
            language="javascript",
            confidence=1.0,
        ),
        Dependency(
            name="axios",
            version="1.4.0",
            latest_version="1.4.1",  # Minor update
            is_outdated=True,
            type=DependencyType.RUNTIME,
            language="javascript",
            confidence=1.0,
        ),
        Dependency(
            name="jest",
            version="29.0.0",
            latest_version="29.0.0",  # Up to date
            is_outdated=False,
            type=DependencyType.DEV,
            language="javascript",
            confidence=1.0,
        ),
    ]

    gaps = await analyzer.analyze(dependencies, [])

    # Should identify gaps for outdated dependencies only
    assert len(gaps) == 2

    # Check severity levels
    gap_names = [g.technology for g in gaps]
    assert "react (javascript)" in gap_names
    assert "axios (javascript)" in gap_names


@pytest.mark.asyncio
async def test_severity_calculation():
    """Test severity level calculation"""
    analyzer = ResearchGapAnalyzer()

    # Test different version gaps
    assert analyzer._calculate_severity("1.0.0", "4.0.0") == "critical"  # 3+ major
    assert analyzer._calculate_severity("1.0.0", "3.0.0") == "high"  # 2 major
    assert analyzer._calculate_severity("1.0.0", "2.0.0") == "high"  # 1 major
    assert analyzer._calculate_severity("1.0.0", "1.5.0") == "low"  # Minor


@pytest.mark.asyncio
async def test_gap_prioritization():
    """Test that gaps are sorted by severity"""
    analyzer = ResearchGapAnalyzer()

    dependencies = [
        Dependency(
            name="low-priority",
            version="1.0.0",
            latest_version="1.1.0",  # Minor
            is_outdated=True,
            type=DependencyType.RUNTIME,
            language="python",
            confidence=1.0,
        ),
        Dependency(
            name="critical-priority",
            version="1.0.0",
            latest_version="5.0.0",  # Major jump
            is_outdated=True,
            type=DependencyType.RUNTIME,
            language="python",
            confidence=1.0,
        ),
        Dependency(
            name="medium-priority",
            version="1.0.0",
            latest_version="2.0.0",
            is_outdated=True,
            type=DependencyType.RUNTIME,
            language="python",
            confidence=1.0,
        ),
    ]

    gaps = await analyzer.analyze(dependencies, [])

    # Should be sorted by severity
    assert gaps[0].severity == "critical"
    assert "critical-priority" in gaps[0].technology


@pytest.mark.asyncio
async def test_effort_estimation():
    """Test effort estimation based on severity"""
    analyzer = ResearchGapAnalyzer()

    # Check effort estimates match severity
    assert analyzer.EFFORT_ESTIMATES["critical"] == "2-4 weeks"
    assert analyzer.EFFORT_ESTIMATES["high"] == "1-2 weeks"
    assert analyzer.EFFORT_ESTIMATES["medium"] == "3-5 days"
    assert analyzer.EFFORT_ESTIMATES["low"] == "1-2 days"


@pytest.mark.asyncio
async def test_suggested_task_generation():
    """Test research task suggestion generation"""
    analyzer = ResearchGapAnalyzer()

    dep = Dependency(
        name="django",
        version="3.0.0",
        latest_version="4.2.0",
        is_outdated=True,
        type=DependencyType.RUNTIME,
        language="python",
        confidence=1.0,
    )

    gap = analyzer._create_gap_from_dependency(dep)

    # Should generate meaningful task
    assert "django" in gap.suggested_task.lower()
    assert "4.2.0" in gap.suggested_task
    assert len(gap.description) > 20  # Should have detailed description
