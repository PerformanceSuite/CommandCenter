# Change Proposal 002: Project Analyzer Service

**Agent**: Agent 2 (project-analyzer-service)
**Phase**: 1 - Foundation
**Status**: DRAFT
**Created**: 2025-10-11
**Target Checkpoint**: 1-3 (3 checkpoints x 2 hours each)

---

## Summary

Build a comprehensive project scanning service that analyzes codebases to automatically detect technologies, dependencies, code structure, and research gaps. Includes multi-language dependency parsers (8 languages), technology detection engine, code structure analyzer, and research gap identifier.

**Goal**: Enable `commandcenter analyze ~/Projects/performia` to detect all technologies and identify research opportunities.

---

## Motivation

Teams need automated ways to:
- Understand what technologies are in their codebase
- Detect outdated dependencies and security vulnerabilities
- Identify research gaps (old versions, deprecated tech)
- Track tech stack evolution over time

**Problem**: Manual tech audits are time-consuming and error-prone
**Solution**: Automated analysis with 8 language parsers + tech detection + gap analysis
**Value**: Technology Radar automatically populated, research tasks auto-generated

---

## Proposed Changes

### Files to Create

```
backend/app/services/
├── project_analyzer.py                 # Main orchestrator (300 LOC)
├── technology_detector.py              # Framework/tool detection (400 LOC)
├── code_analyzer.py                    # AST-based analysis (250 LOC)
├── research_gap_analyzer.py            # Gap identification (200 LOC)
└── parsers/
    ├── __init__.py                     # Parser registry (50 LOC)
    ├── base_parser.py                  # Abstract interface (150 LOC)
    ├── package_json_parser.py          # Node.js/npm (200 LOC)
    ├── requirements_parser.py          # Python pip (150 LOC)
    ├── go_mod_parser.py                # Go modules (150 LOC)
    ├── cargo_toml_parser.py            # Rust (150 LOC)
    ├── pom_xml_parser.py               # Java/Maven (200 LOC)
    ├── build_gradle_parser.py          # Java/Gradle (200 LOC)
    ├── gemfile_parser.py               # Ruby/Bundler (150 LOC)
    └── composer_json_parser.py         # PHP/Composer (150 LOC)

backend/app/schemas/
└── project_analysis.py                 # Pydantic models (300 LOC)

backend/app/models/
└── project_analysis.py                 # SQLAlchemy model (100 LOC)

backend/app/routers/
└── projects.py                         # API endpoints (200 LOC)

backend/tests/test_project_analyzer/
├── __init__.py
├── test_project_analyzer.py            # Main service tests (300 LOC, 12 tests)
├── test_technology_detector.py         # Detector tests (200 LOC, 8 tests)
├── test_code_analyzer.py               # Analyzer tests (150 LOC, 6 tests)
├── test_research_gap_analyzer.py       # Gap tests (150 LOC, 6 tests)
├── test_parsers/
│   ├── __init__.py
│   ├── test_package_json_parser.py     # (100 LOC, 8 tests)
│   ├── test_requirements_parser.py     # (100 LOC, 8 tests)
│   ├── test_go_mod_parser.py           # (100 LOC, 8 tests)
│   ├── test_cargo_toml_parser.py       # (100 LOC, 8 tests)
│   ├── test_pom_xml_parser.py          # (100 LOC, 8 tests)
│   ├── test_build_gradle_parser.py     # (100 LOC, 8 tests)
│   ├── test_gemfile_parser.py          # (100 LOC, 8 tests)
│   └── test_composer_json_parser.py    # (100 LOC, 8 tests)
└── fixtures/
    ├── __init__.py
    ├── sample_projects/                # Test project fixtures
    │   ├── react-project/              # Sample React project
    │   ├── django-project/             # Sample Django project
    │   └── go-project/                 # Sample Go project
    └── analysis_fixtures.py            # Shared fixtures (200 LOC)

docs/PROJECT_ANALYZER.md                # Documentation (800 lines)
```

**Total Estimated**: ~3,500 LOC implementation + ~2,000 LOC tests + 800 lines docs

---

## Implementation Details

### Phase 1: Checkpoint 1 (40% - 2 hours)

**Deliverables**:
1. Main ProjectAnalyzer service (`project_analyzer.py`)
   - `analyze_project()` method
   - Parser orchestration logic
   - Cache checking
2. Base parser interface (`parsers/base_parser.py`)
   - `BaseParser` ABC
   - `can_parse()`, `parse()` methods
   - `get_latest_version()` stub
3. 3 parsers implemented:
   - `package_json_parser.py` (Node.js)
   - `requirements_parser.py` (Python)
   - `go_mod_parser.py` (Go)
4. Schemas (`schemas/project_analysis.py`)
   - `Dependency`, `Technology`, `CodeMetrics`, `ResearchGap`
   - `ProjectAnalysisResult`
5. Basic tests (16 tests)
   - ProjectAnalyzer orchestration tests
   - 3 parser tests (package.json, requirements.txt, go.mod)

**Contracts Exported**:
- `ProjectAnalyzer` class with `analyze_project()` method
- `BaseParser` interface for extension
- `ProjectAnalysisResult` schema

**Tests**: 16/80 passing (20%)

---

### Phase 2: Checkpoint 2 (40% - 2 hours)

**Deliverables**:
1. Remaining 5 parsers:
   - `cargo_toml_parser.py` (Rust)
   - `pom_xml_parser.py` (Java/Maven)
   - `build_gradle_parser.py` (Java/Gradle)
   - `gemfile_parser.py` (Ruby)
   - `composer_json_parser.py` (PHP)
2. Technology detector (`technology_detector.py`)
   - Framework detection (React, Vue, Django, FastAPI, etc.)
   - Database detection (PostgreSQL, MySQL, MongoDB, Redis)
   - Infrastructure detection (Docker, Kubernetes)
   - CI/CD detection (GitHub Actions, GitLab CI)
3. Code analyzer skeleton (`code_analyzer.py`)
   - File counting
   - LOC calculation
   - Language detection
4. Database model (`models/project_analysis.py`)
   - `ProjectAnalysis` table
   - JSONB fields for flexibility
5. Tests (40 tests total)
   - 5 additional parser tests
   - Technology detector tests (8 tests)
   - Code analyzer tests (6 tests)

**Tests**: 56/80 passing (70%)

---

### Phase 3: Checkpoint 3 (20% - 2 hours)

**Deliverables**:
1. Research gap analyzer (`research_gap_analyzer.py`)
   - Compare versions against latest
   - Security vulnerability check (OSV API)
   - Priority scoring
   - Suggested task generation
2. Complete code analyzer (`code_analyzer.py`)
   - AST-based complexity metrics
   - Architecture pattern detection
   - Dependency graph generation
3. API endpoints (`routers/projects.py`)
   - `POST /api/v1/projects/analyze`
   - `GET /api/v1/projects/{id}/analysis`
   - `POST /api/v1/projects/{id}/generate-tasks`
4. Caching layer in ProjectAnalyzer
   - Check/save cached analyses
5. Documentation (`docs/PROJECT_ANALYZER.md`)
   - Supported languages
   - Adding custom parsers
   - Usage examples
6. Final tests (24 tests)
   - Research gap analyzer tests (6 tests)
   - Full code analyzer tests (6 tests)
   - API endpoint tests (4 tests)
   - Integration test: Full project scan (1 test)
   - Performance test: Large codebase (1 test)

**Tests**: 80/80 passing (100%)

---

## Interface Contracts

### ProjectAnalyzer Interface

```python
from pathlib import Path
from typing import Optional
from datetime import datetime
from app.schemas.project_analysis import ProjectAnalysisResult

class ProjectAnalyzer:
    """
    Main service for analyzing project codebases.

    Orchestrates dependency parsing, technology detection,
    code analysis, and research gap identification.
    """

    def __init__(self, db_session):
        """
        Initialize analyzer with database session.

        Args:
            db_session: SQLAlchemy session for caching results
        """
        self.db = db_session
        self.parsers = self._load_parsers()
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

        This is the main entry point. Performs:
        1. Dependency parsing (all detected languages)
        2. Technology detection (frameworks, databases, tools)
        3. Code structure analysis (LOC, complexity, architecture)
        4. Research gap identification (outdated deps, vulns)

        Args:
            project_path: Absolute path to project root
            use_cache: Use cached analysis if available (< 24h old)

        Returns:
            ProjectAnalysisResult with all analysis data

        Raises:
            ValueError: If project_path doesn't exist or isn't a directory
            AnalysisError: If analysis fails (partial results may be returned)
        """
        pass

    def _load_parsers(self) -> List[BaseParser]:
        """Load all available parsers"""
        pass
```

### BaseParser Interface

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
        """
        Check if this parser can handle the project.

        Default implementation checks if any config_files exist.
        Override for custom logic.

        Args:
            project_path: Path to project root

        Returns:
            True if parser can handle this project
        """
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
            List of detected dependencies with metadata

        Raises:
            ParserError: If parsing fails (should not stop other parsers)
        """
        pass

    async def get_latest_version(self, package_name: str) -> Optional[str]:
        """
        Fetch latest version from package registry.

        Override in subclass to implement registry-specific logic.

        Args:
            package_name: Package name (e.g., 'react', 'django')

        Returns:
            Latest version string or None if unavailable
        """
        # Default stub - subclasses override with registry API calls
        return None
```

### ProjectAnalysisResult Schema

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
    category: str  # framework, database, build_tool, infrastructure, ci_cd
    version: Optional[str] = None
    confidence: float  # 0.0-1.0
    file_path: str  # Where detected

class CodeMetrics(BaseModel):
    total_files: int
    lines_of_code: int
    languages: Dict[str, int]  # language -> LOC
    complexity_score: float    # 0-100
    architecture_pattern: Optional[str]  # "monolith", "microservices", "mvc"

class ResearchGap(BaseModel):
    technology: str
    current_version: str
    latest_version: str
    severity: str  # "critical", "high", "medium", "low"
    description: str
    suggested_task: str        # Auto-generated task description
    estimated_effort: str      # "1-2 hours", "1-2 days", "1-2 weeks"

class ProjectAnalysisResult(BaseModel):
    project_path: str
    analyzed_at: str           # ISO 8601 timestamp
    dependencies: List[Dependency]
    technologies: List[Technology]
    code_metrics: CodeMetrics
    research_gaps: List[ResearchGap]
    analysis_duration_ms: int
```

---

## Dependencies

### New Dependencies to Add

```txt
# Add to backend/requirements.txt
httpx>=0.24.0           # Async HTTP for package registry APIs
toml>=0.10.2            # Parse TOML files (Cargo.toml, pyproject.toml)
PyYAML>=6.0             # Already present, for YAML files
lxml>=4.9.0             # Parse XML files (pom.xml)
packaging>=23.0         # Version comparison and parsing
```

### External APIs Used
- **npm registry**: `https://registry.npmjs.org/{package}/latest`
- **PyPI**: `https://pypi.org/pypi/{package}/json`
- **Crates.io**: `https://crates.io/api/v1/crates/{crate}`
- **Maven Central**: `https://search.maven.org/solrsearch/select?q=g:{group}+AND+a:{artifact}`
- **OSV (vulnerability DB)**: `https://api.osv.dev/v1/query`

---

## Testing Strategy

### Unit Tests (70 tests)
- ProjectAnalyzer orchestration (12 tests)
- Each parser (8 parsers × 8 tests = 64 tests)
  - Valid config file parsing
  - Missing config file handling
  - Malformed config handling
  - Empty dependencies
  - Version extraction
  - Latest version fetching (mocked)
  - Dependency type detection
- Technology detector (8 tests)
- Code analyzer (6 tests)
- Research gap analyzer (6 tests)

### Integration Tests (9 tests)
- Full project scan (React project)
- Full project scan (Django project)
- Full project scan (Go project)
- Multiple languages in one project
- Cached analysis retrieval
- API endpoint tests (4 tests)

### Performance Tests (1 test)
- Large monorepo analysis (10k+ files)
- Target: <30 seconds for large projects

### Test Coverage Target
- 85%+ coverage on all modules
- 100% coverage on parsers (critical for accuracy)

---

## Documentation

### PROJECT_ANALYZER.md Contents

1. **Overview**
   - What ProjectAnalyzer does
   - Supported languages and ecosystems
   - Analysis workflow

2. **Supported Languages**
   - JavaScript/TypeScript (npm, package.json)
   - Python (pip, requirements.txt, pyproject.toml)
   - Go (go.mod)
   - Rust (Cargo.toml)
   - Java (Maven, Gradle)
   - Ruby (Gemfile)
   - PHP (composer.json)

3. **Technology Detection Rules**
   - How frameworks are detected
   - How databases are detected
   - How infrastructure is detected
   - Confidence scoring

4. **Adding Custom Parsers**
   - Subclassing BaseParser
   - Implementing parse()
   - Integrating with ProjectAnalyzer
   - Testing your parser

5. **API Usage**
   - Analyze local project
   - Analyze GitHub repo
   - Export results
   - Auto-generate research tasks

6. **Performance Tuning**
   - Caching strategies
   - Large project optimization
   - Parallel parsing

7. **Troubleshooting**
   - Parser errors
   - Registry API timeouts
   - Unsupported file formats

---

## Success Criteria

- ✅ All 80 tests passing
- ✅ 8 parsers implemented and tested
- ✅ Technology detector covers 20+ frameworks/tools
- ✅ Code analyzer functional (LOC, languages, complexity)
- ✅ Research gap analyzer identifies outdated dependencies
- ✅ API endpoints functional
- ✅ Database model with proper indexes
- ✅ 85%+ test coverage
- ✅ Integration test: Analyze CommandCenter itself
- ✅ Performance: <10s for typical projects (<1000 files)
- ✅ Graceful error handling (parser failures don't stop analysis)
- ✅ Documentation complete with examples

---

## Risks & Mitigation

### Risk 1: Registry API Rate Limits
**Risk**: npm/PyPI/etc may rate limit requests
**Mitigation**:
- Cache registry responses for 1 hour
- Batch requests when possible
- Graceful degradation (analysis continues without latest versions)
**Checkpoint**: If rate limited in testing, implement exponential backoff

### Risk 2: Parser Complexity
**Risk**: Some dependency formats are complex (Gradle Kotlin DSL)
**Mitigation**:
- Start with simple cases
- Use regex for version extraction
- Accept 80% accuracy for complex formats
**Checkpoint**: If Gradle parser too complex by checkpoint 2, simplify or defer

### Risk 3: Performance on Large Projects
**Risk**: Analyzing 10k+ file projects may be slow
**Mitigation**:
- Stream file reading (don't load all in memory)
- Parallel parser execution
- Limit code analyzer to key files only
**Checkpoint**: Run performance test in checkpoint 3, optimize if >30s

### Risk 4: Missing Config Files
**Risk**: Projects may have non-standard dependency management
**Mitigation**:
- Parsers return empty list if config missing (don't error)
- Log skipped projects for debugging
- Technology detector can still find frameworks via file patterns
**Checkpoint**: Test with various project structures in checkpoint 2

---

## Coordination Notes

### Exports for Other Agents

**Agent 3 (CLI Interface)** needs:
- `ProjectAnalyzer` class with `analyze_project()` method
- `ProjectAnalysisResult` schema for result formatting
- API endpoints (`POST /api/v1/projects/analyze`)

**Usage by Agent 3**:
```python
from app.services.project_analyzer import ProjectAnalyzer
from app.schemas.project_analysis import ProjectAnalysisResult

# In CLI analyze command
analyzer = ProjectAnalyzer(db_session)
result: ProjectAnalysisResult = await analyzer.analyze_project("/path/to/project")
```

### Imports from Other Agents

**From Agent 1 (MCP Core)**:
- None in Phase 1 (no MCP integration yet)
- In Phase 2, may integrate with MCP Resource Provider

**From Agent 3 (CLI)**:
- None (Agent 3 uses Agent 2, not vice versa)

### Database Integration

Uses existing CommandCenter database:
- Depends on `app.database.get_db()` (already exists)
- Depends on `app.models.Technology` (already exists) - will create relationships

---

## Checkpoint Deliverables Summary

| Checkpoint | Progress | Tests | Key Deliverables |
|------------|----------|-------|------------------|
| 1 | 40% | 16/80 | ProjectAnalyzer, BaseParser, 3 parsers, schemas |
| 2 | 80% | 56/80 | 5 more parsers, tech detector, code analyzer skeleton, DB model |
| 3 | 100% | 80/80 | Research gap analyzer, complete code analyzer, API endpoints, docs |

---

## Review Criteria

### Code Quality
- [ ] Black + Flake8 pass
- [ ] Type hints on all functions
- [ ] Google-style docstrings
- [ ] No TODOs or FIXMEs

### Functionality
- [ ] All 8 parsers work on sample projects
- [ ] Technology detector finds frameworks accurately
- [ ] Code analyzer calculates metrics correctly
- [ ] Research gaps identified with severity
- [ ] API endpoints return correct schemas

### Testing
- [ ] 80/80 tests passing
- [ ] 85%+ coverage
- [ ] Integration tests pass
- [ ] Performance test: <10s for typical projects

### Documentation
- [ ] PROJECT_ANALYZER.md complete
- [ ] All parsers documented
- [ ] Examples for each language

### Coordination
- [ ] STATUS.json updated after each commit
- [ ] Contracts match implementation
- [ ] Agent 3 can import and use ProjectAnalyzer

---

## Next Steps After Completion

1. **Agent 3 (CLI) integration**
   - CLI can call `analyze_project()` method
   - CLI formats and displays results

2. **Phase 2: MCP integration**
   - Agent 4 exposes project analysis via MCP
   - ProjectAnalyzer becomes MCP Resource Provider

3. **Future enhancements**
   - Add more language parsers (C#, Swift, Kotlin)
   - ML-based architecture pattern detection
   - License detection
   - Security score calculation

---

## Notes

- **Error handling**: Partial results are OK (if npm parser fails, continue with others)
- **Async-first**: All I/O operations (file reading, HTTP) use async/await
- **Caching**: Cache both analysis results and registry responses
- **Security**: Validate file paths to prevent directory traversal
- **Extensibility**: Easy to add new parsers (just implement BaseParser)
- Follow **CommandCenter conventions**: Black formatting, type hints, docstrings
