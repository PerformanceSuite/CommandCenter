"""
Research Agent Orchestration Service

Multi-agent research system inspired by AgentFlow patterns.
Manages parallel research tasks with AI agents using multi-provider routing.

Based on:
- AgentFlow/config/agents.json - Agent definitions
- AgentFlow/prompts/base.md - Agent prompt templates
- docs/COMMANDCENTER_RESEARCH_WORKFLOW.md - Research workflow spec
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import json

from app.services.ai_router import ai_router, AIProvider
from app.config import settings

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Research agent roles"""

    TECHNOLOGY_SCOUT = "technology_scout"  # Discover new technologies
    DEEP_RESEARCHER = "deep_researcher"  # Comprehensive technology analysis
    COMPARATOR = "comparator"  # Compare technologies side-by-side
    INTEGRATOR = "integrator"  # Integration feasibility assessment
    MONITOR = "monitor"  # Continuous monitoring of technologies


class ResearchAgentStatus(str, Enum):
    """Agent execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchAgent:
    """
    Individual research agent configuration

    Inspired by AgentFlow agent definitions (config/agents.json)
    """

    def __init__(
        self,
        role: AgentRole,
        model: str,
        provider: AIProvider,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.role = role
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.status = ResearchAgentStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def get_system_prompt(self) -> str:
        """
        Get agent-specific system prompt

        Based on AgentFlow prompts/base.md pattern
        """
        base_prompt = """
You are an autonomous research agent in the CommandCenter multi-agent research system.

## Core Principles
1. **Autonomy**: Work independently to research your assigned technology
2. **Quality**: Provide comprehensive, accurate, evidence-based findings
3. **Structure**: Return findings in structured JSON format
4. **Citation**: Include sources for all claims
        """.strip()

        role_prompts = {
            AgentRole.TECHNOLOGY_SCOUT: """
## Your Role: Technology Scout

**Objective**: Discover and evaluate new technologies relevant to the project

**Responsibilities**:
- Search HackerNews, GitHub, arXiv for emerging technologies
- Identify trending technologies in specific domains
- Assess initial relevance and potential impact
- Provide high-level overview with key metrics

**Output Format**:
```json
{
    "technologies": [
        {
            "name": "Technology Name",
            "category": "Domain (audio-dsp, ai-ml, etc.)",
            "description": "Brief overview (2-3 sentences)",
            "why_relevant": "Relevance to project goals",
            "sources": ["URL1", "URL2"],
            "initial_assessment": {
                "relevance_score": 0-100,
                "maturity": "alpha|beta|stable|mature",
                "hype_level": "low|medium|high"
            }
        }
    ]
}
```
            """.strip(),
            AgentRole.DEEP_RESEARCHER: """
## Your Role: Deep Researcher

**Objective**: Conduct comprehensive analysis of a specific technology

**Responsibilities**:
- Technical deep dive (architecture, capabilities, limitations)
- Performance analysis (latency, throughput, resource usage)
- Integration assessment (APIs, SDKs, dependencies)
- Cost analysis (pricing tiers, total cost of ownership)
- Community and ecosystem evaluation

**Output Format**:
```json
{
    "technology": "Technology Name",
    "analysis": {
        "technical": {
            "architecture": "Description",
            "key_features": ["Feature1", "Feature2"],
            "limitations": ["Limitation1", "Limitation2"]
        },
        "performance": {
            "latency_ms": 50,
            "throughput_qps": 1000,
            "benchmark_source": "URL"
        },
        "integration": {
            "difficulty": "trivial|easy|moderate|complex|very_complex",
            "time_estimate_days": 7,
            "dependencies": ["Dep1", "Dep2"],
            "api_quality": "Assessment of API design"
        },
        "cost": {
            "tier": "free|freemium|affordable|moderate|expensive|enterprise",
            "monthly_usd": 99.00,
            "pricing_model": "Description"
        },
        "ecosystem": {
            "github_stars": 15000,
            "last_commit_days_ago": 2,
            "active_contributors": 50,
            "community_size": "small|medium|large"
        }
    },
    "recommendation": {
        "verdict": "adopt|trial|assess|hold",
        "confidence": "low|medium|high",
        "reasoning": "Detailed explanation"
    },
    "sources": ["URL1", "URL2", "URL3"]
}
```
            """.strip(),
            AgentRole.COMPARATOR: """
## Your Role: Technology Comparator

**Objective**: Compare multiple technologies side-by-side

**Responsibilities**:
- Identify key comparison dimensions
- Gather metrics for each technology
- Highlight strengths and weaknesses
- Provide recommendation based on use case

**Output Format**:
```json
{
    "comparison": {
        "technologies": ["Tech1", "Tech2", "Tech3"],
        "dimensions": {
            "performance": {
                "Tech1": {"latency_ms": 50, "throughput_qps": 1000},
                "Tech2": {"latency_ms": 80, "throughput_qps": 800}
            },
            "cost": {
                "Tech1": {"monthly_usd": 99},
                "Tech2": {"monthly_usd": 49}
            },
            "integration": {
                "Tech1": {"difficulty": "easy", "days": 3},
                "Tech2": {"difficulty": "moderate", "days": 7}
            }
        },
        "winner_by_dimension": {
            "performance": "Tech1",
            "cost": "Tech2",
            "integration": "Tech1"
        }
    },
    "recommendation": {
        "primary_choice": "Tech1",
        "reasoning": "Why Tech1 is best for this use case",
        "runner_up": "Tech2",
        "fallback": "If primary choice doesn't work out"
    },
    "sources": ["URL1", "URL2"]
}
```
            """.strip(),
            AgentRole.INTEGRATOR: """
## Your Role: Integration Feasibility Assessor

**Objective**: Evaluate how easily a technology can be integrated into existing systems

**Responsibilities**:
- Analyze integration points and APIs
- Identify potential conflicts or blockers
- Estimate implementation effort
- Create integration roadmap

**Output Format**:
```json
{
    "technology": "Technology Name",
    "integration_assessment": {
        "difficulty": "trivial|easy|moderate|complex|very_complex",
        "estimated_days": 14,
        "phases": [
            {
                "phase": "Setup & Configuration",
                "tasks": ["Task1", "Task2"],
                "duration_days": 2
            }
        ],
        "blockers": [
            {
                "blocker": "Description",
                "severity": "low|medium|high|critical",
                "mitigation": "How to address"
            }
        ],
        "dependencies": ["Existing System 1", "New Dependency 2"]
    },
    "recommendation": "Proceed|Wait|Alternative",
    "sources": ["URL1"]
}
```
            """.strip(),
            AgentRole.MONITOR: """
## Your Role: Technology Monitor

**Objective**: Continuously monitor technologies for updates, issues, and trends

**Responsibilities**:
- Track HackerNews mentions and sentiment
- Monitor GitHub activity (commits, issues, stars)
- Watch for new releases and breaking changes
- Alert on security vulnerabilities

**Output Format**:
```json
{
    "technology": "Technology Name",
    "monitoring_report": {
        "period": "Last 7 days",
        "hackernews": {
            "mentions": 5,
            "avg_score": 120,
            "sentiment": "positive|neutral|negative",
            "top_story": {"title": "...", "url": "..."}
        },
        "github": {
            "new_commits": 42,
            "stars_gained": 150,
            "new_issues": 12,
            "critical_issues": 0,
            "latest_release": {"version": "v1.2.0", "date": "2025-10-05"}
        },
        "alerts": [
            {
                "type": "security|breaking_change|deprecation|opportunity",
                "severity": "low|medium|high|critical",
                "description": "Alert description",
                "action_required": "What to do"
            }
        ]
    },
    "sources": ["URL1", "URL2"]
}
```
            """.strip(),
        }

        return f"{base_prompt}\n\n{role_prompts.get(self.role, '')}"

    async def execute(self, task_prompt: str) -> Dict[str, Any]:
        """
        Execute research task

        Args:
            task_prompt: Specific research question or task

        Returns:
            Research findings as structured dict
        """
        self.status = ResearchAgentStatus.RUNNING
        self.start_time = datetime.utcnow()

        try:
            # Build messages
            system_prompt = self.get_system_prompt()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task_prompt},
            ]

            # Call AI provider
            response = await ai_router.chat_completion(
                messages=messages,
                model=self.model,
                provider=self.provider,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            # Parse JSON response
            content = response["content"]
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, wrap in generic structure
                result = {
                    "raw_response": content,
                    "parse_error": "Agent returned non-JSON response",
                }

            # Add metadata
            result["_metadata"] = {
                "agent_role": self.role.value,
                "model": response["model"],
                "provider": response["provider"],
                "usage": response["usage"],
                "execution_time_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            }

            self.result = result
            self.status = ResearchAgentStatus.COMPLETED
            self.end_time = datetime.utcnow()

            logger.info(f"✅ Agent {self.role.value} completed research task")
            return result

        except Exception as e:
            self.status = ResearchAgentStatus.FAILED
            self.error = str(e)
            self.end_time = datetime.utcnow()
            logger.error(f"❌ Agent {self.role.value} failed: {e}")
            raise


class ResearchAgentOrchestrator:
    """
    Orchestrates multiple research agents in parallel

    Inspired by AgentFlow multi-agent coordination system
    """

    def __init__(self):
        """Initialize orchestrator"""
        self.agents: List[ResearchAgent] = []
        self.default_model = settings.default_model
        self.default_provider = AIProvider(settings.default_ai_provider)

    async def launch_parallel_research(
        self, tasks: List[Dict[str, Any]], max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Launch multiple research agents in parallel

        Args:
            tasks: List of task dicts with 'role', 'prompt', 'model' (optional)
            max_concurrent: Maximum concurrent agents (default 3)

        Returns:
            List of research results

        Example:
            tasks = [
                {"role": "deep_researcher", "prompt": "Research Rust for audio DSP"},
                {"role": "comparator", "prompt": "Compare Rust vs C++ for audio"},
            ]
        """
        # Create agents
        agents = []
        for task_def in tasks:
            agent = ResearchAgent(
                role=AgentRole(task_def["role"]),
                model=task_def.get("model", self.default_model),
                provider=AIProvider(task_def.get("provider", self.default_provider.value)),
                temperature=task_def.get("temperature", 0.7),
                max_tokens=task_def.get("max_tokens", 4096),
            )
            agents.append((agent, task_def["prompt"]))

        # Execute in parallel with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(agent: ResearchAgent, prompt: str):
            async with semaphore:
                return await agent.execute(prompt)

        # Launch all agents
        results = await asyncio.gather(
            *[execute_with_semaphore(agent, prompt) for agent, prompt in agents],
            return_exceptions=True,
        )

        # Filter out exceptions and return results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Agent {agents[i][0].role} failed: {result}")
                successful_results.append(
                    {
                        "error": str(result),
                        "agent_role": agents[i][0].role.value,
                    }
                )
            else:
                successful_results.append(result)

        return successful_results

    async def technology_deep_dive(
        self,
        technology_name: str,
        research_questions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive technology research using multiple agents

        Args:
            technology_name: Technology to research
            research_questions: Optional specific questions

        Returns:
            Consolidated research report
        """
        # Default research workflow
        tasks = [
            {
                "role": "deep_researcher",
                "prompt": f"Conduct comprehensive research on {technology_name}. Include technical analysis, performance benchmarks, integration assessment, and cost analysis.",
            },
            {
                "role": "integrator",
                "prompt": f"Evaluate integration feasibility for {technology_name} in a full-stack web application (FastAPI backend, React frontend). Identify blockers and create implementation roadmap.",
            },
            {
                "role": "monitor",
                "prompt": f"Provide current monitoring report for {technology_name}. Check HackerNews mentions, GitHub activity, recent releases, and any security alerts from the last 7 days.",
            },
        ]

        # Add custom research questions if provided
        if research_questions:
            for question in research_questions:
                tasks.append(
                    {
                        "role": "deep_researcher",
                        "prompt": f"Research {technology_name}: {question}",
                    }
                )

        # Execute research
        results = await self.launch_parallel_research(tasks, max_concurrent=3)

        # Consolidate results
        report = {
            "technology": technology_name,
            "timestamp": datetime.utcnow().isoformat(),
            "research_findings": results,
            "summary": self._generate_summary(results),
        }

        return report

    def _generate_summary(self, results: List[Dict[str, Any]]) -> str:
        """Generate executive summary from agent results"""
        # TODO: Use AI to generate summary from all agent findings
        return (
            f"Research completed with {len(results)} agents. See individual findings for details."
        )


# Global orchestrator instance
research_orchestrator = ResearchAgentOrchestrator()
