# Plan: Unified Agent Execution Framework

**Created**: 2025-12-31
**Status**: 🟡 Draft
**Supersedes**: `docs/plans/2025-12-31-e2b-full-integration.md`

## Goal

Create a single, unified framework for parallel agent execution that works across all execution environments (local process, E2B sandbox, future backends), replacing the fragmented AI Arena / Research Orchestrator / Sandbox Forks implementations.

## Design Principles

1. **One framework, multiple backends** - Like LLMGateway abstracts LLM providers
2. **Execution environment is configuration** - Not a separate system
3. **Synthesis is pluggable** - Chairman, voting, summary, custom
4. **Backward compatible** - Existing code continues to work
5. **Progressive enhancement** - Add sandbox capability without rewriting

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Application Layer                                │
│   HypothesisService    ResearchService    (Future: Any agent workflow)  │
└─────────────────────────────────────────────┬───────────────────────────┘
                                              │
┌─────────────────────────────────────────────▼───────────────────────────┐
│                      AgentExecutor (Unified)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  execute_parallel(agents, task, environment, strategy) → Results    ││
│  │  synthesize(results, strategy) → SynthesisResult                    ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                              │                                           │
│         ┌────────────────────┼────────────────────┐                     │
│         ▼                    ▼                    ▼                     │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────┐            │
│  │   Local     │    │    Sandbox      │    │   (Future)   │            │
│  │  Executor   │    │    Executor     │    │ Docker/Modal │            │
│  └──────┬──────┘    └────────┬────────┘    └──────────────┘            │
│         │                    │                                          │
│         ▼                    ▼                                          │
│  ┌─────────────┐    ┌─────────────────┐                                │
│  │ LLMGateway  │    │  ComputeGateway │                                │
│  │ (existing)  │    │     (new)       │                                │
│  └─────────────┘    └────────┬────────┘                                │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
             ┌───────────┐         ┌───────────┐
             │    E2B    │         │  (Future) │
             │  Backend  │         │  Backends │
             └───────────┘         └───────────┘
```

---

## Core Interfaces

### File: `backend/libs/agent_framework/__init__.py`

```python
"""
Unified Agent Execution Framework

Provides a single interface for running agents in parallel across
different execution environments (local, sandboxed, distributed).
"""

from .executor import AgentExecutor, ExecutionConfig
from .agents import UnifiedAgent, AgentRole, AgentResult
from .environments import ExecutionEnvironment, LocalExecutor, SandboxExecutor
from .synthesis import SynthesisStrategy, ChairmanSynthesis, VotingSynthesis, SummarySynthesis
from .compute import ComputeGateway, ComputeBackend

__all__ = [
    "AgentExecutor",
    "ExecutionConfig",
    "UnifiedAgent",
    "AgentRole",
    "AgentResult",
    "ExecutionEnvironment",
    "LocalExecutor",
    "SandboxExecutor",
    "SynthesisStrategy",
    "ChairmanSynthesis",
    "VotingSynthesis",
    "SummarySynthesis",
    "ComputeGateway",
    "ComputeBackend",
]
```

---

### File: `backend/libs/agent_framework/agents.py`

```python
"""
Unified Agent abstraction that works in any execution environment.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from libs.llm_gateway import LLMGateway


class AgentRole(str, Enum):
    """Standard agent roles across all frameworks"""

    # AI Arena roles
    ANALYST = "analyst"
    RESEARCHER = "researcher"
    STRATEGIST = "strategist"
    CRITIC = "critic"
    CHAIRMAN = "chairman"

    # Research roles
    TECHNOLOGY_SCOUT = "technology_scout"
    DEEP_RESEARCHER = "deep_researcher"
    COMPARATOR = "comparator"
    INTEGRATOR = "integrator"
    MONITOR = "monitor"

    # Generic
    CUSTOM = "custom"


@dataclass
class AgentResult:
    """Unified result from any agent execution"""

    agent_name: str
    role: AgentRole
    answer: str
    reasoning: str
    confidence: int  # 0-100
    evidence: list[str] = field(default_factory=list)

    # Execution metadata
    model: str = ""
    provider: str = ""
    environment: str = "local"  # local, sandbox, docker, etc.
    execution_time_seconds: float = 0.0

    # Cost tracking
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0

    # For sandbox executions
    sandbox_id: Optional[str] = None
    artifacts: list[str] = field(default_factory=list)  # Files created, PRs, etc.

    # Raw data
    raw_response: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "role": self.role.value,
            "answer": self.answer,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "model": self.model,
            "provider": self.provider,
            "environment": self.environment,
            "execution_time_seconds": self.execution_time_seconds,
            "cost_usd": self.cost_usd,
            "sandbox_id": self.sandbox_id,
            "artifacts": self.artifacts,
        }


@dataclass
class AgentConfig:
    """Configuration for creating an agent"""

    name: str
    role: AgentRole
    system_prompt: str
    provider: str = "claude"  # LLM provider alias
    temperature: float = 0.7
    max_tokens: int = 4096

    # For sandbox execution
    repo_url: Optional[str] = None
    branch: Optional[str] = None
    working_directory: Optional[str] = None

    metadata: dict[str, Any] = field(default_factory=dict)


class UnifiedAgent(ABC):
    """
    Base class for all agents in the unified framework.

    Works with both local execution (LLMGateway) and sandbox execution (E2B).
    Agents don't need to know which environment they're running in.
    """

    def __init__(
        self,
        config: AgentConfig,
        gateway: Optional[LLMGateway] = None,
    ):
        self.config = config
        self.gateway = gateway
        self.name = config.name
        self.role = config.role

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass

    @abstractmethod
    def get_task_prompt(self, task: str, context: Optional[str] = None) -> str:
        """Format the task into a prompt for the agent"""
        pass

    async def execute_local(
        self,
        task: str,
        context: Optional[str] = None,
        previous_results: Optional[list[AgentResult]] = None,
    ) -> AgentResult:
        """
        Execute agent locally using LLMGateway.

        This is the standard execution path for AI Arena and Research agents.
        """
        if not self.gateway:
            raise ValueError("LLMGateway required for local execution")

        start_time = datetime.utcnow()

        messages = self._build_messages(task, context, previous_results)

        response = await self.gateway.complete(
            provider=self.config.provider,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        execution_time = (datetime.utcnow() - start_time).total_seconds()

        return self._parse_response(
            response,
            execution_time=execution_time,
            environment="local",
        )

    def get_sandbox_prompt(self, task: str) -> str:
        """
        Get the full prompt for sandbox execution.

        For sandboxes, we combine system prompt + task into one prompt
        that Claude Code will execute.
        """
        system = self.get_system_prompt()
        task_prompt = self.get_task_prompt(task)

        return f"{system}\n\n---\n\n## Task\n\n{task_prompt}"

    def _build_messages(
        self,
        task: str,
        context: Optional[str],
        previous_results: Optional[list[AgentResult]],
    ) -> list[dict[str, str]]:
        """Build messages for LLM call"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
        ]

        user_content = self.get_task_prompt(task, context)

        if previous_results:
            user_content += "\n\n## Previous Agent Results\n\n"
            for result in previous_results:
                user_content += f"### {result.agent_name} ({result.role.value})\n"
                user_content += f"**Confidence:** {result.confidence}%\n"
                user_content += f"**Answer:** {result.answer}\n"
                user_content += f"**Reasoning:** {result.reasoning}\n\n"

        messages.append({"role": "user", "content": user_content})

        return messages

    @abstractmethod
    def _parse_response(
        self,
        response: dict,
        execution_time: float,
        environment: str,
    ) -> AgentResult:
        """Parse LLM response into AgentResult"""
        pass
```

---

### File: `backend/libs/agent_framework/compute.py`

```python
"""
Compute Gateway - Unified interface for execution backends.

Follows the same pattern as LLMGateway for provider abstraction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import os

import structlog

logger = structlog.get_logger(__name__)


class ComputeBackendType(str, Enum):
    """Available compute backends"""
    E2B = "e2b"
    DOCKER = "docker"  # Future
    MODAL = "modal"    # Future
    LOCAL = "local"    # For testing


@dataclass
class EnvironmentConfig:
    """Configuration for creating an execution environment"""

    backend: ComputeBackendType = ComputeBackendType.E2B
    template: str = "base"
    timeout_seconds: int = 600

    # Git configuration (for code-based tasks)
    repo_url: Optional[str] = None
    branch: Optional[str] = None

    # Environment variables to inject
    env_vars: dict[str, str] = field(default_factory=dict)

    # Resource limits
    memory_mb: int = 2048
    cpu_count: int = 2

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result from executing a command in an environment"""

    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float

    # For structured output (e.g., JSON from Claude Code)
    structured_output: Optional[dict[str, Any]] = None

    # Artifacts produced
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)


@dataclass
class Environment:
    """Handle to a running execution environment"""

    id: str
    backend: ComputeBackendType
    status: str  # creating, running, paused, terminated
    created_at: str

    # For E2B
    e2b_sandbox_id: Optional[str] = None

    # Connection info
    host: Optional[str] = None

    metadata: dict[str, Any] = field(default_factory=dict)


class ComputeBackend(ABC):
    """Abstract base class for compute backends"""

    @abstractmethod
    async def create_environment(self, config: EnvironmentConfig) -> Environment:
        """Create a new execution environment"""
        pass

    @abstractmethod
    async def execute(
        self,
        env: Environment,
        command: str,
        timeout_seconds: int = 300,
    ) -> ExecutionResult:
        """Execute a command in the environment"""
        pass

    @abstractmethod
    async def execute_agent(
        self,
        env: Environment,
        prompt: str,
        model: str = "sonnet",
        max_turns: int = 10,
    ) -> ExecutionResult:
        """Execute a Claude Code agent in the environment"""
        pass

    @abstractmethod
    async def terminate(self, env: Environment) -> None:
        """Terminate and cleanup the environment"""
        pass

    @abstractmethod
    async def get_status(self, env: Environment) -> str:
        """Get current status of environment"""
        pass


class E2BBackend(ComputeBackend):
    """E2B sandbox compute backend"""

    def __init__(self):
        self.api_key = os.environ.get("E2B_API_KEY")
        if not self.api_key:
            logger.warning("E2B_API_KEY not set, sandbox operations will fail")

    async def create_environment(self, config: EnvironmentConfig) -> Environment:
        """Create E2B sandbox"""
        from e2b import Sandbox

        logger.info(
            "creating_e2b_sandbox",
            template=config.template,
            timeout=config.timeout_seconds,
        )

        sandbox = Sandbox.create(
            template=config.template,
            timeout=config.timeout_seconds,
            envs=config.env_vars,
        )

        # Clone repo if specified
        if config.repo_url:
            clone_cmd = f"git clone {config.repo_url} /home/user/repo"
            if config.branch:
                clone_cmd += f" && cd /home/user/repo && git checkout {config.branch}"
            sandbox.commands.run(clone_cmd)

        return Environment(
            id=sandbox.sandbox_id,
            backend=ComputeBackendType.E2B,
            status="running",
            created_at=str(sandbox.created_at) if hasattr(sandbox, 'created_at') else "",
            e2b_sandbox_id=sandbox.sandbox_id,
        )

    async def execute(
        self,
        env: Environment,
        command: str,
        timeout_seconds: int = 300,
    ) -> ExecutionResult:
        """Run command in E2B sandbox"""
        from e2b import Sandbox
        import time

        start = time.perf_counter()

        sandbox = Sandbox.connect(env.e2b_sandbox_id)
        result = sandbox.commands.run(command, timeout=timeout_seconds)

        duration = time.perf_counter() - start

        return ExecutionResult(
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_seconds=duration,
        )

    async def execute_agent(
        self,
        env: Environment,
        prompt: str,
        model: str = "sonnet",
        max_turns: int = 10,
    ) -> ExecutionResult:
        """Run Claude Code agent in E2B sandbox"""
        from e2b import Sandbox
        import time
        import json

        start = time.perf_counter()

        sandbox = Sandbox.connect(env.e2b_sandbox_id)

        # Write prompt to file
        sandbox.files.write("/home/user/prompt.txt", prompt)

        # Run Claude Code with the prompt
        # This uses the Claude Code CLI inside the sandbox
        claude_cmd = f"""
        cd /home/user/repo && \
        claude --print --prompt "$(cat /home/user/prompt.txt)" \
        --model {model} \
        --max-turns {max_turns} \
        --output-format json > /home/user/result.json 2>&1
        """

        result = sandbox.commands.run(claude_cmd, timeout=600)

        # Read structured output
        structured = None
        try:
            result_json = sandbox.files.read("/home/user/result.json")
            structured = json.loads(result_json)
        except Exception:
            pass

        duration = time.perf_counter() - start

        return ExecutionResult(
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_seconds=duration,
            structured_output=structured,
        )

    async def terminate(self, env: Environment) -> None:
        """Kill E2B sandbox"""
        from e2b import Sandbox

        sandbox = Sandbox.connect(env.e2b_sandbox_id)
        sandbox.kill()

        logger.info("sandbox_terminated", sandbox_id=env.e2b_sandbox_id)

    async def get_status(self, env: Environment) -> str:
        """Check if sandbox is still running"""
        from e2b import Sandbox

        try:
            sandbox = Sandbox.connect(env.e2b_sandbox_id)
            return "running" if sandbox.is_running() else "terminated"
        except Exception:
            return "terminated"


class ComputeGateway:
    """
    Unified interface for compute backends.

    Follows the same pattern as LLMGateway - backends are swappable,
    interface is stable.

    Example:
        gateway = ComputeGateway()

        env = await gateway.create_environment(
            backend="e2b",
            config=EnvironmentConfig(
                template="agent-sandbox-dev-node22",
                repo_url="https://github.com/user/repo",
                branch="main",
            )
        )

        result = await gateway.execute_agent(
            env=env,
            prompt="Fix the failing tests",
            model="sonnet",
        )

        await gateway.terminate(env)
    """

    def __init__(self):
        self._backends: dict[ComputeBackendType, ComputeBackend] = {}
        self._register_backends()

    def _register_backends(self):
        """Register available backends"""
        # Always register E2B if API key is available
        if os.environ.get("E2B_API_KEY"):
            self._backends[ComputeBackendType.E2B] = E2BBackend()
            logger.info("compute_gateway_initialized", backends=["e2b"])
        else:
            logger.warning("compute_gateway_initialized", backends=[], note="No E2B_API_KEY")

    def _get_backend(self, backend_type: ComputeBackendType) -> ComputeBackend:
        """Get backend by type"""
        if backend_type not in self._backends:
            raise ValueError(f"Backend {backend_type} not available")
        return self._backends[backend_type]

    async def create_environment(
        self,
        backend: str = "e2b",
        config: Optional[EnvironmentConfig] = None,
    ) -> Environment:
        """Create execution environment"""
        backend_type = ComputeBackendType(backend)
        backend_impl = self._get_backend(backend_type)

        if config is None:
            config = EnvironmentConfig(backend=backend_type)

        return await backend_impl.create_environment(config)

    async def execute(
        self,
        env: Environment,
        command: str,
        timeout_seconds: int = 300,
    ) -> ExecutionResult:
        """Execute command in environment"""
        backend = self._get_backend(env.backend)
        return await backend.execute(env, command, timeout_seconds)

    async def execute_agent(
        self,
        env: Environment,
        prompt: str,
        model: str = "sonnet",
        max_turns: int = 10,
    ) -> ExecutionResult:
        """Execute Claude Code agent in environment"""
        backend = self._get_backend(env.backend)
        return await backend.execute_agent(env, prompt, model, max_turns)

    async def terminate(self, env: Environment) -> None:
        """Terminate environment"""
        backend = self._get_backend(env.backend)
        await backend.terminate(env)

    async def get_status(self, env: Environment) -> str:
        """Get environment status"""
        backend = self._get_backend(env.backend)
        return await backend.get_status(env)

    def available_backends(self) -> list[str]:
        """List available compute backends"""
        return [b.value for b in self._backends.keys()]
```

---

### File: `backend/libs/agent_framework/environments.py`

```python
"""
Execution environment implementations.

Handles the details of running agents locally vs in sandboxes.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional

import structlog

from .agents import AgentResult, UnifiedAgent
from .compute import ComputeGateway, EnvironmentConfig, Environment

if TYPE_CHECKING:
    from libs.llm_gateway import LLMGateway

logger = structlog.get_logger(__name__)


class ExecutionEnvironment(str, Enum):
    """Where agents execute"""
    LOCAL = "local"       # In-process, uses LLMGateway
    SANDBOX = "sandbox"   # E2B isolated container
    # Future:
    # DOCKER = "docker"
    # MODAL = "modal"


@dataclass
class ExecutionContext:
    """Context for agent execution"""

    environment: ExecutionEnvironment
    task: str
    context: Optional[str] = None
    previous_results: Optional[list[AgentResult]] = None

    # For sandbox execution
    repo_url: Optional[str] = None
    branch: Optional[str] = None
    sandbox_template: str = "base"


class EnvironmentExecutor(ABC):
    """Base class for environment-specific executors"""

    @abstractmethod
    async def execute_agent(
        self,
        agent: UnifiedAgent,
        context: ExecutionContext,
    ) -> AgentResult:
        """Execute a single agent"""
        pass

    @abstractmethod
    async def execute_parallel(
        self,
        agents: list[UnifiedAgent],
        context: ExecutionContext,
        max_concurrent: int = 3,
    ) -> list[AgentResult]:
        """Execute multiple agents in parallel"""
        pass


class LocalExecutor(EnvironmentExecutor):
    """
    Execute agents locally using LLMGateway.

    This is the standard execution path - agents run in the current
    process and make API calls to LLM providers.
    """

    def __init__(self, gateway: LLMGateway):
        self.gateway = gateway

    async def execute_agent(
        self,
        agent: UnifiedAgent,
        context: ExecutionContext,
    ) -> AgentResult:
        """Execute single agent locally"""
        # Ensure agent has gateway
        if not agent.gateway:
            agent.gateway = self.gateway

        return await agent.execute_local(
            task=context.task,
            context=context.context,
            previous_results=context.previous_results,
        )

    async def execute_parallel(
        self,
        agents: list[UnifiedAgent],
        context: ExecutionContext,
        max_concurrent: int = 3,
    ) -> list[AgentResult]:
        """Execute agents in parallel with semaphore"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_limit(agent: UnifiedAgent) -> AgentResult:
            async with semaphore:
                return await self.execute_agent(agent, context)

        results = await asyncio.gather(
            *[execute_with_limit(agent) for agent in agents],
            return_exceptions=True,
        )

        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "agent_execution_failed",
                    agent=agents[i].name,
                    error=str(result),
                )
                processed_results.append(AgentResult(
                    agent_name=agents[i].name,
                    role=agents[i].role,
                    answer=f"Execution failed: {result}",
                    reasoning="",
                    confidence=0,
                    environment="local",
                    metadata={"error": str(result)},
                ))
            else:
                processed_results.append(result)

        return processed_results


class SandboxExecutor(EnvironmentExecutor):
    """
    Execute agents in isolated E2B sandboxes.

    Each agent gets its own sandbox with:
    - Cloned repository
    - Claude Code available
    - Full filesystem isolation
    """

    def __init__(self, compute: ComputeGateway):
        self.compute = compute

    async def execute_agent(
        self,
        agent: UnifiedAgent,
        context: ExecutionContext,
    ) -> AgentResult:
        """Execute agent in isolated sandbox"""
        import time

        start = time.perf_counter()

        # Create sandbox environment
        config = EnvironmentConfig(
            template=context.sandbox_template,
            repo_url=context.repo_url,
            branch=context.branch,
            timeout_seconds=600,
        )

        env = await self.compute.create_environment(config=config)

        try:
            # Get full prompt for sandbox execution
            prompt = agent.get_sandbox_prompt(context.task)

            # Execute Claude Code agent in sandbox
            result = await self.compute.execute_agent(
                env=env,
                prompt=prompt,
                model=agent.config.provider,  # "claude" -> use sonnet
                max_turns=10,
            )

            execution_time = time.perf_counter() - start

            # Parse sandbox result into AgentResult
            return self._parse_sandbox_result(
                agent=agent,
                result=result,
                sandbox_id=env.id,
                execution_time=execution_time,
            )

        finally:
            # Always cleanup sandbox
            await self.compute.terminate(env)

    async def execute_parallel(
        self,
        agents: list[UnifiedAgent],
        context: ExecutionContext,
        max_concurrent: int = 3,
    ) -> list[AgentResult]:
        """Execute agents in parallel sandboxes"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_limit(agent: UnifiedAgent, fork_num: int) -> AgentResult:
            async with semaphore:
                # Each fork gets its own branch
                fork_context = ExecutionContext(
                    environment=context.environment,
                    task=context.task,
                    context=context.context,
                    repo_url=context.repo_url,
                    branch=f"{context.branch}-fork-{fork_num}" if context.branch else None,
                    sandbox_template=context.sandbox_template,
                )
                return await self.execute_agent(agent, fork_context)

        results = await asyncio.gather(
            *[execute_with_limit(agent, i + 1) for i, agent in enumerate(agents)],
            return_exceptions=True,
        )

        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "sandbox_execution_failed",
                    agent=agents[i].name,
                    error=str(result),
                )
                processed_results.append(AgentResult(
                    agent_name=agents[i].name,
                    role=agents[i].role,
                    answer=f"Sandbox execution failed: {result}",
                    reasoning="",
                    confidence=0,
                    environment="sandbox",
                    metadata={"error": str(result)},
                ))
            else:
                processed_results.append(result)

        return processed_results

    def _parse_sandbox_result(
        self,
        agent: UnifiedAgent,
        result,  # ExecutionResult
        sandbox_id: str,
        execution_time: float,
    ) -> AgentResult:
        """Parse sandbox execution result into AgentResult"""

        # Try to extract structured output
        if result.structured_output:
            output = result.structured_output
            return AgentResult(
                agent_name=agent.name,
                role=agent.role,
                answer=output.get("answer", result.stdout),
                reasoning=output.get("reasoning", ""),
                confidence=output.get("confidence", 70),
                evidence=output.get("evidence", []),
                environment="sandbox",
                sandbox_id=sandbox_id,
                execution_time_seconds=execution_time,
                cost_usd=output.get("cost", 0.0),
                artifacts=result.files_created + result.files_modified,
                raw_response=result.stdout,
            )

        # Fallback to stdout parsing
        return AgentResult(
            agent_name=agent.name,
            role=agent.role,
            answer=result.stdout[:1000] if result.stdout else "No output",
            reasoning=f"Exit code: {result.exit_code}",
            confidence=70 if result.exit_code == 0 else 30,
            environment="sandbox",
            sandbox_id=sandbox_id,
            execution_time_seconds=execution_time,
            raw_response=result.stdout,
            metadata={
                "exit_code": result.exit_code,
                "stderr": result.stderr,
            },
        )
```

---

### File: `backend/libs/agent_framework/synthesis.py`

```python
"""
Synthesis strategies for combining agent results.

Provides pluggable synthesis: Chairman, Voting, Summary, Custom.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING

import structlog

from .agents import AgentResult

if TYPE_CHECKING:
    from libs.llm_gateway import LLMGateway

logger = structlog.get_logger(__name__)


@dataclass
class SynthesisResult:
    """Result of synthesizing multiple agent outputs"""

    final_answer: str
    confidence: int  # 0-100
    consensus_level: str  # strong, moderate, weak, deadlock

    summary: str
    key_insights: list[str] = field(default_factory=list)
    dissenting_views: list[str] = field(default_factory=list)

    # Aggregated metrics
    total_cost_usd: float = 0.0
    total_execution_time: float = 0.0
    agent_count: int = 0

    # Recommendation
    recommendation: str = ""
    follow_up_questions: list[str] = field(default_factory=list)

    # Raw data
    agent_results: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class SynthesisStrategy(ABC):
    """Base class for synthesis strategies"""

    @abstractmethod
    async def synthesize(
        self,
        results: list[AgentResult],
        task: str,
        context: Optional[str] = None,
    ) -> SynthesisResult:
        """Combine multiple agent results into unified output"""
        pass


class VotingSynthesis(SynthesisStrategy):
    """
    Simple voting-based synthesis.

    Counts votes based on answers and confidence levels.
    Fast, no additional LLM calls required.
    """

    async def synthesize(
        self,
        results: list[AgentResult],
        task: str,
        context: Optional[str] = None,
    ) -> SynthesisResult:
        """Synthesize by voting on answers"""
        if not results:
            return SynthesisResult(
                final_answer="No results to synthesize",
                confidence=0,
                consensus_level="deadlock",
                summary="No agent results available",
            )

        # Group by answer direction (simplified)
        votes: dict[str, list[AgentResult]] = {}
        for result in results:
            # Normalize answer to key
            key = result.answer[:100].lower().strip()
            if key not in votes:
                votes[key] = []
            votes[key].append(result)

        # Find winner
        winner_key = max(votes.keys(), key=lambda k: len(votes[k]))
        winner_results = votes[winner_key]

        # Calculate consensus
        consensus_ratio = len(winner_results) / len(results)
        if consensus_ratio >= 0.8:
            consensus_level = "strong"
        elif consensus_ratio >= 0.6:
            consensus_level = "moderate"
        elif consensus_ratio >= 0.4:
            consensus_level = "weak"
        else:
            consensus_level = "deadlock"

        # Aggregate confidence
        avg_confidence = sum(r.confidence for r in winner_results) / len(winner_results)

        # Collect dissenting views
        dissenting = []
        for key, group in votes.items():
            if key != winner_key:
                for result in group:
                    dissenting.append(f"{result.agent_name}: {result.answer[:200]}")

        # Aggregate costs
        total_cost = sum(r.cost_usd for r in results)
        total_time = sum(r.execution_time_seconds for r in results)

        return SynthesisResult(
            final_answer=winner_results[0].answer,
            confidence=int(avg_confidence),
            consensus_level=consensus_level,
            summary=f"{len(winner_results)}/{len(results)} agents agreed",
            key_insights=[r.reasoning[:200] for r in winner_results[:3]],
            dissenting_views=dissenting[:3],
            total_cost_usd=total_cost,
            total_execution_time=total_time,
            agent_count=len(results),
            agent_results=[r.to_dict() for r in results],
        )


class SummarySynthesis(SynthesisStrategy):
    """
    LLM-based summary synthesis.

    Uses LLMGateway to generate a summary of all agent outputs.
    More expensive but produces higher quality synthesis.
    """

    def __init__(self, gateway: LLMGateway, provider: str = "claude"):
        self.gateway = gateway
        self.provider = provider

    async def synthesize(
        self,
        results: list[AgentResult],
        task: str,
        context: Optional[str] = None,
    ) -> SynthesisResult:
        """Synthesize using LLM summary"""
        if not results:
            return SynthesisResult(
                final_answer="No results to synthesize",
                confidence=0,
                consensus_level="deadlock",
                summary="No agent results available",
            )

        # Build synthesis prompt
        prompt = self._build_synthesis_prompt(results, task, context)

        response = await self.gateway.complete(
            provider=self.provider,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )

        # Parse response (simple extraction)
        content = response["content"]

        # Aggregate metrics
        total_cost = sum(r.cost_usd for r in results) + response["cost"]
        total_time = sum(r.execution_time_seconds for r in results)

        return SynthesisResult(
            final_answer=content,
            confidence=70,  # Default for summary
            consensus_level="moderate",
            summary=content[:500],
            total_cost_usd=total_cost,
            total_execution_time=total_time,
            agent_count=len(results),
            agent_results=[r.to_dict() for r in results],
        )

    def _build_synthesis_prompt(
        self,
        results: list[AgentResult],
        task: str,
        context: Optional[str],
    ) -> str:
        """Build prompt for synthesis"""
        prompt = f"## Task\n{task}\n\n"

        if context:
            prompt += f"## Context\n{context}\n\n"

        prompt += "## Agent Results\n\n"

        for result in results:
            prompt += f"### {result.agent_name} ({result.role.value})\n"
            prompt += f"**Confidence:** {result.confidence}%\n"
            prompt += f"**Answer:** {result.answer}\n"
            prompt += f"**Reasoning:** {result.reasoning}\n\n"

        prompt += """
## Instructions

Synthesize the above agent results into a unified response:
1. Identify the consensus view
2. Note any significant dissenting opinions
3. Provide a clear recommendation
4. Highlight key insights

Be concise and actionable.
"""

        return prompt


class ChairmanSynthesis(SynthesisStrategy):
    """
    Chairman-style synthesis (from AI Arena).

    Uses a dedicated "Chairman" agent to review all responses
    and produce an authoritative final judgment.
    """

    CHAIRMAN_PROMPT = """You are the Chairman of an AI council.

Your role is to:
1. Review all agent responses objectively
2. Weigh evidence and arguments from each perspective
3. Identify areas of consensus and disagreement
4. Synthesize a final, authoritative judgment
5. Acknowledge minority views when they have merit

Be decisive but fair. Your judgment should be actionable.

Respond with JSON:
```json
{
    "final_answer": "Your authoritative conclusion",
    "confidence": 85,
    "consensus_level": "strong|moderate|weak|deadlock",
    "summary": "2-3 sentence executive summary",
    "key_insights": ["Insight 1", "Insight 2"],
    "dissenting_views": ["Notable disagreement"],
    "recommendation": "Clear next step",
    "follow_up_questions": ["Question to explore further"]
}
```
"""

    def __init__(self, gateway: LLMGateway, provider: str = "claude"):
        self.gateway = gateway
        self.provider = provider

    async def synthesize(
        self,
        results: list[AgentResult],
        task: str,
        context: Optional[str] = None,
    ) -> SynthesisResult:
        """Synthesize using Chairman agent"""
        import json

        if not results:
            return SynthesisResult(
                final_answer="No results to synthesize",
                confidence=0,
                consensus_level="deadlock",
                summary="No agent results available",
            )

        # Build Chairman prompt
        prompt = self._build_chairman_prompt(results, task, context)

        response = await self.gateway.complete(
            provider=self.provider,
            messages=[
                {"role": "system", "content": self.CHAIRMAN_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
        )

        # Parse JSON response
        content = response["content"]
        try:
            # Extract JSON from response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(content[json_start:json_end])
            else:
                parsed = {}
        except json.JSONDecodeError:
            parsed = {}

        # Aggregate metrics
        total_cost = sum(r.cost_usd for r in results) + response["cost"]
        total_time = sum(r.execution_time_seconds for r in results)

        return SynthesisResult(
            final_answer=parsed.get("final_answer", content),
            confidence=parsed.get("confidence", 70),
            consensus_level=parsed.get("consensus_level", "moderate"),
            summary=parsed.get("summary", content[:500]),
            key_insights=parsed.get("key_insights", []),
            dissenting_views=parsed.get("dissenting_views", []),
            recommendation=parsed.get("recommendation", ""),
            follow_up_questions=parsed.get("follow_up_questions", []),
            total_cost_usd=total_cost,
            total_execution_time=total_time,
            agent_count=len(results),
            agent_results=[r.to_dict() for r in results],
        )

    def _build_chairman_prompt(
        self,
        results: list[AgentResult],
        task: str,
        context: Optional[str],
    ) -> str:
        """Build prompt for Chairman review"""
        prompt = f"## Original Task\n{task}\n\n"

        if context:
            prompt += f"## Context\n{context}\n\n"

        prompt += "## Council Member Responses\n\n"

        for result in results:
            prompt += f"### {result.agent_name} ({result.role.value})\n"
            prompt += f"**Confidence:** {result.confidence}%\n"
            prompt += f"**Environment:** {result.environment}\n"
            if result.sandbox_id:
                prompt += f"**Sandbox:** {result.sandbox_id}\n"
            prompt += f"**Answer:** {result.answer}\n"
            prompt += f"**Reasoning:** {result.reasoning}\n"
            if result.evidence:
                prompt += f"**Evidence:** {', '.join(result.evidence[:3])}\n"
            prompt += "\n"

        prompt += "\n## Your Task\n\nReview all responses and provide your Chairman synthesis."

        return prompt
```

---

### File: `backend/libs/agent_framework/executor.py`

```python
"""
Main AgentExecutor - the unified entry point.

This is what application code uses to run agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, TYPE_CHECKING

import structlog

from .agents import AgentResult, UnifiedAgent
from .environments import (
    ExecutionEnvironment,
    ExecutionContext,
    LocalExecutor,
    SandboxExecutor,
)
from .synthesis import (
    SynthesisStrategy,
    SynthesisResult,
    ChairmanSynthesis,
    VotingSynthesis,
    SummarySynthesis,
)
from .compute import ComputeGateway

if TYPE_CHECKING:
    from libs.llm_gateway import LLMGateway

logger = structlog.get_logger(__name__)


class SynthesisMode(str, Enum):
    """Available synthesis strategies"""
    CHAIRMAN = "chairman"  # LLM-based authoritative synthesis
    VOTING = "voting"      # Simple vote counting
    SUMMARY = "summary"    # LLM-based summary
    NONE = "none"          # Return raw results


@dataclass
class ExecutionConfig:
    """Configuration for agent execution"""

    environment: ExecutionEnvironment = ExecutionEnvironment.LOCAL
    max_concurrent: int = 3

    # Synthesis
    synthesis_mode: SynthesisMode = SynthesisMode.CHAIRMAN
    synthesis_provider: str = "claude"

    # For sandbox execution
    repo_url: Optional[str] = None
    branch: Optional[str] = None
    sandbox_template: str = "base"

    # Cost limits
    max_cost_usd: Optional[float] = None

    metadata: dict = field(default_factory=dict)


class AgentExecutor:
    """
    Unified Agent Execution Framework.

    Runs agents in parallel across different execution environments
    (local or sandboxed) and synthesizes their results.

    Example:
        from libs.agent_framework import AgentExecutor, ExecutionConfig
        from libs.llm_gateway import LLMGateway

        gateway = LLMGateway()
        executor = AgentExecutor(gateway)

        # Run locally (like current AI Arena)
        result = await executor.execute(
            agents=my_agents,
            task="Validate this hypothesis",
            config=ExecutionConfig(environment="local"),
        )

        # Run in sandboxes (isolated E2B containers)
        result = await executor.execute(
            agents=my_agents,
            task="Fix the failing tests",
            config=ExecutionConfig(
                environment="sandbox",
                repo_url="https://github.com/user/repo",
                branch="main",
            ),
        )
    """

    def __init__(
        self,
        gateway: LLMGateway,
        compute: Optional[ComputeGateway] = None,
    ):
        """
        Initialize executor.

        Args:
            gateway: LLMGateway for LLM calls and local execution
            compute: Optional ComputeGateway for sandbox execution
        """
        self.gateway = gateway
        self.compute = compute or ComputeGateway()

        # Initialize executors
        self._local_executor = LocalExecutor(gateway)
        self._sandbox_executor = SandboxExecutor(self.compute)

        # Initialize synthesis strategies
        self._synthesis_strategies: dict[SynthesisMode, SynthesisStrategy] = {
            SynthesisMode.CHAIRMAN: ChairmanSynthesis(gateway),
            SynthesisMode.VOTING: VotingSynthesis(),
            SynthesisMode.SUMMARY: SummarySynthesis(gateway),
        }

        logger.info(
            "agent_executor_initialized",
            compute_backends=self.compute.available_backends(),
        )

    async def execute(
        self,
        agents: list[UnifiedAgent],
        task: str,
        config: Optional[ExecutionConfig] = None,
        context: Optional[str] = None,
    ) -> SynthesisResult:
        """
        Execute agents and synthesize results.

        Args:
            agents: List of agents to execute
            task: The task/question to process
            config: Execution configuration
            context: Optional additional context

        Returns:
            SynthesisResult with combined output
        """
        if config is None:
            config = ExecutionConfig()

        logger.info(
            "execution_started",
            agent_count=len(agents),
            environment=config.environment.value,
            synthesis=config.synthesis_mode.value,
        )

        # Build execution context
        exec_context = ExecutionContext(
            environment=config.environment,
            task=task,
            context=context,
            repo_url=config.repo_url,
            branch=config.branch,
            sandbox_template=config.sandbox_template,
        )

        # Execute agents based on environment
        if config.environment == ExecutionEnvironment.LOCAL:
            results = await self._local_executor.execute_parallel(
                agents=agents,
                context=exec_context,
                max_concurrent=config.max_concurrent,
            )
        elif config.environment == ExecutionEnvironment.SANDBOX:
            results = await self._sandbox_executor.execute_parallel(
                agents=agents,
                context=exec_context,
                max_concurrent=config.max_concurrent,
            )
        else:
            raise ValueError(f"Unknown environment: {config.environment}")

        logger.info(
            "execution_completed",
            successful=len([r for r in results if r.confidence > 0]),
            failed=len([r for r in results if r.confidence == 0]),
        )

        # Synthesize results
        if config.synthesis_mode == SynthesisMode.NONE:
            # Return raw results without synthesis
            return SynthesisResult(
                final_answer="See individual agent results",
                confidence=0,
                consensus_level="none",
                summary="No synthesis performed",
                agent_results=[r.to_dict() for r in results],
                agent_count=len(results),
                total_cost_usd=sum(r.cost_usd for r in results),
                total_execution_time=sum(r.execution_time_seconds for r in results),
            )

        strategy = self._synthesis_strategies.get(config.synthesis_mode)
        if not strategy:
            raise ValueError(f"Unknown synthesis mode: {config.synthesis_mode}")

        synthesis_result = await strategy.synthesize(
            results=results,
            task=task,
            context=context,
        )

        logger.info(
            "synthesis_completed",
            consensus=synthesis_result.consensus_level,
            confidence=synthesis_result.confidence,
            total_cost=synthesis_result.total_cost_usd,
        )

        return synthesis_result

    async def execute_single(
        self,
        agent: UnifiedAgent,
        task: str,
        config: Optional[ExecutionConfig] = None,
        context: Optional[str] = None,
    ) -> AgentResult:
        """
        Execute a single agent (no synthesis needed).

        Convenience method for simple single-agent tasks.
        """
        if config is None:
            config = ExecutionConfig()

        exec_context = ExecutionContext(
            environment=config.environment,
            task=task,
            context=context,
            repo_url=config.repo_url,
            branch=config.branch,
            sandbox_template=config.sandbox_template,
        )

        if config.environment == ExecutionEnvironment.LOCAL:
            return await self._local_executor.execute_agent(agent, exec_context)
        elif config.environment == ExecutionEnvironment.SANDBOX:
            return await self._sandbox_executor.execute_agent(agent, exec_context)
        else:
            raise ValueError(f"Unknown environment: {config.environment}")
```

---

## Usage Examples

### Example 1: Migrate AI Arena Hypothesis Validation

```python
# Before (current implementation)
from libs.ai_arena import AgentRegistry, HypothesisValidator

registry = AgentRegistry(gateway)
agents = registry.create_default_team()
validator = HypothesisValidator(agents, llm_gateway=gateway)
result = await validator.validate(hypothesis)

# After (unified framework)
from libs.agent_framework import AgentExecutor, ExecutionConfig
from libs.ai_arena import AgentRegistry  # Still use for agent creation

registry = AgentRegistry(gateway)
agents = registry.create_default_team()  # Returns UnifiedAgent instances

executor = AgentExecutor(gateway)
result = await executor.execute(
    agents=agents,
    task=hypothesis.to_debate_question(),
    context=hypothesis.context,
    config=ExecutionConfig(
        environment="local",
        synthesis_mode="chairman",
    ),
)
```

### Example 2: Run Research with Optional Sandbox Isolation

```python
from libs.agent_framework import AgentExecutor, ExecutionConfig, ExecutionEnvironment

executor = AgentExecutor(gateway)

# Standard local research (fast, cheap)
result = await executor.execute(
    agents=research_agents,
    task="Research GraphQL vs REST for our API",
    config=ExecutionConfig(
        environment=ExecutionEnvironment.LOCAL,
        synthesis_mode="summary",
    ),
)

# Sandboxed research with code execution (isolated, thorough)
result = await executor.execute(
    agents=research_agents,
    task="Clone the repo and analyze the API design, suggest improvements",
    config=ExecutionConfig(
        environment=ExecutionEnvironment.SANDBOX,
        repo_url="https://github.com/company/api",
        branch="main",
        synthesis_mode="chairman",
    ),
)
```

### Example 3: Parallel Sandbox Forks (Replaces obox)

```python
from libs.agent_framework import AgentExecutor, ExecutionConfig

executor = AgentExecutor(gateway)

# Create N identical agents for parallel experimentation
agents = [
    create_fix_agent(f"fixer-{i}")
    for i in range(5)
]

result = await executor.execute(
    agents=agents,
    task="Fix the failing tests in different ways, create PRs",
    config=ExecutionConfig(
        environment="sandbox",
        repo_url="https://github.com/company/repo",
        branch="fix-tests",
        max_concurrent=5,
        synthesis_mode="voting",  # Pick the best approach
    ),
)

print(f"Best approach: {result.final_answer}")
print(f"Artifacts: {result.agent_results}")
```

---

## Migration Path

### Phase 1: Create Framework (Week 1)
- [ ] Create `backend/libs/agent_framework/` with all files above
- [ ] Add unit tests for each component
- [ ] Verify E2B backend works in isolation

### Phase 2: Migrate AI Arena (Week 2)
- [ ] Make `BaseAgent` extend `UnifiedAgent`
- [ ] Update `HypothesisValidator` to use `AgentExecutor`
- [ ] Verify all AI Arena tests pass

### Phase 3: Migrate Research Orchestrator (Week 2)
- [ ] Update `ResearchAgent` to extend `UnifiedAgent`
- [ ] Replace `ResearchAgentOrchestrator` with `AgentExecutor`
- [ ] Add sandbox option to research workflows

### Phase 4: Deprecate obox (Week 3)
- [ ] Create migration docs for obox users
- [ ] Provide equivalent `AgentExecutor` patterns
- [ ] Mark `tools/agent-sandboxes/apps/sandbox_workflows/` as deprecated

---

---

## Settings UI: Compute Backend Configuration

Following the existing pattern for LLM providers, add compute backend settings.

### Backend: New Model

**File: `backend/app/models/settings.py`** (add to existing)

```python
class ComputeBackend(Base):
    """Compute backend configuration (E2B, Docker, Modal, etc.)"""

    __tablename__ = "compute_backends"

    id = Column(Integer, primary_key=True)
    alias = Column(String(50), unique=True, nullable=False)  # "e2b", "docker", "modal"
    backend_type = Column(String(50), nullable=False)  # ComputeBackendType enum value
    display_name = Column(String(100), nullable=False)  # "E2B Cloud Sandboxes"

    # Configuration
    api_key_env = Column(String(100), nullable=True)  # "E2B_API_KEY"
    api_key_encrypted = Column(Text, nullable=True)  # Encrypted API key
    api_base = Column(String(255), nullable=True)  # Custom API endpoint

    # Default template/image
    default_template = Column(String(100), default="base")

    # Resource defaults
    default_timeout_seconds = Column(Integer, default=600)
    default_memory_mb = Column(Integer, default=2048)
    max_concurrent = Column(Integer, default=5)

    # Cost tracking
    cost_per_minute = Column(Float, default=0.0)  # USD per sandbox-minute

    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Which backend to use by default

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExecutionEnvironmentConfig(Base):
    """Per-workflow execution environment preferences"""

    __tablename__ = "execution_environment_configs"

    id = Column(Integer, primary_key=True)
    workflow_type = Column(String(50), unique=True, nullable=False)  # "hypothesis", "research", "sandbox_fork"

    # Environment selection
    environment = Column(String(20), default="local")  # "local" or "sandbox"
    compute_backend_id = Column(Integer, ForeignKey("compute_backends.id"), nullable=True)

    # Override defaults
    max_concurrent = Column(Integer, nullable=True)
    timeout_seconds = Column(Integer, nullable=True)
    template = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Backend: Settings Service Extension

**File: `backend/app/services/settings_service.py`** (add methods)

```python
# Default compute backends to seed
DEFAULT_COMPUTE_BACKENDS = [
    {
        "alias": "e2b",
        "backend_type": "e2b",
        "display_name": "E2B Cloud Sandboxes",
        "api_key_env": "E2B_API_KEY",
        "default_template": "base",
        "cost_per_minute": 0.10,
        "is_default": True,
    },
    {
        "alias": "docker-local",
        "backend_type": "docker",
        "display_name": "Local Docker",
        "api_key_env": None,
        "default_template": "python:3.11",
        "cost_per_minute": 0.0,
        "is_default": False,
    },
]

# Default execution configs
DEFAULT_EXECUTION_CONFIGS = [
    {"workflow_type": "hypothesis", "environment": "local", "max_concurrent": 4},
    {"workflow_type": "research", "environment": "local", "max_concurrent": 3},
    {"workflow_type": "sandbox_fork", "environment": "sandbox", "max_concurrent": 5},
]


class SettingsService:
    # ... existing methods ...

    # --- Compute Backend CRUD ---

    def list_compute_backends(self, active_only: bool = False) -> list[ComputeBackend]:
        """List all compute backends."""
        query = self.db.query(ComputeBackend)
        if active_only:
            query = query.filter(ComputeBackend.is_active == True)
        return query.order_by(ComputeBackend.alias).all()

    def get_compute_backend(self, alias: str) -> ComputeBackend | None:
        """Get compute backend by alias."""
        return self.db.query(ComputeBackend).filter(ComputeBackend.alias == alias).first()

    def get_default_compute_backend(self) -> ComputeBackend | None:
        """Get the default compute backend."""
        return self.db.query(ComputeBackend).filter(ComputeBackend.is_default == True).first()

    def set_default_compute_backend(self, alias: str) -> ComputeBackend:
        """Set a backend as the default."""
        # Clear existing default
        self.db.query(ComputeBackend).update({ComputeBackend.is_default: False})

        # Set new default
        backend = self.get_compute_backend(alias)
        if backend:
            backend.is_default = True
            self.db.commit()
            self.db.refresh(backend)
        return backend

    def update_compute_backend(self, alias: str, **kwargs) -> ComputeBackend | None:
        """Update compute backend settings."""
        backend = self.get_compute_backend(alias)
        if not backend:
            return None

        for key, value in kwargs.items():
            if hasattr(backend, key) and key not in ("id", "alias", "created_at"):
                setattr(backend, key, value)

        self.db.commit()
        self.db.refresh(backend)
        return backend

    # --- Execution Environment Config ---

    def get_execution_config(self, workflow_type: str) -> ExecutionEnvironmentConfig | None:
        """Get execution config for a workflow type."""
        return self.db.query(ExecutionEnvironmentConfig).filter(
            ExecutionEnvironmentConfig.workflow_type == workflow_type
        ).first()

    def set_execution_config(
        self,
        workflow_type: str,
        environment: str,
        compute_backend_alias: str | None = None,
        **kwargs
    ) -> ExecutionEnvironmentConfig:
        """Set execution environment for a workflow type."""
        config = self.get_execution_config(workflow_type)

        # Get backend ID if alias provided
        backend_id = None
        if compute_backend_alias:
            backend = self.get_compute_backend(compute_backend_alias)
            if backend:
                backend_id = backend.id

        if config:
            config.environment = environment
            config.compute_backend_id = backend_id
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        else:
            config = ExecutionEnvironmentConfig(
                workflow_type=workflow_type,
                environment=environment,
                compute_backend_id=backend_id,
                **kwargs
            )
            self.db.add(config)

        self.db.commit()
        self.db.refresh(config)
        return config

    def list_execution_configs(self) -> list[ExecutionEnvironmentConfig]:
        """List all execution environment configurations."""
        return self.db.query(ExecutionEnvironmentConfig).order_by(
            ExecutionEnvironmentConfig.workflow_type
        ).all()
```

### Backend: New API Endpoints

**File: `backend/app/routers/settings.py`** (add to existing)

```python
# ============================================================================
# Compute Backend Endpoints
# ============================================================================

class ComputeBackendInfo(BaseModel):
    """Compute backend status info"""
    alias: str
    backend_type: str
    display_name: str
    api_key_env: Optional[str]
    configured: bool
    is_active: bool
    is_default: bool
    default_template: str
    cost_per_minute: float
    max_concurrent: int


class ComputeBackendUpdate(BaseModel):
    """Update compute backend settings"""
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    default_template: Optional[str] = None
    default_timeout_seconds: Optional[int] = None
    max_concurrent: Optional[int] = None


@router.get("/compute-backends")
async def list_compute_backends() -> dict:
    """
    List all compute backends and their configuration status.
    """
    session = get_sync_session()
    try:
        service = SettingsService(session)
        backends = service.list_compute_backends()
        env_vars = read_env_file()

        result = []
        for backend in backends:
            # Check if API key is configured
            configured = True
            if backend.api_key_env:
                value = env_vars.get(backend.api_key_env) or os.environ.get(backend.api_key_env)
                configured = bool(value)

            result.append(ComputeBackendInfo(
                alias=backend.alias,
                backend_type=backend.backend_type,
                display_name=backend.display_name,
                api_key_env=backend.api_key_env,
                configured=configured,
                is_active=backend.is_active,
                is_default=backend.is_default,
                default_template=backend.default_template,
                cost_per_minute=backend.cost_per_minute,
                max_concurrent=backend.max_concurrent,
            ))

        return {"backends": result}
    finally:
        session.close()


@router.put("/compute-backends/{alias}")
async def update_compute_backend(alias: str, request: ComputeBackendUpdate) -> dict:
    """
    Update compute backend settings.
    """
    session = get_sync_session()
    try:
        service = SettingsService(session)

        updates = request.dict(exclude_none=True)

        # Handle is_default specially
        if updates.get("is_default"):
            service.set_default_compute_backend(alias)
            del updates["is_default"]

        if updates:
            backend = service.update_compute_backend(alias, **updates)
            if not backend:
                raise HTTPException(status_code=404, detail=f"Backend {alias} not found")

        backend = service.get_compute_backend(alias)
        return {
            "alias": backend.alias,
            "is_default": backend.is_default,
            "is_active": backend.is_active,
            "default_template": backend.default_template,
        }
    finally:
        session.close()


# ============================================================================
# Execution Environment Endpoints
# ============================================================================

class ExecutionConfigInfo(BaseModel):
    """Execution environment config"""
    workflow_type: str
    environment: str  # "local" or "sandbox"
    compute_backend: Optional[str]  # Backend alias if sandbox
    max_concurrent: Optional[int]
    timeout_seconds: Optional[int]


class ExecutionConfigUpdate(BaseModel):
    """Update execution config"""
    environment: str = Field(..., pattern="^(local|sandbox)$")
    compute_backend: Optional[str] = None
    max_concurrent: Optional[int] = None
    timeout_seconds: Optional[int] = None


@router.get("/execution-configs")
async def list_execution_configs() -> dict:
    """
    List execution environment configuration for all workflow types.
    """
    session = get_sync_session()
    try:
        service = SettingsService(session)
        configs = service.list_execution_configs()

        result = []
        for config in configs:
            backend_alias = None
            if config.compute_backend_id:
                # Get backend alias
                backend = session.query(ComputeBackend).get(config.compute_backend_id)
                if backend:
                    backend_alias = backend.alias

            result.append(ExecutionConfigInfo(
                workflow_type=config.workflow_type,
                environment=config.environment,
                compute_backend=backend_alias,
                max_concurrent=config.max_concurrent,
                timeout_seconds=config.timeout_seconds,
            ))

        return {"configs": result}
    finally:
        session.close()


@router.put("/execution-configs/{workflow_type}")
async def set_execution_config(workflow_type: str, request: ExecutionConfigUpdate) -> dict:
    """
    Set execution environment for a workflow type.

    Workflow types: hypothesis, research, sandbox_fork
    """
    valid_workflows = ["hypothesis", "research", "sandbox_fork"]
    if workflow_type not in valid_workflows:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid workflow type. Valid: {valid_workflows}"
        )

    session = get_sync_session()
    try:
        service = SettingsService(session)

        # Validate backend if sandbox environment
        if request.environment == "sandbox" and request.compute_backend:
            backend = service.get_compute_backend(request.compute_backend)
            if not backend:
                raise HTTPException(
                    status_code=400,
                    detail=f"Compute backend '{request.compute_backend}' not found"
                )

        config = service.set_execution_config(
            workflow_type=workflow_type,
            environment=request.environment,
            compute_backend_alias=request.compute_backend,
            max_concurrent=request.max_concurrent,
            timeout_seconds=request.timeout_seconds,
        )

        return {
            "workflow_type": config.workflow_type,
            "environment": config.environment,
            "message": "Configuration updated"
        }
    finally:
        session.close()
```

### Frontend: Compute Settings Component

**File: `frontend/src/components/Settings/ComputeSettings.tsx`** (new)

```tsx
import React, { useState, useEffect } from 'react';
import { Cloud, Server, CheckCircle, XCircle, Settings2 } from 'lucide-react';

interface ComputeBackend {
  alias: string;
  backend_type: string;
  display_name: string;
  api_key_env: string | null;
  configured: boolean;
  is_active: boolean;
  is_default: boolean;
  default_template: string;
  cost_per_minute: number;
  max_concurrent: number;
}

interface ExecutionConfig {
  workflow_type: string;
  environment: 'local' | 'sandbox';
  compute_backend: string | null;
  max_concurrent: number | null;
}

const WORKFLOW_LABELS: Record<string, string> = {
  hypothesis: 'Hypothesis Validation (AI Arena)',
  research: 'Research Orchestration',
  sandbox_fork: 'Parallel Agent Forks',
};

export const ComputeSettings: React.FC = () => {
  const [backends, setBackends] = useState<ComputeBackend[]>([]);
  const [configs, setConfigs] = useState<ExecutionConfig[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [backendsRes, configsRes] = await Promise.all([
        fetch('/api/v1/settings/compute-backends'),
        fetch('/api/v1/settings/execution-configs'),
      ]);

      const backendsData = await backendsRes.json();
      const configsData = await configsRes.json();

      setBackends(backendsData.backends || []);
      setConfigs(configsData.configs || []);
    } catch (error) {
      console.error('Failed to fetch compute settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateExecutionConfig = async (
    workflowType: string,
    environment: 'local' | 'sandbox',
    computeBackend?: string
  ) => {
    try {
      await fetch(`/api/v1/settings/execution-configs/${workflowType}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          environment,
          compute_backend: environment === 'sandbox' ? computeBackend : null,
        }),
      });

      // Refresh data
      fetchData();
    } catch (error) {
      console.error('Failed to update config:', error);
    }
  };

  const setDefaultBackend = async (alias: string) => {
    try {
      await fetch(`/api/v1/settings/compute-backends/${alias}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_default: true }),
      });

      fetchData();
    } catch (error) {
      console.error('Failed to set default backend:', error);
    }
  };

  if (loading) {
    return <div className="text-slate-400">Loading compute settings...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Compute Backends */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Cloud className="text-primary-600" size={24} />
          <h2 className="text-xl font-bold">Compute Backends</h2>
        </div>
        <p className="text-sm text-slate-400 mb-4">
          Configure where isolated agent execution runs. API keys are managed in the backend .env file.
        </p>

        <div className="space-y-3">
          {backends.map((backend) => (
            <div
              key={backend.alias}
              className={`flex items-center justify-between p-4 border rounded-lg ${
                backend.is_default
                  ? 'border-primary-500 bg-primary-900/20'
                  : 'border-slate-700'
              }`}
            >
              <div className="flex items-center gap-3">
                {backend.configured ? (
                  <CheckCircle className="text-green-500" size={20} />
                ) : (
                  <XCircle className="text-red-500" size={20} />
                )}
                <div>
                  <div className="font-medium text-white flex items-center gap-2">
                    {backend.display_name}
                    {backend.is_default && (
                      <span className="text-xs bg-primary-600 px-2 py-0.5 rounded">
                        Default
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-500">
                    {backend.api_key_env || 'No API key required'} ·
                    ${backend.cost_per_minute.toFixed(2)}/min ·
                    Max {backend.max_concurrent} concurrent
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {backend.configured ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Ready
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    Not Configured
                  </span>
                )}

                {!backend.is_default && backend.configured && (
                  <button
                    onClick={() => setDefaultBackend(backend.alias)}
                    className="text-xs text-primary-400 hover:text-primary-300"
                  >
                    Set Default
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Workflow Execution Environment */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Settings2 className="text-primary-600" size={24} />
          <h2 className="text-xl font-bold">Workflow Execution</h2>
        </div>
        <p className="text-sm text-slate-400 mb-4">
          Choose where each workflow type runs agents. "Local" runs in the backend process.
          "Sandbox" runs in isolated cloud containers.
        </p>

        <div className="space-y-4">
          {configs.map((config) => (
            <div
              key={config.workflow_type}
              className="p-4 border border-slate-700 rounded-lg"
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <div className="font-medium text-white">
                    {WORKFLOW_LABELS[config.workflow_type] || config.workflow_type}
                  </div>
                  <div className="text-xs text-slate-500">
                    {config.environment === 'sandbox' && config.compute_backend
                      ? `Using ${config.compute_backend}`
                      : 'In-process execution'}
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => updateExecutionConfig(config.workflow_type, 'local')}
                  className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition ${
                    config.environment === 'local'
                      ? 'bg-primary-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  <Server className="inline-block mr-1" size={16} />
                  Local
                </button>

                <button
                  onClick={() => {
                    const defaultBackend = backends.find(b => b.is_default && b.configured);
                    if (defaultBackend) {
                      updateExecutionConfig(config.workflow_type, 'sandbox', defaultBackend.alias);
                    }
                  }}
                  disabled={!backends.some(b => b.configured)}
                  className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition ${
                    config.environment === 'sandbox'
                      ? 'bg-primary-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600 disabled:opacity-50'
                  }`}
                >
                  <Cloud className="inline-block mr-1" size={16} />
                  Sandbox
                </button>
              </div>

              {config.environment === 'sandbox' && (
                <div className="mt-3">
                  <label className="block text-xs text-slate-400 mb-1">
                    Compute Backend
                  </label>
                  <select
                    value={config.compute_backend || ''}
                    onChange={(e) => updateExecutionConfig(
                      config.workflow_type,
                      'sandbox',
                      e.target.value
                    )}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded text-sm text-white"
                  >
                    {backends
                      .filter(b => b.configured)
                      .map(b => (
                        <option key={b.alias} value={b.alias}>
                          {b.display_name}
                        </option>
                      ))
                    }
                  </select>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
```

### Frontend: Add to Settings View

**File: `frontend/src/components/Settings/SettingsView.tsx`** (modify)

```tsx
import { ComputeSettings } from './ComputeSettings';

export const SettingsView: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Existing API Key Management */}
      {/* ... */}

      {/* NEW: Compute Backend Settings */}
      <ComputeSettings />

      {/* Existing Repository Management */}
      {/* ... */}
    </div>
  );
};
```

### UI Mockup

```
┌────────────────────────────────────────────────────────────────────┐
│  ☁️  Compute Backends                                              │
├────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ ✓  E2B Cloud Sandboxes                        [Default]    │   │
│  │     E2B_API_KEY · $0.10/min · Max 5 concurrent    [Ready]  │   │
│  └────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ ✓  Local Docker                          [Set Default]     │   │
│  │     No API key required · $0.00/min · Max 3       [Ready]  │   │
│  └────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ ✗  Modal (Coming Soon)                                     │   │
│  │     MODAL_TOKEN_ID · $0.05/min               [Not Config]  │   │
│  └────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  ⚙️  Workflow Execution                                            │
├────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Hypothesis Validation (AI Arena)                           │   │
│  │ In-process execution                                       │   │
│  │ ┌─────────────────┐ ┌─────────────────┐                   │   │
│  │ │ 🖥️  Local       │ │ ☁️  Sandbox     │                   │   │
│  │ │   [SELECTED]    │ │                 │                   │   │
│  │ └─────────────────┘ └─────────────────┘                   │   │
│  └────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Parallel Agent Forks                                       │   │
│  │ Using e2b                                                  │   │
│  │ ┌─────────────────┐ ┌─────────────────┐                   │   │
│  │ │ 🖥️  Local       │ │ ☁️  Sandbox     │                   │   │
│  │ │                 │ │   [SELECTED]    │                   │   │
│  │ └─────────────────┘ └─────────────────┘                   │   │
│  │ Compute Backend: [E2B Cloud Sandboxes    ▼]               │   │
│  └────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

---

## Definition of Done

- [ ] Single `AgentExecutor` handles all parallel agent work
- [ ] Sandbox execution works via `ExecutionEnvironment.SANDBOX`
- [ ] AI Arena hypothesis validation unchanged from user perspective
- [ ] Research orchestration unchanged from user perspective
- [ ] E2B is swappable (just change backend config)
- [ ] All existing tests pass
- [ ] Cost tracking unified across all execution modes
- [ ] Prometheus metrics work for both local and sandbox execution

---

## Notes

- This replaces the 5-phase full integration plan with a cleaner approach
- No new database tables needed (agents store results in existing models)
- No new API endpoints needed (existing APIs work with new framework)
- UI changes minimal (add environment toggle where needed)
- E2B becomes an implementation detail, not a first-class concept
