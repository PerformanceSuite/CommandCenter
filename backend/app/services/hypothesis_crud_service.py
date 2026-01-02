"""
Hypothesis CRUD Service

Database-backed hypothesis management service for Research Hub intelligence integration.
Replaces the in-memory hypothesis service with persistent storage.

Features:
- Full CRUD for hypotheses under research tasks
- Quick hypothesis creation with auto-parent task
- Evidence management
- Debate lifecycle management
- Integration with IntelligenceService for KB operations
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DebateStatus,
    DebateVerdict,
    Hypothesis,
    HypothesisCategory,
    HypothesisStatus,
    ImpactLevel,
    RiskLevel,
    TaskStatus,
)
from app.repositories import ResearchTaskRepository
from app.repositories.intelligence_repository import (
    DebateRepository,
    EvidenceRepository,
    HypothesisRepository,
)
from app.schemas.intelligence import (
    DebateCreate,
    DebateResponse,
    DebateStartResponse,
    EvidenceCreate,
    EvidenceResponse,
    HypothesisCreate,
    HypothesisResponse,
    HypothesisUpdate,
    QuickHypothesisCreate,
    QuickHypothesisResponse,
)

logger = logging.getLogger(__name__)


class HypothesisCrudService:
    """
    Database-backed hypothesis CRUD service.

    All hypotheses are attached to research tasks (parent).
    Provides full lifecycle management including validation via debates.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session"""
        self.db = db
        self.hypothesis_repo = HypothesisRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.debate_repo = DebateRepository(db)
        self.task_repo = ResearchTaskRepository()

        # Track active validation tasks
        self._active_validations: dict[int, asyncio.Task] = {}

    # =========================================================================
    # Hypothesis CRUD
    # =========================================================================

    async def list_by_task(
        self,
        task_id: int,
        skip: int = 0,
        limit: int = 50,
        status: Optional[HypothesisStatus] = None,
    ) -> tuple[list[HypothesisResponse], int]:
        """
        List hypotheses for a research task.

        Args:
            task_id: Research task ID
            skip: Pagination offset
            limit: Max results
            status: Optional status filter

        Returns:
            Tuple of (hypotheses, total_count)
        """
        hypotheses = await self.hypothesis_repo.get_by_task(task_id, skip, limit, status)
        total = await self.hypothesis_repo.count_by_task(task_id, status)

        responses = []
        for h in hypotheses:
            evidence_count = await self.evidence_repo.count_by_hypothesis(h.id)
            debate_count = await self.debate_repo.count_by_hypothesis(h.id)
            responses.append(
                HypothesisResponse(
                    id=h.id,
                    project_id=h.project_id,
                    research_task_id=h.research_task_id,
                    statement=h.statement,
                    category=h.category,
                    status=h.status,
                    impact=h.impact,
                    risk=h.risk,
                    priority_score=h.priority_score,
                    validation_score=h.validation_score,
                    knowledge_entry_id=h.knowledge_entry_id,
                    created_at=h.created_at,
                    updated_at=h.updated_at,
                    evidence_count=evidence_count,
                    debate_count=debate_count,
                )
            )

        return responses, total

    async def list_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 50,
        status: Optional[HypothesisStatus] = None,
    ) -> tuple[list[HypothesisResponse], int]:
        """
        List all hypotheses for a project.

        Args:
            project_id: Project ID
            skip: Pagination offset
            limit: Max results
            status: Optional status filter

        Returns:
            Tuple of (hypotheses, total_count)
        """
        hypotheses = await self.hypothesis_repo.get_by_project(project_id, skip, limit, status)
        total = await self.hypothesis_repo.count_by_project(project_id, status)

        responses = []
        for h in hypotheses:
            evidence_count = await self.evidence_repo.count_by_hypothesis(h.id)
            debate_count = await self.debate_repo.count_by_hypothesis(h.id)
            responses.append(
                HypothesisResponse(
                    id=h.id,
                    project_id=h.project_id,
                    research_task_id=h.research_task_id,
                    statement=h.statement,
                    category=h.category,
                    status=h.status,
                    impact=h.impact,
                    risk=h.risk,
                    priority_score=h.priority_score,
                    validation_score=h.validation_score,
                    knowledge_entry_id=h.knowledge_entry_id,
                    created_at=h.created_at,
                    updated_at=h.updated_at,
                    evidence_count=evidence_count,
                    debate_count=debate_count,
                )
            )

        return responses, total

    async def get_hypothesis(self, hypothesis_id: int) -> HypothesisResponse:
        """
        Get a hypothesis by ID.

        Args:
            hypothesis_id: Hypothesis ID

        Returns:
            HypothesisResponse

        Raises:
            HTTPException: If not found
        """
        hypothesis = await self.hypothesis_repo.get_by_id(hypothesis_id)
        if not hypothesis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hypothesis {hypothesis_id} not found",
            )

        evidence_count = await self.evidence_repo.count_by_hypothesis(hypothesis_id)
        debate_count = await self.debate_repo.count_by_hypothesis(hypothesis_id)

        return HypothesisResponse(
            id=hypothesis.id,
            project_id=hypothesis.project_id,
            research_task_id=hypothesis.research_task_id,
            statement=hypothesis.statement,
            category=hypothesis.category,
            status=hypothesis.status,
            impact=hypothesis.impact,
            risk=hypothesis.risk,
            priority_score=hypothesis.priority_score,
            validation_score=hypothesis.validation_score,
            knowledge_entry_id=hypothesis.knowledge_entry_id,
            created_at=hypothesis.created_at,
            updated_at=hypothesis.updated_at,
            evidence_count=evidence_count,
            debate_count=debate_count,
        )

    async def create_hypothesis(self, task_id: int, data: HypothesisCreate) -> HypothesisResponse:
        """
        Create a hypothesis under a research task.

        Args:
            task_id: Parent research task ID
            data: Hypothesis creation data

        Returns:
            Created hypothesis

        Raises:
            HTTPException: If task not found
        """
        # Verify task exists
        task = await self.task_repo.get(self.db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research task {task_id} not found",
            )

        # Calculate priority score
        priority_score = self._calculate_priority_score(data.impact, data.risk)

        hypothesis = await self.hypothesis_repo.create(
            project_id=task.project_id,
            research_task_id=task_id,
            statement=data.statement,
            category=data.category,
            status=HypothesisStatus.UNTESTED,
            impact=data.impact,
            risk=data.risk,
            priority_score=priority_score,
        )

        await self.db.commit()
        await self.db.refresh(hypothesis)

        return HypothesisResponse(
            id=hypothesis.id,
            project_id=hypothesis.project_id,
            research_task_id=hypothesis.research_task_id,
            statement=hypothesis.statement,
            category=hypothesis.category,
            status=hypothesis.status,
            impact=hypothesis.impact,
            risk=hypothesis.risk,
            priority_score=hypothesis.priority_score,
            validation_score=hypothesis.validation_score,
            knowledge_entry_id=hypothesis.knowledge_entry_id,
            created_at=hypothesis.created_at,
            updated_at=hypothesis.updated_at,
            evidence_count=0,
            debate_count=0,
        )

    async def create_quick_hypothesis(
        self, project_id: int, data: QuickHypothesisCreate
    ) -> QuickHypothesisResponse:
        """
        Create a hypothesis with auto-generated parent task.

        For quick hypothesis creation when there's no existing research task.
        Creates a minimal "ad-hoc hypothesis" task as parent.

        Args:
            project_id: Project ID
            data: Quick hypothesis data

        Returns:
            Created hypothesis with parent task info
        """
        # Create minimal parent task
        task_title = f"Hypothesis: {data.statement[:50]}..."
        task_description = data.context or "Auto-created task for hypothesis validation"

        task = await self.task_repo.create(
            self.db,
            obj_in={
                "project_id": project_id,
                "title": task_title,
                "description": task_description,
                "status": TaskStatus.IN_PROGRESS,
                "task_type": "ad_hoc_hypothesis",
            },
        )

        # Create hypothesis under the new task
        hypothesis_data = HypothesisCreate(
            statement=data.statement,
            category=data.category,
            impact=data.impact,
            risk=data.risk,
        )

        hypothesis_response = await self.create_hypothesis(task.id, hypothesis_data)

        return QuickHypothesisResponse(
            hypothesis_id=hypothesis_response.id,
            research_task_id=task.id,
            hypothesis=hypothesis_response,
        )

    async def update_hypothesis(
        self, hypothesis_id: int, data: HypothesisUpdate
    ) -> HypothesisResponse:
        """
        Update a hypothesis.

        Args:
            hypothesis_id: Hypothesis ID
            data: Update data

        Returns:
            Updated hypothesis

        Raises:
            HTTPException: If not found
        """
        hypothesis = await self.hypothesis_repo.get_by_id(hypothesis_id)
        if not hypothesis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hypothesis {hypothesis_id} not found",
            )

        update_data = data.model_dump(exclude_unset=True)

        # Recalculate priority if impact or risk changed
        if "impact" in update_data or "risk" in update_data:
            impact = update_data.get("impact", hypothesis.impact)
            risk = update_data.get("risk", hypothesis.risk)
            update_data["priority_score"] = self._calculate_priority_score(impact, risk)

        await self.hypothesis_repo.update(hypothesis, **update_data)
        await self.db.commit()
        await self.db.refresh(hypothesis)

        return await self.get_hypothesis(hypothesis_id)

    async def delete_hypothesis(self, hypothesis_id: int) -> None:
        """
        Delete a hypothesis.

        Args:
            hypothesis_id: Hypothesis ID

        Raises:
            HTTPException: If not found
        """
        hypothesis = await self.hypothesis_repo.get_by_id(hypothesis_id)
        if not hypothesis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hypothesis {hypothesis_id} not found",
            )

        await self.hypothesis_repo.delete(hypothesis)
        await self.db.commit()

    # =========================================================================
    # Evidence Management
    # =========================================================================

    async def list_evidence(
        self, hypothesis_id: int, skip: int = 0, limit: int = 50
    ) -> tuple[list[EvidenceResponse], int]:
        """List evidence for a hypothesis"""
        evidence_list = await self.evidence_repo.get_by_hypothesis(hypothesis_id, skip, limit)
        total = await self.evidence_repo.count_by_hypothesis(hypothesis_id)

        responses = [
            EvidenceResponse(
                id=e.id,
                hypothesis_id=e.hypothesis_id,
                content=e.content,
                source_type=e.source_type,
                source_id=e.source_id,
                stance=e.stance,
                confidence=e.confidence,
                created_at=e.created_at,
            )
            for e in evidence_list
        ]

        return responses, total

    async def add_evidence(self, hypothesis_id: int, data: EvidenceCreate) -> EvidenceResponse:
        """
        Add evidence to a hypothesis.

        Args:
            hypothesis_id: Hypothesis ID
            data: Evidence data

        Returns:
            Created evidence

        Raises:
            HTTPException: If hypothesis not found
        """
        hypothesis = await self.hypothesis_repo.get_by_id(hypothesis_id)
        if not hypothesis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hypothesis {hypothesis_id} not found",
            )

        evidence = await self.evidence_repo.create(
            hypothesis_id=hypothesis_id,
            content=data.content,
            source_type=data.source_type,
            source_id=data.source_id,
            stance=data.stance,
            confidence=data.confidence,
        )

        await self.db.commit()
        await self.db.refresh(evidence)

        # Index evidence to KB if available
        try:
            from app.services.intelligence_kb_service import IntelligenceKBService

            kb_service = IntelligenceKBService(hypothesis.project_id)
            await kb_service.index_evidence(
                evidence_id=evidence.id,
                hypothesis_id=hypothesis_id,
                content=evidence.content,
                source_type=evidence.source_type.value,
                stance=evidence.stance.value,
                confidence=evidence.confidence,
                source_id=evidence.source_id,
            )
        except Exception as e:
            logger.warning(f"Failed to index evidence to KB: {e}")

        return EvidenceResponse(
            id=evidence.id,
            hypothesis_id=evidence.hypothesis_id,
            content=evidence.content,
            source_type=evidence.source_type,
            source_id=evidence.source_id,
            stance=evidence.stance,
            confidence=evidence.confidence,
            created_at=evidence.created_at,
        )

    async def accept_suggested_evidence(
        self, hypothesis_id: int, suggestion_indices: list[int]
    ) -> list[EvidenceResponse]:
        """
        Accept suggested evidence from KB query.

        Args:
            hypothesis_id: Hypothesis ID
            suggestion_indices: Indices of suggestions to accept

        Returns:
            List of created evidence
        """
        from app.services.intelligence_service import IntelligenceService

        intelligence_service = IntelligenceService(self.db)
        suggestions_result = await intelligence_service.suggest_evidence(hypothesis_id)

        created_evidence = []
        for idx in suggestion_indices:
            if idx < len(suggestions_result.suggestions):
                suggestion = suggestions_result.suggestions[idx]
                evidence = await self.add_evidence(
                    hypothesis_id,
                    EvidenceCreate(
                        content=suggestion.content,
                        source_type=suggestion.source_type,
                        source_id=suggestion.source_id,
                        stance=suggestion.suggested_stance,
                        confidence=suggestion.confidence,
                    ),
                )
                created_evidence.append(evidence)

        return created_evidence

    # =========================================================================
    # Validation (Debate) Management
    # =========================================================================

    async def start_validation(self, hypothesis_id: int, data: DebateCreate) -> DebateStartResponse:
        """
        Start validation debate for a hypothesis.

        Args:
            hypothesis_id: Hypothesis ID
            data: Debate configuration

        Returns:
            DebateStartResponse with debate_id

        Raises:
            HTTPException: If hypothesis not found or already validating
        """
        hypothesis = await self.hypothesis_repo.get_by_id(hypothesis_id)
        if not hypothesis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hypothesis {hypothesis_id} not found",
            )

        # Check for existing active debate
        active_debate = await self.debate_repo.get_active_by_hypothesis(hypothesis_id)
        if active_debate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Hypothesis {hypothesis_id} already has an active validation",
            )

        # Update hypothesis status
        await self.hypothesis_repo.update(hypothesis, status=HypothesisStatus.VALIDATING)

        # Create debate record
        debate = await self.debate_repo.create(
            hypothesis_id=hypothesis_id,
            status=DebateStatus.PENDING,
            rounds_requested=data.rounds,
            agents_used=data.agents,
        )

        await self.db.commit()
        await self.db.refresh(debate)

        # Start background validation task
        task = asyncio.create_task(
            self._run_validation(debate.id, hypothesis, data.agents, data.rounds)
        )
        self._active_validations[debate.id] = task

        return DebateStartResponse(debate_id=debate.id, status=debate.status)

    async def get_debate(self, debate_id: int) -> DebateResponse:
        """Get debate by ID"""
        debate = await self.debate_repo.get_by_id(debate_id)
        if not debate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Debate {debate_id} not found",
            )

        return DebateResponse(
            id=debate.id,
            hypothesis_id=debate.hypothesis_id,
            status=debate.status,
            rounds_requested=debate.rounds_requested,
            rounds_completed=debate.rounds_completed,
            agents_used=debate.agents_used,
            consensus_level=debate.consensus_level,
            final_verdict=debate.final_verdict,
            verdict_reasoning=debate.verdict_reasoning,
            gap_analysis=debate.gap_analysis,
            suggested_research=debate.suggested_research,
            knowledge_entry_id=debate.knowledge_entry_id,
            started_at=debate.started_at,
            completed_at=debate.completed_at,
        )

    async def _run_validation(
        self,
        debate_id: int,
        hypothesis: Hypothesis,
        agents: list[str],
        rounds: int,
    ) -> None:
        """
        Run validation in background.

        This method executes the multi-agent debate asynchronously.
        """
        try:
            # Update status to running
            debate = await self.debate_repo.get_by_id(debate_id)
            if not debate:
                return

            await self.debate_repo.update(debate, status=DebateStatus.RUNNING)
            await self.db.commit()

            # Prepare validation context (for future use with ValidationContext-aware validator)
            # from app.services.intelligence_service import IntelligenceService
            # intelligence_service = IntelligenceService(self.db)
            # context = await intelligence_service.prepare_validation_context(hypothesis.id)

            # Run actual validation via existing validator
            try:
                from libs.ai_arena.hypothesis.schema import Hypothesis as ArenaHypothesis
                from libs.ai_arena.hypothesis.schema import HypothesisCategory as ArenaCategory
                from libs.ai_arena.hypothesis.validator import HypothesisValidator, ValidationConfig
                from libs.ai_arena.registry import AgentRegistry
                from libs.llm_gateway import LLMGateway

                # Create arena hypothesis from DB hypothesis
                category_map = {
                    HypothesisCategory.CUSTOMER: ArenaCategory.CUSTOMER,
                    HypothesisCategory.PROBLEM: ArenaCategory.PROBLEM,
                    HypothesisCategory.SOLUTION: ArenaCategory.SOLUTION,
                    HypothesisCategory.TECHNICAL: ArenaCategory.TECHNICAL,
                    HypothesisCategory.MARKET: ArenaCategory.MARKET,
                    HypothesisCategory.REGULATORY: ArenaCategory.REGULATORY,
                    HypothesisCategory.COMPETITIVE: ArenaCategory.COMPETITIVE,
                    HypothesisCategory.GTM: ArenaCategory.GTM,
                }

                arena_hypothesis = ArenaHypothesis(
                    statement=hypothesis.statement,
                    category=category_map.get(hypothesis.category, ArenaCategory.TECHNICAL),
                )

                # Create agents
                gateway = LLMGateway()
                registry = AgentRegistry(gateway)
                agent_list = []
                for role in agents:
                    if role.lower() in ["analyst", "researcher", "strategist", "critic"]:
                        agent_list.append(registry.create(role.lower()))

                if not agent_list:
                    raise ValueError("No valid agents for validation")

                # Run validation
                config = ValidationConfig(max_debate_rounds=rounds)
                validator = HypothesisValidator(agent_list, config=config, llm_gateway=gateway)
                result = await validator.validate(hypothesis=arena_hypothesis)

                # Update debate with results
                await self.debate_repo.update(
                    debate,
                    status=DebateStatus.COMPLETED,
                    rounds_completed=result.rounds_taken,
                    consensus_level=self._map_consensus(result.consensus_reached),
                    final_verdict=self._map_verdict(result.status.value),
                    verdict_reasoning=result.reasoning_summary,
                    gap_analysis={"follow_up_questions": result.follow_up_questions},
                    suggested_research={"tasks": self._extract_suggested_tasks(result)},
                    completed_at=datetime.utcnow(),
                )

            except ImportError:
                # Fallback if ai_arena not available - simulate completion
                logger.warning("ai_arena not available, simulating validation")
                await self.debate_repo.update(
                    debate,
                    status=DebateStatus.COMPLETED,
                    rounds_completed=rounds,
                    consensus_level="moderate",
                    final_verdict=DebateVerdict.NEEDS_MORE_DATA,
                    verdict_reasoning="Validation framework not available",
                    completed_at=datetime.utcnow(),
                )

            await self.db.commit()

            # Process validation result
            # TODO: Fix - intelligence_service is undefined (pre-existing bug)
            # debate = await self.debate_repo.get_by_id(debate_id)
            # await intelligence_service.process_validation_result(debate)

        except Exception as e:
            logger.error(f"Validation failed for debate {debate_id}: {e}")

            debate = await self.debate_repo.get_by_id(debate_id)
            if debate:
                await self.debate_repo.update(
                    debate,
                    status=DebateStatus.FAILED,
                    completed_at=datetime.utcnow(),
                )

                # Revert hypothesis status
                await self.hypothesis_repo.update(hypothesis, status=HypothesisStatus.UNTESTED)
                await self.db.commit()

        finally:
            self._active_validations.pop(debate_id, None)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _calculate_priority_score(self, impact: ImpactLevel, risk: RiskLevel) -> float:
        """Calculate priority score from impact and risk"""
        impact_scores = {ImpactLevel.HIGH: 3, ImpactLevel.MEDIUM: 2, ImpactLevel.LOW: 1}
        risk_scores = {RiskLevel.HIGH: 3, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 1}

        # Priority = Impact * Risk (both should be validated first)
        return float(impact_scores.get(impact, 2) * risk_scores.get(risk, 2)) * 10

    def _map_consensus(self, consensus_reached: bool) -> str:
        """Map boolean consensus to level string"""
        return "strong" if consensus_reached else "weak"

    def _map_verdict(self, status_value: str) -> DebateVerdict:
        """Map validation status to debate verdict"""
        status_map = {
            "validated": DebateVerdict.VALIDATED,
            "invalidated": DebateVerdict.INVALIDATED,
            "needs_more_data": DebateVerdict.NEEDS_MORE_DATA,
        }
        return status_map.get(status_value, DebateVerdict.NEEDS_MORE_DATA)

    def _extract_suggested_tasks(self, result: Any) -> list[dict]:
        """Extract suggested research tasks from validation result"""
        tasks = []
        if hasattr(result, "follow_up_questions") and result.follow_up_questions:
            for q in result.follow_up_questions[:3]:
                tasks.append(
                    {
                        "title": f"Investigate: {q[:50]}...",
                        "description": q,
                        "priority": "medium",
                        "effort": "medium",
                    }
                )
        return tasks
