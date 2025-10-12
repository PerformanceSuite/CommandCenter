## Project Analyzer Documentation

**Project Analyzer** is a comprehensive codebase analysis service that automatically detects technologies, dependencies, code structure, and research gaps in software projects. It supports 8+ programming languages and provides actionable insights for keeping projects up-to-date.

---

## Features

- **Multi-Language Dependency Parsing**: Supports Node.js, Python, Go, Rust, Java (Maven/Gradle), Ruby, and PHP
- **Technology Detection**: Identifies frameworks, databases, build tools, and infrastructure (20+ technologies)
- **Code Analysis**: Calculates LOC, complexity, and detects architecture patterns
- **Research Gap Identification**: Flags outdated dependencies with severity levels and upgrade suggestions
- **Caching**: Stores analysis results for fast repeated queries
- **Async/Await**: High-performance I/O operations

---

## Supported Languages & Parsers

| Language   | Parser                | Config Files                           | Registry           |
| ---------- | --------------------- | -------------------------------------- | ------------------ |
| JavaScript | `PackageJsonParser`   | `package.json`                         | npm                |
| Python     | `RequirementsParser`  | `requirements.txt`, `requirements-dev.txt` | PyPI           |
| Go         | `GoModParser`         | `go.mod`                               | Go Proxy           |
| Rust       | `CargoTomlParser`     | `Cargo.toml`                           | crates.io          |
| Java       | `PomXmlParser`        | `pom.xml`                              | Maven Central      |
| Java       | `BuildGradleParser`   | `build.gradle`, `build.gradle.kts`     | Maven Central      |
| Ruby       | `GemfileParser`       | `Gemfile`                              | RubyGems           |
| PHP        | `ComposerJsonParser`  | `composer.json`                        | Packagist          |

---

## API Endpoints

### Analyze Project

**POST** `/api/v1/projects/analyze`

Analyze a project directory and return comprehensive results.

**Request Body**:
```json
{
  "project_path": "/absolute/path/to/project",
  "use_cache": true
}
```

**Response**:
```json
{
  "project_path": "/path/to/project",
  "analyzed_at": "2025-10-11T10:30:00Z",
  "dependencies": [
    {
      "name": "react",
      "version": "18.2.0",
      "type": "runtime",
      "language": "javascript",
      "latest_version": "18.2.0",
      "is_outdated": false,
      "confidence": 1.0
    }
  ],
  "technologies": [
    {
      "name": "react",
      "category": "framework",
      "version": "18.2.0",
      "confidence": 0.95,
      "file_path": "package.json"
    }
  ],
  "code_metrics": {
    "total_files": 150,
    "lines_of_code": 12500,
    "languages": {
      "javascript": 8000,
      "typescript": 4500
    },
    "complexity_score": 45.2,
    "architecture_pattern": "microservices"
  },
  "research_gaps": [
    {
      "technology": "django (python)",
      "current_version": "3.0.0",
      "latest_version": "4.2.0",
      "severity": "high",
      "description": "django is significantly outdated...",
      "suggested_task": "Research django upgrade to v4.2.0...",
      "estimated_effort": "1-2 weeks"
    }
  ],
  "analysis_duration_ms": 3450
}
```

---

### Get Cached Analysis

**GET** `/api/v1/projects/analysis/{analysis_id}`

Retrieve previously cached analysis by ID.

**Response**: Same as analyze endpoint.

---

### Analysis Statistics

**GET** `/api/v1/projects/analysis/statistics`

Get aggregate statistics across all analyses.

**Response**:
```json
{
  "total_analyses": 42,
  "unique_projects": 15,
  "total_dependencies": 850,
  "total_technologies": 125,
  "total_gaps": 38,
  "critical_gaps": 5,
  "high_gaps": 12,
  "outdated_dependencies": 45
}
```

---

## Usage Examples

### Python Usage

```python
from app.services.project_analyzer import ProjectAnalyzer
from sqlalchemy.ext.asyncio import AsyncSession

async def analyze_my_project(db: AsyncSession):
    analyzer = ProjectAnalyzer(db)

    result = await analyzer.analyze_project(
        project_path="/home/user/my-project",
        use_cache=True
    )

    print(f"Found {len(result.dependencies)} dependencies")
    print(f"Detected {len(result.technologies)} technologies")
    print(f"Identified {len(result.research_gaps)} research gaps")

    # Check for critical issues
    critical_gaps = [g for g in result.research_gaps if g.severity == "critical"]
    if critical_gaps:
        print(f"⚠️ {len(critical_gaps)} CRITICAL dependencies need attention!")
```

### cURL Usage

```bash
# Analyze project
curl -X POST http://localhost:8000/api/v1/projects/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/path/to/project",
    "use_cache": true
  }'

# Get statistics
curl http://localhost:8000/api/v1/projects/analysis/statistics
```

---

## Technology Detection Rules

### File-Based Detection

The analyzer scans config files for technology signatures:

| File                  | Detected Technologies                |
| --------------------- | ------------------------------------ |
| `package.json`        | React, Vue, Angular, Next.js, Express, Vite |
| `requirements.txt`    | Django, Flask, FastAPI               |
| `docker-compose.yml`  | PostgreSQL, MySQL, MongoDB, Redis    |
| `Dockerfile`          | Docker                               |
| `go.mod`              | Go                                   |
| `Cargo.toml`          | Rust                                 |

### Directory-Based Detection

Certain directories indicate specific technologies:

- `.github/workflows/` → GitHub Actions
- `.circleci/` → CircleCI
- `terraform/` → Terraform
- `k8s/` or `kubernetes/` → Kubernetes

---

## Code Architecture Patterns

The analyzer can identify common architecture patterns:

| Pattern            | Indicators                                      |
| ------------------ | ----------------------------------------------- |
| Microservices      | `services/`, `microservices/`, `docker-compose` |
| MVC                | `models/`, `views/`, `controllers/`             |
| Clean Architecture | `domain/`, `application/`, `infrastructure/`    |
| Hexagonal          | `ports/`, `adapters/`, `domain/`                |
| Layered            | `presentation/`, `business/`, `data/`           |

---

## Research Gap Severity Levels

Gaps are prioritized by version difference:

| Severity   | Criteria                 | Effort Estimate | Action             |
| ---------- | ------------------------ | --------------- | ------------------ |
| **Critical** | 3+ major versions behind | 2-4 weeks       | URGENT upgrade     |
| **High**   | 2 major versions behind  | 1-2 weeks       | Plan upgrade soon  |
| **Medium** | 1 major version behind   | 3-5 days        | Consider upgrade   |
| **Low**    | Minor/patch behind       | 1-2 days        | Update when convenient |

---

## Adding Custom Parsers

To add a new language parser:

1. **Create parser class** inheriting from `BaseParser`:

```python
from app.services.parsers.base_parser import BaseParser
from app.schemas.project_analysis import Dependency, DependencyType

class MyLanguageParser(BaseParser):
    @property
    def name(self) -> str:
        return "my-language"

    @property
    def config_files(self) -> List[str]:
        return ["my-deps.json"]

    @property
    def language(self) -> str:
        return "mylang"

    async def parse(self, project_path: Path) -> List[Dependency]:
        # Parse config file
        # Return list of Dependency objects
        pass
```

2. **Register parser** in `project_analyzer.py`:

```python
def _load_parsers(self) -> List[BaseParser]:
    return [
        # ... existing parsers ...
        MyLanguageParser(),
    ]
```

3. **Add tests** in `tests/test_project_analyzer/test_parsers.py`

---

## Performance Optimization

### Caching

Analysis results are cached in the database with version tracking:
- Cache key: `project_path`
- Cache invalidation: `analysis_version` change
- Re-analysis: Set `use_cache=False`

### Parallel Processing

All parsers run independently and can be executed in parallel. Latest version lookups use connection pooling to minimize HTTP overhead.

### Skipped Directories

The analyzer skips common build/dependency directories:
- `node_modules/`, `venv/`, `.venv/`
- `__pycache__/`, `.git/`, `.pytest_cache/`
- `build/`, `dist/`, `target/`

---

## Troubleshooting

### Issue: Parser fails on malformed config file

**Solution**: Parsers fail gracefully. Other parsers will continue working. Check logs for specific parser errors.

### Issue: Latest version lookup times out

**Solution**: Increase timeout in parser (default 10s):
```python
async with httpx.AsyncClient(timeout=30.0) as client:
    ...
```

### Issue: Analysis takes too long on large projects

**Solution**:
1. Check if `node_modules/` or `venv/` are properly excluded
2. Reduce analysis scope by analyzing subdirectories
3. Use caching for repeated analyses

### Issue: Wrong language detected

**Solution**: Add file extension mapping in `CodeAnalyzer.LANGUAGE_EXTENSIONS`

---

## Interpreting Results

### Dependency Confidence Scores

- **1.0**: Exact version found in config file
- **0.8**: Package found but version is inferred/missing

### Technology Confidence Scores

- **1.0**: Directory-based detection (definitive)
- **0.95**: File pattern match (very likely)
- **0.8-0.9**: Heuristic detection (probable)

### Code Complexity Score

- **0-30**: Simple project (< 100 files, < 10k LOC)
- **30-60**: Medium complexity
- **60-100**: High complexity (1000+ files, deep nesting)

---

## Database Schema

### `project_analyses` Table

```sql
CREATE TABLE project_analyses (
    id SERIAL PRIMARY KEY,
    project_path VARCHAR(1024) NOT NULL UNIQUE,
    detected_technologies JSON,
    dependencies JSON,
    code_metrics JSON,
    research_gaps JSON,
    analysis_version VARCHAR(50) DEFAULT '1.0.0',
    analysis_duration_ms INTEGER DEFAULT 0,
    analyzed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_project_analyses_project_path ON project_analyses(project_path);
CREATE INDEX ix_project_analyses_analyzed_at ON project_analyses(analyzed_at);
```

---

## Integration with Research Tasks

Future enhancement: Auto-generate research tasks from gaps.

```python
# Planned feature
await analyzer.generate_research_tasks(
    analysis_id=42,
    severity_threshold="high"  # Only create tasks for high/critical gaps
)
```

---

## Contributing

When adding new technologies to detect:

1. Update `TechnologyDetector.FILE_DETECTION_RULES` or `DIRECTORY_DETECTION_RULES`
2. Add test case in `test_technology_detector.py`
3. Document in this README

---

## Performance Benchmarks

Typical analysis times (MacBook Pro M1, 16GB RAM):

- **Small project** (< 50 files): 1-3 seconds
- **Medium project** (100-500 files): 3-8 seconds
- **Large project** (1000+ files): 10-20 seconds
- **Monorepo** (5000+ files): 30-60 seconds

---

## Security Considerations

- **Path Validation**: All paths are validated to prevent directory traversal
- **Registry APIs**: No authentication required for public registries
- **Private Packages**: Will fail silently if registry lookup fails
- **File Permissions**: Analyzer respects file system permissions

---

## Future Enhancements

- [ ] GitHub repository analysis (fetch and analyze remote repos)
- [ ] Vulnerability scanning integration (OSV API)
- [ ] Breaking change detection between versions
- [ ] Cost analysis for paid services
- [ ] License compatibility checking
- [ ] Auto-generate upgrade PRs
