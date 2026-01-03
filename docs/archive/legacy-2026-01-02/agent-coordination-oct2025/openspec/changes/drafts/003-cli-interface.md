# Change Proposal 003: CLI Interface

**Agent**: Agent 3 (cli-interface)
**Phase**: 1 - Foundation
**Status**: DRAFT
**Created**: 2025-10-11
**Target Checkpoint**: 1-3 (3 checkpoints x 2 hours each)

---

## Summary

Build a professional command-line interface (CLI) for CommandCenter using Click framework. Provides terminal-based access to project analysis, agent orchestration, RAG search, and configuration management with rich terminal output (progress bars, tables, colors).

**Goal**: Enable `commandcenter analyze ~/Projects/performia` workflow directly from terminal.

---

## Motivation

Developers want to:
- Analyze projects without opening browser/UI
- Integrate CommandCenter into shell scripts and CI/CD
- Get instant analysis results in terminal
- Configure CommandCenter via CLI

**Problem**: Current CommandCenter requires browser UI for all operations
**Solution**: Full-featured CLI with Click + Rich for beautiful terminal UX
**Value**: Developer velocity, scriptability, CI/CD integration

---

## Proposed Changes

### Files to Create

```
backend/cli/
├── __init__.py                         # CLI module init (20 LOC)
├── commandcenter.py                    # Main entry point (150 LOC)
├── config.py                           # Configuration management (200 LOC)
├── output.py                           # Rich terminal output (300 LOC)
├── api_client.py                       # Backend API client (250 LOC)
├── commands/
│   ├── __init__.py
│   ├── analyze.py                      # Analyze commands (300 LOC)
│   ├── agents.py                       # Agent commands (250 LOC)
│   ├── search.py                       # Search commands (150 LOC)
│   └── config.py                       # Config commands (150 LOC)
├── completion/
│   ├── commandcenter.bash              # Bash completion (100 lines)
│   ├── commandcenter.zsh               # Zsh completion (100 lines)
│   └── commandcenter.fish              # Fish completion (80 lines)
└── utils/
    ├── __init__.py
    ├── validators.py                   # Input validation (150 LOC)
    └── formatters.py                   # Data formatting (150 LOC)

backend/tests/test_cli/
├── __init__.py
├── test_analyze.py                     # Analyze tests (250 LOC, 12 tests)
├── test_agents.py                      # Agent tests (200 LOC, 8 tests)
├── test_search.py                      # Search tests (150 LOC, 6 tests)
├── test_config.py                      # Config tests (200 LOC, 10 tests)
├── test_output.py                      # Output tests (100 LOC, 4 tests)
└── fixtures/
    ├── __init__.py
    └── cli_fixtures.py                 # Test fixtures (150 LOC)

backend/pyproject.toml                  # Package config (100 lines)
docs/CLI_GUIDE.md                       # User documentation (1000 lines)
```

**Total Estimated**: ~2,500 LOC implementation + ~1,050 LOC tests + ~1000 lines docs

---

## Implementation Details

### Phase 1: Checkpoint 1 (40% - 2 hours)

**Deliverables**:
1. Main CLI entry point (`commandcenter.py`)
   - Click app with global options (--verbose, --config, --format)
   - Version command
   - Help text and examples
2. Configuration system (`config.py`)
   - `Config` Pydantic model
   - `~/.commandcenter/config.yaml` management
   - Load/save/get/set methods
3. API client (`api_client.py`)
   - `APIClient` class for backend communication
   - Authentication handling
   - Error handling with retries
4. Basic analyze command (`commands/analyze.py`)
   - `commandcenter analyze <path>` - basic project analysis
   - Progress spinner during analysis
   - Simple text output (no rich formatting yet)
5. Config commands (`commands/config.py`)
   - `commandcenter config init`
   - `commandcenter config set <key> <value>`
   - `commandcenter config get <key>`
6. Package configuration (`pyproject.toml`)
   - Entry point: `commandcenter` command
   - Dependencies specification
7. Basic tests (15 tests)
   - CLI invocation tests
   - Config management tests
   - API client tests (mocked)

**Contracts Exported**:
- `commandcenter` CLI command (installable via pip)
- `Config` class for configuration management
- `APIClient` for programmatic backend access

**Tests**: 15/40 passing (37.5%)

---

### Phase 2: Checkpoint 2 (40% - 2 hours)

**Deliverables**:
1. Rich terminal output (`output.py`)
   - `display_analysis_results()` with tables and trees
   - Progress bars for long operations
   - Color-coded status messages
   - Syntax highlighting for code snippets
2. Complete analyze commands (`commands/analyze.py`)
   - `--github <owner/repo>` - Analyze GitHub repos
   - `--export json|yaml` - Export results
   - `--create-tasks` - Auto-generate research tasks
   - `--no-cache` - Force fresh analysis
   - `commandcenter analyze stats` - Show statistics
3. Agent orchestration commands (`commands/agents.py`)
   - `commandcenter agents launch` - Start agents
   - `commandcenter agents status` - Show agent status
   - `commandcenter agents logs <agent-id>` - View logs
4. Search commands (`commands/search.py`)
   - `commandcenter search <query>` - RAG-powered search
   - `--filter technology|research` - Filter results
5. Validators and formatters (`utils/`)
   - Path validation
   - GitHub repo format validation
   - Result formatting helpers
6. Tests (20 tests total)
   - Analyze command tests (7 tests)
   - Agent command tests (8 tests)
   - Search command tests (6 tests)
   - Output formatting tests (4 tests)

**Tests**: 35/40 passing (87.5%)

---

### Phase 3: Checkpoint 3 (20% - 2 hours)

**Deliverables**:
1. Shell completion scripts (`completion/`)
   - Bash completion script
   - Zsh completion script
   - Fish completion script
   - `commandcenter completion bash|zsh|fish` command to generate scripts
2. Advanced features:
   - `--watch` mode for analyze command (re-analyze on file changes)
   - `--interactive` mode for search (multi-query session)
   - `--format json|yaml|table` global option working everywhere
3. Enhanced output features:
   - Dependency tree visualization
   - Research gap severity coloring
   - Export to file functionality
4. Documentation (`docs/CLI_GUIDE.md`)
   - Installation instructions
   - Command reference with examples
   - Configuration guide
   - Shell completion setup
   - Troubleshooting
5. Polish:
   - Comprehensive help text for all commands
   - Error messages with suggestions
   - `NO_COLOR` environment variable support
6. Final tests (5 tests)
   - Integration test: Full analyze workflow against live backend
   - Shell completion tests
   - Watch mode tests
   - Export tests

**Tests**: 40/40 passing (100%)

---

## Interface Contracts

### CLI Command Structure

```
commandcenter
├── analyze
│   ├── project <path>          # Analyze local project
│   │   ├── --github            # Analyze GitHub repo
│   │   ├── --watch             # Watch mode
│   │   ├── --export            # Export results
│   │   ├── --create-tasks      # Auto-generate tasks
│   │   └── --no-cache          # Force fresh analysis
│   └── stats                   # Show analysis statistics
├── agents
│   ├── launch                  # Launch agent workflow
│   │   ├── --workflow          # Workflow type
│   │   └── --max-concurrent    # Max concurrent agents
│   ├── status [ID]             # Show agent status
│   ├── stop <ID>               # Stop agents
│   ├── logs <ID>               # View agent logs
│   │   └── --follow            # Follow logs
│   └── retry <ID>              # Retry failed agent
├── search <query>              # RAG-powered search
│   ├── --filter                # Filter by type
│   └── --interactive           # Interactive mode
├── config
│   ├── init                    # Initialize config
│   ├── set <key> <value>       # Set config value
│   ├── get <key>               # Get config value
│   └── list                    # List all config
├── completion <shell>          # Generate completion script
└── --version                   # Show version
```

### Config File Schema

`~/.commandcenter/config.yaml`:
```yaml
# CommandCenter CLI Configuration

# API Configuration
api:
  url: http://localhost:8000
  timeout: 30
  verify_ssl: true

# Authentication
auth:
  token: null  # Set via: commandcenter config set auth.token <token>

# Output Preferences
output:
  format: table  # table, json, yaml
  color: auto    # auto, always, never
  verbose: false

# Analysis Defaults
analysis:
  cache: true
  create_tasks: false
  export_path: ./analysis-results

# Agent Orchestration
agents:
  max_concurrent: 3
  retry_failed: true
  log_level: info
```

### APIClient Interface

```python
from typing import Optional, List, Dict, Any
import httpx

class APIClient:
    """
    Client for CommandCenter backend API.

    Handles authentication, retries, and error handling.
    """

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        """
        Initialize API client.

        Args:
            base_url: Backend API URL (e.g., http://localhost:8000)
            auth_token: Optional authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers=self._get_headers()
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers including auth if available"""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def analyze_project(
        self,
        project_path: str,
        use_cache: bool = True
    ) -> "ProjectAnalysisResult":
        """
        Analyze a local project.

        Args:
            project_path: Absolute path to project
            use_cache: Use cached results if available

        Returns:
            ProjectAnalysisResult from Agent 2

        Raises:
            APIError: If API request fails
        """
        response = await self._client.post(
            "/api/v1/projects/analyze",
            json={
                "project_path": project_path,
                "use_cache": use_cache
            }
        )
        response.raise_for_status()
        return ProjectAnalysisResult(**response.json())

    async def analyze_github_repo(
        self,
        repo: str,
        use_cache: bool = True
    ) -> "ProjectAnalysisResult":
        """
        Analyze a GitHub repository.

        Args:
            repo: Repository in format 'owner/name'
            use_cache: Use cached results if available

        Returns:
            ProjectAnalysisResult from Agent 2
        """
        response = await self._client.post(
            "/api/v1/projects/analyze-github",
            json={
                "repository": repo,
                "use_cache": use_cache
            }
        )
        response.raise_for_status()
        return ProjectAnalysisResult(**response.json())

    async def create_research_tasks_from_analysis(
        self,
        analysis_id: int
    ) -> List[Dict[str, Any]]:
        """
        Auto-generate research tasks from analysis gaps.

        Args:
            analysis_id: ID of project analysis

        Returns:
            List of created ResearchTask objects
        """
        response = await self._client.post(
            f"/api/v1/projects/{analysis_id}/generate-tasks"
        )
        response.raise_for_status()
        return response.json()

    async def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        response = await self._client.get("/api/v1/projects/analysis/statistics")
        response.raise_for_status()
        return response.json()

    async def launch_agents(
        self,
        workflow: str,
        max_concurrent: int = 3
    ) -> "OrchestrationResult":
        """Launch agent orchestration (stub for Phase 2)"""
        # Stub implementation - Phase 2 agents will implement backend
        raise NotImplementedError("Agent orchestration coming in Phase 2")

    async def search_knowledge(
        self,
        query: str,
        filter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """RAG-powered knowledge search"""
        params = {"q": query}
        if filter_type:
            params["type"] = filter_type

        response = await self._client.get("/api/v1/knowledge/query", params=params)
        response.raise_for_status()
        return response.json()
```

### Config Interface

```python
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel

class APIConfig(BaseModel):
    url: str = "http://localhost:8000"
    timeout: int = 30
    verify_ssl: bool = True

class AuthConfig(BaseModel):
    token: Optional[str] = None

class OutputConfig(BaseModel):
    format: str = "table"  # table, json, yaml
    color: str = "auto"    # auto, always, never
    verbose: bool = False

class Config(BaseModel):
    api: APIConfig = APIConfig()
    auth: AuthConfig = AuthConfig()
    output: OutputConfig = OutputConfig()
    # ... other config sections

    @classmethod
    def load(cls, path: Path) -> "Config":
        """
        Load configuration from YAML file.

        Creates default config if file doesn't exist.

        Args:
            path: Path to config file (~/.commandcenter/config.yaml)

        Returns:
            Config instance
        """
        if not path.exists():
            config = cls()
            config.save(path)
            return config

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def save(self, path: Path):
        """
        Save configuration to YAML file.

        Args:
            path: Path to config file
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(
                self.dict(),
                f,
                default_flow_style=False,
                sort_keys=False
            )

    def get(self, key: str):
        """
        Get nested config value by dot notation.

        Example: config.get('api.url') -> 'http://localhost:8000'

        Args:
            key: Dot-separated key path

        Returns:
            Config value
        """
        parts = key.split(".")
        value = self
        for part in parts:
            value = getattr(value, part)
        return value

    def set(self, key: str, value):
        """
        Set nested config value by dot notation.

        Example: config.set('api.url', 'http://localhost:9000')

        Args:
            key: Dot-separated key path
            value: New value
        """
        parts = key.split(".")
        obj = self
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
```

---

## Dependencies

### New Dependencies to Add

```txt
# Add to backend/requirements.txt (CLI extras)
click>=8.1.0            # CLI framework
rich>=13.0.0            # Rich terminal output
httpx>=0.24.0           # Already added by Agent 2, for API client
pyyaml>=6.0             # Already present, for config
watchdog>=3.0.0         # For --watch mode
```

### Optional Dependencies

```toml
[project.optional-dependencies]
cli = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "watchdog>=3.0.0"
]
```

---

## Testing Strategy

### Unit Tests (35 tests)
- **Analyze commands** (12 tests)
  - Basic project analysis
  - GitHub repo analysis
  - Export to JSON/YAML
  - Create tasks flag
  - No-cache flag
  - Stats command
  - Error handling (invalid path, API errors)
- **Agent commands** (8 tests)
  - Launch agents
  - Status display
  - Logs retrieval
  - Stop agents
- **Search commands** (6 tests)
  - Basic search
  - Filtered search
  - Interactive mode
  - Empty results
- **Config commands** (10 tests)
  - Init config
  - Set/get values
  - List all config
  - Invalid keys
  - Nested config paths
- **Output formatting** (4 tests)
  - Table format
  - JSON format
  - YAML format
  - Color modes

### Integration Tests (5 tests)
- Full analyze workflow against live backend
- Config persistence across CLI invocations
- Shell completion generation
- Watch mode (file change detection)
- Export to file

### Test Coverage Target
- 80%+ coverage on all CLI modules
- 100% coverage on config management (critical)

---

## Documentation

### CLI_GUIDE.md Contents

1. **Installation**
   ```bash
   pip install commandcenter[cli]
   commandcenter --version
   ```

2. **Quick Start**
   - Initialize configuration
   - Analyze first project
   - View results

3. **Command Reference**
   - `analyze` commands with examples
   - `agents` commands with examples
   - `search` commands with examples
   - `config` commands with examples

4. **Configuration**
   - Config file location
   - All config options explained
   - Environment variable overrides

5. **Shell Completion**
   - Bash setup
   - Zsh setup
   - Fish setup

6. **Advanced Usage**
   - Watch mode
   - CI/CD integration
   - Scripting with commandcenter
   - JSON output for parsing

7. **Troubleshooting**
   - Connection errors
   - Authentication issues
   - Config problems
   - Common errors

---

## Success Criteria

- ✅ All 40 tests passing
- ✅ All command groups implemented (analyze, agents, search, config)
- ✅ Rich terminal output working (tables, trees, progress bars, colors)
- ✅ Configuration management functional
- ✅ Shell completion for bash, zsh, fish
- ✅ Package installable via pip
- ✅ `commandcenter` command works globally after install
- ✅ 80%+ test coverage
- ✅ Integration test: Full workflow against live backend
- ✅ Help text comprehensive with examples
- ✅ CLI_GUIDE.md complete
- ✅ NO_COLOR environment variable respected
- ✅ Works on Linux, macOS, Windows

---

## Risks & Mitigation

### Risk 1: Backend API Not Ready
**Risk**: Some API endpoints may not exist yet (agents, advanced features)
**Mitigation**:
- Use stubs for unimplemented endpoints
- Mock API client in tests
- CLI displays "Coming in Phase 2" message for stub features
**Checkpoint**: Mark stub features clearly in checkpoint 1

### Risk 2: Rich Output Complexity
**Risk**: Rich library has learning curve, output may be buggy
**Mitigation**:
- Start with simple text output in checkpoint 1
- Add rich formatting in checkpoint 2
- Fall back to plain text if terminal doesn't support colors
**Checkpoint**: Test on different terminals in checkpoint 2

### Risk 3: Shell Completion
**Risk**: Completion scripts are tricky, may not work in all shells
**Mitigation**:
- Use Click's built-in completion support
- Test on common shells (bash 5, zsh, fish)
- Document known issues
**Checkpoint**: If completion broken in checkpoint 3, document as known issue

### Risk 4: Watch Mode Reliability
**Risk**: File watching may be unreliable or slow
**Mitigation**:
- Use watchdog library (proven solution)
- Debounce file changes (1 second delay)
- Allow manual re-trigger with Enter key
**Checkpoint**: If watch mode buggy in checkpoint 3, make it optional feature

---

## Coordination Notes

### Exports for Other Agents

- None (CLI is end-user facing, not used by other agents)

### Imports from Other Agents

**From Agent 2 (Project Analyzer)** needs:
- `ProjectAnalyzer` class (indirect via API)
- `ProjectAnalysisResult` schema for result typing
- API endpoint: `POST /api/v1/projects/analyze`

**Usage**:
```python
# In commands/analyze.py
from app.schemas.project_analysis import ProjectAnalysisResult
from cli.api_client import APIClient

api = APIClient(config.api.url, config.auth.token)
result: ProjectAnalysisResult = await api.analyze_project("/path/to/project")
```

**From Agent 1 (MCP Core)**:
- None in Phase 1 (no CLI integration with MCP yet)

### Package Installation

CLI will be installed as part of CommandCenter:
```bash
pip install -e backend/  # Development install
# or
pip install commandcenter[cli]  # Production install
```

Entry point registered in `pyproject.toml`:
```toml
[project.scripts]
commandcenter = "cli.commandcenter:cli"
```

---

## Checkpoint Deliverables Summary

| Checkpoint | Progress | Tests | Key Deliverables |
|------------|----------|-------|------------------|
| 1 | 40% | 15/40 | CLI entry point, config system, API client, basic analyze, config commands |
| 2 | 80% | 35/40 | Rich output, complete analyze, agents commands, search commands, utils |
| 3 | 100% | 40/40 | Shell completion, watch mode, docs, polish, integration tests |

---

## Review Criteria

### Code Quality
- [ ] Black + Flake8 pass
- [ ] Type hints on all functions
- [ ] Google-style docstrings
- [ ] No TODOs or FIXMEs

### Functionality
- [ ] All commands work as specified
- [ ] Rich output displays correctly
- [ ] Config management works
- [ ] Shell completion generates scripts
- [ ] Package installs and `commandcenter` command available

### Testing
- [ ] 40/40 tests passing
- [ ] 80%+ coverage
- [ ] Integration test passes
- [ ] Tested on Linux and macOS

### Documentation
- [ ] CLI_GUIDE.md complete
- [ ] All commands have help text
- [ ] Examples for common workflows

### User Experience
- [ ] Error messages are helpful
- [ ] Progress indicators show for long operations
- [ ] Colors improve readability
- [ ] Help text explains all options

### Coordination
- [ ] STATUS.json updated after each commit
- [ ] Successfully imports from Agent 2
- [ ] No blockers for users

---

## Next Steps After Completion

1. **User testing**
   - Internal dogfooding
   - Gather feedback on UX
   - Iterate on output formatting

2. **Phase 2 integration**
   - Agent orchestration commands become functional
   - Connect to real agent backend (Agent 5)

3. **Future enhancements**
   - TUI (Text User Interface) mode
   - Plugin system for custom commands
   - Aliases for common workflows
   - Shell history integration

---

## Notes

- **UX Focus**: This is user-facing - every detail matters
- **Error messages**: Should be helpful, not technical
- **Performance**: Commands should feel instant (<1s response)
- **Colors**: Improve readability but respect NO_COLOR
- **Cross-platform**: Test on Linux, macOS, Windows (use pathlib)
- **Accessibility**: Provide non-color output modes
- Follow **CommandCenter conventions**: Black formatting, type hints, docstrings
