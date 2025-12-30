"""
Intelligence Service

Orchestrates the research intelligence cycle:
Research Agents → Findings → KnowledgeBeast → Hypotheses → Validation → Evidence → Gaps → Research

This service provides:
- Evidence suggestion from KB and findings
- Validation context preparation for debate agents
- Post-validation processing (indexing, gap analysis)
- Research findings indexing
- Gap-to-task conversion
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Debate,
    DebateStatus,
    DebateVerdict,
    EvidenceSourceType,
    EvidenceStance,
    HypothesisStatus,
    ResearchTask,
    TaskStatus,
)
from app.repositories.intelligence_repository import (
    DebateRepository,
    EvidenceRepository,
    HypothesisRepository,
    ResearchFindingRepository,
)
from app.schemas.intelligence import EvidenceSuggestion, GapSuggestion, ValidationContext

logger = logging.getLogger(__name__)


@dataclass
class EvidenceSuggestionResult:
    """Result of evidence suggestion query"""

    suggestions: list[EvidenceSuggestion]
    query_used: str


class IntelligenceService:
    """
    Orchestrates the research → validate → learn cycle.

    The intelligence loop:
    1. Research agents produce findings
    2. Findings are indexed in KnowledgeBeast
    3. Findings suggest hypotheses
    4. Validation queries KB for context
    5. Debate produces evidence + verdict
    6. Validated knowledge indexed in KB
    7. Gaps suggest new research tasks
    8. Cycle continues
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session"""
        self.db = db
        self.hypothesis_repo = HypothesisRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.debate_repo = DebateRepository(db)
        self.finding_repo = ResearchFindingRepository(db)

    async def suggest_evidence(
        self, hypothesis_id: int, limit: int = 10
    ) -> EvidenceSuggestionResult:
        """
        Suggest evidence for a hypothesis from KB and findings.

        1. Get hypothesis and its parent task
        2. Query task's findings for relevant content
        3. Query KnowledgeBeast for related knowledge
        4. Rank by relevance to hypothesis statement
        5. Return suggestions with source attribution

        Args:
            hypothesis_id: Hypothesis to find evidence for
            limit: Maximum suggestions to return

        Returns:
            EvidenceSuggestionResult with ranked suggestions
        """
        hypothesis = await self.hypothesis_repo.get_by_id(hypothesis_id)
        if not hypothesis:
            return EvidenceSuggestionResult(suggestions=[], query_used="")

        suggestions: list[EvidenceSuggestion] = []
        query = hypothesis.statement

        # Get findings from parent task
        findings = await self.finding_repo.get_by_task(hypothesis.research_task_id, limit=limit)

        for finding in findings:
            # Simple relevance scoring based on word overlap
            relevance = self._calculate_relevance(query, finding.content)
            if relevance > 0.1:  # Threshold
                suggestions.append(
                    EvidenceSuggestion(
                        content=finding.content,
                        source_type=EvidenceSourceType.RESEARCH_FINDING,
                        source_id=str(finding.id),
                        suggested_stance=self._infer_stance(hypothesis.statement, finding.content),
                        confidence=finding.confidence,
                        relevance_score=relevance,
                        source_collection="findings",
                    )
                )

        # Try to query KnowledgeBeast if available
        try:
            from app.services.intelligence_kb_service import IntelligenceKBService

            kb_service = IntelligenceKBService(hypothesis.project_id)
            kb_results = await kb_service.query_for_evidence(hypothesis.statement, limit=limit)

            for result in kb_results:
                # Avoid duplicates from findings
                if result.get("collection") == "findings":
                    source_id = result.get("metadata", {}).get("finding_id")
                    if any(s.source_id == str(source_id) for s in suggestions):
                        continue

                suggestions.append(
                    EvidenceSuggestion(
                        content=result.get("content", ""),
                        source_type=EvidenceSourceType.KNOWLEDGE_BASE,
                        source_id=result.get("metadata", {}).get("doc_id"),
                        suggested_stance=self._infer_stance(
                            hypothesis.statement, result.get("content", "")
                        ),
                        confidence=result.get("score", 0.5),
                        relevance_score=result.get("score", 0.5),
                        source_collection=result.get("collection", "unknown"),
                    )
                )

        except ImportError:
            logger.debug("KnowledgeBeast not available for evidence suggestion")
        except Exception as e:
            logger.warning(f"KB query failed for evidence suggestion: {e}")

        # Sort by relevance and limit
        suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
        return EvidenceSuggestionResult(suggestions=suggestions[:limit], query_used=query)

    async def prepare_validation_context(self, hypothesis_id: int) -> Optional[ValidationContext]:
        """
        Build context package for debate agents.

        Includes:
        - Hypothesis statement + metadata
        - Parent task description + findings
        - Linked evidence
        - RAG query to KB for related validated hypotheses
        - RAG query for contradicting evidence

        Args:
            hypothesis_id: Hypothesis to prepare context for

        Returns:
            ValidationContext with all relevant information
        """
        hypothesis = await self.hypothesis_repo.get_by_id(hypothesis_id, load_relations=True)
        if not hypothesis:
            return None

        # Get parent task
        from app.repositories import ResearchTaskRepository

        task_repo = ResearchTaskRepository(self.db)
        task = await task_repo.get_by_id(hypothesis.research_task_id)
        if not task:
            return None

        # Get existing evidence
        evidence_list = await self.evidence_repo.get_by_hypothesis(hypothesis_id)
        evidence_responses = [
            {
                "id": e.id,
                "hypothesis_id": e.hypothesis_id,
                "content": e.content,
                "source_type": e.source_type.value,
                "source_id": e.source_id,
                "stance": e.stance.value,
                "confidence": e.confidence,
                "created_at": e.created_at.isoformat(),
            }
            for e in evidence_list
        ]

        # Query KB for related knowledge
        related_findings = []
        related_hypotheses = []
        contradicting = []

        try:
            from app.services.intelligence_kb_service import IntelligenceKBService

            kb_service = IntelligenceKBService(hypothesis.project_id)
            kb_results = await kb_service.query_for_evidence(hypothesis.statement, limit=15)

            for result in kb_results:
                collection = result.get("collection", "")
                if collection == "findings":
                    related_findings.append(result)
                elif collection == "hypotheses":
                    related_hypotheses.append(result)

                # Check for contradicting evidence
                stance = self._infer_stance(hypothesis.statement, result.get("content", ""))
                if stance == EvidenceStance.CONTRADICTING:
                    contradicting.append(result)

        except Exception as e:
            logger.warning(f"KB query failed for validation context: {e}")

        return ValidationContext(
            hypothesis_id=hypothesis.id,
            statement=hypothesis.statement,
            category=hypothesis.category,
            impact=hypothesis.impact,
            risk=hypothesis.risk,
            task_id=task.id,
            task_title=task.title,
            task_description=task.description,
            evidence=evidence_responses,
            related_findings=related_findings,
            related_hypotheses=related_hypotheses,
            contradicting_evidence=contradicting,
        )

    async def process_validation_result(self, debate: Debate) -> None:
        """
        Process completed debate results.

        After debate completes:
        1. Update hypothesis status based on verdict
        2. Parse gap analysis into structured suggestions
        3. If validated: index hypothesis + reasoning to KB
        4. If needs_more_data: prepare suggested research tasks

        Args:
            debate: Completed debate to process
        """
        if debate.status != DebateStatus.COMPLETED:
            return

        # Get hypothesis
        hypothesis = await self.hypothesis_repo.get_by_id(debate.hypothesis_id)
        if not hypothesis:
            return

        # Update hypothesis status based on verdict
        new_status = self._verdict_to_status(debate.final_verdict)
        await self.hypothesis_repo.update(
            hypothesis,
            status=new_status,
            validation_score=self._calculate_validation_score(debate),
        )

        # Index validated hypothesis to KB
        if debate.final_verdict == DebateVerdict.VALIDATED:
            try:
                from app.services.intelligence_kb_service import IntelligenceKBService

                kb_service = IntelligenceKBService(hypothesis.project_id)
                doc_id = await kb_service.index_validated_hypothesis(
                    hypothesis_id=hypothesis.id,
                    statement=hypothesis.statement,
                    category=hypothesis.category.value,
                    status=new_status.value,
                    validation_score=hypothesis.validation_score,
                    verdict=debate.final_verdict.value if debate.final_verdict else None,
                    verdict_reasoning=debate.verdict_reasoning,
                )
                await self.hypothesis_repo.update(hypothesis, knowledge_entry_id=doc_id)

            except Exception as e:
                logger.warning(f"Failed to index validated hypothesis: {e}")

        await self.db.commit()

    async def index_research_findings(self, task_id: int) -> int:
        """
        Index all unindexed findings from a task to KnowledgeBeast.

        Args:
            task_id: Research task ID

        Returns:
            Count of findings indexed
        """
        findings = await self.finding_repo.get_unindexed_by_task(task_id)
        if not findings:
            return 0

        # Get project_id from first finding's task
        from app.repositories import ResearchTaskRepository

        task_repo = ResearchTaskRepository(self.db)
        task = await task_repo.get_by_id(task_id)
        if not task:
            return 0

        indexed_count = 0

        try:
            from app.services.intelligence_kb_service import IntelligenceKBService

            kb_service = IntelligenceKBService(task.project_id)

            for finding in findings:
                try:
                    doc_id = await kb_service.index_finding(
                        finding_id=finding.id,
                        task_id=task_id,
                        content=finding.content,
                        finding_type=finding.finding_type.value,
                        agent_role=finding.agent_role,
                        confidence=finding.confidence,
                        sources=finding.sources,
                    )
                    await self.finding_repo.update(finding, knowledge_entry_id=doc_id)
                    indexed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to index finding {finding.id}: {e}")

            await self.db.commit()

        except ImportError:
            logger.warning("KnowledgeBeast not available for findings indexing")
        except Exception as e:
            logger.error(f"Failed to index findings: {e}")

        return indexed_count

    async def get_suggested_tasks_from_gap(self, debate_id: int) -> list[GapSuggestion]:
        """
        Get suggested research tasks from debate gap analysis.

        Args:
            debate_id: Debate ID with gap analysis

        Returns:
            List of task suggestions
        """
        debate = await self.debate_repo.get_by_id(debate_id)
        if not debate or not debate.suggested_research:
            return []

        suggestions = []
        suggested_research = debate.suggested_research

        # Parse structured suggestions from gap analysis
        if isinstance(suggested_research, dict):
            tasks = suggested_research.get("tasks", [])
            for i, task in enumerate(tasks):
                if isinstance(task, dict):
                    suggestions.append(
                        GapSuggestion(
                            title=task.get("title", f"Research Task {i + 1}"),
                            description=task.get("description", ""),
                            priority=task.get("priority", "medium"),
                            estimated_effort=task.get("effort", "medium"),
                        )
                    )
        elif isinstance(suggested_research, list):
            for i, item in enumerate(suggested_research):
                if isinstance(item, str):
                    suggestions.append(
                        GapSuggestion(
                            title=item[:100],
                            description=item,
                            priority="medium",
                            estimated_effort="medium",
                        )
                    )
                elif isinstance(item, dict):
                    suggestions.append(
                        GapSuggestion(
                            title=item.get("title", f"Research Task {i + 1}"),
                            description=item.get("description", ""),
                            priority=item.get("priority", "medium"),
                            estimated_effort=item.get("effort", "medium"),
                        )
                    )

        return suggestions

    async def create_task_from_gap(
        self, debate_id: int, suggestion_index: int
    ) -> Optional[ResearchTask]:
        """
        Create a research task from a gap analysis suggestion.

        Args:
            debate_id: Debate ID with the suggestion
            suggestion_index: Index of the suggestion to use

        Returns:
            Created ResearchTask or None
        """
        suggestions = await self.get_suggested_tasks_from_gap(debate_id)
        if suggestion_index >= len(suggestions):
            return None

        suggestion = suggestions[suggestion_index]

        # Get debate to find project_id
        debate = await self.debate_repo.get_by_id(debate_id)
        if not debate:
            return None

        hypothesis = await self.hypothesis_repo.get_by_id(debate.hypothesis_id)
        if not hypothesis:
            return None

        # Create research task
        from app.repositories import ResearchTaskRepository

        task_repo = ResearchTaskRepository(self.db)
        task = await task_repo.create(
            project_id=hypothesis.project_id,
            title=suggestion.title,
            description=suggestion.description,
            status=TaskStatus.PENDING,
            task_type="research",
            metadata_={
                "source": "gap_analysis",
                "debate_id": debate_id,
                "hypothesis_id": hypothesis.id,
            },
        )

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_intelligence_summary(self, project_id: int) -> dict[str, Any]:
        """
        Get combined intelligence statistics for a project.

        Returns:
            Summary with research tasks, hypotheses, KB stats, and gaps
        """
        # Hypothesis stats
        hypothesis_stats = await self.hypothesis_repo.get_statistics_by_project(project_id)

        # Count open gaps (hypotheses needing more data)
        needs_attention = await self.hypothesis_repo.get_needing_attention(project_id, limit=100)

        # KB stats (if available)
        kb_stats = {"documents": 0, "findings_indexed": 0, "hypotheses_indexed": 0}
        try:
            from app.services.intelligence_kb_service import IntelligenceKBService

            kb_service = IntelligenceKBService(project_id)
            collection_stats = await kb_service.get_collection_stats()
            kb_stats = {
                "findings_indexed": collection_stats.get("findings", {}).get("document_count", 0),
                "hypotheses_indexed": collection_stats.get("hypotheses", {}).get(
                    "document_count", 0
                ),
                "evidence_indexed": collection_stats.get("evidence", {}).get("document_count", 0),
            }
        except Exception:
            pass

        # Find oldest gap
        oldest_gap = None
        if needs_attention:
            oldest = min(needs_attention, key=lambda h: h.created_at)
            oldest_gap = oldest.created_at.isoformat()

        return {
            "hypotheses": hypothesis_stats,
            "knowledge_base": kb_stats,
            "gaps": {
                "open_count": len(
                    [h for h in needs_attention if h.status == HypothesisStatus.NEEDS_MORE_DATA]
                ),
                "oldest_gap": oldest_gap,
            },
        }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _calculate_relevance(self, query: str, content: str) -> float:
        """Simple word overlap relevance scoring"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())

        if not query_words:
            return 0.0

        overlap = len(query_words & content_words)
        return overlap / len(query_words)

    def _infer_stance(self, hypothesis: str, content: str) -> EvidenceStance:
        """Infer evidence stance based on content analysis"""
        # Simple heuristic - look for negation words near hypothesis keywords
        negation_words = {
            "not",
            "no",
            "never",
            "neither",
            "nobody",
            "nothing",
            "fail",
            "wrong",
            "incorrect",
            "false",
        }
        content_lower = content.lower()

        hypothesis_keywords = set(hypothesis.lower().split())
        content_words = content_lower.split()

        # Check for negation near hypothesis keywords
        for i, word in enumerate(content_words):
            if word in hypothesis_keywords:
                # Check surrounding words for negation
                start = max(0, i - 3)
                end = min(len(content_words), i + 3)
                surrounding = set(content_words[start:end])
                if surrounding & negation_words:
                    return EvidenceStance.CONTRADICTING

        # Default to neutral if no clear signal
        if any(kw in content_lower for kw in hypothesis_keywords):
            return EvidenceStance.SUPPORTING

        return EvidenceStance.NEUTRAL

    def _verdict_to_status(self, verdict: Optional[DebateVerdict]) -> HypothesisStatus:
        """Convert debate verdict to hypothesis status"""
        if verdict == DebateVerdict.VALIDATED:
            return HypothesisStatus.VALIDATED
        elif verdict == DebateVerdict.INVALIDATED:
            return HypothesisStatus.INVALIDATED
        elif verdict == DebateVerdict.NEEDS_MORE_DATA:
            return HypothesisStatus.NEEDS_MORE_DATA
        return HypothesisStatus.UNTESTED

    def _calculate_validation_score(self, debate: Debate) -> float:
        """Calculate validation score from debate results"""
        # Base score from consensus level
        consensus_scores = {
            "strong": 0.9,
            "moderate": 0.7,
            "weak": 0.5,
            "deadlock": 0.3,
        }

        base_score = 0.5
        if debate.consensus_level:
            base_score = consensus_scores.get(debate.consensus_level.value, 0.5)

        # Adjust based on verdict
        if debate.final_verdict == DebateVerdict.VALIDATED:
            return min(1.0, base_score + 0.1)
        elif debate.final_verdict == DebateVerdict.INVALIDATED:
            return max(0.0, base_score - 0.1)

        return base_score
