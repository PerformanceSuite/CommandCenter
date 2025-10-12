# Agent 3: CLI Interface

**Agent Name**: cli-interface
**Phase**: 2 (Core Features)
**Branch**: agent/cli-interface
**Duration**: 8-12 hours
**Dependencies**: Agent 2 (Project Analyzer Service)

---

## Mission

Build a professional command-line interface (CLI) for CommandCenter that provides developers with a powerful terminal experience. The CLI enables project analysis, agent orchestration, and system management without leaving the terminal.

You are implementing a Click-based CLI with rich terminal output, configuration management, shell completion, and seamless integration with CommandCenter's backend services.

---

## Deliverables

### 1. CLI Entry Point (`backend/cli/commandcenter.py`)
- Main CLI application using Click
- Command groups: `analyze`, `agents`, `config`, `search`
- Global options (--verbose, --config, --format)
- Help text and examples
- Version command

### 2. Analyze Commands (`backend/cli/commands/analyze.py`)
- `commandcenter analyze <path>` - Analyze project directory
- `commandcenter analyze --github <owner/repo>` - Analyze GitHub repo
- `commandcenter analyze --watch` - Watch mode with live updates
- `commandcenter analyze --export json|yaml` - Export results
- `commandcenter analyze --create-tasks` - Auto-generate research tasks

### 3. Agent Orchestration Commands (`backend/cli/commands/agents.py`)
- `commandcenter agents launch` - Start agent orchestration
- `commandcenter agents status` - Show agent status
- `commandcenter agents stop` - Stop running agents
- `commandcenter agents logs <agent-id>` - View agent logs
- `commandcenter agents retry <agent-id>` - Retry failed agent

### 4. Search Commands (`backend/cli/commands/search.py`)
- `commandcenter search <query>` - RAG-powered search
- `commandcenter search --filter technology|research` - Filter by type
- `commandcenter search --interactive` - Interactive search mode

### 5. Configuration Management (`backend/cli/config.py`)
- Config file: `~/.commandcenter/config.yaml`
- `commandcenter config init` - Initialize config
- `commandcenter config set <key> <value>` - Set config value
- `commandcenter config get <key>` - Get config value
- `commandcenter config list` - List all config
- API endpoint URL configuration
- Authentication token management

### 6. Rich Terminal Output (`backend/cli/output.py`)
- Progress bars for long operations
- Syntax-highlighted code snippets
- Tables for structured data (using Rich library)
- Color-coded status messages
- Spinners for async operations
- Tree views for dependency graphs

### 7. Shell Completion (`backend/cli/completion/`)
- Bash completion script
- Zsh completion script
- Fish completion script
- `commandcenter completion bash|zsh|fish` - Generate completion script

### 8. Package Configuration (`backend/setup.py` or `pyproject.toml`)
- Setuptools/Poetry configuration
- Entry point: `commandcenter` command
- Dependencies specification
- CLI extras: `pip install commandcenter[cli]`

### 9. Tests (`backend/tests/test_cli/`)
- Click test runner (CliRunner)
- Command invocation tests
- Configuration tests
- Output formatting tests
- Integration test: Full analyze workflow

---

## Technical Specifications

### CLI Architecture

```
backend/
├── cli/
│   ├── __init__.py
│   ├── commandcenter.py     # Main entry point
│   ├── config.py            # Configuration management
│   ├── output.py            # Rich terminal output
│   ├── api_client.py        # Backend API client
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── analyze.py       # Analyze commands
│   │   ├── agents.py        # Agent commands
│   │   ├── search.py        # Search commands
│   │   └── config.py        # Config commands
│   ├── completion/
│   │   ├── commandcenter.bash
│   │   ├── commandcenter.zsh
│   │   └── commandcenter.fish
│   └── utils/
│       ├── __init__.py
│       ├── validators.py    # Input validation
│       └── formatters.py    # Data formatting
└── tests/
    └── test_cli/
        ├── test_analyze.py
        ├── test_agents.py
        ├── test_config.py
        └── test_output.py
```

### Configuration Schema

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

---

## Implementation Guidelines

### 1. Main CLI Entry Point (`cli/commandcenter.py`)

```python
import click
from pathlib import Path
from cli.config import Config
from cli.commands import analyze, agents, search, config as config_cmd

@click.group()
@click.version_option(version="0.1.0", prog_name="commandcenter")
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to config file (default: ~/.commandcenter/config.yaml)"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output"
)
@click.option(
    "--format",
    type=click.Choice(["table", "json", "yaml"]),
    default=None,
    help="Output format"
)
@click.pass_context
def cli(ctx, config, verbose, format):
    """
    CommandCenter CLI - R&D Management & Knowledge Base

    Analyze projects, orchestrate agents, and search knowledge.

    Examples:
      commandcenter analyze .
      commandcenter agents launch
      commandcenter search "FastAPI authentication"
    """
    # Initialize context
    ctx.ensure_object(dict)

    # Load config
    config_path = config or Path.home() / ".commandcenter" / "config.yaml"
    ctx.obj["config"] = Config.load(config_path)

    # Override with CLI options
    if verbose:
        ctx.obj["config"].output.verbose = True
    if format:
        ctx.obj["config"].output.format = format

# Register command groups
cli.add_command(analyze.analyze)
cli.add_command(agents.agents)
cli.add_command(search.search)
cli.add_command(config_cmd.config)

if __name__ == "__main__":
    cli()
```

### 2. Analyze Commands (`cli/commands/analyze.py`)

```python
import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from cli.api_client import APIClient
from cli.output import (
    display_analysis_results,
    display_error,
    display_success
)

console = Console()

@click.group()
def analyze():
    """Analyze projects to detect technologies and research gaps"""
    pass

@analyze.command("project")
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option(
    "--github",
    help="Analyze GitHub repository (format: owner/repo)"
)
@click.option(
    "--watch",
    is_flag=True,
    help="Watch mode: re-analyze on file changes"
)
@click.option(
    "--export",
    type=click.Choice(["json", "yaml"]),
    help="Export results to file"
)
@click.option(
    "--create-tasks",
    is_flag=True,
    help="Auto-generate research tasks from gaps"
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable cache, force fresh analysis"
)
@click.pass_context
def project(ctx, path, github, watch, export, create_tasks, no_cache):
    """
    Analyze a project directory or GitHub repository.

    Examples:
      commandcenter analyze project .
      commandcenter analyze project --github facebook/react
      commandcenter analyze project . --create-tasks --export json
    """
    config = ctx.obj["config"]
    api = APIClient(config.api.url, config.auth.token)

    if github:
        # Analyze GitHub repository
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Analyzing {github}...",
                total=None
            )

            try:
                result = api.analyze_github_repo(
                    github,
                    use_cache=not no_cache
                )
                progress.update(task, completed=True)
            except Exception as e:
                display_error(f"Analysis failed: {e}")
                raise click.Abort()
    else:
        # Analyze local directory
        path = Path(path).resolve()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Analyzing {path.name}...",
                total=None
            )

            try:
                result = api.analyze_project(
                    str(path),
                    use_cache=not no_cache
                )
                progress.update(task, completed=True)
            except Exception as e:
                display_error(f"Analysis failed: {e}")
                raise click.Abort()

    # Display results
    display_analysis_results(result, format=config.output.format)

    # Create research tasks if requested
    if create_tasks:
        console.print("\n[bold]Creating research tasks...[/bold]")
        tasks = api.create_research_tasks_from_analysis(result.id)
        display_success(f"Created {len(tasks)} research tasks")

    # Export if requested
    if export:
        export_path = Path(f"analysis-{result.id}.{export}")
        with open(export_path, "w") as f:
            if export == "json":
                f.write(result.json(indent=2))
            else:
                import yaml
                f.write(yaml.dump(result.dict()))
        display_success(f"Exported to {export_path}")

@analyze.command("stats")
@click.pass_context
def stats(ctx):
    """Show analysis statistics"""
    config = ctx.obj["config"]
    api = APIClient(config.api.url, config.auth.token)

    stats = api.get_analysis_statistics()

    # Display as table
    from rich.table import Table

    table = Table(title="Analysis Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Analyses", str(stats["total_analyses"]))
    table.add_row("Projects Scanned", str(stats["projects_scanned"]))
    table.add_row("Technologies Detected", str(stats["technologies_detected"]))
    table.add_row("Research Gaps Found", str(stats["research_gaps_found"]))

    console.print(table)
```

### 3. Agent Commands (`cli/commands/agents.py`)

```python
import click
from rich.console import Console
from rich.live import Live
from rich.table import Table
from cli.api_client import APIClient
from cli.output import display_error, display_success

console = Console()

@click.group()
def agents():
    """Manage and orchestrate agents"""
    pass

@agents.command("launch")
@click.option(
    "--workflow",
    type=click.Choice(["full", "analyze-only", "custom"]),
    default="full",
    help="Workflow to execute"
)
@click.option(
    "--max-concurrent",
    type=int,
    default=3,
    help="Maximum concurrent agents"
)
@click.pass_context
def launch(ctx, workflow, max_concurrent):
    """
    Launch agent orchestration workflow.

    Examples:
      commandcenter agents launch
      commandcenter agents launch --workflow analyze-only
    """
    config = ctx.obj["config"]
    api = APIClient(config.api.url, config.auth.token)

    console.print(f"[bold]Launching {workflow} workflow...[/bold]")

    try:
        orchestration = api.launch_agents(
            workflow=workflow,
            max_concurrent=max_concurrent
        )

        display_success(f"Orchestration started: {orchestration.id}")

        # Live status updates
        with Live(generate_agent_table(orchestration), refresh_per_second=2) as live:
            while not orchestration.is_complete:
                orchestration = api.get_orchestration_status(orchestration.id)
                live.update(generate_agent_table(orchestration))

        console.print("\n[bold green]Orchestration complete![/bold green]")

    except Exception as e:
        display_error(f"Orchestration failed: {e}")
        raise click.Abort()

@agents.command("status")
@click.argument("orchestration_id", required=False)
@click.pass_context
def status(ctx, orchestration_id):
    """Show agent orchestration status"""
    config = ctx.obj["config"]
    api = APIClient(config.api.url, config.auth.token)

    if orchestration_id:
        # Show specific orchestration
        orchestration = api.get_orchestration_status(orchestration_id)
        console.print(generate_agent_table(orchestration))
    else:
        # Show all recent orchestrations
        orchestrations = api.list_orchestrations(limit=10)

        table = Table(title="Recent Orchestrations")
        table.add_column("ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Started", style="yellow")
        table.add_column("Agents", style="blue")

        for orch in orchestrations:
            table.add_row(
                str(orch.id),
                orch.status,
                orch.started_at.strftime("%Y-%m-%d %H:%M"),
                f"{orch.completed_agents}/{orch.total_agents}"
            )

        console.print(table)

@agents.command("logs")
@click.argument("agent_id")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.pass_context
def logs(ctx, agent_id, follow):
    """View logs for specific agent"""
    config = ctx.obj["config"]
    api = APIClient(config.api.url, config.auth.token)

    try:
        if follow:
            # Stream logs
            for log_entry in api.stream_agent_logs(agent_id):
                console.print(log_entry)
        else:
            # Get all logs
            logs = api.get_agent_logs(agent_id)
            for log_entry in logs:
                console.print(log_entry)
    except Exception as e:
        display_error(f"Failed to fetch logs: {e}")
        raise click.Abort()

def generate_agent_table(orchestration) -> Table:
    """Generate Rich table for agent status"""
    table = Table(title=f"Orchestration {orchestration.id}")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Progress", style="yellow")
    table.add_column("Duration", style="blue")

    for agent in orchestration.agents:
        status_emoji = {
            "pending": "⏸️",
            "running": "▶️",
            "completed": "✅",
            "failed": "❌"
        }.get(agent.status, "❓")

        table.add_row(
            agent.name,
            f"{status_emoji} {agent.status}",
            f"{agent.progress}%",
            agent.duration or "-"
        )

    return table
```

### 4. Configuration Management (`cli/config.py`)

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
    format: str = "table"
    color: str = "auto"
    verbose: bool = False

class AnalysisConfig(BaseModel):
    cache: bool = True
    create_tasks: bool = False
    export_path: str = "./analysis-results"

class AgentsConfig(BaseModel):
    max_concurrent: int = 3
    retry_failed: bool = True
    log_level: str = "info"

class Config(BaseModel):
    api: APIConfig = APIConfig()
    auth: AuthConfig = AuthConfig()
    output: OutputConfig = OutputConfig()
    analysis: AnalysisConfig = AnalysisConfig()
    agents: AgentsConfig = AgentsConfig()

    @classmethod
    def load(cls, path: Path) -> "Config":
        """Load configuration from YAML file"""
        if not path.exists():
            # Create default config
            config = cls()
            config.save(path)
            return config

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def save(self, path: Path):
        """Save configuration to YAML file"""
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(
                self.dict(),
                f,
                default_flow_style=False,
                sort_keys=False
            )

    def get(self, key: str):
        """Get nested config value by dot notation (e.g., 'api.url')"""
        parts = key.split(".")
        value = self
        for part in parts:
            value = getattr(value, part)
        return value

    def set(self, key: str, value):
        """Set nested config value by dot notation"""
        parts = key.split(".")
        obj = self
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
```

### 5. Rich Output (`cli/output.py`)

```python
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()

def display_analysis_results(result, format="table"):
    """Display project analysis results"""

    if format == "json":
        syntax = Syntax(result.json(indent=2), "json", theme="monokai")
        console.print(syntax)
        return

    # Summary panel
    summary = Panel(
        f"[bold]Project:[/bold] {result.project_path}\n"
        f"[bold]Analyzed:[/bold] {result.analyzed_at}\n"
        f"[bold]Duration:[/bold] {result.analysis_duration_ms}ms",
        title="Analysis Summary",
        border_style="green"
    )
    console.print(summary)

    # Technologies table
    if result.technologies:
        tech_table = Table(title="Detected Technologies")
        tech_table.add_column("Name", style="cyan")
        tech_table.add_column("Category", style="blue")
        tech_table.add_column("Version", style="green")
        tech_table.add_column("Confidence", style="yellow")

        for tech in result.technologies:
            tech_table.add_row(
                tech.name,
                tech.category,
                tech.version or "-",
                f"{tech.confidence:.0%}"
            )

        console.print("\n")
        console.print(tech_table)

    # Dependencies tree
    if result.dependencies:
        console.print("\n[bold]Dependencies:[/bold]")

        deps_by_type = {}
        for dep in result.dependencies:
            deps_by_type.setdefault(dep.type, []).append(dep)

        for dep_type, deps in deps_by_type.items():
            tree = Tree(f"[bold]{dep_type.upper()}[/bold]")
            for dep in deps[:10]:  # Limit to 10 per type
                status = "🔴" if dep.is_outdated else "🟢"
                tree.add(f"{status} {dep.name}@{dep.version}")
            console.print(tree)

    # Research gaps
    if result.research_gaps:
        console.print("\n[bold red]Research Gaps:[/bold red]")

        gaps_table = Table()
        gaps_table.add_column("Technology", style="cyan")
        gaps_table.add_column("Current", style="yellow")
        gaps_table.add_column("Latest", style="green")
        gaps_table.add_column("Severity", style="red")

        for gap in result.research_gaps:
            gaps_table.add_row(
                gap.technology,
                gap.current_version,
                gap.latest_version,
                gap.severity
            )

        console.print(gaps_table)

def display_success(message: str):
    """Display success message"""
    console.print(f"[bold green]✓[/bold green] {message}")

def display_error(message: str):
    """Display error message"""
    console.print(f"[bold red]✗[/bold red] {message}", style="red")

def display_warning(message: str):
    """Display warning message"""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}", style="yellow")
```

### 6. Package Configuration (`pyproject.toml`)

```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "commandcenter"
version = "0.1.0"
description = "R&D Management & Knowledge Base CLI"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "httpx>=0.24.0",
    "pyyaml>=6.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
]

[project.scripts]
commandcenter = "cli.commandcenter:cli"

[tool.setuptools.packages.find]
where = ["."]
include = ["cli*"]
```

---

## Testing Strategy

### Unit Tests

**Command Tests** (`tests/test_cli/test_analyze.py`):
```python
from click.testing import CliRunner
import pytest
from cli.commandcenter import cli

def test_analyze_project_command():
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create dummy project
        with open("package.json", "w") as f:
            f.write('{"dependencies": {"react": "^18.0.0"}}')

        result = runner.invoke(cli, ["analyze", "project", "."])

        assert result.exit_code == 0
        assert "react" in result.output

def test_analyze_with_export():
    runner = CliRunner()

    result = runner.invoke(cli, ["analyze", "project", ".", "--export", "json"])

    assert result.exit_code == 0
    assert "analysis-" in result.output
    # Verify file created
```

**Configuration Tests**:
```python
def test_config_init():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["config", "init"])

        assert result.exit_code == 0
        assert Path("~/.commandcenter/config.yaml").expanduser().exists()

def test_config_set_get():
    runner = CliRunner()

    # Set value
    runner.invoke(cli, ["config", "set", "api.url", "http://example.com"])

    # Get value
    result = runner.invoke(cli, ["config", "get", "api.url"])

    assert "http://example.com" in result.output
```

### Integration Tests

```python
@pytest.mark.integration
def test_full_analyze_workflow(backend_server):
    """Test full analyze workflow against live backend"""
    runner = CliRunner()

    result = runner.invoke(cli, [
        "analyze", "project", ".",
        "--create-tasks",
        "--export", "json"
    ])

    assert result.exit_code == 0
    assert "Technologies" in result.output
    assert "research tasks" in result.output
```

---

## Dependencies

```txt
# Add to backend/requirements.txt (CLI extras)
click>=8.1.0
rich>=13.0.0
httpx>=0.24.0
pyyaml>=6.0
watchdog>=3.0.0  # For --watch mode
```

---

## Documentation

Create `docs/CLI_GUIDE.md` with:
- Installation instructions
- Command reference
- Configuration guide
- Examples for common workflows
- Shell completion setup
- Troubleshooting

---

## Success Criteria

- ✅ All command groups implemented (analyze, agents, search, config)
- ✅ Rich terminal output with tables, trees, progress bars
- ✅ Configuration management functional
- ✅ Shell completion for bash, zsh, fish
- ✅ Package installable via pip
- ✅ 80%+ test coverage
- ✅ Integration test: Full workflow works against live backend
- ✅ Help text comprehensive and examples provided
- ✅ CLI documented in CLI_GUIDE.md
- ✅ No external dependencies on UI/frontend

---

## Notes

- **UX Focus**: Prioritize developer experience with clear output and helpful errors
- **Performance**: Use async API calls, show progress for long operations
- **Error Handling**: Graceful degradation, helpful error messages
- **Offline Mode**: Cache recent results for offline viewing
- **Colors**: Respect NO_COLOR environment variable

---

## Self-Review Checklist

Before marking PR as ready:
- [ ] All 9 deliverables complete
- [ ] All commands tested with CliRunner
- [ ] Rich output displays correctly in terminal
- [ ] Shell completion scripts generated and tested
- [ ] Package installable and command works globally
- [ ] Tests pass (pytest tests/test_cli/ -v)
- [ ] Linting passes (black, flake8)
- [ ] Type hints on all functions
- [ ] Docstrings (Google style) on all classes/methods
- [ ] CLI_GUIDE.md documentation complete
- [ ] Example workflows in docs
- [ ] No TODOs or FIXMEs left
- [ ] Self-review score: 10/10
