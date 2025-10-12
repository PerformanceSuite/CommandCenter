# Agent 4: Project Manager MCP Server

**Agent Name**: project-manager-mcp-server
**Phase**: 2 (Integration)
**Branch**: agent/project-manager-mcp
**Duration**: 8-10 hours
**Dependencies**: Agent 1 (mcp-core-infrastructure), Agent 2 (project-analyzer-service)

---

## Mission

Build the Project Manager MCP server that exposes CommandCenter's project analysis and management capabilities to AI assistants and other MCP clients. This server provides resources (project data, analysis results), tools (analyze projects, create tasks), and prompts (analysis templates) to enable AI-driven project management workflows.

You are integrating the MCP core infrastructure (Agent 1) with the ProjectAnalyzer service (Agent 2) to create a powerful MCP server for project intelligence.

---

## Deliverables

### 1. Project Manager MCP Server (`backend/app/mcp/servers/project_manager.py`)
- Concrete implementation of `MCPServer` base class
- Server initialization and capability registration
- Lifecycle management (startup, shutdown, cleanup)
- Integration with database session management

### 2. Resource Providers (`backend/app/mcp/servers/project_manager/resources.py`)
- **ProjectsResource**: List all projects with metadata
- **ProjectDetailsResource**: Detailed project information (URI: `project://{project_id}`)
- **AnalysisResultsResource**: Project analysis results (URI: `analysis://{project_id}`)
- **TechnologiesResource**: Technologies detected in projects
- **ResearchGapsResource**: Identified research gaps by project

### 3. Tool Providers (`backend/app/mcp/servers/project_manager/tools.py`)
- **analyze_project**: Trigger full project analysis
  - Input: `project_path` (string), `force_rescan` (boolean)
  - Output: Analysis summary with technology count, research gaps
- **create_research_tasks**: Generate research tasks from gaps
  - Input: `project_id` (int), `gap_ids` (list[int])
  - Output: List of created research task IDs
- **launch_agents**: Launch agents for research tasks
  - Input: `project_id` (int), `task_ids` (list[int]), `concurrency` (int)
  - Output: Workflow execution ID and status
- **get_project_summary**: Quick project overview
  - Input: `project_id` (int)
  - Output: Summary stats (tech count, task count, last analysis)

### 4. Prompt Providers (`backend/app/mcp/servers/project_manager/prompts.py`)
- **project_analysis_template**: Template for analyzing project structure
  - Arguments: `project_name`, `technologies`, `dependencies`
  - Output: Formatted prompt for AI analysis
- **research_orchestration_template**: Template for planning research
  - Arguments: `research_gaps`, `priority_level`
  - Output: Formatted prompt for research planning
- **technology_comparison_template**: Compare detected vs recommended technologies
  - Arguments: `current_stack`, `recommended_stack`
  - Output: Formatted comparison prompt

### 5. Server Configuration (`backend/app/mcp/servers/project_manager/config.py`)
- Server metadata (name, version, description)
- Capability declarations
- Resource URI schemas
- Tool schema definitions

### 6. Server Registration (`backend/app/mcp/registry.py`)
- Auto-discovery mechanism for MCP servers
- Server registry pattern
- Health check endpoints for each server
- Server status monitoring

### 7. API Integration (`backend/app/routers/mcp.py`)
- REST endpoints to interact with MCP servers
- `GET /api/v1/mcp/servers` - List available MCP servers
- `POST /api/v1/mcp/servers/{name}/resources` - Query resources
- `POST /api/v1/mcp/servers/{name}/tools/{tool_name}` - Execute tool
- `GET /api/v1/mcp/servers/{name}/prompts` - List prompts

### 8. Tests (`backend/tests/test_mcp/test_project_manager_server.py`)
- Server initialization tests
- Resource provider tests (list, read each resource type)
- Tool provider tests (each tool with valid/invalid inputs)
- Prompt provider tests (template rendering)
- Integration test: Full MCP workflow from client perspective
- Error handling tests

---

## Technical Specifications

### Server Architecture

```
backend/app/mcp/servers/
├── __init__.py
├── project_manager.py        # Main server class
└── project_manager/
    ├── __init__.py
    ├── resources.py           # Resource providers
    ├── tools.py               # Tool providers
    ├── prompts.py             # Prompt providers
    └── config.py              # Server configuration
```

### Resource URIs

```
project://1                    # Project details
project://1/technologies       # Technologies in project 1
project://1/research-gaps      # Research gaps for project 1
analysis://1                   # Latest analysis results for project 1
analysis://1/history           # Analysis history for project 1
```

### Tool Schemas

```json
{
  "name": "analyze_project",
  "description": "Analyze a project directory and detect technologies",
  "inputSchema": {
    "type": "object",
    "properties": {
      "project_path": {
        "type": "string",
        "description": "Absolute path to project directory"
      },
      "force_rescan": {
        "type": "boolean",
        "description": "Force re-analysis even if cached",
        "default": false
      }
    },
    "required": ["project_path"]
  }
}
```

---

## Implementation Guidelines

### 1. Project Manager Server (`project_manager.py`)

```python
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.mcp.server import MCPServer
from app.mcp.servers.project_manager.resources import (
    ProjectsResourceProvider,
    ProjectDetailsResourceProvider,
    AnalysisResultsResourceProvider
)
from app.mcp.servers.project_manager.tools import ProjectManagerToolProvider
from app.mcp.servers.project_manager.prompts import ProjectManagerPromptProvider
from app.database import get_db

class ProjectManagerMCPServer(MCPServer):
    """MCP Server for project analysis and management"""

    def __init__(self, db_session: Session):
        super().__init__(name="project-manager", version="1.0.0")
        self.db = db_session

        # Register providers
        self.register_resource_provider(ProjectsResourceProvider(db_session))
        self.register_resource_provider(ProjectDetailsResourceProvider(db_session))
        self.register_resource_provider(AnalysisResultsResourceProvider(db_session))
        self.register_tool_provider(ProjectManagerToolProvider(db_session))
        self.register_prompt_provider(ProjectManagerPromptProvider())

    async def initialize(self) -> Dict[str, Any]:
        """Initialize and return server capabilities"""
        return {
            "protocolVersion": "0.1.0",
            "capabilities": {
                "resources": True,
                "tools": True,
                "prompts": True
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version,
                "description": "Project analysis and management server"
            }
        }

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources from registered providers"""
        resources = []
        for provider in self.resource_providers:
            resources.extend(await provider.list_resources())
        return resources

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read specific resource by URI"""
        # Parse URI scheme to route to correct provider
        scheme = uri.split("://")[0]
        for provider in self.resource_providers:
            if hasattr(provider, 'handles_scheme') and provider.handles_scheme(scheme):
                return await provider.read_resource(uri)
        raise ValueError(f"No provider found for URI: {uri}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        tools = []
        for provider in self.tool_providers:
            tools.extend(await provider.list_tools())
        return tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool"""
        for provider in self.tool_providers:
            if hasattr(provider, 'has_tool') and provider.has_tool(name):
                return await provider.call_tool(name, arguments)
        raise ValueError(f"Tool not found: {name}")
```

### 2. Resource Provider Example (`resources.py`)

```python
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.mcp.providers.base import ResourceProvider
from app.models import Repository, Technology
from app.services.project_analyzer import ProjectAnalyzer

class ProjectsResourceProvider(ResourceProvider):
    """Provides list of all projects"""

    def __init__(self, db: Session):
        self.db = db

    def handles_scheme(self, scheme: str) -> bool:
        return scheme == "projects"

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all project resources"""
        return [{
            "uri": "projects://list",
            "name": "Projects List",
            "description": "All projects tracked in CommandCenter",
            "mimeType": "application/json"
        }]

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read projects list"""
        if uri == "projects://list":
            repos = self.db.query(Repository).all()
            return {
                "contents": [{
                    "uri": f"project://{repo.id}",
                    "name": f"{repo.owner}/{repo.name}",
                    "mimeType": "application/json",
                    "text": repo.description or ""
                } for repo in repos]
            }
        raise ValueError(f"Unknown projects URI: {uri}")

class ProjectDetailsResourceProvider(ResourceProvider):
    """Provides detailed project information"""

    def __init__(self, db: Session):
        self.db = db

    def handles_scheme(self, scheme: str) -> bool:
        return scheme == "project"

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available project detail resources"""
        repos = self.db.query(Repository).all()
        return [{
            "uri": f"project://{repo.id}",
            "name": f"{repo.owner}/{repo.name}",
            "description": f"Details for project {repo.name}",
            "mimeType": "application/json"
        } for repo in repos]

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read specific project details"""
        # Parse: project://123 or project://123/technologies
        parts = uri.replace("project://", "").split("/")
        project_id = int(parts[0])

        repo = self.db.query(Repository).filter(Repository.id == project_id).first()
        if not repo:
            raise ValueError(f"Project not found: {project_id}")

        if len(parts) == 1:
            # Full project details
            return {
                "contents": [{
                    "uri": uri,
                    "name": f"{repo.owner}/{repo.name}",
                    "mimeType": "application/json",
                    "text": self._format_project_details(repo)
                }]
            }
        elif len(parts) == 2 and parts[1] == "technologies":
            # Technologies for this project
            techs = repo.technologies
            return {
                "contents": [{
                    "uri": uri,
                    "name": f"Technologies in {repo.name}",
                    "mimeType": "application/json",
                    "text": self._format_technologies(techs)
                }]
            }
        else:
            raise ValueError(f"Unknown project URI: {uri}")

    def _format_project_details(self, repo: Repository) -> str:
        """Format project as JSON string"""
        import json
        return json.dumps({
            "id": repo.id,
            "name": repo.name,
            "owner": repo.owner,
            "description": repo.description,
            "url": repo.url,
            "last_commit_sha": repo.last_commit_sha,
            "synced_at": repo.synced_at.isoformat() if repo.synced_at else None,
            "technology_count": len(repo.technologies)
        }, indent=2)

    def _format_technologies(self, techs: List[Technology]) -> str:
        """Format technologies as JSON string"""
        import json
        return json.dumps([{
            "id": tech.id,
            "title": tech.title,
            "domain": tech.domain,
            "status": tech.status,
            "relevance": tech.relevance
        } for tech in techs], indent=2)
```

### 3. Tool Provider Example (`tools.py`)

```python
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.mcp.providers.base import ToolProvider
from app.services.project_analyzer import ProjectAnalyzer
from app.services.research_service import ResearchService

class ProjectManagerToolProvider(ToolProvider):
    """Provides project management tools"""

    def __init__(self, db: Session):
        self.db = db
        self.analyzer = ProjectAnalyzer(db)
        self.research_service = ResearchService(db)

    def has_tool(self, name: str) -> bool:
        return name in ["analyze_project", "create_research_tasks",
                       "launch_agents", "get_project_summary"]

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [
            {
                "name": "analyze_project",
                "description": "Analyze a project directory and detect technologies",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Absolute path to project directory"
                        },
                        "force_rescan": {
                            "type": "boolean",
                            "description": "Force re-analysis even if cached",
                            "default": False
                        }
                    },
                    "required": ["project_path"]
                }
            },
            {
                "name": "create_research_tasks",
                "description": "Create research tasks from identified gaps",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "integer"},
                        "gap_ids": {
                            "type": "array",
                            "items": {"type": "integer"}
                        }
                    },
                    "required": ["project_id", "gap_ids"]
                }
            },
            {
                "name": "get_project_summary",
                "description": "Get quick overview of project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "integer"}
                    },
                    "required": ["project_id"]
                }
            }
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with given arguments"""
        if name == "analyze_project":
            return await self._analyze_project(arguments)
        elif name == "create_research_tasks":
            return await self._create_research_tasks(arguments)
        elif name == "get_project_summary":
            return await self._get_project_summary(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _analyze_project(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project and return results"""
        project_path = args["project_path"]
        force_rescan = args.get("force_rescan", False)

        result = await self.analyzer.analyze_project(
            project_path=project_path,
            force_rescan=force_rescan
        )

        return {
            "success": True,
            "project_id": result["project_id"],
            "technologies_detected": result["technology_count"],
            "research_gaps": result["research_gaps"],
            "analysis_time": result["analysis_time_ms"]
        }

    async def _create_research_tasks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create research tasks from gaps"""
        project_id = args["project_id"]
        gap_ids = args["gap_ids"]

        task_ids = await self.research_service.create_tasks_from_gaps(
            project_id=project_id,
            gap_ids=gap_ids
        )

        return {
            "success": True,
            "created_task_ids": task_ids,
            "task_count": len(task_ids)
        }

    async def _get_project_summary(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get project summary stats"""
        from app.models import Repository, ResearchTask

        project_id = args["project_id"]
        repo = self.db.query(Repository).filter(Repository.id == project_id).first()

        if not repo:
            raise ValueError(f"Project not found: {project_id}")

        task_count = self.db.query(ResearchTask).filter(
            ResearchTask.repository_id == project_id
        ).count()

        return {
            "project_id": repo.id,
            "name": f"{repo.owner}/{repo.name}",
            "technology_count": len(repo.technologies),
            "research_task_count": task_count,
            "last_synced": repo.synced_at.isoformat() if repo.synced_at else None
        }
```

### 4. Prompt Provider Example (`prompts.py`)

```python
from typing import Dict, Any, List
from app.mcp.providers.base import PromptProvider

class ProjectManagerPromptProvider(PromptProvider):
    """Provides prompt templates for project analysis"""

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List all available prompt templates"""
        return [
            {
                "name": "project_analysis_template",
                "description": "Template for analyzing project structure",
                "arguments": [
                    {
                        "name": "project_name",
                        "description": "Name of the project",
                        "required": True
                    },
                    {
                        "name": "technologies",
                        "description": "List of detected technologies",
                        "required": True
                    },
                    {
                        "name": "dependencies",
                        "description": "Project dependencies",
                        "required": False
                    }
                ]
            },
            {
                "name": "research_orchestration_template",
                "description": "Template for planning research workflows",
                "arguments": [
                    {
                        "name": "research_gaps",
                        "description": "List of identified research gaps",
                        "required": True
                    },
                    {
                        "name": "priority_level",
                        "description": "Priority level (high, medium, low)",
                        "required": False
                    }
                ]
            }
        ]

    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> str:
        """Get prompt template with arguments filled in"""
        if name == "project_analysis_template":
            return self._project_analysis_prompt(arguments)
        elif name == "research_orchestration_template":
            return self._research_orchestration_prompt(arguments)
        else:
            raise ValueError(f"Unknown prompt: {name}")

    def _project_analysis_prompt(self, args: Dict[str, Any]) -> str:
        """Generate project analysis prompt"""
        project_name = args["project_name"]
        technologies = args["technologies"]
        dependencies = args.get("dependencies", "Not provided")

        return f"""# Project Analysis: {project_name}

## Detected Technologies
{self._format_list(technologies)}

## Dependencies
{dependencies}

## Analysis Tasks
Please analyze this project and:
1. Identify the primary technology stack
2. Assess the maturity of each technology
3. Identify potential security concerns
4. Suggest areas for improvement
5. Recommend research topics for gaps in current implementation

Provide a detailed analysis with actionable recommendations.
"""

    def _research_orchestration_prompt(self, args: Dict[str, Any]) -> str:
        """Generate research orchestration prompt"""
        research_gaps = args["research_gaps"]
        priority = args.get("priority_level", "medium")

        return f"""# Research Orchestration Plan

## Identified Research Gaps ({priority} priority)
{self._format_list(research_gaps)}

## Orchestration Strategy
Please create a research workflow plan that:
1. Prioritizes gaps by impact and urgency
2. Identifies dependencies between research tasks
3. Suggests appropriate AI models/agents for each task
4. Estimates time and resources needed
5. Proposes parallel vs sequential execution strategy

Provide a detailed workflow plan with task assignments.
"""

    def _format_list(self, items: List[str]) -> str:
        """Format list as markdown bullets"""
        if isinstance(items, list):
            return "\n".join(f"- {item}" for item in items)
        return str(items)
```

---

## Testing Strategy

### Unit Tests
- Test each resource provider (list and read operations)
- Test each tool with valid and invalid inputs
- Test prompt template rendering with various arguments
- Test URI parsing and routing

### Integration Tests
- Full MCP workflow: list resources → read resource → call tool
- Database integration (ensure proper session management)
- Error handling (invalid URIs, missing projects, etc.)
- Server initialization and shutdown

### Example Test (`test_project_manager_server.py`)

```python
import pytest
from sqlalchemy.orm import Session
from app.mcp.servers.project_manager import ProjectManagerMCPServer
from app.models import Repository, Technology

@pytest.mark.asyncio
async def test_server_initialization(db_session: Session):
    """Test server initializes with correct capabilities"""
    server = ProjectManagerMCPServer(db_session)
    capabilities = await server.initialize()

    assert capabilities["serverInfo"]["name"] == "project-manager"
    assert capabilities["capabilities"]["resources"] is True
    assert capabilities["capabilities"]["tools"] is True
    assert capabilities["capabilities"]["prompts"] is True

@pytest.mark.asyncio
async def test_list_resources(db_session: Session, sample_repository):
    """Test listing all resources"""
    server = ProjectManagerMCPServer(db_session)
    await server.initialize()

    resources = await server.list_resources()

    assert len(resources) > 0
    assert any(r["uri"] == "projects://list" for r in resources)

@pytest.mark.asyncio
async def test_read_project_resource(db_session: Session, sample_repository):
    """Test reading specific project resource"""
    server = ProjectManagerMCPServer(db_session)
    await server.initialize()

    uri = f"project://{sample_repository.id}"
    resource = await server.read_resource(uri)

    assert "contents" in resource
    assert len(resource["contents"]) > 0

@pytest.mark.asyncio
async def test_analyze_project_tool(db_session: Session, tmp_path):
    """Test analyze_project tool execution"""
    server = ProjectManagerMCPServer(db_session)
    await server.initialize()

    # Create mock project directory
    project_path = tmp_path / "test-project"
    project_path.mkdir()
    (project_path / "package.json").write_text('{"name": "test"}')

    result = await server.call_tool("analyze_project", {
        "project_path": str(project_path),
        "force_rescan": False
    })

    assert result["success"] is True
    assert "technologies_detected" in result
    assert "research_gaps" in result

@pytest.mark.asyncio
async def test_project_analysis_prompt(db_session: Session):
    """Test project analysis prompt generation"""
    server = ProjectManagerMCPServer(db_session)
    await server.initialize()

    prompts = await server.list_prompts()
    assert any(p["name"] == "project_analysis_template" for p in prompts)

    # Test prompt generation
    for provider in server.prompt_providers:
        prompt_text = await provider.get_prompt(
            "project_analysis_template",
            {
                "project_name": "TestProject",
                "technologies": ["React", "TypeScript"],
                "dependencies": "react@18, typescript@5"
            }
        )

        assert "TestProject" in prompt_text
        assert "React" in prompt_text
        assert "TypeScript" in prompt_text
```

---

## Dependencies

```txt
# Already present from Agent 1 (mcp-core-infrastructure)
jsonrpc-python>=0.12.0
pydantic>=2.0.0

# No additional dependencies needed
```

---

## Integration Points

### With Agent 1 (MCP Core)
- Inherits from `MCPServer` base class
- Uses `ResourceProvider`, `ToolProvider`, `PromptProvider` interfaces
- Uses protocol handler for JSON-RPC communication

### With Agent 2 (Project Analyzer)
- Calls `ProjectAnalyzer.analyze_project()` in tools
- Retrieves analysis results from database
- Uses technology detection results

### With Existing Services
- `ResearchService` for task creation
- Database models: `Repository`, `Technology`, `ResearchTask`
- Database session management via FastAPI dependency injection

---

## API Endpoints (`routers/mcp.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.mcp.servers.project_manager import ProjectManagerMCPServer

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])

@router.get("/servers")
async def list_mcp_servers():
    """List all available MCP servers"""
    return {
        "servers": [
            {
                "name": "project-manager",
                "version": "1.0.0",
                "description": "Project analysis and management",
                "status": "active"
            }
        ]
    }

@router.post("/servers/{server_name}/resources")
async def query_resources(
    server_name: str,
    uri: str = None,
    db: Session = Depends(get_db)
):
    """Query resources from MCP server"""
    if server_name == "project-manager":
        server = ProjectManagerMCPServer(db)
        await server.initialize()

        if uri:
            return await server.read_resource(uri)
        else:
            return {"resources": await server.list_resources()}
    else:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_name}")

@router.post("/servers/{server_name}/tools/{tool_name}")
async def execute_tool(
    server_name: str,
    tool_name: str,
    arguments: dict,
    db: Session = Depends(get_db)
):
    """Execute tool on MCP server"""
    if server_name == "project-manager":
        server = ProjectManagerMCPServer(db)
        await server.initialize()
        return await server.call_tool(tool_name, arguments)
    else:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_name}")
```

---

## Documentation

Update `docs/MCP_ARCHITECTURE.md` with:
- Project Manager server overview
- Available resources and URIs
- Tool descriptions and examples
- Prompt template usage
- Example workflows using the server

---

## Success Criteria

- ✅ ProjectManagerMCPServer implements all MCP protocol methods
- ✅ All resource providers functional (projects, analysis results)
- ✅ All tools working (analyze_project, create_research_tasks, etc.)
- ✅ All prompts rendering correctly with arguments
- ✅ Server registration and discovery working
- ✅ REST API endpoints for MCP server interaction
- ✅ 80%+ test coverage
- ✅ Integration tests pass
- ✅ Documentation complete with examples
- ✅ Self-review score: 10/10

---

## Notes

- Follow async/await patterns throughout
- Proper database session management (use dependency injection)
- Comprehensive error handling (invalid URIs, missing projects, tool errors)
- Extensive logging for debugging
- URI scheme validation and routing
- Tool input validation using Pydantic

---

## Self-Review Checklist

Before marking PR as ready:
- [ ] All 8 deliverables complete
- [ ] Tests pass (pytest tests/test_mcp/test_project_manager_server.py -v)
- [ ] Integration with Agent 1 (MCP core) verified
- [ ] Integration with Agent 2 (ProjectAnalyzer) verified
- [ ] Linting passes (black, flake8)
- [ ] Type hints on all functions
- [ ] Docstrings (Google style) on all classes/methods
- [ ] API endpoints working (manual test via Swagger UI)
- [ ] Documentation updated
- [ ] No TODOs or FIXMEs left
- [ ] Self-review score: 10/10
