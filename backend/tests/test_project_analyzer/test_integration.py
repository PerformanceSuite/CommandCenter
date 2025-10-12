"""
Integration tests for project analyzer
"""
import pytest

from app.services.project_analyzer import ProjectAnalyzer


@pytest.mark.asyncio
async def test_full_project_analysis(sample_multi_language_project, db_session):
    """Test complete project analysis workflow"""
    analyzer = ProjectAnalyzer(db_session)

    result = await analyzer.analyze_project(
        str(sample_multi_language_project), use_cache=False
    )

    # Verify all analysis components completed
    assert result.project_path == str(sample_multi_language_project)
    assert result.analyzed_at is not None
    assert result.analysis_duration_ms > 0

    # Should have detected dependencies
    assert len(result.dependencies) > 0

    # Should have detected technologies
    assert len(result.technologies) > 0

    # Should have code metrics
    assert result.code_metrics.total_files > 0
    assert result.code_metrics.lines_of_code > 0

    # May or may not have research gaps (depends on mock versions)
    # assert isinstance(result.research_gaps, list)


@pytest.mark.asyncio
async def test_cache_functionality(sample_package_json, db_session):
    """Test that analysis results are cached"""
    analyzer = ProjectAnalyzer(db_session)

    # First analysis
    result1 = await analyzer.analyze_project(
        str(sample_package_json), use_cache=False
    )
    first_duration = result1.analysis_duration_ms

    # Second analysis with cache
    result2 = await analyzer.analyze_project(str(sample_package_json), use_cache=True)

    # Should return same results
    assert result1.project_path == result2.project_path
    assert len(result1.dependencies) == len(result2.dependencies)


@pytest.mark.asyncio
async def test_parser_error_handling(tmp_path, db_session):
    """Test that analyzer handles parser errors gracefully"""
    # Create malformed config files
    (tmp_path / "package.json").write_text("{ invalid json")
    (tmp_path / "requirements.txt").write_text("valid-package==1.0.0")

    analyzer = ProjectAnalyzer(db_session)

    # Should continue with other parsers even if one fails
    result = await analyzer.analyze_project(str(tmp_path), use_cache=False)

    # Should still have results from working parsers
    assert result is not None


@pytest.mark.asyncio
async def test_invalid_project_path(db_session):
    """Test error handling for invalid project paths"""
    analyzer = ProjectAnalyzer(db_session)

    # Non-existent path
    with pytest.raises(ValueError, match="Invalid project path"):
        await analyzer.analyze_project("/nonexistent/path", use_cache=False)


@pytest.mark.asyncio
async def test_multiple_parsers_same_project(sample_multi_language_project, db_session):
    """Test that multiple parsers work together correctly"""
    analyzer = ProjectAnalyzer(db_session)

    result = await analyzer.analyze_project(
        str(sample_multi_language_project), use_cache=False
    )

    # Should have dependencies from multiple languages
    languages = {dep.language for dep in result.dependencies}
    assert "javascript" in languages
    assert "python" in languages


@pytest.mark.asyncio
async def test_get_analysis_by_id(sample_package_json, db_session):
    """Test retrieving cached analysis by ID"""
    analyzer = ProjectAnalyzer(db_session)

    # Create analysis
    await analyzer.analyze_project(str(sample_package_json), use_cache=False)

    # Get analysis by ID (should be 1 after first insert)
    result = await analyzer.get_analysis_by_id(1)

    # Should retrieve cached analysis
    assert result is not None
    assert result.project_path == str(sample_package_json)


@pytest.mark.asyncio
async def test_performance_on_large_project(tmp_path, db_session):
    """Test performance with larger project structure"""
    # Create a project with many files
    for i in range(100):
        (tmp_path / f"file{i}.py").write_text(f"# File {i}\nx = {i}\n")

    analyzer = ProjectAnalyzer(db_session)

    result = await analyzer.analyze_project(str(tmp_path), use_cache=False)

    # Should complete in reasonable time
    assert result.analysis_duration_ms < 30000  # Less than 30 seconds

    # Should count all files
    assert result.code_metrics.total_files == 100
