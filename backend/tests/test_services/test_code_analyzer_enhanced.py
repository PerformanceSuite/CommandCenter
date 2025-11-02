"""
Tests for enhanced code analyzer with AST analysis.
"""

import pytest
from pathlib import Path
import tempfile
import textwrap

from app.services.code_analyzer import CodeAnalyzer, ASTComplexityVisitor
import ast


@pytest.fixture
def analyzer():
    """Create code analyzer instance."""
    return CodeAnalyzer()


@pytest.fixture
def temp_python_file():
    """Create temporary Python file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        code = textwrap.dedent(
            """
            import os
            import sys

            class TestClass:
                def __init__(self):
                    self.value = 0

                def method_one(self):
                    if self.value > 0:
                        return True
                    return False

                def method_two(self, x, y):
                    result = 0
                    for i in range(x):
                        if i % 2 == 0:
                            result += y
                    return result

            def standalone_function(a, b):
                try:
                    return a / b
                except ZeroDivisionError:
                    return 0
        """
        )
        f.write(code)
        f.flush()
        yield Path(f.name)

    # Cleanup
    Path(f.name).unlink(missing_ok=True)


class TestASTComplexityVisitor:
    """Tests for AST complexity visitor."""

    def test_visitor_counts_functions(self):
        """Test visitor counts function definitions."""
        code = textwrap.dedent(
            """
            def func1():
                pass

            def func2():
                pass

            async def func3():
                pass
        """
        )
        tree = ast.parse(code)
        visitor = ASTComplexityVisitor()
        visitor.visit(tree)

        assert visitor.functions == 3
        assert visitor.complexity >= 4  # Base + 3 functions

    def test_visitor_counts_classes(self):
        """Test visitor counts class definitions."""
        code = textwrap.dedent(
            """
            class ClassA:
                pass

            class ClassB:
                def method(self):
                    pass
        """
        )
        tree = ast.parse(code)
        visitor = ASTComplexityVisitor()
        visitor.visit(tree)

        assert visitor.classes == 2
        assert visitor.functions == 1  # method

    def test_visitor_counts_imports(self):
        """Test visitor counts imports."""
        code = textwrap.dedent(
            """
            import os
            import sys
            from pathlib import Path
            from typing import List, Dict
        """
        )
        tree = ast.parse(code)
        visitor = ASTComplexityVisitor()
        visitor.visit(tree)

        assert visitor.imports == 4

    def test_visitor_calculates_complexity(self):
        """Test visitor calculates cyclomatic complexity."""
        code = textwrap.dedent(
            """
            def complex_function(x):
                if x > 0:
                    for i in range(x):
                        if i % 2 == 0:
                            pass
                while x > 10:
                    x -= 1
                try:
                    result = 1 / x
                except ZeroDivisionError:
                    result = 0
                return result
        """
        )
        tree = ast.parse(code)
        visitor = ASTComplexityVisitor()
        visitor.visit(tree)

        # Complexity: 1 (base) + 1 (func) + 2 (if) + 1 (for) + 1 (while) + 1 (except) = 7
        assert visitor.complexity >= 7

    def test_visitor_counts_boolean_operations(self):
        """Test visitor counts boolean operations."""
        code = textwrap.dedent(
            """
            def func(a, b, c):
                if a and b or c:
                    pass
        """
        )
        tree = ast.parse(code)
        visitor = ASTComplexityVisitor()
        visitor.visit(tree)

        # Complexity from and/or operations
        assert visitor.complexity >= 3


class TestCodeAnalyzerEnhanced:
    """Tests for enhanced code analyzer."""

    @pytest.mark.asyncio
    async def test_analyze_python_file(self, analyzer, temp_python_file):
        """Test AST analysis of Python file."""
        metrics = await analyzer._analyze_python_file(temp_python_file)

        assert metrics is not None
        assert metrics["functions"] > 0
        assert metrics["classes"] > 0
        assert metrics["imports"] > 0
        assert metrics["complexity"] > 1

    @pytest.mark.asyncio
    async def test_analyze_returns_enhanced_metrics(self, analyzer):
        """Test analyze returns enhanced metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create Python file
            py_file = tmpdir_path / "test.py"
            py_file.write_text(
                textwrap.dedent(
                    """
                def test_func():
                    if True:
                        pass
            """
                )
            )

            result = await analyzer.analyze(tmpdir_path)

            assert result.total_files > 0
            assert result.lines_of_code > 0
            assert result.cyclomatic_complexity is not None
            assert result.total_functions is not None
            assert result.total_classes is not None

    @pytest.mark.asyncio
    async def test_analyze_handles_syntax_errors_gracefully(self, analyzer):
        """Test analyzer handles files with syntax errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create Python file with syntax error
            py_file = tmpdir_path / "bad.py"
            py_file.write_text("def bad syntax(")

            # Should not raise, but skip the bad file
            result = await analyzer.analyze(tmpdir_path)

            assert result.total_files >= 0

    @pytest.mark.asyncio
    async def test_complexity_score_uses_ast_metrics(self, analyzer):
        """Test complexity score incorporates AST metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create complex Python file
            py_file = tmpdir_path / "complex.py"
            py_file.write_text(
                textwrap.dedent(
                    """
                def very_complex(x, y, z):
                    if x > 0:
                        for i in range(x):
                            if i % 2 == 0:
                                while y > 0:
                                    y -= 1
                                    if z:
                                        pass
            """
                )
            )

            result = await analyzer.analyze(tmpdir_path)

            # Complexity score should be > 0
            assert result.complexity_score > 0
            # Should have cyclomatic complexity
            assert result.cyclomatic_complexity is not None
            assert result.cyclomatic_complexity > 5  # Complex function

    @pytest.mark.asyncio
    async def test_analyze_multiple_python_files(self, analyzer):
        """Test analyzing directory with multiple Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create multiple Python files
            for i in range(3):
                py_file = tmpdir_path / f"file{i}.py"
                py_file.write_text(
                    textwrap.dedent(
                        f"""
                    class Class{i}:
                        def method(self):
                            if True:
                                pass
                """
                    )
                )

            result = await analyzer.analyze(tmpdir_path)

            assert result.total_files == 3
            assert result.total_classes == 3
            assert result.total_functions == 3
            assert result.cyclomatic_complexity is not None

    @pytest.mark.asyncio
    async def test_average_complexity_calculation(self, analyzer):
        """Test average complexity is calculated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create two files with known complexity
            py_file1 = tmpdir_path / "simple.py"
            py_file1.write_text("def simple(): pass")

            py_file2 = tmpdir_path / "complex.py"
            py_file2.write_text(
                textwrap.dedent(
                    """
                def complex(x):
                    if x > 0:
                        for i in range(10):
                            if i % 2:
                                pass
            """
                )
            )

            result = await analyzer.analyze(tmpdir_path)

            # Average should be between simple and complex
            assert result.cyclomatic_complexity is not None
            assert result.cyclomatic_complexity > 1
