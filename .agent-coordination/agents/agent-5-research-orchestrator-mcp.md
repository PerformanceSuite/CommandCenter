# Agent 5: Research Orchestrator MCP Server

**Agent Name**: research-orchestrator-mcp-server
**Phase**: 2 (Integration)
**Branch**: agent/research-orchestrator-mcp
**Duration**: 10-12 hours
**Dependencies**: Agent 1 (mcp-core-infrastructure), Agent 2 (project-analyzer-service)

---

## Mission

Build the Research Orchestrator MCP server that automates research workflow generation and agent task execution based on project analysis. This server analyzes research gaps, generates intelligent workflows, selects appropriate AI models/agents, and orchestrates parallel research execution.

You are creating the brain that transforms project analysis into actionable, automated research workflows.

---

## Deliverables

### 1. Research Orchestrator MCP Server (`backend/app/mcp/servers/research_orchestrator.py`)
- Concrete implementation of `MCPServer` base class
- Integration with ResearchService and ProjectAnalyzer
- Workflow state management
- Agent execution coordination

### 2. Workflow Generation Engine (`backend/app/services/workflow_generator.py`)
- Automatic workflow generation from project analysis
- Dependency graph construction (task A → task B)
- Priority calculation algorithm
- Parallelization strategy (max concurrent agents)
- Workflow validation and optimization

### 3. Agent Task Templating System (`backend/app/services/agent_templates.py`)
- Template library for common research tasks
- Task-specific prompt generation
- Context injection (project data, technologies, constraints)
- Template categories:
  - **Security Analysis**: Vulnerability scanning, dependency audits
  - **Performance Review**: Bottleneck identification, optimization suggestions
  - **Best Practices**: Code quality, architecture patterns
  - **Technology Comparison**: Alternative solutions, migration paths
  - **Documentation**: README generation, API docs

### 4. Model Selection Logic (`backend/app/services/model_selector.py`)
- Model/provider selection based on task type
- Cost optimization (use appropriate model for complexity)
- Capability matching (code analysis vs text generation)
- Provider configuration:
  - **Anthropic** (Claude): Architecture, code analysis, complex reasoning
  - **OpenAI** (GPT-4): General research, documentation
  - **Local models**: Simple tasks, privacy-sensitive data
- Fallback strategies if primary model unavailable

### 5. Results Aggregation Service (`backend/app/services/results_aggregator.py`)
- Collect results from multiple agents
- Result synthesis and summarization
- Conflict resolution (contradicting recommendations)
- Quality scoring for agent outputs
- Generate final research report

### 6. Resource/Tool/Prompt Providers (`backend/app/mcp/servers/research_orchestrator/`)
- **Resources**:
  - `workflow://{workflow_id}` - Workflow details and status
  - `workflow://{workflow_id}/results` - Aggregated results
  - `agent-tasks://list` - All agent tasks with status
- **Tools**:
  - `generate_workflow` - Create workflow from project analysis
  - `execute_workflow` - Start workflow execution
  - `get_workflow_status` - Check progress
  - `cancel_workflow` - Stop running workflow
- **Prompts**:
  - `research_task_template` - Template for agent research tasks
  - `result_synthesis_template` - Template for aggregating results

### 7. Workflow Execution Engine (`backend/app/services/workflow_executor.py`)
- Async task execution with concurrency control
- Task dependency resolution
- Progress tracking and status updates
- Error handling and retry logic
- Cleanup on cancellation

### 8. Tests (`backend/tests/test_mcp/test_research_orchestrator_server.py`)
- Workflow generation tests (various project types)
- Model selection tests (correct model for task type)
- Task templating tests
- Execution engine tests (parallel execution, dependencies)
- Results aggregation tests
- Integration test: Full workflow from generation to results

---

## Technical Specifications

### Workflow Schema

```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

class TaskType(str, Enum):
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_REVIEW = "performance_review"
    BEST_PRACTICES = "best_practices"
    TECH_COMPARISON = "technology_comparison"
    DOCUMENTATION = "documentation"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentTask(BaseModel):
    id: str
    type: TaskType
    title: str
    description: str
    prompt: str
    model: str  # "claude-3-5-sonnet", "gpt-4", etc.
    provider: str  # "anthropic", "openai", etc.
    dependencies: List[str] = []  # Task IDs that must complete first
    priority: int = 0  # Higher = more important
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class Workflow(BaseModel):
    id: str
    project_id: int
    tasks: List[AgentTask]
    max_concurrent: int = 3
    status: TaskStatus = TaskStatus.PENDING
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    results_summary: Optional[str] = None
```

### Workflow Generation Algorithm

```python
class WorkflowGenerator:
    """Generate research workflows from project analysis"""

    async def generate_workflow(
        self,
        project_id: int,
        research_gaps: List[Dict[str, Any]],
        priority_filter: Optional[str] = None
    ) -> Workflow:
        """
        Generate workflow from research gaps

        Steps:
        1. Categorize gaps by type (security, performance, etc.)
        2. Create agent tasks for each gap
        3. Build dependency graph
        4. Calculate priorities
        5. Select models for each task
        6. Optimize for parallel execution
        """
        pass
```

### Model Selection Matrix

```python
MODEL_SELECTION_MATRIX = {
    TaskType.SECURITY_ANALYSIS: {
        "preferred": "claude-3-5-sonnet-20241022",
        "provider": "anthropic",
        "reason": "Superior code analysis and vulnerability detection"
    },
    TaskType.PERFORMANCE_REVIEW: {
        "preferred": "claude-3-5-sonnet-20241022",
        "provider": "anthropic",
        "reason": "Excellent at identifying bottlenecks and optimization strategies"
    },
    TaskType.BEST_PRACTICES: {
        "preferred": "gpt-4-turbo",
        "provider": "openai",
        "reason": "Strong knowledge of industry standards and patterns"
    },
    TaskType.TECH_COMPARISON: {
        "preferred": "claude-3-5-sonnet-20241022",
        "provider": "anthropic",
        "reason": "Comprehensive technology knowledge and comparison skills"
    },
    TaskType.DOCUMENTATION: {
        "preferred": "gpt-4",
        "provider": "openai",
        "reason": "Excellent documentation generation and clarity"
    }
}
```

---

## Implementation Guidelines

### 1. Research Orchestrator Server (`research_orchestrator.py`)

```python
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.mcp.server import MCPServer
from app.services.workflow_generator import WorkflowGenerator
from app.services.workflow_executor import WorkflowExecutor
from app.services.results_aggregator import ResultsAggregator

class ResearchOrchestratorMCPServer(MCPServer):
    """MCP Server for automated research orchestration"""

    def __init__(self, db_session: Session):
        super().__init__(name="research-orchestrator", version="1.0.0")
        self.db = db_session
        self.workflow_generator = WorkflowGenerator(db_session)
        self.workflow_executor = WorkflowExecutor(db_session)
        self.results_aggregator = ResultsAggregator(db_session)

        # In-memory workflow storage (use Redis in production)
        self.workflows: Dict[str, Workflow] = {}

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
                "description": "Automated research workflow orchestration"
            }
        }
```

### 2. Workflow Generation Engine (`workflow_generator.py`)

```python
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from app.models import Repository, Technology, ResearchTask
from app.services.model_selector import ModelSelector
from app.services.agent_templates import AgentTemplates

class WorkflowGenerator:
    """Generate research workflows from project analysis"""

    def __init__(self, db: Session):
        self.db = db
        self.model_selector = ModelSelector()
        self.templates = AgentTemplates()

    async def generate_workflow(
        self,
        project_id: int,
        priority_filter: Optional[str] = None,
        max_concurrent: int = 3
    ) -> Workflow:
        """Generate workflow from project analysis"""

        # 1. Load project and research gaps
        repo = self.db.query(Repository).filter(Repository.id == project_id).first()
        if not repo:
            raise ValueError(f"Project not found: {project_id}")

        research_tasks = self.db.query(ResearchTask).filter(
            ResearchTask.repository_id == project_id,
            ResearchTask.status == "pending"
        ).all()

        if priority_filter:
            research_tasks = [t for t in research_tasks if t.priority == priority_filter]

        # 2. Categorize and create agent tasks
        agent_tasks = []
        for research_task in research_tasks:
            task_type = self._categorize_task(research_task)
            agent_task = await self._create_agent_task(
                research_task=research_task,
                task_type=task_type,
                project=repo
            )
            agent_tasks.append(agent_task)

        # 3. Build dependency graph
        agent_tasks = self._build_dependencies(agent_tasks)

        # 4. Calculate priorities
        agent_tasks = self._calculate_priorities(agent_tasks)

        # 5. Create workflow
        workflow = Workflow(
            id=str(uuid.uuid4()),
            project_id=project_id,
            tasks=agent_tasks,
            max_concurrent=max_concurrent,
            created_at=datetime.utcnow().isoformat()
        )

        return workflow

    def _categorize_task(self, research_task: ResearchTask) -> TaskType:
        """Categorize research task by type"""
        title_lower = research_task.title.lower()
        description_lower = (research_task.description or "").lower()

        if any(kw in title_lower or kw in description_lower
               for kw in ["security", "vulnerability", "audit", "cve"]):
            return TaskType.SECURITY_ANALYSIS

        elif any(kw in title_lower or kw in description_lower
                 for kw in ["performance", "optimization", "bottleneck", "slow"]):
            return TaskType.PERFORMANCE_REVIEW

        elif any(kw in title_lower or kw in description_lower
                 for kw in ["compare", "alternative", "vs", "migration"]):
            return TaskType.TECH_COMPARISON

        elif any(kw in title_lower or kw in description_lower
                 for kw in ["documentation", "readme", "docs", "guide"]):
            return TaskType.DOCUMENTATION

        else:
            return TaskType.BEST_PRACTICES

    async def _create_agent_task(
        self,
        research_task: ResearchTask,
        task_type: TaskType,
        project: Repository
    ) -> AgentTask:
        """Create agent task from research task"""

        # Select appropriate model
        model_config = self.model_selector.select_model(task_type)

        # Generate task prompt
        prompt = await self.templates.generate_prompt(
            task_type=task_type,
            research_task=research_task,
            project=project
        )

        return AgentTask(
            id=str(uuid.uuid4()),
            type=task_type,
            title=research_task.title,
            description=research_task.description or "",
            prompt=prompt,
            model=model_config["model"],
            provider=model_config["provider"],
            priority=self._map_priority(research_task.priority)
        )

    def _build_dependencies(self, tasks: List[AgentTask]) -> List[AgentTask]:
        """Build task dependency graph"""
        # Security analysis should complete before other tasks can use its findings
        security_tasks = [t for t in tasks if t.type == TaskType.SECURITY_ANALYSIS]
        other_tasks = [t for t in tasks if t.type != TaskType.SECURITY_ANALYSIS]

        for task in other_tasks:
            # Add security tasks as dependencies
            task.dependencies = [st.id for st in security_tasks]

        return security_tasks + other_tasks

    def _calculate_priorities(self, tasks: List[AgentTask]) -> List[AgentTask]:
        """Calculate execution priorities"""
        # Priority factors:
        # - Task type importance
        # - Number of dependents
        # - User-specified priority

        for task in tasks:
            base_priority = task.priority

            # Security gets highest priority
            if task.type == TaskType.SECURITY_ANALYSIS:
                task.priority = base_priority + 100

            # Tasks with many dependents get higher priority
            dependent_count = sum(1 for t in tasks if task.id in t.dependencies)
            task.priority += dependent_count * 10

        return sorted(tasks, key=lambda t: t.priority, reverse=True)

    def _map_priority(self, priority_str: Optional[str]) -> int:
        """Map priority string to numeric value"""
        priority_map = {"high": 100, "medium": 50, "low": 10}
        return priority_map.get(priority_str or "medium", 50)
```

### 3. Agent Task Templates (`agent_templates.py`)

```python
from typing import Dict, Any
from app.models import Repository, ResearchTask

class AgentTemplates:
    """Prompt templates for different agent task types"""

    async def generate_prompt(
        self,
        task_type: TaskType,
        research_task: ResearchTask,
        project: Repository
    ) -> str:
        """Generate prompt for agent task"""

        if task_type == TaskType.SECURITY_ANALYSIS:
            return self._security_analysis_prompt(research_task, project)
        elif task_type == TaskType.PERFORMANCE_REVIEW:
            return self._performance_review_prompt(research_task, project)
        elif task_type == TaskType.BEST_PRACTICES:
            return self._best_practices_prompt(research_task, project)
        elif task_type == TaskType.TECH_COMPARISON:
            return self._tech_comparison_prompt(research_task, project)
        elif task_type == TaskType.DOCUMENTATION:
            return self._documentation_prompt(research_task, project)
        else:
            return self._generic_prompt(research_task, project)

    def _security_analysis_prompt(
        self,
        research_task: ResearchTask,
        project: Repository
    ) -> str:
        """Generate security analysis prompt"""
        return f"""# Security Analysis: {research_task.title}

## Project Context
- **Project**: {project.owner}/{project.name}
- **Description**: {project.description or "N/A"}
- **Technologies**: {", ".join(t.title for t in project.technologies)}

## Research Task
{research_task.description}

## Your Mission
Conduct a comprehensive security analysis focusing on:
1. **Vulnerability Assessment**: Identify potential security vulnerabilities
2. **Dependency Audit**: Review third-party dependencies for known CVEs
3. **Authentication/Authorization**: Analyze access control mechanisms
4. **Data Protection**: Evaluate data encryption and privacy measures
5. **Best Practices**: Check compliance with OWASP Top 10 and security standards

## Expected Output
Provide a structured security report with:
- Executive summary of findings
- Detailed vulnerability list (severity: critical/high/medium/low)
- Actionable remediation steps
- Priority recommendations

**Format**: Markdown with clear sections
"""

    def _performance_review_prompt(
        self,
        research_task: ResearchTask,
        project: Repository
    ) -> str:
        """Generate performance review prompt"""
        return f"""# Performance Review: {research_task.title}

## Project Context
- **Project**: {project.owner}/{project.name}
- **Technologies**: {", ".join(t.title for t in project.technologies)}

## Research Task
{research_task.description}

## Your Mission
Analyze project performance and identify optimization opportunities:
1. **Bottleneck Identification**: Find performance bottlenecks in code
2. **Resource Usage**: Evaluate CPU, memory, I/O efficiency
3. **Scalability**: Assess ability to handle increased load
4. **Query Optimization**: Database query performance (if applicable)
5. **Frontend Performance**: Page load times, bundle sizes (if applicable)

## Expected Output
Provide a performance analysis report with:
- Performance metrics and benchmarks
- Identified bottlenecks with code references
- Optimization recommendations (quick wins + long-term)
- Estimated performance improvements

**Format**: Markdown with charts/graphs if relevant
"""

    def _tech_comparison_prompt(
        self,
        research_task: ResearchTask,
        project: Repository
    ) -> str:
        """Generate technology comparison prompt"""
        return f"""# Technology Comparison: {research_task.title}

## Current Stack
- **Project**: {project.owner}/{project.name}
- **Technologies**: {", ".join(t.title for t in project.technologies)}

## Research Task
{research_task.description}

## Your Mission
Compare current technology choices with alternatives:
1. **Current Technology Assessment**: Strengths and weaknesses
2. **Alternative Solutions**: Viable alternatives with pros/cons
3. **Migration Path**: If recommending change, provide migration strategy
4. **Cost Analysis**: Development time, learning curve, maintenance
5. **Ecosystem**: Community support, tooling, documentation

## Expected Output
Provide a technology comparison report with:
- Comparison matrix (feature-by-feature)
- Recommendation with justification
- Migration guide (if applicable)
- Risk assessment

**Format**: Markdown with comparison tables
"""

    def _generic_prompt(
        self,
        research_task: ResearchTask,
        project: Repository
    ) -> str:
        """Generic research prompt"""
        return f"""# Research Task: {research_task.title}

## Project Context
- **Project**: {project.owner}/{project.name}
- **Description**: {project.description or "N/A"}

## Task Description
{research_task.description}

## Expected Output
Provide a comprehensive analysis addressing the research task.
Include actionable recommendations and best practices.

**Format**: Markdown with clear structure
"""
```

### 4. Workflow Executor (`workflow_executor.py`)

```python
import asyncio
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.model_selector import ModelSelector

class WorkflowExecutor:
    """Execute research workflows with parallel agent execution"""

    def __init__(self, db: Session):
        self.db = db
        self.model_selector = ModelSelector()

    async def execute_workflow(self, workflow: Workflow) -> Workflow:
        """Execute workflow with concurrency control"""
        workflow.status = TaskStatus.RUNNING
        workflow.started_at = datetime.utcnow().isoformat()

        try:
            # Execute tasks respecting dependencies and concurrency limit
            completed_tasks = set()
            while len(completed_tasks) < len(workflow.tasks):
                # Find tasks ready to execute (dependencies satisfied)
                ready_tasks = [
                    task for task in workflow.tasks
                    if task.status == TaskStatus.PENDING
                    and all(dep in completed_tasks for dep in task.dependencies)
                ]

                if not ready_tasks:
                    # Check if we're deadlocked
                    running_tasks = [t for t in workflow.tasks if t.status == TaskStatus.RUNNING]
                    if not running_tasks:
                        raise Exception("Workflow deadlock detected")
                    # Wait for running tasks to complete
                    await asyncio.sleep(1)
                    continue

                # Execute up to max_concurrent tasks
                batch = ready_tasks[:workflow.max_concurrent]

                # Execute batch in parallel
                results = await asyncio.gather(
                    *[self._execute_task(task) for task in batch],
                    return_exceptions=True
                )

                # Update task statuses
                for task, result in zip(batch, results):
                    if isinstance(result, Exception):
                        task.status = TaskStatus.FAILED
                        task.error = str(result)
                    else:
                        task.status = TaskStatus.COMPLETED
                        task.result = result
                        completed_tasks.add(task.id)

            workflow.status = TaskStatus.COMPLETED
            workflow.completed_at = datetime.utcnow().isoformat()

        except Exception as e:
            workflow.status = TaskStatus.FAILED
            # Mark all pending/running tasks as failed
            for task in workflow.tasks:
                if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                    task.status = TaskStatus.FAILED
                    task.error = f"Workflow failed: {str(e)}"

        return workflow

    async def _execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a single agent task"""
        task.status = TaskStatus.RUNNING

        try:
            # Get API client for the provider
            client = self.model_selector.get_client(task.provider)

            # Execute task based on provider
            if task.provider == "anthropic":
                result = await self._execute_anthropic_task(client, task)
            elif task.provider == "openai":
                result = await self._execute_openai_task(client, task)
            else:
                raise ValueError(f"Unsupported provider: {task.provider}")

            return result

        except Exception as e:
            raise Exception(f"Task execution failed: {str(e)}")

    async def _execute_anthropic_task(self, client: Any, task: AgentTask) -> Dict[str, Any]:
        """Execute task using Anthropic API"""
        response = await client.messages.create(
            model=task.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": task.prompt}]
        )

        return {
            "content": response.content[0].text,
            "model": task.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }
```

---

## Testing Strategy

### Unit Tests
- Workflow generation from various project types
- Model selection for each task type
- Task dependency graph construction
- Priority calculation algorithm
- Task template rendering

### Integration Tests
- Full workflow execution (mock AI providers)
- Parallel task execution with dependencies
- Error handling and retry logic
- Results aggregation

### Example Test

```python
@pytest.mark.asyncio
async def test_workflow_generation(db_session: Session, sample_repository):
    """Test workflow generation from project analysis"""
    generator = WorkflowGenerator(db_session)

    # Create research tasks
    task1 = ResearchTask(
        title="Security audit",
        description="Analyze security vulnerabilities",
        repository_id=sample_repository.id,
        priority="high"
    )
    db_session.add(task1)
    db_session.commit()

    workflow = await generator.generate_workflow(
        project_id=sample_repository.id,
        max_concurrent=2
    )

    assert len(workflow.tasks) > 0
    assert workflow.project_id == sample_repository.id
    assert any(t.type == TaskType.SECURITY_ANALYSIS for t in workflow.tasks)
```

---

## Success Criteria

- ✅ Workflow generation from project analysis working
- ✅ Model selection logic implemented
- ✅ Task templates for all task types
- ✅ Workflow executor handles parallel execution
- ✅ Dependency resolution working
- ✅ Results aggregation functional
- ✅ MCP server integration complete
- ✅ 80%+ test coverage
- ✅ Documentation complete
- ✅ Self-review score: 10/10

---

## Self-Review Checklist

Before marking PR as ready:
- [ ] All 8 deliverables complete
- [ ] Tests pass
- [ ] Integration with Agent 1 (MCP core) verified
- [ ] Integration with Agent 2 (ProjectAnalyzer) verified
- [ ] Linting passes (black, flake8)
- [ ] Type hints on all functions
- [ ] Docstrings complete
- [ ] Documentation updated
- [ ] No TODOs or FIXMEs left
- [ ] Self-review score: 10/10
