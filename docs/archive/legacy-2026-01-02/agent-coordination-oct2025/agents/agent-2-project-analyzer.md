# Agent 2: Project Analyzer Service

**Agent Name**: project-analyzer-service
**Phase**: 2 (Core Features)
**Branch**: agent/project-analyzer-service
**Duration**: 10-14 hours
**Dependencies**: Agent 1 (MCP Core Infrastructure)

---

## Mission

Build a comprehensive project scanning service that analyzes codebases to automatically detect technologies, dependencies, code structure, and research gaps. This service forms the intelligence layer that populates CommandCenter's technology radar and identifies research opportunities.

You are implementing multi-language dependency parsing, AST-based code analysis, and technology detection to provide deep insights into project architecture and help teams stay current with their tech stack.

---

## Deliverables

### 1. ProjectAnalyzer Service (`backend/app/services/project_analyzer.py`)
- Main orchestration service
- Project scanning workflow
- Technology detection engine
- Code structure analysis
- Research gap identification
- Integration with Technology and ResearchTask models
- Caching layer for repeated scans

### 2. Dependency Parsers (`backend/app/services/parsers/`)
- `package_json_parser.py` - Node.js/npm projects
- `requirements_parser.py` - Python pip/pipenv
- `go_mod_parser.py` - Go modules
- `cargo_toml_parser.py` - Rust projects
- `pom_xml_parser.py` - Java/Maven
- `build_gradle_parser.py` - Java/Gradle (Kotlin DSL support)
- `gemfile_parser.py` - Ruby/Bundler
- `composer_json_parser.py` - PHP/Composer
- `base_parser.py` - Abstract parser interface

### 3. Technology Detection Engine (`backend/app/services/technology_detector.py`)
- Framework detection (React, Vue, Django, FastAPI, etc.)
- Build tool identification (Webpack, Vite, Make, etc.)
- Database detection (PostgreSQL, MySQL, MongoDB, Redis)
- Infrastructure detection (Docker, Kubernetes, Terraform)
- CI/CD detection (.github/workflows, .gitlab-ci.yml, etc.)
- Version extraction from config files
- Confidence scoring for detections

### 4. Code Structure Analyzer (`backend/app/services/code_analyzer.py`)
- AST-based analysis using `ast` (Python), `esprima` (JS), etc.
- Component/module counting
- Complexity metrics (LOC, cyclomatic complexity)
- Architecture pattern detection (MVC, microservices, monolith)
- Entry point detection (main.py, index.js, etc.)
- Import/dependency graph generation

### 5. Research Gap Identifier (`backend/app/services/research_gap_analyzer.py`)
- Compare detected versions against latest releases
- Identify deprecated dependencies
- Security vulnerability scanning (via OSV API)
- Breaking change detection for major version gaps
- Suggest research tasks for outdated technologies
- Priority scoring (critical/high/medium/low)

### 6. API Endpoints (`backend/app/routers/projects.py`)
- `POST /api/v1/projects/analyze` - Analyze project directory
- `GET /api/v1/projects/{id}/analysis` - Get cached analysis
- `POST /api/v1/projects/analyze-github` - Analyze GitHub repo
- `GET /api/v1/projects/analysis/statistics` - Analysis statistics
- `POST /api/v1/projects/{id}/generate-tasks` - Auto-generate research tasks

### 7. Database Models (`backend/app/models/project_analysis.py`)
- `ProjectAnalysis` model:
  - `id`, `project_path`, `analyzed_at`
  - `detected_technologies` (JSONB)
  - `dependencies` (JSONB)
  - `code_metrics` (JSONB)
  - `research_gaps` (JSONB)
  - `analysis_version` (for cache invalidation)

### 8. Tests (`backend/tests/test_project_analyzer/`)
- Parser tests with fixtures for each language
- Technology detector tests
- Code analyzer tests
- Research gap analyzer tests
- Integration test: Full project scan
- Performance tests for large codebases

---

## Technical Specifications

### ProjectAnalyzer Architecture

```
backend/app/services/
├── project_analyzer.py       # Main orchestrator
├── technology_detector.py    # Framework/tool detection
├── code_analyzer.py          # AST-based analysis
├── research_gap_analyzer.py  # Gap identification
└── parsers/
    ├── __init__.py
    ├── base_parser.py        # Abstract interface
    ├── package_json_parser.py
    ├── requirements_parser.py
    ├── go_mod_parser.py
    ├── cargo_toml_parser.py
    ├── pom_xml_parser.py
    ├── build_gradle_parser.py
    ├── gemfile_parser.py
    └── composer_json_parser.py
```

### Analysis Output Schema

```python
from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum

class DependencyType(str, Enum):
    RUNTIME = "runtime"
    DEV = "dev"
    BUILD = "build"
    PEER = "peer"

class Dependency(BaseModel):
    name: str
    version: str
    type: DependencyType
    language: str
    latest_version: Optional[str] = None
    is_outdated: bool = False
    has_vulnerabilities: bool = False
    confidence: float  # 0.0-1.0

class Technology(BaseModel):
    name: str
    category: str  # framework, database, build_tool, etc.
    version: Optional[str] = None
    confidence: float
    file_path: str  # Where detected

class CodeMetrics(BaseModel):
    total_files: int
    lines_of_code: int
    languages: Dict[str, int]  # language -> LOC
    complexity_score: float
    architecture_pattern: Optional[str]

class ResearchGap(BaseModel):
    technology: str
    current_version: str
    latest_version: str
    severity: str  # critical, high, medium, low
    description: str
    suggested_task: str
    estimated_effort: str  # "1-2 hours", "1-2 days", etc.

class ProjectAnalysisResult(BaseModel):
    project_path: str
    analyzed_at: str
    dependencies: List[Dependency]
    technologies: List[Technology]
    code_metrics: CodeMetrics
    research_gaps: List[ResearchGap]
    analysis_duration_ms: int
```

---

## Implementation Guidelines

### 1. ProjectAnalyzer Service (`project_analyzer.py`)

```python
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from app.services.parsers.base_parser import BaseParser
from app.services.technology_detector import TechnologyDetector
from app.services.code_analyzer import CodeAnalyzer
from app.services.research_gap_analyzer import ResearchGapAnalyzer
from app.models.project_analysis import ProjectAnalysis
from app.schemas.project_analysis import ProjectAnalysisResult

class ProjectAnalyzer:
    """
    Main service for analyzing project codebases.

    Orchestrates dependency parsing, technology detection,
    code analysis, and research gap identification.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.parsers: List[BaseParser] = self._load_parsers()
        self.tech_detector = TechnologyDetector()
        self.code_analyzer = CodeAnalyzer()
        self.gap_analyzer = ResearchGapAnalyzer()

    async def analyze_project(
        self,
        project_path: str,
        use_cache: bool = True
    ) -> ProjectAnalysisResult:
        """
        Analyze a project directory.

        Args:
            project_path: Absolute path to project root
            use_cache: Use cached analysis if available

        Returns:
            ProjectAnalysisResult with all analysis data
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
        research_gaps = await self._identify_gaps(
            dependencies,
            technologies
        )

        # Calculate duration
        duration_ms = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )

        # Build result
        result = ProjectAnalysisResult(
            project_path=str(path),
            analyzed_at=datetime.utcnow().isoformat(),
            dependencies=dependencies,
            technologies=technologies,
            code_metrics=code_metrics,
            research_gaps=research_gaps,
            analysis_duration_ms=duration_ms
        )

        # Cache result
        await self._cache_analysis(result)

        return result

    async def _parse_dependencies(self, path: Path) -> List[Dependency]:
        """Run all applicable parsers on project"""
        dependencies = []

        for parser in self.parsers:
            if parser.can_parse(path):
                deps = await parser.parse(path)
                dependencies.extend(deps)

        return dependencies

    async def _detect_technologies(self, path: Path) -> List[Technology]:
        """Detect frameworks, tools, databases"""
        return await self.tech_detector.detect(path)

    async def _analyze_code(self, path: Path) -> CodeMetrics:
        """Analyze code structure and complexity"""
        return await self.code_analyzer.analyze(path)

    async def _identify_gaps(
        self,
        dependencies: List[Dependency],
        technologies: List[Technology]
    ) -> List[ResearchGap]:
        """Identify outdated dependencies and research gaps"""
        return await self.gap_analyzer.analyze(dependencies, technologies)

    def _load_parsers(self) -> List[BaseParser]:
        """Load all available parsers"""
        from app.services.parsers import (
            PackageJsonParser,
            RequirementsParser,
            GoModParser,
            CargoTomlParser,
            PomXmlParser,
            BuildGradleParser,
            GemfileParser,
            ComposerJsonParser
        )

        return [
            PackageJsonParser(),
            RequirementsParser(),
            GoModParser(),
            CargoTomlParser(),
            PomXmlParser(),
            BuildGradleParser(),
            GemfileParser(),
            ComposerJsonParser()
        ]
```

### 2. Base Parser Interface (`parsers/base_parser.py`)

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from app.schemas.project_analysis import Dependency

class BaseParser(ABC):
    """Abstract base class for dependency parsers"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Parser name (e.g., 'npm', 'pip', 'cargo')"""
        pass

    @property
    @abstractmethod
    def config_files(self) -> List[str]:
        """Config files this parser handles (e.g., ['package.json'])"""
        pass

    @property
    @abstractmethod
    def language(self) -> str:
        """Language this parser handles (e.g., 'javascript', 'python')"""
        pass

    def can_parse(self, project_path: Path) -> bool:
        """Check if this parser can handle the project"""
        for config_file in self.config_files:
            if (project_path / config_file).exists():
                return True
        return False

    @abstractmethod
    async def parse(self, project_path: Path) -> List[Dependency]:
        """
        Parse dependencies from project.

        Args:
            project_path: Path to project root

        Returns:
            List of detected dependencies
        """
        pass

    async def get_latest_version(self, package_name: str) -> str:
        """
        Fetch latest version from package registry.

        Override in subclass to implement registry-specific logic.
        """
        raise NotImplementedError
```

### 3. Example Parser (`parsers/package_json_parser.py`)

```python
import json
import httpx
from pathlib import Path
from typing import List
from app.services.parsers.base_parser import BaseParser
from app.schemas.project_analysis import Dependency, DependencyType

class PackageJsonParser(BaseParser):
    """Parser for Node.js package.json files"""

    @property
    def name(self) -> str:
        return "npm"

    @property
    def config_files(self) -> List[str]:
        return ["package.json"]

    @property
    def language(self) -> str:
        return "javascript"

    async def parse(self, project_path: Path) -> List[Dependency]:
        """Parse package.json dependencies"""
        package_json_path = project_path / "package.json"

        if not package_json_path.exists():
            return []

        with open(package_json_path, 'r') as f:
            data = json.load(f)

        dependencies = []

        # Parse runtime dependencies
        for name, version in data.get("dependencies", {}).items():
            dependencies.append(
                Dependency(
                    name=name,
                    version=self._clean_version(version),
                    type=DependencyType.RUNTIME,
                    language=self.language,
                    confidence=1.0
                )
            )

        # Parse dev dependencies
        for name, version in data.get("devDependencies", {}).items():
            dependencies.append(
                Dependency(
                    name=name,
                    version=self._clean_version(version),
                    type=DependencyType.DEV,
                    language=self.language,
                    confidence=1.0
                )
            )

        # Fetch latest versions (async batch)
        await self._enrich_with_latest_versions(dependencies)

        return dependencies

    def _clean_version(self, version: str) -> str:
        """Remove semver operators (^, ~, >=, etc.)"""
        return version.lstrip("^~>=<")

    async def _enrich_with_latest_versions(
        self,
        dependencies: List[Dependency]
    ):
        """Fetch latest versions from npm registry"""
        async with httpx.AsyncClient() as client:
            for dep in dependencies:
                try:
                    latest = await self.get_latest_version(dep.name)
                    dep.latest_version = latest
                    dep.is_outdated = latest != dep.version
                except Exception:
                    # Silently fail for missing packages
                    pass

    async def get_latest_version(self, package_name: str) -> str:
        """Fetch latest version from npm registry"""
        url = f"https://registry.npmjs.org/{package_name}/latest"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return data["version"]
```

### 4. Technology Detector (`technology_detector.py`)

```python
from pathlib import Path
from typing import List, Dict, Optional
import re
from app.schemas.project_analysis import Technology

class TechnologyDetector:
    """
    Detect frameworks, databases, build tools, and infrastructure.

    Uses file patterns, config analysis, and heuristics.
    """

    # Detection rules: file pattern -> technology
    DETECTION_RULES = {
        # Frontend frameworks
        "package.json": {
            "react": {"patterns": [r'"react":\s*"'], "category": "framework"},
            "vue": {"patterns": [r'"vue":\s*"'], "category": "framework"},
            "angular": {"patterns": [r'"@angular/core":\s*"'], "category": "framework"},
            "svelte": {"patterns": [r'"svelte":\s*"'], "category": "framework"},
        },
        # Backend frameworks
        "requirements.txt": {
            "django": {"patterns": [r"Django=="], "category": "framework"},
            "flask": {"patterns": [r"Flask=="], "category": "framework"},
            "fastapi": {"patterns": [r"fastapi=="], "category": "framework"},
        },
        # Databases
        "docker-compose.yml": {
            "postgresql": {"patterns": [r"image:\s*postgres"], "category": "database"},
            "mysql": {"patterns": [r"image:\s*mysql"], "category": "database"},
            "mongodb": {"patterns": [r"image:\s*mongo"], "category": "database"},
            "redis": {"patterns": [r"image:\s*redis"], "category": "database"},
        },
        # Infrastructure
        "Dockerfile": {
            "docker": {"patterns": [r"FROM\s+"], "category": "infrastructure"},
        },
        "kubernetes": {
            "kubernetes": {"patterns": [r"apiVersion:\s*"], "category": "infrastructure"},
        },
    }

    async def detect(self, project_path: Path) -> List[Technology]:
        """
        Detect all technologies in project.

        Returns list of detected technologies with confidence scores.
        """
        technologies = []

        # File-based detection
        for file_pattern, rules in self.DETECTION_RULES.items():
            matches = list(project_path.glob(f"**/{file_pattern}"))

            for file_path in matches:
                content = file_path.read_text()

                for tech_name, rule in rules.items():
                    for pattern in rule["patterns"]:
                        if re.search(pattern, content):
                            version = self._extract_version(content, pattern)

                            technologies.append(
                                Technology(
                                    name=tech_name,
                                    category=rule["category"],
                                    version=version,
                                    confidence=0.95,
                                    file_path=str(file_path.relative_to(project_path))
                                )
                            )

        # Directory-based detection
        technologies.extend(self._detect_by_directory(project_path))

        # Deduplicate by name
        return self._deduplicate(technologies)

    def _extract_version(self, content: str, pattern: str) -> Optional[str]:
        """Extract version number from matched pattern"""
        # Implement version extraction logic
        # e.g., "react": "^18.2.0" -> "18.2.0"
        pass

    def _detect_by_directory(self, project_path: Path) -> List[Technology]:
        """Detect technologies by directory structure"""
        technologies = []

        # Example: .github/workflows -> GitHub Actions
        if (project_path / ".github" / "workflows").exists():
            technologies.append(
                Technology(
                    name="github-actions",
                    category="ci_cd",
                    version=None,
                    confidence=1.0,
                    file_path=".github/workflows"
                )
            )

        return technologies

    def _deduplicate(
        self,
        technologies: List[Technology]
    ) -> List[Technology]:
        """Remove duplicate technologies, keeping highest confidence"""
        seen = {}
        for tech in technologies:
            if tech.name not in seen or tech.confidence > seen[tech.name].confidence:
                seen[tech.name] = tech
        return list(seen.values())
```

### 5. API Endpoints (`routers/projects.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.project_analyzer import ProjectAnalyzer
from app.schemas.project_analysis import (
    ProjectAnalysisRequest,
    ProjectAnalysisResult
)

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

@router.post("/analyze", response_model=ProjectAnalysisResult)
async def analyze_project(
    request: ProjectAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a project directory.

    Scans codebase to detect dependencies, technologies,
    code metrics, and research gaps.
    """
    analyzer = ProjectAnalyzer(db)

    try:
        result = await analyzer.analyze_project(
            project_path=request.project_path,
            use_cache=request.use_cache
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/{analysis_id}/analysis", response_model=ProjectAnalysisResult)
async def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """Get cached project analysis by ID"""
    # Implementation
    pass

@router.post("/{analysis_id}/generate-tasks")
async def generate_research_tasks(
    analysis_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Auto-generate research tasks from analysis gaps.

    Creates ResearchTask entries for each identified gap.
    """
    # Implementation
    pass
```

---

## Testing Strategy

### Unit Tests

**Parser Tests** (`tests/test_project_analyzer/test_parsers/`):
```python
import pytest
from pathlib import Path
from app.services.parsers.package_json_parser import PackageJsonParser

@pytest.fixture
def sample_package_json(tmp_path):
    """Create sample package.json"""
    package_json = tmp_path / "package.json"
    package_json.write_text('''
    {
      "dependencies": {
        "react": "^18.2.0",
        "axios": "~1.4.0"
      },
      "devDependencies": {
        "jest": ">=29.0.0"
      }
    }
    ''')
    return tmp_path

@pytest.mark.asyncio
async def test_parse_package_json(sample_package_json):
    parser = PackageJsonParser()

    dependencies = await parser.parse(sample_package_json)

    assert len(dependencies) == 3
    assert any(d.name == "react" and d.version == "18.2.0" for d in dependencies)
    assert any(d.name == "jest" and d.type == DependencyType.DEV for d in dependencies)
```

**Technology Detector Tests**:
```python
@pytest.mark.asyncio
async def test_detect_react_project(tmp_path):
    # Create mock React project
    package_json = tmp_path / "package.json"
    package_json.write_text('{"dependencies": {"react": "^18.2.0"}}')

    detector = TechnologyDetector()
    technologies = await detector.detect(tmp_path)

    react_tech = next(t for t in technologies if t.name == "react")
    assert react_tech.category == "framework"
    assert react_tech.confidence > 0.9
```

### Integration Tests

**Full Project Scan**:
```python
@pytest.mark.asyncio
async def test_full_project_analysis(db_session, sample_project):
    analyzer = ProjectAnalyzer(db_session)

    result = await analyzer.analyze_project(str(sample_project))

    assert len(result.dependencies) > 0
    assert len(result.technologies) > 0
    assert result.code_metrics.total_files > 0
    assert result.analysis_duration_ms > 0
```

### Performance Tests

```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_analyze_large_monorepo(large_project_fixture):
    """Test analysis performance on 10k+ file project"""
    start = time.time()

    result = await analyzer.analyze_project(large_project_fixture)

    duration = time.time() - start
    assert duration < 30  # Should complete in under 30 seconds
```

---

## Dependencies

```txt
# Add to backend/requirements.txt
httpx>=0.24.0           # Async HTTP for package registry APIs
toml>=0.10.2            # Parse TOML files (Cargo.toml, pyproject.toml)
PyYAML>=6.0             # Parse YAML files (docker-compose, k8s)
lxml>=4.9.0             # Parse XML files (pom.xml)
esprima>=4.0.1          # JavaScript AST parser
```

---

## Documentation

Create `docs/PROJECT_ANALYZER.md` with:
- Supported languages and parsers
- Technology detection rules
- Adding custom parsers
- API usage examples
- Interpreting analysis results
- Performance tuning for large projects

---

## Success Criteria

- ✅ All 8 parsers implemented and tested
- ✅ Technology detector covers 20+ frameworks/tools
- ✅ Code analyzer supports Python, JavaScript, Go
- ✅ Research gap analyzer identifies outdated dependencies
- ✅ API endpoints functional and documented
- ✅ Database model with proper indexes
- ✅ 80%+ test coverage
- ✅ Integration test: Analyze real-world project (e.g., CommandCenter itself)
- ✅ Analysis completes in <10s for typical projects (<1000 files)
- ✅ Handles missing/malformed config files gracefully

---

## Notes

- **Performance**: Use async/await for I/O (registry APIs, file reading)
- **Caching**: Cache registry responses (latest versions) for 1 hour
- **Error Handling**: Partial failures OK (e.g., if npm registry down, continue with other parsers)
- **Extensibility**: Easy to add new parsers (implement BaseParser)
- **Security**: Validate file paths to prevent directory traversal

---

## Self-Review Checklist

Before marking PR as ready:
- [ ] All 8 deliverables complete
- [ ] All parsers have test fixtures
- [ ] Technology detector tested with real projects
- [ ] API endpoints tested with integration tests
- [ ] Tests pass (pytest tests/test_project_analyzer/ -v)
- [ ] Linting passes (black, flake8)
- [ ] Type hints on all functions
- [ ] Docstrings (Google style) on all classes/methods
- [ ] PROJECT_ANALYZER.md documentation complete
- [ ] Example usage in docs
- [ ] Performance benchmarks run
- [ ] No TODOs or FIXMEs left
- [ ] Self-review score: 10/10
