"""
Persona Store - Simple file-based storage for agent personas.

Personas are stored as YAML files for easy editing and version control.
Each persona defines the "who" - role, expertise, personality, constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import structlog
import yaml

logger = structlog.get_logger(__name__)


@dataclass
class Persona:
    """
    Agent persona definition.

    A persona defines:
    - Who the agent is (role, expertise)
    - How it should behave (system prompt)
    - Execution hints (model, temperature, sandbox requirements)
    """

    name: str
    display_name: str
    description: str
    system_prompt: str
    category: str = "custom"  # assessment, verification, coding, synthesis, custom
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096
    requires_sandbox: bool = False
    preferred_languages: list[str] = field(default_factory=list)
    tool_permissions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "requires_sandbox": self.requires_sandbox,
            "preferred_languages": self.preferred_languages,
            "tool_permissions": self.tool_permissions,
            "tags": self.tags,
            "system_prompt": self.system_prompt,
        }


# Default personas directory
PERSONAS_DIR = Path(__file__).parent / "personas"


class PersonaStore:
    """
    File-based persona storage.

    Personas are stored as YAML files in a directory.
    Each file is named {persona_name}.yaml.

    Example:
        store = PersonaStore()

        # List all personas
        personas = store.list()

        # Get a specific persona
        coder = store.get("backend-coder")

        # Save a new persona
        store.save(my_persona)
    """

    def __init__(self, personas_dir: Optional[Path] = None):
        """
        Initialize the persona store.

        Args:
            personas_dir: Directory to store personas. Defaults to module's personas/ dir.
        """
        self.dir = personas_dir or PERSONAS_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    def list(self, category: Optional[str] = None) -> list[Persona]:
        """
        List all personas, optionally filtered by category.

        Args:
            category: Optional category filter (assessment, coding, verification, etc.)

        Returns:
            List of Persona objects, sorted by name.
        """
        personas = []

        for f in self.dir.glob("*.yaml"):
            if f.name.startswith("_"):
                continue  # Skip index/meta files
            try:
                persona = self.get(f.stem)
                if category is None or persona.category == category:
                    personas.append(persona)
            except Exception as e:
                logger.warning("failed_to_load_persona", file=f.name, error=str(e))

        return sorted(personas, key=lambda p: p.name)

    def get(self, name: str) -> Persona:
        """
        Get a persona by name.

        Args:
            name: Persona name (without .yaml extension)

        Returns:
            Persona object

        Raises:
            FileNotFoundError: If persona doesn't exist
        """
        path = self.dir / f"{name}.yaml"

        if not path.exists():
            raise FileNotFoundError(f"Persona not found: {name}")

        with open(path) as f:
            data = yaml.safe_load(f)

        return Persona(
            name=data.get("name", name),
            display_name=data.get("display_name", name),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            category=data.get("category", "custom"),
            model=data.get("model", "claude-sonnet-4-20250514"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4096),
            requires_sandbox=data.get("requires_sandbox", False),
            preferred_languages=data.get("preferred_languages", []),
            tool_permissions=data.get("tool_permissions", []),
            tags=data.get("tags", []),
        )

    def save(self, persona: Persona) -> None:
        """
        Save a persona to file.

        Args:
            persona: Persona to save
        """
        path = self.dir / f"{persona.name}.yaml"

        with open(path, "w") as f:
            yaml.dump(
                persona.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        logger.info("persona_saved", name=persona.name, path=str(path))

    def delete(self, name: str) -> bool:
        """
        Delete a persona.

        Args:
            name: Persona name to delete

        Returns:
            True if deleted, False if didn't exist
        """
        path = self.dir / f"{name}.yaml"

        if path.exists():
            path.unlink()
            logger.info("persona_deleted", name=name)
            return True

        return False

    def exists(self, name: str) -> bool:
        """Check if a persona exists."""
        return (self.dir / f"{name}.yaml").exists()
