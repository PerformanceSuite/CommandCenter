"""
Agent Registry for AI Arena

Manages agent lifecycle, creation, and access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from .agents import AnalystAgent, BaseAgent, CriticAgent, ResearcherAgent, StrategistAgent

if TYPE_CHECKING:
    from libs.llm_gateway import LLMGateway

logger = structlog.get_logger(__name__)


# Map of agent role to agent class
AGENT_TYPES: dict[str, type[BaseAgent]] = {
    "analyst": AnalystAgent,
    "researcher": ResearcherAgent,
    "strategist": StrategistAgent,
    "critic": CriticAgent,
}


class AgentRegistry:
    """
    Registry for managing AI Arena agents.

    Provides centralized creation, storage, and access to agents.
    Supports both predefined agent types and custom configurations.

    Example:
        gateway = LLMGateway()
        registry = AgentRegistry(gateway)

        # Create default debate team
        registry.create_default_team()

        # Get specific agent
        analyst = registry.get("analyst")

        # List all agents
        for agent in registry.list_agents():
            print(agent.name, agent.provider)
    """

    def __init__(self, gateway: LLMGateway):
        """
        Initialize the agent registry.

        Args:
            gateway: LLMGateway instance shared by all agents
        """
        self.gateway = gateway
        self._agents: dict[str, BaseAgent] = {}

    def create(
        self,
        role: str,
        name: str | None = None,
        provider: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> BaseAgent:
        """
        Create and register an agent.

        Args:
            role: Agent role ('analyst', 'researcher', 'strategist', 'critic')
            name: Optional custom name (defaults to role capitalized)
            provider: Optional provider override
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Created agent instance

        Raises:
            ValueError: If role is unknown
        """
        if role not in AGENT_TYPES:
            raise ValueError(f"Unknown agent role: {role}. Available: {list(AGENT_TYPES.keys())}")

        agent_class = AGENT_TYPES[role]
        agent_name = name or role.capitalize()

        agent = agent_class(
            gateway=self.gateway,
            name=agent_name,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self._agents[agent_name.lower()] = agent
        logger.info(
            "agent_created",
            name=agent_name,
            role=role,
            provider=agent.provider,
        )

        return agent

    def register(self, agent: BaseAgent) -> None:
        """
        Register an existing agent instance.

        Args:
            agent: Agent to register
        """
        self._agents[agent.name.lower()] = agent
        logger.info(
            "agent_registered",
            name=agent.name,
            role=agent.role,
            provider=agent.provider,
        )

    def get(self, name: str) -> BaseAgent | None:
        """
        Get an agent by name.

        Args:
            name: Agent name (case-insensitive)

        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(name.lower())

    def remove(self, name: str) -> bool:
        """
        Remove an agent from the registry.

        Args:
            name: Agent name (case-insensitive)

        Returns:
            True if agent was removed, False if not found
        """
        key = name.lower()
        if key in self._agents:
            del self._agents[key]
            logger.info("agent_removed", name=name)
            return True
        return False

    def list_agents(self) -> list[BaseAgent]:
        """
        List all registered agents.

        Returns:
            List of agent instances
        """
        return list(self._agents.values())

    def list_names(self) -> list[str]:
        """
        List names of all registered agents.

        Returns:
            List of agent names
        """
        return [agent.name for agent in self._agents.values()]

    def clear(self) -> None:
        """Remove all agents from registry."""
        self._agents.clear()
        logger.info("registry_cleared")

    def create_default_team(self) -> list[BaseAgent]:
        """
        Create the default debate team with one of each role.

        Returns:
            List of created agents [Analyst, Researcher, Strategist, Critic]
        """
        agents = []
        for role in AGENT_TYPES:
            agent = self.create(role)
            agents.append(agent)

        logger.info(
            "default_team_created",
            agents=[a.name for a in agents],
        )

        return agents

    def __len__(self) -> int:
        """Return number of registered agents."""
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        """Check if agent is registered."""
        return name.lower() in self._agents

    def __iter__(self):
        """Iterate over registered agents."""
        return iter(self._agents.values())
