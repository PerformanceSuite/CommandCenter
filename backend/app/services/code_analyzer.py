"""
Code structure analyzer using AST and file metrics
"""

import ast
import asyncio
from pathlib import Path
from typing import Dict, Optional

from app.schemas.project_analysis import CodeMetrics


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

        # Calculate complexity score (simple heuristic)
        complexity_score = await self._calculate_complexity(
            project_path, total_files, lines_of_code
        )

        # Detect architecture pattern
        architecture = await self._detect_architecture(project_path)

        return CodeMetrics(
            total_files=total_files,
            lines_of_code=lines_of_code,
            languages=languages,
            complexity_score=complexity_score,
            architecture_pattern=architecture,
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

    async def _calculate_complexity(
        self, project_path: Path, total_files: int, lines_of_code: int
    ) -> float:
        """
        Calculate complexity score.

        Uses file count, LOC, and directory depth as heuristics.

        Args:
            project_path: Project root path
            total_files: Total file count
            lines_of_code: Total LOC

        Returns:
            Complexity score (0-100, higher = more complex)
        """
        # Simple heuristic based on size
        file_score = min(total_files / 100, 30)  # Max 30 points
        loc_score = min(lines_of_code / 10000, 40)  # Max 40 points

        # Directory depth score
        max_depth = 0
        for path in project_path.rglob("*"):
            if path.is_file() and not self._should_skip(path):
                depth = len(path.relative_to(project_path).parts)
                max_depth = max(max_depth, depth)

        depth_score = min(max_depth * 3, 30)  # Max 30 points

        total_score = file_score + loc_score + depth_score
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
