"""Base classes for composable coding skills."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar, Generic
from pydantic import BaseModel

T_Input = TypeVar("T_Input", bound=BaseModel)
T_Output = TypeVar("T_Output", bound=BaseModel)


@dataclass
class SkillMetadata:
    """Metadata for skill discovery via Skills API."""
    id: str
    name: str
    description: str
    category: str  # discover, validate, improve
    phase: str     # The Loop phase
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    examples: list[dict] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)


class Skill(ABC, Generic[T_Input, T_Output]):
    """
    Base class for composable coding skills.

    Each skill is:
    - Independently usable (no required orchestration)
    - Discoverable via Skills API
    - Callable via MCP tools
    - Composable with other skills
    """

    @classmethod
    @abstractmethod
    def metadata(cls) -> SkillMetadata:
        """Return skill metadata for discovery."""
        pass

    @abstractmethod
    async def execute(self, input: T_Input, context: dict | None = None) -> T_Output:
        """
        Execute the skill.

        Args:
            input: Validated input data
            context: Optional context from previous skills (loose coupling)

        Returns:
            Skill output with suggested_next_skills for composability hints
        """
        pass

    def get_prompt(self) -> str:
        """Get the prompt template for this skill."""
        prompt_path = Path(__file__).parents[2] / "prompts" / f"{self.metadata().id}.md"
        return prompt_path.read_text() if prompt_path.exists() else ""


# ============================================================================
# Skill Registry - enables discovery
# ============================================================================

_SKILL_REGISTRY: dict[str, type[Skill]] = {}


def register_skill(skill_cls: type[Skill]) -> type[Skill]:
    """Decorator to register a skill for discovery."""
    metadata = skill_cls.metadata()
    _SKILL_REGISTRY[metadata.id] = skill_cls
    return skill_cls


def get_skill(skill_id: str) -> type[Skill] | None:
    """Get a skill class by ID."""
    return _SKILL_REGISTRY.get(skill_id)


def list_skills(category: str | None = None, phase: str | None = None) -> list[SkillMetadata]:
    """
    List all registered skills.

    Args:
        category: Filter by category (discover, validate, improve)
        phase: Filter by Loop phase (DISCOVER, VALIDATE, IMPROVE)
    """
    skills = [cls.metadata() for cls in _SKILL_REGISTRY.values()]

    if category:
        skills = [s for s in skills if s.category == category]
    if phase:
        skills = [s for s in skills if s.phase == phase]

    return skills


def get_skill_schema(skill_id: str) -> dict | None:
    """Get JSON schema for a skill's input/output."""
    skill_cls = get_skill(skill_id)
    if not skill_cls:
        return None

    meta = skill_cls.metadata()
    return {
        "id": meta.id,
        "input_schema": meta.input_schema.model_json_schema(),
        "output_schema": meta.output_schema.model_json_schema(),
    }
