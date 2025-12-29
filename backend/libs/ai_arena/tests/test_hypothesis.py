"""Tests for AI Arena Hypothesis Validation Module"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from libs.ai_arena.agents import AgentResponse
from libs.ai_arena.debate import ConsensusLevel, DebateResult, DebateRound, DebateStatus
from libs.ai_arena.hypothesis.registry import HypothesisRegistry
from libs.ai_arena.hypothesis.report import ValidationReportGenerator
from libs.ai_arena.hypothesis.schema import (
    Hypothesis,
    HypothesisCategory,
    HypothesisCreate,
    HypothesisEvidence,
    HypothesisPriority,
    HypothesisStatus,
    HypothesisUpdate,
    HypothesisValidationResult,
    ImpactLevel,
    RiskLevel,
    TestabilityLevel,
)
from libs.ai_arena.hypothesis.validator import HypothesisValidator, ValidationConfig


class TestHypothesisSchema:
    """Tests for hypothesis schema models"""

    def test_create_hypothesis(self):
        """Should create a valid Hypothesis"""
        hypothesis = Hypothesis(
            id="hyp_test123",
            statement="Enterprise customers will pay $2K/month",
            category=HypothesisCategory.REVENUE,
            impact=ImpactLevel.HIGH,
            risk=RiskLevel.HIGH,
            testability=TestabilityLevel.MEDIUM,
            success_criteria="5 of 10 prospects confirm",
        )

        assert hypothesis.id == "hyp_test123"
        assert hypothesis.statement == "Enterprise customers will pay $2K/month"
        assert hypothesis.category == HypothesisCategory.REVENUE
        assert hypothesis.status == HypothesisStatus.UNTESTED
        assert hypothesis.priority is not None
        assert hypothesis.priority.score > 0

    def test_hypothesis_priority_calculation(self):
        """Should calculate priority from impact, risk, testability"""
        # High impact, high risk, easy testability = high priority
        high_priority = HypothesisPriority.calculate(
            ImpactLevel.HIGH,
            RiskLevel.HIGH,
            TestabilityLevel.EASY,
        )

        # Low impact, low risk, hard testability = low priority
        low_priority = HypothesisPriority.calculate(
            ImpactLevel.LOW,
            RiskLevel.LOW,
            TestabilityLevel.HARD,
        )

        assert high_priority.score > low_priority.score

    def test_hypothesis_add_evidence(self):
        """Should add evidence to hypothesis"""
        hypothesis = Hypothesis(
            id="hyp_test",
            statement="Test hypothesis",
            category=HypothesisCategory.MARKET,
            impact=ImpactLevel.MEDIUM,
            risk=RiskLevel.MEDIUM,
            testability=TestabilityLevel.MEDIUM,
            success_criteria="Test criteria",
        )

        evidence = HypothesisEvidence(
            source="Industry Report",
            content="Market size is $10B",
            supports=True,
            confidence=85,
        )

        hypothesis.add_evidence(evidence)

        assert len(hypothesis.evidence) == 1
        assert hypothesis.supporting_count == 1
        assert hypothesis.contradicting_count == 0

    def test_hypothesis_to_debate_question(self):
        """Should convert hypothesis to debate question"""
        hypothesis = Hypothesis(
            id="hyp_test",
            statement="Customers will pay $100/month",
            category=HypothesisCategory.REVENUE,
            impact=ImpactLevel.HIGH,
            risk=RiskLevel.HIGH,
            testability=TestabilityLevel.MEDIUM,
            success_criteria="3 signed letters of intent",
            context="B2B SaaS market",
        )

        question = hypothesis.to_debate_question()

        assert "Customers will pay $100/month" in question
        assert "revenue" in question.lower()
        assert "3 signed letters of intent" in question
        assert "B2B SaaS market" in question

    def test_hypothesis_create_schema(self):
        """Should validate HypothesisCreate schema"""
        create_data = HypothesisCreate(
            statement="Test statement that is long enough",
            category=HypothesisCategory.CUSTOMER,
            impact=ImpactLevel.HIGH,
            risk=RiskLevel.MEDIUM,
            testability=TestabilityLevel.EASY,
            success_criteria="Test criteria",
            tags=["customer", "validation"],
        )

        assert create_data.statement == "Test statement that is long enough"
        assert create_data.category == HypothesisCategory.CUSTOMER
        assert len(create_data.tags) == 2


class TestHypothesisRegistry:
    """Tests for HypothesisRegistry"""

    @pytest.fixture
    def registry(self):
        """Create empty registry"""
        return HypothesisRegistry()

    def test_create_hypothesis(self, registry):
        """Should create hypothesis and assign ID"""
        hypothesis = registry.create(
            HypothesisCreate(
                statement="Test hypothesis statement",
                category=HypothesisCategory.MARKET,
                impact=ImpactLevel.HIGH,
                risk=RiskLevel.HIGH,
                testability=TestabilityLevel.MEDIUM,
                success_criteria="Test success criteria",
            )
        )

        assert hypothesis.id.startswith("hyp_")
        assert hypothesis.statement == "Test hypothesis statement"
        assert len(registry) == 1

    def test_get_hypothesis(self, registry):
        """Should retrieve hypothesis by ID"""
        created = registry.create(
            HypothesisCreate(
                statement="Test hypothesis statement",
                category=HypothesisCategory.REVENUE,
                impact=ImpactLevel.MEDIUM,
                risk=RiskLevel.MEDIUM,
                testability=TestabilityLevel.MEDIUM,
                success_criteria="Test criteria",
            )
        )

        retrieved = registry.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.statement == created.statement

    def test_update_hypothesis(self, registry):
        """Should update hypothesis fields"""
        hypothesis = registry.create(
            HypothesisCreate(
                statement="Original statement text",
                category=HypothesisCategory.MARKET,
                impact=ImpactLevel.LOW,
                risk=RiskLevel.LOW,
                testability=TestabilityLevel.HARD,
                success_criteria="Original criteria",
            )
        )

        original_score = hypothesis.priority.score

        updated = registry.update(
            hypothesis.id,
            HypothesisUpdate(
                statement="Updated statement text",
                impact=ImpactLevel.HIGH,
                risk=RiskLevel.HIGH,
            ),
        )

        assert updated is not None
        assert updated.statement == "Updated statement text"
        assert updated.impact == ImpactLevel.HIGH
        # Priority should be recalculated with higher values
        assert updated.priority.score > original_score

    def test_delete_hypothesis(self, registry):
        """Should delete hypothesis"""
        hypothesis = registry.create(
            HypothesisCreate(
                statement="To be deleted statement",
                category=HypothesisCategory.TECHNICAL,
                impact=ImpactLevel.LOW,
                risk=RiskLevel.LOW,
                testability=TestabilityLevel.EASY,
                success_criteria="Deletion criteria",
            )
        )

        result = registry.delete(hypothesis.id)

        assert result is True
        assert registry.get(hypothesis.id) is None
        assert len(registry) == 0

    def test_list_hypotheses_with_filter(self, registry):
        """Should filter hypotheses by status and category"""
        # Create multiple hypotheses
        registry.create(
            HypothesisCreate(
                statement="Market hypothesis one",
                category=HypothesisCategory.MARKET,
                impact=ImpactLevel.HIGH,
                risk=RiskLevel.HIGH,
                testability=TestabilityLevel.MEDIUM,
                success_criteria="Market criteria",
            )
        )
        registry.create(
            HypothesisCreate(
                statement="Pricing hypothesis one",
                category=HypothesisCategory.REVENUE,
                impact=ImpactLevel.MEDIUM,
                risk=RiskLevel.MEDIUM,
                testability=TestabilityLevel.MEDIUM,
                success_criteria="Pricing criteria",
            )
        )

        market_hypotheses = registry.list(category=HypothesisCategory.MARKET)
        untested = registry.list(status=HypothesisStatus.UNTESTED)

        assert len(market_hypotheses) == 1
        assert len(untested) == 2

    def test_get_prioritized(self, registry):
        """Should return hypotheses sorted by priority"""
        # Low priority
        registry.create(
            HypothesisCreate(
                statement="Low priority hypothesis",
                category=HypothesisCategory.TECHNICAL,
                impact=ImpactLevel.LOW,
                risk=RiskLevel.LOW,
                testability=TestabilityLevel.HARD,
                success_criteria="Low priority criteria",
            )
        )
        # High priority
        registry.create(
            HypothesisCreate(
                statement="High priority hypothesis",
                category=HypothesisCategory.REVENUE,
                impact=ImpactLevel.HIGH,
                risk=RiskLevel.HIGH,
                testability=TestabilityLevel.EASY,
                success_criteria="High priority criteria",
            )
        )

        prioritized = registry.get_prioritized()

        assert len(prioritized) == 2
        assert prioritized[0].impact == ImpactLevel.HIGH  # High priority first

    def test_add_evidence(self, registry):
        """Should add evidence to hypothesis"""
        hypothesis = registry.create(
            HypothesisCreate(
                statement="Hypothesis for evidence",
                category=HypothesisCategory.CUSTOMER,
                impact=ImpactLevel.MEDIUM,
                risk=RiskLevel.MEDIUM,
                testability=TestabilityLevel.MEDIUM,
                success_criteria="Evidence criteria",
            )
        )

        evidence = HypothesisEvidence(
            source="Customer Interview",
            content="Customer confirmed interest",
            supports=True,
            confidence=80,
        )

        updated = registry.add_evidence(hypothesis.id, evidence)

        assert updated is not None
        assert len(updated.evidence) == 1
        assert updated.supporting_count == 1

    def test_get_statistics(self, registry):
        """Should return registry statistics"""
        registry.create(
            HypothesisCreate(
                statement="Hypothesis for stats",
                category=HypothesisCategory.MARKET,
                impact=ImpactLevel.HIGH,
                risk=RiskLevel.HIGH,
                testability=TestabilityLevel.MEDIUM,
                success_criteria="Stats criteria",
            )
        )

        stats = registry.get_statistics()

        assert stats["total"] == 1
        assert stats["untested_count"] == 1
        assert "by_category" in stats


class TestHypothesisValidator:
    """Tests for HypothesisValidator"""

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents"""
        agents = []
        for name in ["analyst", "researcher", "strategist"]:
            agent = MagicMock()
            agent.name = name
            agent.respond = AsyncMock()
            agents.append(agent)
        return agents

    @pytest.fixture
    def sample_hypothesis(self):
        """Create sample hypothesis"""
        return Hypothesis(
            id="hyp_test123",
            statement="Enterprise customers will pay $2K/month",
            category=HypothesisCategory.REVENUE,
            impact=ImpactLevel.HIGH,
            risk=RiskLevel.HIGH,
            testability=TestabilityLevel.MEDIUM,
            success_criteria="5 of 10 prospects confirm",
        )

    @pytest.fixture
    def mock_debate_result(self):
        """Create mock debate result"""
        return DebateResult(
            debate_id="debate_123",
            question="Test question",
            rounds=[
                DebateRound(
                    round_number=0,
                    responses=[
                        AgentResponse(
                            answer="The hypothesis is likely valid",
                            reasoning="Based on market analysis...",
                            confidence=85,
                            evidence=["Industry report A"],
                            agent_name="analyst",
                            model="claude",
                        ),
                        AgentResponse(
                            answer="The hypothesis appears validated",
                            reasoning="Current trends show...",
                            confidence=80,
                            evidence=["Market data B"],
                            agent_name="researcher",
                            model="gemini",
                        ),
                    ],
                    consensus_level=ConsensusLevel.MODERATE,
                )
            ],
            final_answer="The hypothesis is likely valid based on consensus",
            final_confidence=82.5,
            consensus_level=ConsensusLevel.MODERATE,
            dissenting_views=[],
            status=DebateStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            total_cost=0.5,
        )

    @pytest.mark.asyncio
    async def test_validate_hypothesis(self, mock_agents, sample_hypothesis, mock_debate_result):
        """Should validate hypothesis through debate"""
        # Setup mock
        with patch("libs.ai_arena.hypothesis.validator.DebateOrchestrator") as MockOrchestrator:
            mock_orchestrator = MagicMock()
            mock_orchestrator.debate = AsyncMock(return_value=mock_debate_result)
            MockOrchestrator.return_value = mock_orchestrator

            validator = HypothesisValidator(mock_agents)
            result = await validator.validate(sample_hypothesis)

            assert result.hypothesis_id == sample_hypothesis.id
            assert result.status in [
                HypothesisStatus.VALIDATED,
                HypothesisStatus.NEEDS_MORE_DATA,
            ]
            assert result.validation_score > 0
            assert result.debate_id == "debate_123"
            assert result.consensus_reached is True

    @pytest.mark.asyncio
    async def test_validate_updates_hypothesis(
        self, mock_agents, sample_hypothesis, mock_debate_result
    ):
        """Should update hypothesis with validation results"""
        with patch("libs.ai_arena.hypothesis.validator.DebateOrchestrator") as MockOrchestrator:
            mock_orchestrator = MagicMock()
            mock_orchestrator.debate = AsyncMock(return_value=mock_debate_result)
            MockOrchestrator.return_value = mock_orchestrator

            validator = HypothesisValidator(mock_agents)
            await validator.validate(sample_hypothesis)

            # Hypothesis should be updated
            assert sample_hypothesis.status != HypothesisStatus.UNTESTED
            assert sample_hypothesis.validation_score is not None
            assert sample_hypothesis.validated_at is not None
            assert len(sample_hypothesis.debate_results) > 0

    def test_validation_config_defaults(self):
        """Should have sensible defaults"""
        config = ValidationConfig()

        assert config.max_debate_rounds == 3
        assert config.consensus_threshold == 0.7
        assert config.validation_threshold == 70.0
        assert config.invalidation_threshold == 40.0


class TestValidationReportGenerator:
    """Tests for ValidationReportGenerator"""

    @pytest.fixture
    def generator(self):
        """Create report generator"""
        return ValidationReportGenerator()

    @pytest.fixture
    def sample_hypothesis(self):
        """Create sample hypothesis"""
        return Hypothesis(
            id="hyp_report_test",
            statement="Test hypothesis for report",
            category=HypothesisCategory.MARKET,
            impact=ImpactLevel.HIGH,
            risk=RiskLevel.HIGH,
            testability=TestabilityLevel.MEDIUM,
            success_criteria="Test criteria",
        )

    @pytest.fixture
    def sample_result(self):
        """Create sample validation result"""
        return HypothesisValidationResult(
            hypothesis_id="hyp_report_test",
            status=HypothesisStatus.VALIDATED,
            validation_score=85.0,
            debate_id="debate_456",
            consensus_reached=True,
            rounds_taken=2,
            final_answer="The hypothesis is valid",
            reasoning_summary="Multiple factors support this...",
            recommendation="Proceed with implementation",
            follow_up_questions=["What is the CAC?"],
            total_cost=0.75,
            duration_seconds=45.0,
        )

    def test_generate_single_report(self, generator, sample_hypothesis, sample_result):
        """Should generate report for single hypothesis"""
        report = generator.generate_single_report(
            hypothesis=sample_hypothesis,
            result=sample_result,
        )

        assert report.hypothesis_count == 1
        assert report.total_validated == 1
        assert report.average_confidence == 85.0
        assert len(report.key_findings) > 0
        assert len(report.recommendations) > 0

    def test_generate_batch_report(self, generator):
        """Should generate report for multiple hypotheses"""
        hypotheses = [
            Hypothesis(
                id=f"hyp_{i}",
                statement=f"Hypothesis {i}",
                category=HypothesisCategory.MARKET,
                impact=ImpactLevel.HIGH,
                risk=RiskLevel.HIGH,
                testability=TestabilityLevel.MEDIUM,
                success_criteria="Criteria",
            )
            for i in range(3)
        ]

        results = [
            HypothesisValidationResult(
                hypothesis_id=f"hyp_{i}",
                status=status,
                validation_score=score,
                debate_id=f"debate_{i}",
                consensus_reached=True,
                rounds_taken=2,
                final_answer="Answer",
                reasoning_summary="Reasoning",
                recommendation="Recommendation",
                total_cost=0.5,
                duration_seconds=30.0,
            )
            for i, (status, score) in enumerate(
                [
                    (HypothesisStatus.VALIDATED, 85.0),
                    (HypothesisStatus.INVALIDATED, 75.0),
                    (HypothesisStatus.NEEDS_MORE_DATA, 55.0),
                ]
            )
        ]

        report = generator.generate_batch_report(
            title="Test Batch Report",
            hypotheses=hypotheses,
            results=results,
        )

        assert report.hypothesis_count == 3
        assert report.total_validated == 1
        assert report.total_invalidated == 1
        assert report.total_inconclusive == 1

    def test_report_to_markdown(self, generator, sample_hypothesis, sample_result):
        """Should convert report to markdown"""
        report = generator.generate_single_report(
            hypothesis=sample_hypothesis,
            result=sample_result,
        )

        markdown = report.to_markdown()

        assert "# " in markdown  # Has headers
        assert "Test hypothesis for report" in markdown
        assert "VALIDATED" in markdown
        assert "85" in markdown  # Confidence score


class TestHypothesisEvents:
    """Tests for hypothesis event publishing"""

    def test_validation_started_event(self):
        """Should create validation started event"""
        from libs.ai_arena.hypothesis.events import HypothesisValidationStartedEvent

        event = HypothesisValidationStartedEvent(
            validation_id="val_123",
            hypothesis_id="hyp_456",
            hypothesis_statement="Test hypothesis",
            category=HypothesisCategory.REVENUE,
            agent_count=3,
            max_rounds=3,
        )

        assert event.validation_id == "val_123"
        assert event.hypothesis_id == "hyp_456"
        assert event.timestamp is not None

    def test_validation_completed_event(self):
        """Should create validation completed event"""
        from libs.ai_arena.hypothesis.events import HypothesisValidationCompletedEvent

        event = HypothesisValidationCompletedEvent(
            validation_id="val_789",
            hypothesis_id="hyp_abc",
            status=HypothesisStatus.VALIDATED,
            validation_score=85.0,
            consensus_reached=True,
            rounds_taken=2,
            final_answer="Valid hypothesis",
            recommendation="Proceed",
            total_cost=0.5,
            duration_seconds=30.0,
        )

        assert event.status == HypothesisStatus.VALIDATED
        assert event.validation_score == 85.0
        assert event.consensus_reached is True

    @pytest.mark.asyncio
    async def test_event_publisher_without_nats(self):
        """Should work without NATS (logging mode)"""
        from libs.ai_arena.hypothesis.events import HypothesisEventPublisher

        publisher = HypothesisEventPublisher(None)  # No NATS client

        # Should not raise
        await publisher.publish_validation_started(
            validation_id="val_test",
            hypothesis_id="hyp_test",
            hypothesis_statement="Test",
            category=HypothesisCategory.MARKET,
            agent_count=3,
            max_rounds=3,
        )


class TestHypothesisEvidence:
    """Tests for HypothesisEvidence model"""

    def test_create_evidence(self):
        """Should create valid evidence"""
        evidence = HypothesisEvidence(
            source="Customer Interview",
            content="Customer confirmed willingness to pay",
            supports=True,
            confidence=85,
        )

        assert evidence.source == "Customer Interview"
        assert evidence.supports is True
        assert evidence.confidence == 85
        assert evidence.id.startswith("ev_")

    def test_evidence_auto_generates_id(self):
        """Should auto-generate ID if not provided"""
        evidence1 = HypothesisEvidence(
            source="Source A",
            content="Content",
            supports=True,
        )
        evidence2 = HypothesisEvidence(
            source="Source B",
            content="Content",
            supports=False,
        )

        assert evidence1.id != evidence2.id
        assert evidence1.id.startswith("ev_")
        assert evidence2.id.startswith("ev_")
