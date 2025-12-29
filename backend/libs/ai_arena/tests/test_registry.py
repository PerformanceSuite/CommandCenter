"""Tests for AgentRegistry"""

from unittest.mock import MagicMock

import pytest
from libs.ai_arena import AGENT_TYPES, AgentRegistry
from libs.ai_arena.agents import AnalystAgent, CriticAgent, ResearcherAgent, StrategistAgent


class TestAgentRegistry:
    """Tests for AgentRegistry"""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway"""
        return MagicMock()

    @pytest.fixture
    def registry(self, mock_gateway):
        """Create registry with mock gateway"""
        return AgentRegistry(mock_gateway)

    def test_create_analyst(self, registry):
        """Should create analyst agent"""
        agent = registry.create("analyst")

        assert isinstance(agent, AnalystAgent)
        assert agent.name == "Analyst"
        assert agent.provider == "claude"

    def test_create_researcher(self, registry):
        """Should create researcher agent"""
        agent = registry.create("researcher")

        assert isinstance(agent, ResearcherAgent)
        assert agent.name == "Researcher"
        assert agent.provider == "gemini"

    def test_create_strategist(self, registry):
        """Should create strategist agent"""
        agent = registry.create("strategist")

        assert isinstance(agent, StrategistAgent)
        assert agent.name == "Strategist"
        assert agent.provider == "gpt"

    def test_create_critic(self, registry):
        """Should create critic agent"""
        agent = registry.create("critic")

        assert isinstance(agent, CriticAgent)
        assert agent.name == "Critic"
        assert agent.provider == "claude"

    def test_create_with_custom_name(self, registry):
        """Should create agent with custom name"""
        agent = registry.create("analyst", name="DataExpert")

        assert agent.name == "DataExpert"

    def test_create_with_custom_provider(self, registry):
        """Should create agent with custom provider"""
        agent = registry.create("analyst", provider="gpt")

        assert agent.provider == "gpt"

    def test_create_unknown_role_raises(self, registry):
        """Should raise error for unknown role"""
        with pytest.raises(ValueError) as exc_info:
            registry.create("unknown_role")

        assert "Unknown agent role" in str(exc_info.value)

    def test_get_agent(self, registry):
        """Should retrieve agent by name"""
        registry.create("analyst")

        agent = registry.get("analyst")

        assert agent is not None
        assert agent.role == "analyst"

    def test_get_case_insensitive(self, registry):
        """Should retrieve agent case-insensitively"""
        registry.create("analyst", name="MyAnalyst")

        assert registry.get("myanalyst") is not None
        assert registry.get("MYANALYST") is not None

    def test_get_missing_returns_none(self, registry):
        """Should return None for missing agent"""
        result = registry.get("nonexistent")

        assert result is None

    def test_remove_agent(self, registry):
        """Should remove agent from registry"""
        registry.create("analyst")
        assert "analyst" in registry

        result = registry.remove("analyst")

        assert result is True
        assert "analyst" not in registry

    def test_remove_missing_returns_false(self, registry):
        """Should return False when removing nonexistent agent"""
        result = registry.remove("nonexistent")

        assert result is False

    def test_list_agents(self, registry):
        """Should list all registered agents"""
        registry.create("analyst")
        registry.create("critic")

        agents = registry.list_agents()

        assert len(agents) == 2
        roles = {a.role for a in agents}
        assert roles == {"analyst", "critic"}

    def test_list_names(self, registry):
        """Should list agent names"""
        registry.create("analyst")
        registry.create("researcher")

        names = registry.list_names()

        assert set(names) == {"Analyst", "Researcher"}

    def test_clear(self, registry):
        """Should remove all agents"""
        registry.create("analyst")
        registry.create("critic")
        assert len(registry) == 2

        registry.clear()

        assert len(registry) == 0

    def test_create_default_team(self, registry):
        """Should create all four agent types"""
        agents = registry.create_default_team()

        assert len(agents) == 4
        assert len(registry) == 4

        roles = {a.role for a in agents}
        assert roles == {"analyst", "researcher", "strategist", "critic"}

    def test_len(self, registry):
        """Should return number of agents"""
        assert len(registry) == 0

        registry.create("analyst")
        assert len(registry) == 1

        registry.create("critic")
        assert len(registry) == 2

    def test_contains(self, registry):
        """Should check if agent is registered"""
        registry.create("analyst")

        assert "analyst" in registry
        assert "critic" not in registry

    def test_iter(self, registry):
        """Should iterate over agents"""
        registry.create("analyst")
        registry.create("critic")

        agents = list(registry)

        assert len(agents) == 2

    def test_register_external_agent(self, registry, mock_gateway):
        """Should register externally created agent"""
        agent = AnalystAgent(gateway=mock_gateway, name="ExternalAnalyst")

        registry.register(agent)

        assert registry.get("externalanalyst") is agent


class TestAgentTypes:
    """Tests for AGENT_TYPES constant"""

    def test_all_roles_defined(self):
        """Should have all expected roles"""
        expected = {"analyst", "researcher", "strategist", "critic"}
        assert set(AGENT_TYPES.keys()) == expected

    def test_correct_agent_classes(self):
        """Should map to correct agent classes"""
        assert AGENT_TYPES["analyst"] == AnalystAgent
        assert AGENT_TYPES["researcher"] == ResearcherAgent
        assert AGENT_TYPES["strategist"] == StrategistAgent
        assert AGENT_TYPES["critic"] == CriticAgent
