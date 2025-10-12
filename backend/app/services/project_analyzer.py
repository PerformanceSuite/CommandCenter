"""
Main project analyzer service
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_analysis import ProjectAnalysis
from app.schemas.project_analysis import (
    CodeMetrics,
    Dependency,
    DetectedTechnology,
    ProjectAnalysisResult,
    ResearchGap,
)
from app.services.code_analyzer import CodeAnalyzer
from app.services.parsers import (
    BaseParser,
    BuildGradleParser,
    CargoTomlParser,
    ComposerJsonParser,
    GemfileParser,
    GoModParser,
    PackageJsonParser,
    PomXmlParser,
    RequirementsParser,
)
from app.services.research_gap_analyzer import ResearchGapAnalyzer
from app.services.technology_detector import TechnologyDetector

# Current analysis version (increment when logic changes)
ANALYSIS_VERSION = "1.0.0"


class ProjectAnalyzer:
    """
    Main service for analyzing project codebases.

    Orchestrates dependency parsing, technology detection,
    code analysis, and research gap identification.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize project analyzer.

        Args:
            db: Database session
        """
        self.db = db
        self.parsers: List[BaseParser] = self._load_parsers()
        self.tech_detector = TechnologyDetector()
        self.code_analyzer = CodeAnalyzer()
        self.gap_analyzer = ResearchGapAnalyzer()

    async def analyze_project(
        self, project_path: str, use_cache: bool = True
    ) -> ProjectAnalysisResult:
        """
        Analyze a project directory.

        Args:
            project_path: Absolute path to project root
            use_cache: Use cached analysis if available

        Returns:
            ProjectAnalysisResult with all analysis data

        Raises:
            ValueError: If project path invalid
        """
        start_time = datetime.utcnow()
        path = Path(project_path)

        if not path.exists() or not path.is_dir():
            raise ValueError(f"Invalid project path: {project_path}")

        # Check cache
        if use_cache:
            cached = await self._get_cached_analysis(project_path)
            if cached:
                return cached

        # Run analysis phases
        dependencies = await self._parse_dependencies(path)
        technologies = await self._detect_technologies(path)
        code_metrics = await self._analyze_code(path)
        research_gaps = await self._identify_gaps(dependencies, technologies)

        # Calculate duration
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Build result
        result = ProjectAnalysisResult(
            project_path=str(path),
            analyzed_at=datetime.utcnow(),
            dependencies=dependencies,
            technologies=technologies,
            code_metrics=code_metrics,
            research_gaps=research_gaps,
            analysis_duration_ms=duration_ms,
        )

        # Cache result
        await self._cache_analysis(result)

        return result

    async def _parse_dependencies(self, path: Path) -> List[Dependency]:
        """
        Run all applicable parsers on project.

        Args:
            path: Project root path

        Returns:
            List of all detected dependencies
        """
        dependencies = []

        for parser in self.parsers:
            if parser.can_parse(path):
                try:
                    deps = await parser.parse(path)
                    dependencies.extend(deps)
                except Exception as e:
                    # Log error but continue with other parsers
                    print(f"Parser {parser.name} failed: {e}")
                    continue

        return dependencies

    async def _detect_technologies(self, path: Path) -> List[DetectedTechnology]:
        """
        Detect frameworks, tools, databases.

        Args:
            path: Project root path

        Returns:
            List of detected technologies
        """
        return await self.tech_detector.detect(path)

    async def _analyze_code(self, path: Path) -> CodeMetrics:
        """
        Analyze code structure and complexity.

        Args:
            path: Project root path

        Returns:
            Code metrics
        """
        return await self.code_analyzer.analyze(path)

    async def _identify_gaps(
        self, dependencies: List[Dependency], technologies: List[DetectedTechnology]
    ) -> List[ResearchGap]:
        """
        Identify outdated dependencies and research gaps.

        Args:
            dependencies: Detected dependencies
            technologies: Detected technologies

        Returns:
            List of research gaps
        """
        return await self.gap_analyzer.analyze(dependencies, technologies)

    async def _get_cached_analysis(
        self, project_path: str
    ) -> Optional[ProjectAnalysisResult]:
        """
        Get cached analysis if available and valid.

        Args:
            project_path: Project path

        Returns:
            Cached analysis result or None
        """
        stmt = select(ProjectAnalysis).where(
            ProjectAnalysis.project_path == project_path,
            ProjectAnalysis.analysis_version == ANALYSIS_VERSION,
        )

        result = await self.db.execute(stmt)
        cached = result.scalar_one_or_none()

        if not cached:
            return None

        # Convert database model to result schema
        return ProjectAnalysisResult(
            project_path=cached.project_path,
            analyzed_at=cached.analyzed_at,
            dependencies=(
                [Dependency(**dep) for dep in cached.dependencies.get("items", [])]
                if cached.dependencies
                else []
            ),
            technologies=(
                [
                    DetectedTechnology(**tech)
                    for tech in cached.detected_technologies.get("items", [])
                ]
                if cached.detected_technologies
                else []
            ),
            code_metrics=(
                CodeMetrics(**cached.code_metrics)
                if cached.code_metrics
                else CodeMetrics(
                    total_files=0,
                    lines_of_code=0,
                    languages={},
                    complexity_score=0.0,
                )
            ),
            research_gaps=(
                [ResearchGap(**gap) for gap in cached.research_gaps.get("items", [])]
                if cached.research_gaps
                else []
            ),
            analysis_duration_ms=cached.analysis_duration_ms,
        )

    async def _cache_analysis(self, result: ProjectAnalysisResult) -> None:
        """
        Cache analysis result in database.

        Args:
            result: Analysis result to cache
        """
        # Convert result to database model
        analysis = ProjectAnalysis(
            project_path=result.project_path,
            detected_technologies={
                "items": [tech.model_dump() for tech in result.technologies]
            },
            dependencies={"items": [dep.model_dump() for dep in result.dependencies]},
            code_metrics=result.code_metrics.model_dump(),
            research_gaps={"items": [gap.model_dump() for gap in result.research_gaps]},
            analysis_version=ANALYSIS_VERSION,
            analysis_duration_ms=result.analysis_duration_ms,
            analyzed_at=result.analyzed_at,
        )

        # Upsert (update if exists, insert if not)
        stmt = select(ProjectAnalysis).where(
            ProjectAnalysis.project_path == result.project_path
        )
        existing_result = await self.db.execute(stmt)
        existing = existing_result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.detected_technologies = analysis.detected_technologies
            existing.dependencies = analysis.dependencies
            existing.code_metrics = analysis.code_metrics
            existing.research_gaps = analysis.research_gaps
            existing.analysis_version = analysis.analysis_version
            existing.analysis_duration_ms = analysis.analysis_duration_ms
            existing.analyzed_at = analysis.analyzed_at
        else:
            # Insert new
            self.db.add(analysis)

        await self.db.commit()

    def _load_parsers(self) -> List[BaseParser]:
        """
        Load all available parsers.

        Returns:
            List of parser instances
        """
        return [
            PackageJsonParser(),
            RequirementsParser(),
            GoModParser(),
            CargoTomlParser(),
            PomXmlParser(),
            BuildGradleParser(),
            GemfileParser(),
            ComposerJsonParser(),
        ]

    async def get_analysis_by_id(
        self, analysis_id: int
    ) -> Optional[ProjectAnalysisResult]:
        """
        Get analysis by ID.

        Args:
            analysis_id: Analysis ID

        Returns:
            Analysis result or None
        """
        stmt = select(ProjectAnalysis).where(ProjectAnalysis.id == analysis_id)
        result = await self.db.execute(stmt)
        cached = result.scalar_one_or_none()

        if not cached:
            return None

        # Convert database model to result schema
        return ProjectAnalysisResult(
            project_path=cached.project_path,
            analyzed_at=cached.analyzed_at,
            dependencies=(
                [Dependency(**dep) for dep in cached.dependencies.get("items", [])]
                if cached.dependencies
                else []
            ),
            technologies=(
                [
                    DetectedTechnology(**tech)
                    for tech in cached.detected_technologies.get("items", [])
                ]
                if cached.detected_technologies
                else []
            ),
            code_metrics=(
                CodeMetrics(**cached.code_metrics)
                if cached.code_metrics
                else CodeMetrics(
                    total_files=0,
                    lines_of_code=0,
                    languages={},
                    complexity_score=0.0,
                )
            ),
            research_gaps=(
                [ResearchGap(**gap) for gap in cached.research_gaps.get("items", [])]
                if cached.research_gaps
                else []
            ),
            analysis_duration_ms=cached.analysis_duration_ms,
        )
