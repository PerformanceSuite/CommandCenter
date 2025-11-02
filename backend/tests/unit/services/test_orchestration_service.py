"""Unit tests for ResearchAgentOrchestrator service."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.research_agent_orchestrator import (
    AgentRole,
    ResearchAgent,
    ResearchAgentOrchestrator,
)


@pytest.mark.unit
class TestResearchAgentOrchestrator:
    """Test ResearchAgentOrchestrator class"""

    @pytest.mark.asyncio
    async def test_orchestration_patterns(self):
        """ResearchAgentOrchestrator coordinates multiple agents."""
        orchestrator = ResearchAgentOrchestrator()

        # Mock the execute method on ResearchAgent
        mock_results = [
            {"role": "deep_researcher", "findings": "Test findings", "status": "completed"},
            {"role": "comparator", "findings": "Comparison results", "status": "completed"},
        ]

        with patch.object(ResearchAgent, "execute", new_callable=AsyncMock) as mock_execute:
            # Set up mock to return different results based on call order
            mock_execute.side_effect = mock_results

            tasks = [
                {"role": "deep_researcher", "prompt": "Research Python"},
                {"role": "comparator", "prompt": "Compare Python vs Ruby"},
            ]

            results = await orchestrator.launch_parallel_research(tasks)

            # Verify results
            assert len(results) == 2
            assert results[0]["role"] == "deep_researcher"
            assert results[1]["role"] == "comparator"
            assert mock_execute.call_count == 2

    @pytest.mark.asyncio
    async def test_service_coordination_with_failures(self):
        """ResearchAgentOrchestrator handles agent failures gracefully."""
        orchestrator = ResearchAgentOrchestrator()

        with patch.object(ResearchAgent, "execute", new_callable=AsyncMock) as mock_execute:
            # First agent succeeds, second fails
            mock_execute.side_effect = [
                {"role": "deep_researcher", "findings": "Success"},
                Exception("Agent execution failed"),
            ]

            tasks = [
                {"role": "deep_researcher", "prompt": "Research topic 1"},
                {"role": "comparator", "prompt": "Research topic 2"},
            ]

            results = await orchestrator.launch_parallel_research(tasks)

            # Should have 2 results (one success, one error)
            assert len(results) == 2
            assert results[0]["findings"] == "Success"
            assert "error" in results[1]
            assert "Agent execution failed" in results[1]["error"]
