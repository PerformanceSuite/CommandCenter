"""
Code structure analyzer using AST and file metrics
"""

import ast
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.schemas.project_analysis import CodeMetrics


class ASTComplexityVisitor(ast.NodeVisitor):
    """
    AST visitor to calculate cyclomatic complexity.

    Counts decision points in code (if, while, for, and, or, etc.)
    """

    def __init__(self):
        self.complexity = 1  # Base complexity
        self.functions = 0
        self.classes = 0
        self.imports = 0

    def visit_FunctionDef(self, node):
        """Count function definitions"""
        self.functions += 1
        self.complexity += 1  # Each function adds complexity
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Count async function definitions"""
        self.functions += 1
        self.complexity += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Count class definitions"""
        self.classes += 1
        self.generic_visit(node)

    def visit_If(self, node):
        """Count if statements"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        """Count while loops"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        """Count for loops"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        """Count boolean operations (and/or)"""
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        """Count exception handlers"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        """Count context managers"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_Import(self, node):
        """Count imports"""
        self.imports += 1
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Count from imports"""
        self.imports += 1
        self.generic_visit(node)


class CodeAnalyzer:
    """
    Analyze code structure and complexity.

    Uses AST-based analysis for supported languages and
    simple file counting for others.
    """

    # File extensions by language
    LANGUAGE_EXTENSIONS: Dict[str, list] = {
        "python": [".py"],
        "javascript": [".js", ".jsx", ".mjs"],
        "typescript": [".ts", ".tsx"],
        "go": [".go"],
        "rust": [".rs"],
        "java": [".java"],
        "kotlin": [".kt", ".kts"],
        "ruby": [".rb"],
        "php": [".php"],
        "c": [".c", ".h"],
        "cpp": [".cpp", ".hpp", ".cc", ".hh"],
        "csharp": [".cs"],
        "swift": [".swift"],
        "dart": [".dart"],
    }

    # Architecture patterns to detect
    ARCHITECTURE_PATTERNS: Dict[str, list] = {
        "microservices": ["services/", "microservices/", "docker-compose"],
        "mvc": ["models/", "views/", "controllers/"],
        "mvvm": ["viewmodels/", "views/", "models/"],
        "clean_architecture": ["domain/", "application/", "infrastructure/"],
        "hexagonal": ["ports/", "adapters/", "domain/"],
        "layered": ["presentation/", "business/", "data/"],
    }

    async def analyze(self, project_path: Path) -> CodeMetrics:
        """
        Analyze code structure and complexity.

        Args:
            project_path: Path to project root

        Returns:
            CodeMetrics with analysis results
        """
        # Count files and LOC by language
        total_files = 0
        lines_of_code = 0
        languages: Dict[str, int] = {}

        # AST analysis metrics (Python only for now)
        ast_metrics = {
            "total_complexity": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_imports": 0,
            "analyzed_files": 0,
        }

        # Walk through all files
        for file_path in project_path.rglob("*"):
            # Skip common ignore patterns
            if self._should_skip(file_path):
                continue

            if file_path.is_file():
                total_files += 1

                # Determine language
                language = self._detect_language(file_path)
                if language:
                    # Count lines
                    loc = await self._count_lines(file_path)
                    lines_of_code += loc
                    languages[language] = languages.get(language, 0) + loc

                    # Perform AST analysis for Python files
                    if language == "python":
                        file_metrics = await self._analyze_python_file(file_path)
                        if file_metrics:
                            ast_metrics["total_complexity"] += file_metrics[
                                "complexity"
                            ]
                            ast_metrics["total_functions"] += file_metrics["functions"]
                            ast_metrics["total_classes"] += file_metrics["classes"]
                            ast_metrics["total_imports"] += file_metrics["imports"]
                            ast_metrics["analyzed_files"] += 1

        # Calculate complexity score using both heuristics and AST data
        complexity_score = await self._calculate_complexity(
            project_path, total_files, lines_of_code, ast_metrics
        )

        # Detect architecture pattern
        architecture = await self._detect_architecture(project_path)

        # Calculate average complexity per file (if we analyzed any Python files)
        avg_complexity = None
        if ast_metrics["analyzed_files"] > 0:
            avg_complexity = round(
                ast_metrics["total_complexity"] / ast_metrics["analyzed_files"], 2
            )

        return CodeMetrics(
            total_files=total_files,
            lines_of_code=lines_of_code,
            languages=languages,
            complexity_score=complexity_score,
            architecture_pattern=architecture,
            cyclomatic_complexity=avg_complexity,
            total_functions=ast_metrics["total_functions"],
            total_classes=ast_metrics["total_classes"],
        )

    def _should_skip(self, path: Path) -> bool:
        """
        Check if path should be skipped.

        Args:
            path: Path to check

        Returns:
            True if should be skipped
        """
        skip_patterns = [
            "node_modules",
            "venv",
            ".venv",
            "__pycache__",
            ".git",
            ".pytest_cache",
            "build",
            "dist",
            "target",
            ".next",
            "coverage",
            ".coverage",
            "vendor",
        ]

        return any(pattern in str(path) for pattern in skip_patterns)

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """
        Detect programming language from file extension.

        Args:
            file_path: Path to file

        Returns:
            Language name or None
        """
        suffix = file_path.suffix.lower()

        for language, extensions in self.LANGUAGE_EXTENSIONS.items():
            if suffix in extensions:
                return language

        return None

    async def _count_lines(self, file_path: Path) -> int:
        """
        Count lines of code in file.

        Args:
            file_path: Path to file

        Returns:
            Number of lines
        """

        def _count():
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return sum(1 for line in f if line.strip())
            except Exception:
                return 0

        return await asyncio.to_thread(_count)

    async def _analyze_python_file(self, file_path: Path) -> Optional[Dict]:
        """
        Perform AST-based analysis on Python file.

        Args:
            file_path: Path to Python file

        Returns:
            Dictionary with complexity metrics or None if analysis fails
        """

        def _analyze():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()

                tree = ast.parse(source, filename=str(file_path))
                visitor = ASTComplexityVisitor()
                visitor.visit(tree)

                return {
                    "complexity": visitor.complexity,
                    "functions": visitor.functions,
                    "classes": visitor.classes,
                    "imports": visitor.imports,
                }
            except Exception:
                # Skip files that can't be parsed
                return None

        return await asyncio.to_thread(_analyze)

    async def _calculate_complexity(
        self,
        project_path: Path,
        total_files: int,
        lines_of_code: int,
        ast_metrics: Dict,
    ) -> float:
        """
        Calculate complexity score.

        Uses file count, LOC, directory depth, and AST metrics.

        Args:
            project_path: Project root path
            total_files: Total file count
            lines_of_code: Total LOC
            ast_metrics: AST analysis metrics

        Returns:
            Complexity score (0-100, higher = more complex)
        """
        # Size-based heuristics
        file_score = min(total_files / 100, 25)  # Max 25 points
        loc_score = min(lines_of_code / 10000, 30)  # Max 30 points

        # Directory depth score
        max_depth = 0
        for path in project_path.rglob("*"):
            if path.is_file() and not self._should_skip(path):
                depth = len(path.relative_to(project_path).parts)
                max_depth = max(max_depth, depth)

        depth_score = min(max_depth * 2, 20)  # Max 20 points

        # AST-based complexity score (if available)
        ast_score = 0
        if ast_metrics["analyzed_files"] > 0:
            avg_file_complexity = (
                ast_metrics["total_complexity"] / ast_metrics["analyzed_files"]
            )
            # Normalize: avg complexity of 5-10 is typical, 20+ is high
            ast_score = min(avg_file_complexity / 20 * 25, 25)  # Max 25 points

        total_score = file_score + loc_score + depth_score + ast_score
        return round(total_score, 2)

    async def _detect_architecture(self, project_path: Path) -> Optional[str]:
        """
        Detect architecture pattern.

        Args:
            project_path: Project root path

        Returns:
            Architecture pattern name or None
        """
        # Get all subdirectory names (lowercase)
        subdirs = {
            p.name.lower()
            for p in project_path.rglob("*")
            if p.is_dir() and not self._should_skip(p)
        }

        # Check each pattern
        for pattern_name, indicators in self.ARCHITECTURE_PATTERNS.items():
            matches = sum(
                1
                for indicator in indicators
                if any(indicator.rstrip("/") in subdir for subdir in subdirs)
            )

            # If majority of indicators present, classify as that pattern
            if matches >= len(indicators) * 0.6:
                return pattern_name

        return None
