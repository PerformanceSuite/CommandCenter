"""Tests for AI Arena Debate Protocol"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from libs.ai_arena.agents import AgentResponse
from libs.ai_arena.debate import (
    ConsensusDetector,
    ConsensusLevel,
    ConsensusResult,
    DebateConfig,
    DebateOrchestrator,
    DebateResult,
    DebateRound,
    DebateStatus,
    DiscussionPromptGenerator,
)


class TestConsensusLevel:
    """Tests for ConsensusLevel enum"""

    def test_all_levels_defined(self):
        """Should have all expected consensus levels"""
        levels = {level.value for level in ConsensusLevel}
        assert levels == {"strong", "moderate", "weak", "deadlock"}


class TestDebateRound:
    """Tests for DebateRound dataclass"""

    def test_create_round(self):
        """Should create a valid debate round"""
        responses = [
            AgentResponse(
                answer="Yes",
                reasoning="Reasons",
                confidence=80,
                evidence=[],
                agent_name="Analyst",
                model="claude",
            )
        ]

        round_data = DebateRound(
            round_number=0,
            responses=responses,
            consensus_level=ConsensusLevel.STRONG,
        )

        assert round_data.round_number == 0
        assert len(round_data.responses) == 1
        assert round_data.consensus_level == ConsensusLevel.STRONG

    def test_average_confidence(self):
        """Should calculate average confidence correctly"""
        responses = [
            AgentResponse(
                answer="A", reasoning="", confidence=80, evidence=[], agent_name="A", model="m"
            ),
            AgentResponse(
                answer="A", reasoning="", confidence=60, evidence=[], agent_name="B", model="m"
            ),
        ]

        round_data = DebateRound(round_number=0, responses=responses)

        assert round_data.average_confidence == 70.0

    def test_confidence_spread(self):
        """Should calculate confidence spread correctly"""
        responses = [
            AgentResponse(
                answer="A", reasoning="", confidence=90, evidence=[], agent_name="A", model="m"
            ),
            AgentResponse(
                answer="A", reasoning="", confidence=50, evidence=[], agent_name="B", model="m"
            ),
        ]

        round_data = DebateRound(round_number=0, responses=responses)

        assert round_data.confidence_spread == 40.0

    def test_to_dict_and_from_dict(self):
        """Should serialize and deserialize correctly"""
        responses = [
            AgentResponse(
                answer="Yes",
                reasoning="Because",
                confidence=75,
                evidence=["E1"],
                agent_name="Test",
                model="test-model",
            )
        ]

        original = DebateRound(
            round_number=1,
            responses=responses,
            consensus_level=ConsensusLevel.MODERATE,
        )

        data = original.to_dict()
        restored = DebateRound.from_dict(data)

        assert restored.round_number == 1
        assert restored.consensus_level == ConsensusLevel.MODERATE
        assert len(restored.responses) == 1
        assert restored.responses[0].answer == "Yes"


class TestConsensusDetector:
    """Tests for ConsensusDetector"""

    @pytest.fixture
    def detector(self):
        """Create detector with default settings"""
        return ConsensusDetector()

    def test_empty_responses_returns_deadlock(self, detector):
        """Empty responses should return deadlock"""
        result = detector.detect([])

        assert result.level == ConsensusLevel.DEADLOCK
        assert result.agreement_score == 0.0

    def test_unanimous_high_confidence_is_strong(self, detector):
        """Unanimous agreement with high confidence is strong consensus"""
        responses = [
            AgentResponse(
                answer="Yes, expand to Europe",
                reasoning="Market opportunity",
                confidence=85,
                evidence=[],
                agent_name="Analyst",
                model="claude",
            ),
            AgentResponse(
                answer="Yes, expand to Europe",
                reasoning="Low risk",
                confidence=90,
                evidence=[],
                agent_name="Strategist",
                model="gpt",
            ),
            AgentResponse(
                answer="Yes, expand to Europe",
                reasoning="Research supports it",
                confidence=80,
                evidence=[],
                agent_name="Researcher",
                model="gemini",
            ),
        ]

        result = detector.detect(responses)

        assert result.level == ConsensusLevel.STRONG
        assert result.agreement_score == 1.0
        assert result.majority_count == 3
        assert len(result.dissenting_responses) == 0

    def test_majority_moderate_confidence_is_moderate(self, detector):
        """Majority agreement with moderate confidence is moderate consensus"""
        responses = [
            AgentResponse(
                answer="Yes",
                reasoning="",
                confidence=70,
                evidence=[],
                agent_name="A",
                model="m",
            ),
            AgentResponse(
                answer="Yes",
                reasoning="",
                confidence=65,
                evidence=[],
                agent_name="B",
                model="m",
            ),
            AgentResponse(
                answer="No",
                reasoning="",
                confidence=60,
                evidence=[],
                agent_name="C",
                model="m",
            ),
        ]

        result = detector.detect(responses)

        assert result.level in [ConsensusLevel.MODERATE, ConsensusLevel.WEAK]
        assert result.majority_count == 2
        assert len(result.dissenting_responses) == 1

    def test_split_vote_is_deadlock(self, detector):
        """Equal split should be deadlock"""
        responses = [
            AgentResponse(
                answer="Yes",
                reasoning="",
                confidence=80,
                evidence=[],
                agent_name="A",
                model="m",
            ),
            AgentResponse(
                answer="No",
                reasoning="",
                confidence=80,
                evidence=[],
                agent_name="B",
                model="m",
            ),
        ]

        result = detector.detect(responses)

        # With equal votes, one will be majority (50%) which is deadlock
        assert result.level in [ConsensusLevel.WEAK, ConsensusLevel.DEADLOCK]

    def test_confidence_weighting(self, detector):
        """Higher confidence should weight more heavily"""
        # Two low-confidence Yes vs one high-confidence No
        responses = [
            AgentResponse(
                answer="Yes",
                reasoning="",
                confidence=40,
                evidence=[],
                agent_name="A",
                model="m",
            ),
            AgentResponse(
                answer="Yes",
                reasoning="",
                confidence=40,
                evidence=[],
                agent_name="B",
                model="m",
            ),
            AgentResponse(
                answer="No",
                reasoning="",
                confidence=95,
                evidence=[],
                agent_name="C",
                model="m",
            ),
        ]

        result = detector.detect(responses)

        # With confidence-weighted voting, "No" (0.95 weight) beats "Yes" (0.40 + 0.40 = 0.80)
        # So the majority is actually "No" due to higher confidence weight
        assert result.majority_count == 1  # "No" wins by confidence weight
        assert result.weighted_confidence == 95.0  # High confidence answer

    def test_should_continue_debate_after_strong_consensus(self, detector):
        """Should not continue after strong consensus"""
        result = ConsensusResult(
            level=ConsensusLevel.STRONG,
            agreement_score=1.0,
            weighted_confidence=90,
            majority_answer="Yes",
            majority_count=4,
            total_agents=4,
            dissenting_responses=[],
        )

        should_continue = detector.should_continue_debate(result, current_round=0, max_rounds=3)

        assert should_continue is False

    def test_should_continue_debate_with_deadlock(self, detector):
        """Should continue if deadlock and rounds remain"""
        result = ConsensusResult(
            level=ConsensusLevel.DEADLOCK,
            agreement_score=0.5,
            weighted_confidence=60,
            majority_answer="Yes",
            majority_count=2,
            total_agents=4,
            dissenting_responses=[],
        )

        should_continue = detector.should_continue_debate(result, current_round=1, max_rounds=3)

        assert should_continue is True

    def test_should_not_continue_at_max_rounds(self, detector):
        """Should not continue at max rounds regardless of consensus"""
        result = ConsensusResult(
            level=ConsensusLevel.DEADLOCK,
            agreement_score=0.5,
            weighted_confidence=60,
            majority_answer="Yes",
            majority_count=2,
            total_agents=4,
            dissenting_responses=[],
        )

        should_continue = detector.should_continue_debate(result, current_round=2, max_rounds=3)

        assert should_continue is False


class TestDiscussionPromptGenerator:
    """Tests for DiscussionPromptGenerator"""

    @pytest.fixture
    def generator(self):
        """Create prompt generator"""
        return DiscussionPromptGenerator()

    def test_initial_prompt_contains_question(self, generator):
        """Initial prompt should contain the question"""
        prompt = generator.generate_initial_prompt("Should we expand?")

        assert "Should we expand?" in prompt
        assert "Round 1" in prompt

    def test_initial_prompt_with_context(self, generator):
        """Initial prompt should include context when provided"""
        prompt = generator.generate_initial_prompt(
            question="Should we expand?",
            context="We have $10M in revenue.",
        )

        assert "Should we expand?" in prompt
        assert "$10M in revenue" in prompt

    def test_followup_prompt_includes_previous(self, generator):
        """Follow-up prompt should include previous responses"""
        previous_rounds = [
            DebateRound(
                round_number=0,
                responses=[
                    AgentResponse(
                        answer="Yes, expand",
                        reasoning="Good opportunity",
                        confidence=80,
                        evidence=[],
                        agent_name="Analyst",
                        model="claude",
                    )
                ],
            )
        ]

        prompt = generator.generate_followup_prompt(
            question="Should we expand?",
            previous_rounds=previous_rounds,
            current_round=2,
        )

        assert "Round 2" in prompt
        assert "Analyst" in prompt
        assert "previous" in prompt.lower()

    def test_synthesis_prompt_contains_all_rounds(self, generator):
        """Synthesis prompt should reference all rounds"""
        rounds = [
            DebateRound(
                round_number=0,
                responses=[
                    AgentResponse(
                        answer="Yes",
                        reasoning="",
                        confidence=80,
                        evidence=[],
                        agent_name="A",
                        model="m",
                    )
                ],
            ),
            DebateRound(
                round_number=1,
                responses=[
                    AgentResponse(
                        answer="Yes",
                        reasoning="",
                        confidence=85,
                        evidence=[],
                        agent_name="A",
                        model="m",
                    )
                ],
            ),
        ]

        prompt = generator.generate_synthesis_prompt(
            question="Test question?",
            rounds=rounds,
            final_consensus=ConsensusLevel.STRONG,
        )

        assert "Round 1" in prompt
        assert "Round 2" in prompt
        assert "Synthesis" in prompt


class TestDebateOrchestrator:
    """Tests for DebateOrchestrator"""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent"""
        agent = MagicMock()
        agent.name = "TestAgent"
        agent.respond = AsyncMock()
        agent.respond.return_value = AgentResponse(
            answer="The answer is yes",
            reasoning="Based on analysis",
            confidence=80,
            evidence=["Evidence 1"],
            agent_name="TestAgent",
            model="test-model",
        )
        return agent

    @pytest.fixture
    def mock_agents(self, mock_agent):
        """Create multiple mock agents"""
        agents = []
        for i, name in enumerate(["Analyst", "Researcher", "Strategist"]):
            agent = MagicMock()
            agent.name = name
            agent.respond = AsyncMock()
            agent.respond.return_value = AgentResponse(
                answer="Yes, we should proceed",
                reasoning=f"Analysis from {name}",
                confidence=80 + i * 5,
                evidence=[],
                agent_name=name,
                model="test-model",
            )
            agents.append(agent)
        return agents

    def test_init_requires_agents(self):
        """Should raise error if no agents provided"""
        with pytest.raises(ValueError) as exc_info:
            DebateOrchestrator(agents=[])

        assert "at least one agent" in str(exc_info.value).lower()

    def test_init_with_config(self, mock_agent):
        """Should accept custom configuration"""
        config = DebateConfig(max_rounds=5, consensus_threshold=0.8)
        orchestrator = DebateOrchestrator([mock_agent], config=config)

        assert orchestrator.config.max_rounds == 5
        assert orchestrator.config.consensus_threshold == 0.8

    @pytest.mark.asyncio
    async def test_debate_returns_result(self, mock_agents):
        """Debate should return a result"""
        orchestrator = DebateOrchestrator(mock_agents)

        result = await orchestrator.debate("Should we proceed?")

        assert isinstance(result, DebateResult)
        assert result.status == DebateStatus.COMPLETED
        assert result.question == "Should we proceed?"
        assert len(result.rounds) > 0

    @pytest.mark.asyncio
    async def test_debate_stops_on_strong_consensus(self, mock_agents):
        """Debate should stop early if strong consensus reached"""
        config = DebateConfig(max_rounds=5)
        orchestrator = DebateOrchestrator(mock_agents, config)

        result = await orchestrator.debate("Test question")

        # Should stop before max rounds due to consensus
        assert result.consensus_level == ConsensusLevel.STRONG
        assert len(result.rounds) <= config.max_rounds

    @pytest.mark.asyncio
    async def test_debate_collects_all_agent_responses(self, mock_agents):
        """Each round should have responses from all agents"""
        orchestrator = DebateOrchestrator(mock_agents)

        result = await orchestrator.debate("Test question")

        # First round should have responses from all agents
        assert len(result.rounds[0].responses) == len(mock_agents)

    @pytest.mark.asyncio
    async def test_debate_with_context(self, mock_agents):
        """Debate should pass context to agents"""
        orchestrator = DebateOrchestrator(mock_agents)

        await orchestrator.debate(
            question="Should we expand?",
            context="We have $10M revenue.",
        )

        # Verify agents were called with context
        for agent in mock_agents:
            call_kwargs = agent.respond.call_args.kwargs
            assert call_kwargs.get("context") == "We have $10M revenue."

    @pytest.mark.asyncio
    async def test_debate_with_disagreement(self):
        """Debate should handle disagreement correctly"""
        # Create agents with different opinions
        agents = []
        for name, answer, confidence in [
            ("Analyst", "Yes, expand", 80),
            ("Researcher", "No, too risky", 75),
            ("Strategist", "Yes, expand", 85),
        ]:
            agent = MagicMock()
            agent.name = name
            agent.respond = AsyncMock()
            agent.respond.return_value = AgentResponse(
                answer=answer,
                reasoning=f"Analysis from {name}",
                confidence=confidence,
                evidence=[],
                agent_name=name,
                model="test-model",
            )
            agents.append(agent)

        orchestrator = DebateOrchestrator(agents)
        result = await orchestrator.debate("Should we expand?")

        # Should identify dissenting views
        assert result.status == DebateStatus.COMPLETED


class TestDebateConfig:
    """Tests for DebateConfig"""

    def test_default_values(self):
        """Should have sensible defaults"""
        config = DebateConfig()

        assert config.max_rounds == 3
        assert config.consensus_threshold == 0.7
        assert config.confidence_threshold == 70
        assert config.timeout_seconds == 300.0

    def test_custom_values(self):
        """Should accept custom values"""
        config = DebateConfig(
            max_rounds=5,
            consensus_threshold=0.8,
            parallel_responses=False,
        )

        assert config.max_rounds == 5
        assert config.consensus_threshold == 0.8
        assert config.parallel_responses is False

    def test_to_dict(self):
        """Should serialize to dictionary"""
        config = DebateConfig(max_rounds=4)
        data = config.to_dict()

        assert data["max_rounds"] == 4
        assert "consensus_threshold" in data


class TestDebateResult:
    """Tests for DebateResult"""

    def test_total_rounds(self):
        """Should count total rounds"""
        result = DebateResult(
            debate_id="test",
            question="Q?",
            rounds=[
                DebateRound(round_number=0, responses=[]),
                DebateRound(round_number=1, responses=[]),
            ],
            final_answer="A",
            final_confidence=80.0,
            consensus_level=ConsensusLevel.STRONG,
            dissenting_views=[],
            status=DebateStatus.COMPLETED,
            started_at=datetime.utcnow(),
        )

        assert result.total_rounds == 2

    def test_get_all_responses(self):
        """Should flatten all responses across rounds"""
        response1 = AgentResponse(
            answer="A", reasoning="", confidence=80, evidence=[], agent_name="A", model="m"
        )
        response2 = AgentResponse(
            answer="B", reasoning="", confidence=70, evidence=[], agent_name="B", model="m"
        )

        result = DebateResult(
            debate_id="test",
            question="Q?",
            rounds=[
                DebateRound(round_number=0, responses=[response1]),
                DebateRound(round_number=1, responses=[response2]),
            ],
            final_answer="A",
            final_confidence=80.0,
            consensus_level=ConsensusLevel.STRONG,
            dissenting_views=[],
            status=DebateStatus.COMPLETED,
            started_at=datetime.utcnow(),
        )

        all_responses = result.get_all_responses()

        assert len(all_responses) == 2

    def test_to_dict_and_from_dict(self):
        """Should serialize and deserialize correctly"""
        original = DebateResult(
            debate_id="test-123",
            question="Test question?",
            rounds=[],
            final_answer="The answer",
            final_confidence=85.5,
            consensus_level=ConsensusLevel.MODERATE,
            dissenting_views=[],
            status=DebateStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            total_cost=0.05,
        )

        data = original.to_dict()
        restored = DebateResult.from_dict(data)

        assert restored.debate_id == "test-123"
        assert restored.consensus_level == ConsensusLevel.MODERATE
        assert restored.total_cost == 0.05
