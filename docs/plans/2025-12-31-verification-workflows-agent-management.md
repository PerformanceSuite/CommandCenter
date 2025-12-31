# Plan Addition: Verification Workflows & Agent Management UI

**Added**: 2025-12-31
**Status**: 🟡 Draft
**Extends**: `docs/plans/2025-12-31-unified-agent-framework.md`

---

## Overview

This addition covers three interconnected features:

1. **VerificationWorkflow** - Arena-style Assess → Challenge → Arbitrate → Learn
2. **Agent/Persona Management UI** - Create, edit, manage agent definitions
3. **Prompt Improver** - AI-assisted prompt refinement to prevent conflicts and improve clarity

These build on top of the AgentExecutor to provide a complete self-improving assessment system.

---

## Part 1: Verification Workflow

### Concept

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      VERIFICATION WORKFLOW                               │
│                                                                         │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────────┐    │
│   │ ASSESS  │ →  │CHALLENGE│ →  │ ARBITRATE│ →  │ LEARN (KB/Skills)│   │
│   └─────────┘    └─────────┘    └─────────┘    └─────────────────┘    │
│       │              │              │                  │               │
│       ▼              ▼              ▼                  ▼               │
│   Parallel      "Prove it"     Synthesize        Update KB with       │
│   domain        scrutiny of    surviving         verified facts,      │
│   assessments   each claim     facts             update Skills with   │
│                                                  methodology fixes     │
└─────────────────────────────────────────────────────────────────────────┘
```

### File: `backend/libs/agent_framework/workflows/verification.py`

```python
"""
Verification Workflow - Arena-style assessment with dialectic validation.

Pattern: Assess → Challenge → Arbitrate → Learn
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

import structlog

from ..executor import AgentExecutor, ExecutionConfig, SynthesisMode
from ..agents import AgentResult, UnifiedAgent, AgentRole
from ..environments import ExecutionEnvironment
from ..synthesis import SynthesisResult

if TYPE_CHECKING:
    from app.services.knowledgebeast_service import KnowledgeBeastService

logger = structlog.get_logger(__name__)


class VerificationPhase(str, Enum):
    """Phases of verification workflow"""
    ASSESS = "assess"
    CHALLENGE = "challenge"
    ARBITRATE = "arbitrate"
    LEARN = "learn"


@dataclass
class VerifiedFact:
    """A fact that survived the verification process"""
    claim: str
    original_source: str  # Which assessment agent
    challenger_verdict: str  # "verified", "partial", "refuted"
    evidence: list[str]
    confidence: int  # 0-100
    methodology_used: str

    def to_dict(self) -> dict:
        return {
            "claim": self.claim,
            "source": self.original_source,
            "verdict": self.challenger_verdict,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "methodology": self.methodology_used,
        }


@dataclass
class MethodologyImprovement:
    """A lesson learned about how to do assessments better"""
    category: str  # "counting", "definition", "blind_spot", "prompt"
    description: str
    before: str  # What was done
    after: str  # What should be done
    affected_agents: list[str]

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "description": self.description,
            "before": self.before,
            "after": self.after,
            "affected_agents": self.affected_agents,
        }


@dataclass
class VerificationResult:
    """Complete result of a verification workflow"""

    # Summary
    original_task: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Phase results
    assessment_results: list[AgentResult] = field(default_factory=list)
    challenge_results: list[AgentResult] = field(default_factory=list)
    arbitration_result: Optional[SynthesisResult] = None

    # Verified outputs
    verified_facts: list[VerifiedFact] = field(default_factory=list)
    refuted_claims: list[dict] = field(default_factory=list)
    methodology_improvements: list[MethodologyImprovement] = field(default_factory=list)

    # Metrics
    total_cost_usd: float = 0.0
    total_duration_seconds: float = 0.0

    # For KB storage
    kb_entries_created: int = 0
    skills_updated: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task": self.original_task,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "verified_facts": [f.to_dict() for f in self.verified_facts],
            "refuted_claims": self.refuted_claims,
            "methodology_improvements": [m.to_dict() for m in self.methodology_improvements],
            "metrics": {
                "total_cost_usd": self.total_cost_usd,
                "duration_seconds": self.total_duration_seconds,
                "kb_entries": self.kb_entries_created,
                "skills_updated": self.skills_updated,
            },
        }


class VerificationWorkflow:
    """
    Arena-style verification workflow.

    Runs a complete Assess → Challenge → Arbitrate → Learn cycle.

    Example:
        workflow = VerificationWorkflow(
            executor=executor,
            kb_service=kb_service,
        )

        result = await workflow.run(
            task="Assess the health of CommandCenter",
            assessment_agents=domain_agents,
            challenger_agent=challenger,
            arbiter_agent=arbiter,
            repo_url="https://github.com/org/repo",
        )

        print(f"Verified facts: {len(result.verified_facts)}")
        print(f"Methodology improvements: {len(result.methodology_improvements)}")
    """

    def __init__(
        self,
        executor: AgentExecutor,
        kb_service: Optional[KnowledgeBeastService] = None,
        skills_path: str = "~/.claude/skills",
    ):
        self.executor = executor
        self.kb_service = kb_service
        self.skills_path = skills_path

    async def run(
        self,
        task: str,
        assessment_agents: list[UnifiedAgent],
        challenger_agent: UnifiedAgent,
        arbiter_agent: UnifiedAgent,
        repo_url: Optional[str] = None,
        branch: str = "main",
        environment: ExecutionEnvironment = ExecutionEnvironment.SANDBOX,
        auto_learn: bool = True,
    ) -> VerificationResult:
        """
        Run complete verification workflow.

        Args:
            task: What to assess
            assessment_agents: Domain expert agents (Backend, Frontend, etc.)
            challenger_agent: Agent that challenges claims
            arbiter_agent: Agent that synthesizes final verdict
            repo_url: Repository to assess (for sandbox execution)
            branch: Git branch
            environment: Where to run agents
            auto_learn: Whether to automatically update KB and skills

        Returns:
            VerificationResult with verified facts and learnings
        """
        result = VerificationResult(
            original_task=task,
            started_at=datetime.utcnow(),
        )

        logger.info(
            "verification_workflow_started",
            task=task[:100],
            assessors=len(assessment_agents),
            environment=environment.value,
        )

        # Phase 1: ASSESS
        logger.info("phase_started", phase="assess")
        assessment_synthesis = await self._run_assessment(
            task=task,
            agents=assessment_agents,
            repo_url=repo_url,
            branch=branch,
            environment=environment,
        )
        result.assessment_results = [
            AgentResult(**r) for r in assessment_synthesis.agent_results
        ]
        result.total_cost_usd += assessment_synthesis.total_cost_usd

        # Phase 2: CHALLENGE
        logger.info("phase_started", phase="challenge")
        challenge_result = await self._run_challenge(
            challenger=challenger_agent,
            assessment_claims=self._extract_claims(assessment_synthesis),
            repo_url=repo_url,
            branch=branch,
            environment=environment,
        )
        result.challenge_results = [challenge_result]
        result.total_cost_usd += challenge_result.cost_usd

        # Phase 3: ARBITRATE
        logger.info("phase_started", phase="arbitrate")
        arbitration = await self._run_arbitration(
            arbiter=arbiter_agent,
            assessment_synthesis=assessment_synthesis,
            challenge_result=challenge_result,
        )
        result.arbitration_result = arbitration
        result.total_cost_usd += arbitration.total_cost_usd

        # Parse arbitration into structured outputs
        verified, refuted, improvements = self._parse_arbitration(arbitration)
        result.verified_facts = verified
        result.refuted_claims = refuted
        result.methodology_improvements = improvements

        # Phase 4: LEARN
        if auto_learn:
            logger.info("phase_started", phase="learn")
            kb_count, skills_updated = await self._apply_learnings(result)
            result.kb_entries_created = kb_count
            result.skills_updated = skills_updated

        result.completed_at = datetime.utcnow()
        result.total_duration_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()

        logger.info(
            "verification_workflow_completed",
            verified_facts=len(result.verified_facts),
            refuted_claims=len(result.refuted_claims),
            improvements=len(result.methodology_improvements),
            cost=result.total_cost_usd,
            duration=result.total_duration_seconds,
        )

        return result

    async def _run_assessment(
        self,
        task: str,
        agents: list[UnifiedAgent],
        repo_url: Optional[str],
        branch: str,
        environment: ExecutionEnvironment,
    ) -> SynthesisResult:
        """Phase 1: Run parallel assessment agents"""

        config = ExecutionConfig(
            environment=environment,
            repo_url=repo_url,
            branch=branch,
            max_concurrent=len(agents),  # All in parallel
            synthesis_mode=SynthesisMode.SUMMARY,  # Combine assessments
        )

        return await self.executor.execute(
            agents=agents,
            task=task,
            config=config,
        )

    async def _run_challenge(
        self,
        challenger: UnifiedAgent,
        assessment_claims: str,
        repo_url: Optional[str],
        branch: str,
        environment: ExecutionEnvironment,
    ) -> AgentResult:
        """Phase 2: Challenge the assessment claims"""

        challenge_task = f"""
## Assessment Claims to Challenge

{assessment_claims}

## Your Task

For EACH claim above:
1. Demand methodology - "How was this counted/determined?"
2. Verify independently - Run your own commands to check
3. Find blind spots - What did they miss?
4. Check for contradictions - Do claims conflict with each other?

Output your findings as JSON:
```json
{{
    "verified_claims": [
        {{"claim": "...", "my_evidence": "...", "confidence": 95}}
    ],
    "refuted_claims": [
        {{"claim": "...", "actual": "...", "methodology_error": "..."}}
    ],
    "partial_claims": [
        {{"claim": "...", "correct_part": "...", "incorrect_part": "..."}}
    ],
    "methodology_issues": [
        {{"issue": "...", "recommendation": "..."}}
    ],
    "blind_spots": [
        {{"missed": "...", "importance": "high|medium|low"}}
    ]
}}
```
"""

        config = ExecutionConfig(
            environment=environment,
            repo_url=repo_url,
            branch=branch,
            synthesis_mode=SynthesisMode.NONE,
        )

        return await self.executor.execute_single(
            agent=challenger,
            task=challenge_task,
            config=config,
        )

    async def _run_arbitration(
        self,
        arbiter: UnifiedAgent,
        assessment_synthesis: SynthesisResult,
        challenge_result: AgentResult,
    ) -> SynthesisResult:
        """Phase 3: Arbiter synthesizes final verdict"""

        context = f"""
## Original Assessment Summary

{assessment_synthesis.summary}

### Key Findings from Assessors
{json.dumps(assessment_synthesis.key_insights, indent=2)}

## Challenger's Verification

{challenge_result.answer}

### Challenger's Confidence: {challenge_result.confidence}%
"""

        arbiter_task = """
As the Arbiter, synthesize the assessment and challenge into:

1. **Verified Facts** - Claims that survived challenge scrutiny
2. **Refuted Claims** - Claims that failed verification
3. **Methodology Improvements** - How to do better next time

Output as JSON:
```json
{
    "verdict": "Assessment is X% accurate",
    "verified_facts": [
        {
            "claim": "...",
            "evidence": ["..."],
            "confidence": 95,
            "methodology": "How this was verified"
        }
    ],
    "refuted_claims": [
        {
            "original_claim": "...",
            "actual_finding": "...",
            "why_wrong": "..."
        }
    ],
    "methodology_improvements": [
        {
            "category": "counting|definition|blind_spot|prompt",
            "description": "...",
            "before": "What was done",
            "after": "What should be done"
        }
    ],
    "recommendations": ["..."]
}
```
"""

        config = ExecutionConfig(
            environment=ExecutionEnvironment.LOCAL,  # Arbiter doesn't need sandbox
            synthesis_mode=SynthesisMode.CHAIRMAN,
        )

        return await self.executor.execute(
            agents=[arbiter],
            task=arbiter_task,
            context=context,
            config=config,
        )

    def _extract_claims(self, synthesis: SynthesisResult) -> str:
        """Extract claims from assessment for challenger to verify"""
        claims = []

        for i, result in enumerate(synthesis.agent_results):
            claims.append(f"### Agent: {result.get('agent_name', f'Agent {i+1}')}")
            claims.append(f"Role: {result.get('role', 'unknown')}")
            claims.append(f"Confidence: {result.get('confidence', 'N/A')}%")
            claims.append(f"Claims:\n{result.get('answer', '')[:2000]}")
            claims.append("")

        return "\n".join(claims)

    def _parse_arbitration(
        self,
        arbitration: SynthesisResult,
    ) -> tuple[list[VerifiedFact], list[dict], list[MethodologyImprovement]]:
        """Parse arbiter output into structured data"""

        verified = []
        refuted = []
        improvements = []

        # Try to parse JSON from arbitration
        try:
            content = arbitration.final_answer
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(content[json_start:json_end])

                for v in data.get("verified_facts", []):
                    verified.append(VerifiedFact(
                        claim=v.get("claim", ""),
                        original_source=v.get("source", "assessment"),
                        challenger_verdict="verified",
                        evidence=v.get("evidence", []),
                        confidence=v.get("confidence", 70),
                        methodology_used=v.get("methodology", ""),
                    ))

                refuted = data.get("refuted_claims", [])

                for m in data.get("methodology_improvements", []):
                    improvements.append(MethodologyImprovement(
                        category=m.get("category", "general"),
                        description=m.get("description", ""),
                        before=m.get("before", ""),
                        after=m.get("after", ""),
                        affected_agents=m.get("affected_agents", []),
                    ))
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("arbitration_parse_failed", error=str(e))

        return verified, refuted, improvements

    async def _apply_learnings(
        self,
        result: VerificationResult,
    ) -> tuple[int, list[str]]:
        """Phase 4: Update KB and Skills with learnings"""

        kb_count = 0
        skills_updated = []

        # Store verified facts in KB
        if self.kb_service:
            for fact in result.verified_facts:
                try:
                    await self.kb_service.add_entry(
                        content=fact.claim,
                        metadata={
                            "type": "verified_fact",
                            "source": fact.original_source,
                            "confidence": fact.confidence,
                            "evidence": fact.evidence,
                            "verified_at": datetime.utcnow().isoformat(),
                        },
                    )
                    kb_count += 1
                except Exception as e:
                    logger.error("kb_entry_failed", error=str(e))

        # Update skills with methodology improvements
        for improvement in result.methodology_improvements:
            try:
                skill_name = self._get_skill_for_improvement(improvement)
                if skill_name:
                    await self._update_skill(skill_name, improvement)
                    skills_updated.append(skill_name)
            except Exception as e:
                logger.error("skill_update_failed", error=str(e))

        return kb_count, skills_updated

    def _get_skill_for_improvement(self, improvement: MethodologyImprovement) -> Optional[str]:
        """Map improvement category to skill name"""
        category_to_skill = {
            "counting": "project-assessment",
            "definition": "project-assessment",
            "blind_spot": "project-assessment",
            "prompt": "agent-prompts",
        }
        return category_to_skill.get(improvement.category)

    async def _update_skill(
        self,
        skill_name: str,
        improvement: MethodologyImprovement,
    ) -> None:
        """Append improvement to skill's learnings section"""
        import os
        from pathlib import Path

        skill_path = Path(os.path.expanduser(self.skills_path)) / skill_name / "SKILL.md"

        if not skill_path.exists():
            logger.warning("skill_not_found", skill=skill_name)
            return

        # Append to learnings section
        learning_entry = f"""
### Learning: {improvement.description}
- **Category**: {improvement.category}
- **Before**: {improvement.before}
- **After**: {improvement.after}
- **Recorded**: {datetime.utcnow().isoformat()}
"""

        with open(skill_path, "a") as f:
            f.write(f"\n{learning_entry}")

        logger.info("skill_updated", skill=skill_name, improvement=improvement.description)
```

---

## Part 2: Agent/Persona Management

### Data Models

**File: `backend/app/models/agent_persona.py`** (new)

```python
"""
Agent Persona models - Reusable agent definitions.

Personas define WHO an agent is (role, personality, expertise).
Agent Configs define HOW an agent executes (model, environment, parameters).
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship

from app.database import Base


class PersonaCategory(str, Enum):
    """Categories of agent personas"""
    ASSESSMENT = "assessment"      # Domain expert assessors
    VERIFICATION = "verification"  # Challengers, validators
    SYNTHESIS = "synthesis"        # Arbiters, summarizers
    RESEARCH = "research"          # Research agents
    CODING = "coding"              # Code-focused agents
    CUSTOM = "custom"


class AgentPersona(Base):
    """
    Reusable agent persona definition.

    A persona defines the "who" - role, expertise, personality, constraints.
    Think of it as a character sheet for an AI agent.
    """
    __tablename__ = "agent_personas"

    id = Column(Integer, primary_key=True)

    # Identity
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(PersonaCategory), default=PersonaCategory.CUSTOM)

    # The core prompt
    system_prompt = Column(Text, nullable=False)

    # Prompt metadata (for improver)
    prompt_version = Column(Integer, default=1)
    prompt_last_improved = Column(DateTime, nullable=True)
    prompt_improvement_notes = Column(Text, nullable=True)

    # Execution hints
    suggested_model = Column(String(50), default="claude")  # LLM provider alias
    suggested_temperature = Column(Float, default=0.7)
    suggested_max_tokens = Column(Integer, default=4096)
    requires_sandbox = Column(Boolean, default=False)

    # For code-focused personas
    preferred_languages = Column(JSON, default=list)  # ["python", "typescript"]
    tool_permissions = Column(JSON, default=list)  # ["filesystem", "git", "web_search"]

    # Organization
    tags = Column(JSON, default=list)
    is_builtin = Column(Boolean, default=False)  # True for system-provided personas
    is_active = Column(Boolean, default=True)

    # Audit
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workflow_assignments = relationship("WorkflowAgentAssignment", back_populates="persona")


class WorkflowTemplate(Base):
    """
    Reusable workflow template.

    Defines a sequence of agent executions with synthesis strategy.
    """
    __tablename__ = "workflow_templates"

    id = Column(Integer, primary_key=True)

    # Identity
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Workflow type
    workflow_type = Column(String(50), nullable=False)  # "verification", "research", "parallel_fork"

    # Execution settings
    default_environment = Column(String(20), default="local")  # "local" or "sandbox"
    default_synthesis_mode = Column(String(50), default="chairman")
    max_concurrent_agents = Column(Integer, default=5)

    # For repo-based workflows
    requires_repo = Column(Boolean, default=False)
    default_branch = Column(String(100), default="main")

    # Cost controls
    max_cost_usd = Column(Float, nullable=True)
    max_duration_minutes = Column(Integer, nullable=True)

    # Organization
    tags = Column(JSON, default=list)
    is_builtin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Audit
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent_assignments = relationship("WorkflowAgentAssignment", back_populates="workflow")


class WorkflowAgentAssignment(Base):
    """
    Assigns personas to workflow steps.

    Defines which agents run in which phase of a workflow.
    """
    __tablename__ = "workflow_agent_assignments"

    id = Column(Integer, primary_key=True)

    workflow_id = Column(Integer, ForeignKey("workflow_templates.id"), nullable=False)
    persona_id = Column(Integer, ForeignKey("agent_personas.id"), nullable=False)

    # Step configuration
    step_order = Column(Integer, nullable=False)  # 1, 2, 3...
    step_name = Column(String(100), nullable=False)  # "assess", "challenge", "arbitrate"

    # Execution mode for this step
    execution_mode = Column(String(20), default="parallel")  # "parallel" or "sequential"

    # Override persona defaults
    override_model = Column(String(50), nullable=True)
    override_temperature = Column(Float, nullable=True)
    override_max_tokens = Column(Integer, nullable=True)
    override_environment = Column(String(20), nullable=True)

    # Task template (with placeholders)
    task_template = Column(Text, nullable=True)  # "Assess {repo_name} focusing on {domain}"

    # Relationships
    workflow = relationship("WorkflowTemplate", back_populates="agent_assignments")
    persona = relationship("AgentPersona", back_populates="workflow_assignments")
```

### Built-in Personas

**File: `backend/app/services/persona_service.py`**

```python
"""
Service for managing agent personas and workflows.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.agent_persona import (
    AgentPersona, PersonaCategory,
    WorkflowTemplate, WorkflowAgentAssignment
)


# Built-in personas to seed on first run
BUILTIN_PERSONAS = [
    # Assessment Personas
    {
        "name": "backend-assessor",
        "display_name": "Backend Assessor",
        "description": "Expert in backend architecture, APIs, databases, and services.",
        "category": PersonaCategory.ASSESSMENT,
        "system_prompt": """You are a Backend Assessment Expert.

Your expertise includes:
- API design and REST/GraphQL patterns
- Database schema and query optimization
- Service architecture and microservices
- Authentication, authorization, security
- Performance and scalability

When assessing a codebase:
1. Count and catalog all API endpoints, services, and models
2. Evaluate architecture patterns and code organization
3. Identify security concerns and tech debt
4. Assess test coverage and code quality
5. Provide specific, actionable recommendations

Always show your methodology. For counts, show the exact commands used.
Output findings in structured JSON format.""",
        "suggested_model": "claude",
        "requires_sandbox": True,
        "preferred_languages": ["python", "javascript", "go"],
        "tags": ["assessment", "backend", "api"],
        "is_builtin": True,
    },
    {
        "name": "frontend-assessor",
        "display_name": "Frontend Assessor",
        "description": "Expert in frontend architecture, React, components, and UX.",
        "category": PersonaCategory.ASSESSMENT,
        "system_prompt": """You are a Frontend Assessment Expert.

Your expertise includes:
- React/Vue/Angular component architecture
- State management patterns
- CSS/styling approaches
- Build tooling and bundling
- Accessibility and performance

When assessing a codebase:
1. Catalog all components, hooks, and routes
2. Evaluate component reusability and code sharing
3. Check for accessibility issues
4. Assess bundle size and performance
5. Review testing coverage

Always show your methodology with specific file paths and counts.
Output findings in structured JSON format.""",
        "suggested_model": "claude",
        "requires_sandbox": True,
        "preferred_languages": ["typescript", "javascript"],
        "tags": ["assessment", "frontend", "react"],
        "is_builtin": True,
    },

    # Verification Personas
    {
        "name": "challenger",
        "display_name": "Challenger Agent",
        "description": "Critical reviewer that stress-tests claims through dialectic scrutiny.",
        "category": PersonaCategory.VERIFICATION,
        "system_prompt": """You are a Challenger Agent - a critical reviewer.

Your role is NOT to redo work, but to CHALLENGE claims through:
1. Demanding methodology - "How did you count this?"
2. Probing blind spots - "Did you check X?"
3. Finding contradictions - "You said A but also B"
4. Requesting evidence - "Show me the command/path/proof"
5. Independent verification - Run your own checks

You are adversarial but FAIR. Goal is TRUTH, not winning.

For each claim:
- What was the methodology?
- What might have been missed?
- Can you reproduce the finding?
- What's the confidence level?

Output as JSON with verified_claims, refuted_claims, methodology_issues.""",
        "suggested_model": "claude",
        "requires_sandbox": True,
        "tags": ["verification", "challenger", "critic"],
        "is_builtin": True,
    },
    {
        "name": "arbiter",
        "display_name": "Arbiter Agent",
        "description": "Synthesizes assessment and challenge into authoritative verdict.",
        "category": PersonaCategory.SYNTHESIS,
        "system_prompt": """You are the Arbiter - the final authority.

Given assessment claims and challenger verification, you:
1. Determine which facts SURVIVED scrutiny (verified)
2. Identify claims that FAILED verification (refuted)
3. Extract METHODOLOGY improvements for future assessments
4. Provide clear RECOMMENDATIONS

Your verdict is AUTHORITATIVE. Be decisive but acknowledge uncertainty.

Output as JSON:
{
    "verdict": "Overall assessment accuracy",
    "verified_facts": [...],
    "refuted_claims": [...],
    "methodology_improvements": [...],
    "recommendations": [...]
}""",
        "suggested_model": "claude",
        "requires_sandbox": False,  # Arbiter works with text, not code
        "tags": ["synthesis", "arbiter", "verdict"],
        "is_builtin": True,
    },
]


BUILTIN_WORKFLOWS = [
    {
        "name": "project-verification",
        "display_name": "Project Verification Workflow",
        "description": "Full Assess → Challenge → Arbitrate → Learn cycle for project health.",
        "workflow_type": "verification",
        "default_environment": "sandbox",
        "default_synthesis_mode": "chairman",
        "requires_repo": True,
        "tags": ["verification", "assessment", "health"],
        "is_builtin": True,
        "steps": [
            {
                "step_order": 1,
                "step_name": "assess",
                "persona_name": "backend-assessor",
                "execution_mode": "parallel",
            },
            {
                "step_order": 1,  # Same order = parallel
                "step_name": "assess",
                "persona_name": "frontend-assessor",
                "execution_mode": "parallel",
            },
            {
                "step_order": 2,
                "step_name": "challenge",
                "persona_name": "challenger",
                "execution_mode": "sequential",
            },
            {
                "step_order": 3,
                "step_name": "arbitrate",
                "persona_name": "arbiter",
                "execution_mode": "sequential",
            },
        ],
    },
]


class PersonaService:
    """Service for managing personas and workflows"""

    def __init__(self, db: Session):
        self.db = db

    async def seed_builtins(self):
        """Seed built-in personas and workflows"""

        # Create personas
        for persona_data in BUILTIN_PERSONAS:
            existing = self.db.query(AgentPersona).filter(
                AgentPersona.name == persona_data["name"]
            ).first()

            if not existing:
                persona = AgentPersona(**persona_data)
                self.db.add(persona)

        self.db.commit()

        # Create workflows
        for workflow_data in BUILTIN_WORKFLOWS:
            steps = workflow_data.pop("steps", [])

            existing = self.db.query(WorkflowTemplate).filter(
                WorkflowTemplate.name == workflow_data["name"]
            ).first()

            if not existing:
                workflow = WorkflowTemplate(**workflow_data)
                self.db.add(workflow)
                self.db.commit()

                # Add steps
                for step in steps:
                    persona = self.db.query(AgentPersona).filter(
                        AgentPersona.name == step["persona_name"]
                    ).first()

                    if persona:
                        assignment = WorkflowAgentAssignment(
                            workflow_id=workflow.id,
                            persona_id=persona.id,
                            step_order=step["step_order"],
                            step_name=step["step_name"],
                            execution_mode=step["execution_mode"],
                        )
                        self.db.add(assignment)

                self.db.commit()

    # CRUD operations
    def list_personas(
        self,
        category: Optional[PersonaCategory] = None,
        active_only: bool = True,
    ) -> list[AgentPersona]:
        query = self.db.query(AgentPersona)
        if category:
            query = query.filter(AgentPersona.category == category)
        if active_only:
            query = query.filter(AgentPersona.is_active == True)
        return query.order_by(AgentPersona.name).all()

    def get_persona(self, name: str) -> Optional[AgentPersona]:
        return self.db.query(AgentPersona).filter(AgentPersona.name == name).first()

    def create_persona(self, **kwargs) -> AgentPersona:
        persona = AgentPersona(**kwargs)
        self.db.add(persona)
        self.db.commit()
        self.db.refresh(persona)
        return persona

    def update_persona(self, name: str, **kwargs) -> Optional[AgentPersona]:
        persona = self.get_persona(name)
        if not persona:
            return None

        for key, value in kwargs.items():
            if hasattr(persona, key) and key not in ("id", "name", "is_builtin", "created_at"):
                setattr(persona, key, value)

        self.db.commit()
        self.db.refresh(persona)
        return persona

    def list_workflows(self, active_only: bool = True) -> list[WorkflowTemplate]:
        query = self.db.query(WorkflowTemplate)
        if active_only:
            query = query.filter(WorkflowTemplate.is_active == True)
        return query.order_by(WorkflowTemplate.name).all()

    def get_workflow(self, name: str) -> Optional[WorkflowTemplate]:
        return self.db.query(WorkflowTemplate).filter(
            WorkflowTemplate.name == name
        ).first()
```

---

## Part 3: Prompt Improver

### Concept

The Prompt Improver analyzes agent prompts and suggests improvements:

1. **Conflict Detection** - Find contradictory instructions
2. **Clarity Enhancement** - Make instructions more specific
3. **Structure Optimization** - Add missing sections (output format, constraints)
4. **AI-Friendliness** - Rewrite for better LLM comprehension

### File: `backend/libs/agent_framework/prompt_improver.py`

```python
"""
Prompt Improver - AI-assisted prompt refinement.

Analyzes prompts for conflicts, ambiguity, and suboptimal patterns.
Suggests improvements to make prompts more effective.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from libs.llm_gateway import LLMGateway

logger = structlog.get_logger(__name__)


class IssueType(str, Enum):
    """Types of prompt issues"""
    CONFLICT = "conflict"           # Contradictory instructions
    AMBIGUITY = "ambiguity"         # Unclear instructions
    MISSING_OUTPUT = "missing_output"  # No output format specified
    MISSING_CONSTRAINTS = "missing_constraints"  # No guardrails
    VERBOSITY = "verbosity"         # Too wordy
    STRUCTURE = "structure"         # Poor organization
    SCOPE = "scope"                 # Scope creep or unclear boundaries


class Severity(str, Enum):
    """Issue severity"""
    HIGH = "high"       # Will likely cause problems
    MEDIUM = "medium"   # May cause inconsistent results
    LOW = "low"         # Minor improvement opportunity


@dataclass
class PromptIssue:
    """An identified issue in a prompt"""
    issue_type: IssueType
    severity: Severity
    description: str
    location: str  # Which part of the prompt
    suggestion: str

    def to_dict(self) -> dict:
        return {
            "type": self.issue_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "location": self.location,
            "suggestion": self.suggestion,
        }


@dataclass
class PromptAnalysis:
    """Complete analysis of a prompt"""
    original_prompt: str
    issues: list[PromptIssue] = field(default_factory=list)

    # Scores (0-100)
    clarity_score: int = 0
    structure_score: int = 0
    completeness_score: int = 0
    overall_score: int = 0

    # Improved version
    improved_prompt: Optional[str] = None
    improvement_summary: str = ""

    def to_dict(self) -> dict:
        return {
            "issues": [i.to_dict() for i in self.issues],
            "scores": {
                "clarity": self.clarity_score,
                "structure": self.structure_score,
                "completeness": self.completeness_score,
                "overall": self.overall_score,
            },
            "improved_prompt": self.improved_prompt,
            "improvement_summary": self.improvement_summary,
        }


ANALYZER_PROMPT = """You are a Prompt Engineering Expert.

Analyze the following prompt for an AI agent and identify issues.

## Prompt to Analyze

```
{prompt}
```

## Analysis Tasks

1. **Conflict Detection**: Find any contradictory instructions
   - Example: "Be concise" vs "Provide detailed explanations"
   - Example: "Never ask questions" vs "Clarify unclear requests"

2. **Ambiguity Check**: Find vague or unclear instructions
   - Example: "Do a good job" (what defines good?)
   - Example: "Handle edge cases" (which ones?)

3. **Structure Review**: Check organization
   - Is there a clear role definition?
   - Are responsibilities clearly listed?
   - Is there an output format specification?
   - Are there constraints/guardrails?

4. **Completeness Check**: What's missing?
   - Error handling instructions?
   - Edge case guidance?
   - Output format specification?
   - Success criteria?

5. **Verbosity Check**: Can anything be more concise?
   - Redundant instructions?
   - Overly wordy sections?

## Output Format

Respond with JSON:
```json
{
    "issues": [
        {
            "type": "conflict|ambiguity|missing_output|missing_constraints|verbosity|structure|scope",
            "severity": "high|medium|low",
            "description": "What the issue is",
            "location": "Which section/lines",
            "suggestion": "How to fix it"
        }
    ],
    "scores": {
        "clarity": 0-100,
        "structure": 0-100,
        "completeness": 0-100,
        "overall": 0-100
    },
    "improvement_summary": "Brief summary of main improvements needed"
}
```
"""

IMPROVER_PROMPT = """You are a Prompt Engineering Expert.

Given a prompt and its issues, create an improved version.

## Original Prompt

```
{prompt}
```

## Identified Issues

{issues}

## Improvement Guidelines

1. **Resolve all conflicts** - Choose one clear direction
2. **Clarify ambiguities** - Be specific and concrete
3. **Add missing structure**:
   - Clear role definition at top
   - Numbered responsibilities
   - Explicit output format
   - Constraints/guardrails section
4. **Reduce verbosity** - Every word should earn its place
5. **Maintain intent** - Don't change what the prompt is trying to do

## Output

Provide ONLY the improved prompt, no explanation needed.
The improved prompt should be ready to use as-is.
"""


class PromptImprover:
    """
    Analyzes and improves agent prompts.

    Example:
        improver = PromptImprover(gateway)

        analysis = await improver.analyze(my_prompt)
        print(f"Score: {analysis.overall_score}")
        print(f"Issues: {len(analysis.issues)}")

        if analysis.overall_score < 80:
            improved = await improver.improve(my_prompt)
            print(f"Improved prompt: {improved.improved_prompt}")
    """

    def __init__(
        self,
        gateway: LLMGateway,
        provider: str = "claude",
    ):
        self.gateway = gateway
        self.provider = provider

    async def analyze(self, prompt: str) -> PromptAnalysis:
        """
        Analyze a prompt for issues.

        Returns analysis with issues and scores, but no improved version.
        """
        import json

        analysis_request = ANALYZER_PROMPT.format(prompt=prompt)

        response = await self.gateway.complete(
            provider=self.provider,
            messages=[{"role": "user", "content": analysis_request}],
            temperature=0.3,
            max_tokens=2000,
        )

        content = response["content"]

        # Parse JSON response
        analysis = PromptAnalysis(original_prompt=prompt)

        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(content[json_start:json_end])

                for issue_data in data.get("issues", []):
                    analysis.issues.append(PromptIssue(
                        issue_type=IssueType(issue_data.get("type", "ambiguity")),
                        severity=Severity(issue_data.get("severity", "medium")),
                        description=issue_data.get("description", ""),
                        location=issue_data.get("location", ""),
                        suggestion=issue_data.get("suggestion", ""),
                    ))

                scores = data.get("scores", {})
                analysis.clarity_score = scores.get("clarity", 70)
                analysis.structure_score = scores.get("structure", 70)
                analysis.completeness_score = scores.get("completeness", 70)
                analysis.overall_score = scores.get("overall", 70)
                analysis.improvement_summary = data.get("improvement_summary", "")

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("prompt_analysis_parse_failed", error=str(e))
            analysis.overall_score = 50
            analysis.improvement_summary = "Analysis parsing failed"

        return analysis

    async def improve(
        self,
        prompt: str,
        analysis: Optional[PromptAnalysis] = None,
    ) -> PromptAnalysis:
        """
        Analyze and improve a prompt.

        If analysis is not provided, will analyze first.
        Returns analysis with improved_prompt filled in.
        """
        if analysis is None:
            analysis = await self.analyze(prompt)

        # Format issues for improver
        issues_text = "\n".join([
            f"- [{i.severity.value.upper()}] {i.issue_type.value}: {i.description}\n"
            f"  Location: {i.location}\n"
            f"  Suggestion: {i.suggestion}"
            for i in analysis.issues
        ])

        if not issues_text:
            issues_text = "No major issues identified, but general improvements may be possible."

        improve_request = IMPROVER_PROMPT.format(
            prompt=prompt,
            issues=issues_text,
        )

        response = await self.gateway.complete(
            provider=self.provider,
            messages=[{"role": "user", "content": improve_request}],
            temperature=0.3,
            max_tokens=4000,
        )

        analysis.improved_prompt = response["content"].strip()

        # Remove markdown code fences if present
        if analysis.improved_prompt.startswith("```"):
            lines = analysis.improved_prompt.split("\n")
            # Remove first and last lines if they're fences
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            analysis.improved_prompt = "\n".join(lines)

        return analysis

    async def quick_check(self, prompt: str) -> dict:
        """
        Quick check for common issues without full analysis.

        Returns dict with quick findings - useful for real-time feedback.
        """
        findings = {
            "has_role_definition": False,
            "has_output_format": False,
            "has_constraints": False,
            "potential_conflicts": [],
            "word_count": len(prompt.split()),
            "quick_suggestions": [],
        }

        prompt_lower = prompt.lower()

        # Check for role definition
        role_keywords = ["you are", "your role", "act as", "you're a"]
        findings["has_role_definition"] = any(k in prompt_lower for k in role_keywords)

        # Check for output format
        output_keywords = ["output format", "respond with", "return as", "output as", "json", "format:"]
        findings["has_output_format"] = any(k in prompt_lower for k in output_keywords)

        # Check for constraints
        constraint_keywords = ["do not", "don't", "never", "always", "must", "constraint", "rule"]
        findings["has_constraints"] = any(k in prompt_lower for k in constraint_keywords)

        # Quick suggestions
        if not findings["has_role_definition"]:
            findings["quick_suggestions"].append("Add a clear role definition at the start")
        if not findings["has_output_format"]:
            findings["quick_suggestions"].append("Specify the expected output format")
        if findings["word_count"] > 1000:
            findings["quick_suggestions"].append("Consider condensing - prompt is quite long")

        # Check for potential conflicts (simple heuristics)
        conflict_pairs = [
            ("concise", "detailed"),
            ("brief", "comprehensive"),
            ("never ask", "clarify"),
            ("don't explain", "explain your"),
        ]

        for a, b in conflict_pairs:
            if a in prompt_lower and b in prompt_lower:
                findings["potential_conflicts"].append(f"Possible conflict: '{a}' vs '{b}'")

        return findings
```

---

## Part 4: Frontend Components

### Agent Persona Editor

**File: `frontend/src/components/Agents/PersonaEditor.tsx`**

```tsx
import React, { useState, useEffect } from 'react';
import { Bot, Sparkles, AlertTriangle, CheckCircle } from 'lucide-react';
import MonacoEditor from '@monaco-editor/react';

interface PersonaEditorProps {
  persona?: AgentPersona;
  onSave: (persona: Partial<AgentPersona>) => void;
  onCancel: () => void;
}

interface PromptAnalysis {
  issues: Array<{
    type: string;
    severity: string;
    description: string;
    suggestion: string;
  }>;
  scores: {
    clarity: number;
    structure: number;
    completeness: number;
    overall: number;
  };
  improved_prompt?: string;
}

export const PersonaEditor: React.FC<PersonaEditorProps> = ({
  persona,
  onSave,
  onCancel,
}) => {
  const [name, setName] = useState(persona?.name || '');
  const [displayName, setDisplayName] = useState(persona?.display_name || '');
  const [description, setDescription] = useState(persona?.description || '');
  const [category, setCategory] = useState(persona?.category || 'custom');
  const [systemPrompt, setSystemPrompt] = useState(persona?.system_prompt || '');

  const [analysis, setAnalysis] = useState<PromptAnalysis | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [improving, setImproving] = useState(false);
  const [quickCheck, setQuickCheck] = useState<any>(null);

  // Debounced quick check on prompt changes
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (systemPrompt.length > 50) {
        const response = await fetch('/api/v1/agents/prompts/quick-check', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: systemPrompt }),
        });
        const data = await response.json();
        setQuickCheck(data);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [systemPrompt]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const response = await fetch('/api/v1/agents/prompts/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: systemPrompt }),
      });
      const data = await response.json();
      setAnalysis(data);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleImprove = async () => {
    setImproving(true);
    try {
      const response = await fetch('/api/v1/agents/prompts/improve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: systemPrompt }),
      });
      const data = await response.json();
      setAnalysis(data);
    } finally {
      setImproving(false);
    }
  };

  const applyImprovement = () => {
    if (analysis?.improved_prompt) {
      setSystemPrompt(analysis.improved_prompt);
      setAnalysis(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="text-primary-500" size={24} />
          <h2 className="text-xl font-bold">
            {persona ? 'Edit Persona' : 'Create Persona'}
          </h2>
        </div>
      </div>

      {/* Basic Info */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Name (slug)</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value.toLowerCase().replace(/\s+/g, '-'))}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded"
            placeholder="my-custom-agent"
            disabled={persona?.is_builtin}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Display Name</label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded"
            placeholder="My Custom Agent"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded"
          rows={2}
          placeholder="What this agent does..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Category</label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded"
        >
          <option value="assessment">Assessment</option>
          <option value="verification">Verification</option>
          <option value="synthesis">Synthesis</option>
          <option value="research">Research</option>
          <option value="coding">Coding</option>
          <option value="custom">Custom</option>
        </select>
      </div>

      {/* System Prompt Editor */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium">System Prompt</label>
          <div className="flex items-center gap-2">
            {/* Quick Check Indicators */}
            {quickCheck && (
              <div className="flex items-center gap-2 text-xs">
                {quickCheck.has_role_definition ? (
                  <span className="text-green-500">✓ Role</span>
                ) : (
                  <span className="text-yellow-500">⚠ No role</span>
                )}
                {quickCheck.has_output_format ? (
                  <span className="text-green-500">✓ Output</span>
                ) : (
                  <span className="text-yellow-500">⚠ No format</span>
                )}
                <span className="text-slate-400">{quickCheck.word_count} words</span>
              </div>
            )}

            <button
              onClick={handleAnalyze}
              disabled={analyzing || !systemPrompt}
              className="px-3 py-1 text-sm bg-slate-700 rounded hover:bg-slate-600 disabled:opacity-50"
            >
              {analyzing ? 'Analyzing...' : 'Analyze'}
            </button>
            <button
              onClick={handleImprove}
              disabled={improving || !systemPrompt}
              className="px-3 py-1 text-sm bg-primary-600 rounded hover:bg-primary-500 disabled:opacity-50 flex items-center gap-1"
            >
              <Sparkles size={14} />
              {improving ? 'Improving...' : 'Improve'}
            </button>
          </div>
        </div>

        <div className="border border-slate-600 rounded overflow-hidden">
          <MonacoEditor
            height="300px"
            language="markdown"
            theme="vs-dark"
            value={systemPrompt}
            onChange={(value) => setSystemPrompt(value || '')}
            options={{
              minimap: { enabled: false },
              wordWrap: 'on',
              lineNumbers: 'off',
            }}
          />
        </div>

        {/* Quick Check Suggestions */}
        {quickCheck?.quick_suggestions?.length > 0 && (
          <div className="mt-2 p-2 bg-yellow-900/20 border border-yellow-700 rounded text-sm">
            <div className="font-medium text-yellow-500 mb-1">Quick suggestions:</div>
            <ul className="list-disc list-inside text-yellow-300">
              {quickCheck.quick_suggestions.map((s: string, i: number) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Potential Conflicts */}
        {quickCheck?.potential_conflicts?.length > 0 && (
          <div className="mt-2 p-2 bg-red-900/20 border border-red-700 rounded text-sm">
            <div className="font-medium text-red-500 mb-1 flex items-center gap-1">
              <AlertTriangle size={14} />
              Potential conflicts detected:
            </div>
            <ul className="list-disc list-inside text-red-300">
              {quickCheck.potential_conflicts.map((c: string, i: number) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Analysis Results */}
      {analysis && (
        <div className="border border-slate-600 rounded p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Prompt Analysis</h3>
            <div className="flex items-center gap-4">
              <ScoreBadge label="Clarity" score={analysis.scores.clarity} />
              <ScoreBadge label="Structure" score={analysis.scores.structure} />
              <ScoreBadge label="Complete" score={analysis.scores.completeness} />
              <ScoreBadge label="Overall" score={analysis.scores.overall} highlight />
            </div>
          </div>

          {/* Issues */}
          {analysis.issues.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-400">Issues Found:</h4>
              {analysis.issues.map((issue, i) => (
                <div
                  key={i}
                  className={`p-2 rounded text-sm ${
                    issue.severity === 'high'
                      ? 'bg-red-900/20 border border-red-700'
                      : issue.severity === 'medium'
                      ? 'bg-yellow-900/20 border border-yellow-700'
                      : 'bg-slate-800 border border-slate-700'
                  }`}
                >
                  <div className="font-medium">
                    [{issue.severity.toUpperCase()}] {issue.type}: {issue.description}
                  </div>
                  <div className="text-slate-400 mt-1">💡 {issue.suggestion}</div>
                </div>
              ))}
            </div>
          )}

          {/* Improved Version */}
          {analysis.improved_prompt && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-green-400">
                  ✨ Improved Version Available
                </h4>
                <button
                  onClick={applyImprovement}
                  className="px-3 py-1 text-sm bg-green-600 rounded hover:bg-green-500"
                >
                  Apply Improvement
                </button>
              </div>
              <pre className="p-3 bg-slate-900 rounded text-xs overflow-auto max-h-48">
                {analysis.improved_prompt}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-slate-700 rounded hover:bg-slate-600"
        >
          Cancel
        </button>
        <button
          onClick={() => onSave({
            name,
            display_name: displayName,
            description,
            category,
            system_prompt: systemPrompt,
          })}
          disabled={!name || !displayName || !systemPrompt}
          className="px-4 py-2 bg-primary-600 rounded hover:bg-primary-500 disabled:opacity-50"
        >
          Save Persona
        </button>
      </div>
    </div>
  );
};

const ScoreBadge: React.FC<{
  label: string;
  score: number;
  highlight?: boolean;
}> = ({ label, score, highlight }) => {
  const color = score >= 80 ? 'green' : score >= 60 ? 'yellow' : 'red';

  return (
    <div className={`text-center ${highlight ? 'scale-110' : ''}`}>
      <div className={`text-lg font-bold text-${color}-500`}>{score}</div>
      <div className="text-xs text-slate-400">{label}</div>
    </div>
  );
};
```

### Workflow Builder

**File: `frontend/src/components/Agents/WorkflowBuilder.tsx`**

```tsx
import React, { useState, useEffect } from 'react';
import {
  GitBranch, Plus, Trash2, ArrowRight, Settings2,
  Play, Users, Bot
} from 'lucide-react';

interface WorkflowStep {
  id: string;
  step_order: number;
  step_name: string;
  persona_name: string;
  execution_mode: 'parallel' | 'sequential';
}

interface WorkflowBuilderProps {
  workflow?: WorkflowTemplate;
  personas: AgentPersona[];
  onSave: (workflow: Partial<WorkflowTemplate>, steps: WorkflowStep[]) => void;
  onCancel: () => void;
}

export const WorkflowBuilder: React.FC<WorkflowBuilderProps> = ({
  workflow,
  personas,
  onSave,
  onCancel,
}) => {
  const [name, setName] = useState(workflow?.name || '');
  const [displayName, setDisplayName] = useState(workflow?.display_name || '');
  const [description, setDescription] = useState(workflow?.description || '');
  const [workflowType, setWorkflowType] = useState(workflow?.workflow_type || 'verification');
  const [steps, setSteps] = useState<WorkflowStep[]>([]);

  // Group steps by order for visual representation
  const stepGroups = steps.reduce((groups, step) => {
    const order = step.step_order;
    if (!groups[order]) groups[order] = [];
    groups[order].push(step);
    return groups;
  }, {} as Record<number, WorkflowStep[]>);

  const addStep = (order: number) => {
    const newStep: WorkflowStep = {
      id: `step-${Date.now()}`,
      step_order: order,
      step_name: order === 1 ? 'assess' : order === 2 ? 'challenge' : 'arbitrate',
      persona_name: personas[0]?.name || '',
      execution_mode: order === 1 ? 'parallel' : 'sequential',
    };
    setSteps([...steps, newStep]);
  };

  const removeStep = (id: string) => {
    setSteps(steps.filter(s => s.id !== id));
  };

  const updateStep = (id: string, updates: Partial<WorkflowStep>) => {
    setSteps(steps.map(s => s.id === id ? { ...s, ...updates } : s));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <GitBranch className="text-primary-500" size={24} />
        <h2 className="text-xl font-bold">
          {workflow ? 'Edit Workflow' : 'Create Workflow'}
        </h2>
      </div>

      {/* Basic Info */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Name (slug)</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value.toLowerCase().replace(/\s+/g, '-'))}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded"
            placeholder="my-workflow"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Display Name</label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded"
            placeholder="My Workflow"
          />
        </div>
      </div>

      {/* Workflow Type */}
      <div>
        <label className="block text-sm font-medium mb-1">Workflow Type</label>
        <select
          value={workflowType}
          onChange={(e) => setWorkflowType(e.target.value)}
          className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded"
        >
          <option value="verification">Verification (Assess → Challenge → Arbitrate)</option>
          <option value="research">Research (Parallel exploration)</option>
          <option value="parallel_fork">Parallel Fork (Multiple approaches)</option>
          <option value="custom">Custom</option>
        </select>
      </div>

      {/* Workflow Steps Builder */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium">Workflow Steps</label>
          <button
            onClick={() => addStep(Object.keys(stepGroups).length + 1)}
            className="px-3 py-1 text-sm bg-primary-600 rounded hover:bg-primary-500 flex items-center gap-1"
          >
            <Plus size={14} />
            Add Step
          </button>
        </div>

        {/* Visual Step Builder */}
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <div className="flex items-stretch gap-4 overflow-x-auto">
            {Object.entries(stepGroups)
              .sort(([a], [b]) => Number(a) - Number(b))
              .map(([order, groupSteps], groupIndex) => (
                <React.Fragment key={order}>
                  {groupIndex > 0 && (
                    <div className="flex items-center">
                      <ArrowRight className="text-slate-500" size={24} />
                    </div>
                  )}

                  {/* Step Group */}
                  <div className="flex-shrink-0 w-64 bg-slate-800 border border-slate-600 rounded-lg p-3">
                    <div className="text-xs text-slate-400 mb-2">
                      Step {order}
                      {groupSteps.length > 1 && (
                        <span className="ml-2 text-primary-400">(parallel)</span>
                      )}
                    </div>

                    <div className="space-y-2">
                      {groupSteps.map((step) => (
                        <div
                          key={step.id}
                          className="bg-slate-900 border border-slate-700 rounded p-2"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <select
                              value={step.persona_name}
                              onChange={(e) => updateStep(step.id, { persona_name: e.target.value })}
                              className="flex-1 px-2 py-1 bg-slate-800 border border-slate-600 rounded text-sm"
                            >
                              {personas.map((p) => (
                                <option key={p.name} value={p.name}>
                                  {p.display_name}
                                </option>
                              ))}
                            </select>
                            <button
                              onClick={() => removeStep(step.id)}
                              className="ml-2 p-1 text-red-500 hover:bg-red-900/20 rounded"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>

                          <input
                            type="text"
                            value={step.step_name}
                            onChange={(e) => updateStep(step.id, { step_name: e.target.value })}
                            className="w-full px-2 py-1 bg-slate-800 border border-slate-600 rounded text-xs"
                            placeholder="Step name (e.g., assess)"
                          />
                        </div>
                      ))}

                      {/* Add parallel agent to this step */}
                      <button
                        onClick={() => {
                          const newStep: WorkflowStep = {
                            id: `step-${Date.now()}`,
                            step_order: Number(order),
                            step_name: groupSteps[0]?.step_name || 'step',
                            persona_name: personas[0]?.name || '',
                            execution_mode: 'parallel',
                          };
                          setSteps([...steps, newStep]);
                        }}
                        className="w-full py-1 text-xs text-slate-400 border border-dashed border-slate-600 rounded hover:border-primary-500 hover:text-primary-400"
                      >
                        + Add parallel agent
                      </button>
                    </div>
                  </div>
                </React.Fragment>
              ))}

            {/* Add new step group */}
            <div className="flex items-center">
              {Object.keys(stepGroups).length > 0 && (
                <ArrowRight className="text-slate-500 mr-4" size={24} />
              )}
              <button
                onClick={() => addStep(Object.keys(stepGroups).length + 1)}
                className="w-48 h-full min-h-32 border-2 border-dashed border-slate-600 rounded-lg flex flex-col items-center justify-center gap-2 text-slate-400 hover:border-primary-500 hover:text-primary-400"
              >
                <Plus size={24} />
                <span className="text-sm">Add Step</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-slate-700 rounded hover:bg-slate-600"
        >
          Cancel
        </button>
        <button
          onClick={() => onSave(
            { name, display_name: displayName, description, workflow_type: workflowType },
            steps
          )}
          disabled={!name || !displayName || steps.length === 0}
          className="px-4 py-2 bg-primary-600 rounded hover:bg-primary-500 disabled:opacity-50"
        >
          Save Workflow
        </button>
      </div>
    </div>
  );
};
```

---

## API Endpoints Summary

Add to `backend/app/routers/agents.py`:

```python
# Personas
GET    /api/v1/agents/personas              # List all personas
GET    /api/v1/agents/personas/{name}       # Get persona by name
POST   /api/v1/agents/personas              # Create persona
PUT    /api/v1/agents/personas/{name}       # Update persona
DELETE /api/v1/agents/personas/{name}       # Delete persona

# Workflows
GET    /api/v1/agents/workflows             # List all workflows
GET    /api/v1/agents/workflows/{name}      # Get workflow by name
POST   /api/v1/agents/workflows             # Create workflow
PUT    /api/v1/agents/workflows/{name}      # Update workflow
DELETE /api/v1/agents/workflows/{name}      # Delete workflow
POST   /api/v1/agents/workflows/{name}/run  # Execute workflow

# Prompt Improver
POST   /api/v1/agents/prompts/quick-check   # Quick check (fast)
POST   /api/v1/agents/prompts/analyze       # Full analysis
POST   /api/v1/agents/prompts/improve       # Analyze + improve

# Verification
POST   /api/v1/agents/verify                # Run verification workflow
GET    /api/v1/agents/verify/{id}           # Get verification result
GET    /api/v1/agents/verify/{id}/facts     # Get verified facts
GET    /api/v1/agents/verify/{id}/learnings # Get methodology improvements
```

---

## Migration & Database

Add migration `016_add_agent_personas.py`:

```python
def upgrade():
    # Create agent_personas table
    op.create_table(
        'agent_personas',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('category', sa.String(50)),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('prompt_version', sa.Integer(), default=1),
        sa.Column('prompt_last_improved', sa.DateTime()),
        sa.Column('suggested_model', sa.String(50)),
        sa.Column('suggested_temperature', sa.Float()),
        sa.Column('requires_sandbox', sa.Boolean()),
        sa.Column('preferred_languages', sa.JSON()),
        sa.Column('tool_permissions', sa.JSON()),
        sa.Column('tags', sa.JSON()),
        sa.Column('is_builtin', sa.Boolean()),
        sa.Column('is_active', sa.Boolean()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )

    # Create workflow_templates table
    op.create_table(
        'workflow_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('workflow_type', sa.String(50)),
        sa.Column('default_environment', sa.String(20)),
        sa.Column('default_synthesis_mode', sa.String(50)),
        sa.Column('max_concurrent_agents', sa.Integer()),
        sa.Column('requires_repo', sa.Boolean()),
        sa.Column('tags', sa.JSON()),
        sa.Column('is_builtin', sa.Boolean()),
        sa.Column('is_active', sa.Boolean()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )

    # Create workflow_agent_assignments table
    op.create_table(
        'workflow_agent_assignments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workflow_id', sa.Integer(), sa.ForeignKey('workflow_templates.id')),
        sa.Column('persona_id', sa.Integer(), sa.ForeignKey('agent_personas.id')),
        sa.Column('step_order', sa.Integer()),
        sa.Column('step_name', sa.String(100)),
        sa.Column('execution_mode', sa.String(20)),
        sa.Column('override_model', sa.String(50)),
        sa.Column('override_temperature', sa.Float()),
        sa.Column('task_template', sa.Text()),
    )
```

---

## Definition of Done

### Part 1: Verification Workflow
- [ ] VerificationWorkflow class implemented
- [ ] Assess → Challenge → Arbitrate → Learn flow works
- [ ] KB integration stores verified facts
- [ ] Skills get updated with methodology improvements

### Part 2: Agent/Persona Management
- [ ] AgentPersona model and CRUD
- [ ] WorkflowTemplate model and CRUD
- [ ] Built-in personas seeded on startup
- [ ] Built-in workflows seeded on startup

### Part 3: Prompt Improver
- [ ] Quick check endpoint (real-time feedback)
- [ ] Full analysis endpoint
- [ ] Improvement endpoint
- [ ] Conflict detection working
- [ ] Structure scoring working

### Part 4: Frontend
- [ ] Persona list view
- [ ] Persona editor with Monaco
- [ ] Real-time quick check indicators
- [ ] Full analysis panel
- [ ] Apply improvement button
- [ ] Workflow builder with visual steps
- [ ] Workflow execution trigger

---

## UI Mockup: Agent Management

```
┌────────────────────────────────────────────────────────────────────────────┐
│  🤖 Agent Personas                                          [+ New Persona] │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Assessment                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 🔹 Backend Assessor              Expert in APIs, DBs, services      │  │
│  │    Category: Assessment | Model: claude | Sandbox: Yes    [Edit]    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 🔹 Frontend Assessor             Expert in React, components, UX    │  │
│  │    Category: Assessment | Model: claude | Sandbox: Yes    [Edit]    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  Verification                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 🔹 Challenger Agent              Critical reviewer, stress-tests    │  │
│  │    Category: Verification | Model: claude | Sandbox: Yes  [Edit]    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 🔹 Arbiter Agent                 Final authority, synthesizes       │  │
│  │    Category: Synthesis | Model: claude | Sandbox: No      [Edit]    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│  📋 Workflows                                               [+ New Workflow]│
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Project Verification Workflow                                       │  │
│  │ Full Assess → Challenge → Arbitrate → Learn cycle                   │  │
│  │                                                                     │  │
│  │ ┌─────────┐     ┌─────────┐     ┌─────────┐                        │  │
│  │ │ Backend │     │         │     │         │                        │  │
│  │ │Assessor │ ──▶ │Challenger│ ──▶ │ Arbiter │                        │  │
│  │ │Frontend │     │         │     │         │                        │  │
│  │ │Assessor │     │         │     │         │                        │  │
│  │ └─────────┘     └─────────┘     └─────────┘                        │  │
│  │    Step 1          Step 2          Step 3                          │  │
│  │  (parallel)     (sequential)    (sequential)                       │  │
│  │                                                                     │  │
│  │ [Edit]  [Run ▶]                                                    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

*This plan addition extends the Unified Agent Framework with verification workflows, persona management, and prompt improvement capabilities.*
