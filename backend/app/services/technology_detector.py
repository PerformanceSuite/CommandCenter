"""
Technology detection engine for identifying frameworks, databases, and tools
"""

import asyncio
import re
from pathlib import Path
from typing import Dict, List


from app.schemas.project_analysis import DetectedTechnology


class TechnologyDetector:
    """
    Detect frameworks, databases, build tools, and infrastructure.

    Uses file patterns, config analysis, and heuristics to identify
    technologies with confidence scoring.
    """

    # Detection rules: file pattern -> technologies
    FILE_DETECTION_RULES: Dict[str, Dict[str, Dict]] = {
        "package.json": {
            "react": {
                "patterns": [r'"react":\s*"'],
                "category": "framework",
                "version_pattern": r'"react":\s*"[\^~]?([0-9.]+)"',
            },
            "vue": {
                "patterns": [r'"vue":\s*"'],
                "category": "framework",
                "version_pattern": r'"vue":\s*"[\^~]?([0-9.]+)"',
            },
            "angular": {
                "patterns": [r'"@angular/core":\s*"'],
                "category": "framework",
                "version_pattern": r'"@angular/core":\s*"[\^~]?([0-9.]+)"',
            },
            "svelte": {
                "patterns": [r'"svelte":\s*"'],
                "category": "framework",
                "version_pattern": r'"svelte":\s*"[\^~]?([0-9.]+)"',
            },
            "express": {
                "patterns": [r'"express":\s*"'],
                "category": "framework",
                "version_pattern": r'"express":\s*"[\^~]?([0-9.]+)"',
            },
            "nestjs": {
                "patterns": [r'"@nestjs/core":\s*"'],
                "category": "framework",
                "version_pattern": r'"@nestjs/core":\s*"[\^~]?([0-9.]+)"',
            },
            "next": {
                "patterns": [r'"next":\s*"'],
                "category": "framework",
                "version_pattern": r'"next":\s*"[\^~]?([0-9.]+)"',
            },
            "vite": {
                "patterns": [r'"vite":\s*"'],
                "category": "build_tool",
                "version_pattern": r'"vite":\s*"[\^~]?([0-9.]+)"',
            },
            "webpack": {
                "patterns": [r'"webpack":\s*"'],
                "category": "build_tool",
                "version_pattern": r'"webpack":\s*"[\^~]?([0-9.]+)"',
            },
        },
        "requirements.txt": {
            "django": {
                "patterns": [r"^Django=="],
                "category": "framework",
                "version_pattern": r"Django==([0-9.]+)",
            },
            "flask": {
                "patterns": [r"^Flask==", r"^flask=="],
                "category": "framework",
                "version_pattern": r"[Ff]lask==([0-9.]+)",
            },
            "fastapi": {
                "patterns": [r"^fastapi=="],
                "category": "framework",
                "version_pattern": r"fastapi==([0-9.]+)",
            },
        },
        "docker-compose.yml": {
            "postgresql": {
                "patterns": [r"image:\s*postgres"],
                "category": "database",
                "version_pattern": r"image:\s*postgres:([0-9.]+)",
            },
            "mysql": {
                "patterns": [r"image:\s*mysql"],
                "category": "database",
                "version_pattern": r"image:\s*mysql:([0-9.]+)",
            },
            "mongodb": {
                "patterns": [r"image:\s*mongo"],
                "category": "database",
                "version_pattern": r"image:\s*mongo:([0-9.]+)",
            },
            "redis": {
                "patterns": [r"image:\s*redis"],
                "category": "database",
                "version_pattern": r"image:\s*redis:([0-9.]+)",
            },
            "elasticsearch": {
                "patterns": [r"image:\s*elasticsearch"],
                "category": "database",
                "version_pattern": r"image:\s*elasticsearch:([0-9.]+)",
            },
        },
        "Dockerfile": {
            "docker": {
                "patterns": [r"^FROM\s+"],
                "category": "infrastructure",
                "version_pattern": None,
            },
        },
        "Cargo.toml": {
            "rust": {
                "patterns": [r"\[package\]"],
                "category": "language",
                "version_pattern": None,
            },
        },
        "go.mod": {
            "go": {
                "patterns": [r"^module\s+"],
                "category": "language",
                "version_pattern": r"^go\s+([0-9.]+)",
            },
        },
    }

    # Directory-based detection
    DIRECTORY_DETECTION_RULES: Dict[str, Dict] = {
        ".github/workflows": {
            "name": "github-actions",
            "category": "ci_cd",
            "confidence": 1.0,
        },
        ".gitlab-ci.yml": {
            "name": "gitlab-ci",
            "category": "ci_cd",
            "confidence": 1.0,
        },
        ".circleci": {"name": "circleci", "category": "ci_cd", "confidence": 1.0},
        "terraform": {
            "name": "terraform",
            "category": "infrastructure",
            "confidence": 0.9,
        },
        "k8s": {"name": "kubernetes", "category": "infrastructure", "confidence": 0.9},
        "kubernetes": {
            "name": "kubernetes",
            "category": "infrastructure",
            "confidence": 0.9,
        },
    }

    async def detect(self, project_path: Path) -> List[DetectedTechnology]:
        """
        Detect all technologies in project.

        Args:
            project_path: Path to project root

        Returns:
            List of detected technologies with confidence scores
        """
        technologies = []

        # File-based detection
        file_techs = await self._detect_from_files(project_path)
        technologies.extend(file_techs)

        # Directory-based detection
        dir_techs = await self._detect_from_directories(project_path)
        technologies.extend(dir_techs)

        # Deduplicate by name (keep highest confidence)
        return self._deduplicate(technologies)

    async def _detect_from_files(self, project_path: Path) -> List[DetectedTechnology]:
        """
        Detect technologies from config files.

        Args:
            project_path: Project root path

        Returns:
            List of detected technologies
        """
        technologies = []

        for file_pattern, rules in self.FILE_DETECTION_RULES.items():
            # Find all matching files
            matches = list(project_path.glob(f"**/{file_pattern}"))

            for file_path in matches:
                try:
                    content = await self._read_file_async(file_path)

                    for tech_name, rule in rules.items():
                        for pattern in rule["patterns"]:
                            if re.search(pattern, content, re.MULTILINE):
                                # Extract version if pattern provided
                                version = None
                                if rule.get("version_pattern"):
                                    version_match = re.search(
                                        rule["version_pattern"], content, re.MULTILINE
                                    )
                                    if version_match:
                                        version = version_match.group(1)

                                technologies.append(
                                    DetectedTechnology(
                                        name=tech_name,
                                        category=rule["category"],
                                        version=version,
                                        confidence=0.95,
                                        file_path=str(file_path.relative_to(project_path)),
                                    )
                                )
                                break  # Found, no need to check other patterns

                except Exception:
                    # Skip files that can't be read
                    continue

        return technologies

    async def _detect_from_directories(self, project_path: Path) -> List[DetectedTechnology]:
        """
        Detect technologies by directory structure.

        Args:
            project_path: Project root path

        Returns:
            List of detected technologies
        """
        technologies = []

        for dir_pattern, rule in self.DIRECTORY_DETECTION_RULES.items():
            # Check if directory or file exists
            if (project_path / dir_pattern).exists():
                technologies.append(
                    DetectedTechnology(
                        name=rule["name"],
                        category=rule["category"],
                        version=None,
                        confidence=rule["confidence"],
                        file_path=dir_pattern,
                    )
                )

        return technologies

    def _deduplicate(self, technologies: List[DetectedTechnology]) -> List[DetectedTechnology]:
        """
        Remove duplicate technologies, keeping highest confidence.

        Args:
            technologies: List of detected technologies

        Returns:
            Deduplicated list
        """
        seen = {}
        for tech in technologies:
            if tech.name not in seen or tech.confidence > seen[tech.name].confidence:
                seen[tech.name] = tech
        return list(seen.values())

    async def _read_file_async(self, file_path: Path) -> str:
        """
        Asynchronously read file contents.

        Args:
            file_path: Path to file

        Returns:
            File contents as string
        """

        def _read():
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        return await asyncio.to_thread(_read)
