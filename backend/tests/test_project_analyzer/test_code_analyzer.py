"""
Tests for code analyzer
"""
import pytest

from app.services.code_analyzer import CodeAnalyzer


@pytest.mark.asyncio
async def test_analyze_multi_language_project(sample_multi_language_project):
    """Test code analysis on multi-language project"""
    analyzer = CodeAnalyzer()

    metrics = await analyzer.analyze(sample_multi_language_project)

    # Should count files
    assert metrics.total_files > 0

    # Should detect multiple languages
    assert "python" in metrics.languages
    assert "typescript" in metrics.languages

    # Should have positive LOC
    assert metrics.lines_of_code > 0

    # Should calculate complexity
    assert metrics.complexity_score >= 0


@pytest.mark.asyncio
async def test_language_detection():
    """Test language detection from file extensions"""
    analyzer = CodeAnalyzer()
    from pathlib import Path

    # Test various file extensions
    assert analyzer._detect_language(Path("test.py")) == "python"
    assert analyzer._detect_language(Path("test.js")) == "javascript"
    assert analyzer._detect_language(Path("test.ts")) == "typescript"
    assert analyzer._detect_language(Path("test.go")) == "go"
    assert analyzer._detect_language(Path("test.rs")) == "rust"
    assert analyzer._detect_language(Path("test.java")) == "java"

    # Unknown extension
    assert analyzer._detect_language(Path("test.xyz")) is None


@pytest.mark.asyncio
async def test_skip_patterns():
    """Test that certain directories are skipped"""
    analyzer = CodeAnalyzer()
    from pathlib import Path

    # Should skip common build/dependency directories
    assert analyzer._should_skip(Path("/project/node_modules/package"))
    assert analyzer._should_skip(Path("/project/venv/lib/python"))
    assert analyzer._should_skip(Path("/project/.git/objects"))
    assert analyzer._should_skip(Path("/project/__pycache__/module.pyc"))

    # Should not skip normal directories
    assert not analyzer._should_skip(Path("/project/src/main.py"))


@pytest.mark.asyncio
async def test_complexity_calculation(tmp_path):
    """Test complexity score calculation"""
    analyzer = CodeAnalyzer()

    # Create multiple files with different sizes
    (tmp_path / "file1.py").write_text("x = 1\ny = 2\n")
    (tmp_path / "file2.py").write_text("def foo():\n    pass\n")
    (tmp_path / "file3.py").write_text("class Bar:\n    pass\n")

    metrics = await analyzer.analyze(tmp_path)

    # Complexity should be based on file count, LOC, and depth
    assert metrics.complexity_score > 0


@pytest.mark.asyncio
async def test_empty_project(tmp_path):
    """Test analysis of empty project"""
    analyzer = CodeAnalyzer()

    metrics = await analyzer.analyze(tmp_path)

    # Should handle empty project gracefully
    assert metrics.total_files == 0
    assert metrics.lines_of_code == 0
    assert len(metrics.languages) == 0
    assert metrics.complexity_score == 0.0
