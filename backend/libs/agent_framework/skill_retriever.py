"""
Skill Retriever - Fetches relevant skills from CommandCenter for agent prompts.

Queries the Skills API to find relevant patterns, architectures, and methodologies
that can help agents complete their tasks more effectively.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)

# Default API base URL - can be overridden via environment
DEFAULT_API_BASE = "http://localhost:8000/api/v1"


@dataclass
class RetrievedSkill:
    """A skill retrieved from the database."""

    slug: str
    name: str
    category: str
    description: str
    content: str
    effectiveness_score: float

    def to_prompt_section(self) -> str:
        """Format skill for inclusion in agent prompt."""
        return f"""### {self.name}
**Category:** {self.category}

{self.content}
"""


class SkillRetriever:
    """
    Retrieves relevant skills from CommandCenter's Skills API.

    Example:
        retriever = SkillRetriever()

        skills = await retriever.find_relevant(
            task="Implement WebSocket subscriptions",
            categories=["pattern", "architecture"],
            limit=3
        )

        for skill in skills:
            print(skill.name, skill.effectiveness_score)
    """

    def __init__(self, api_base: str = DEFAULT_API_BASE, timeout: float = 10.0):
        """
        Initialize skill retriever.

        Args:
            api_base: Base URL for Skills API
            timeout: Request timeout in seconds
        """
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    async def find_relevant(
        self,
        task: str,
        categories: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        limit: int = 5,
        min_effectiveness: float = 0.0,
    ) -> list[RetrievedSkill]:
        """
        Find skills relevant to a task.

        Args:
            task: Task description to match against
            categories: Filter by skill categories (pattern, architecture, methodology)
            tags: Filter by tags (domains like "agents", "infrastructure")
            limit: Maximum skills to return
            min_effectiveness: Minimum effectiveness score threshold

        Returns:
            List of relevant skills, sorted by effectiveness
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Search skills
                response = await client.post(
                    f"{self.api_base}/skills/search",
                    json={
                        "query": task,
                        "category": categories[0] if categories and len(categories) == 1 else None,
                        "tags": tags,
                        "min_effectiveness": min_effectiveness,
                        "include_private": False,
                    },
                )

                if response.status_code != 200:
                    logger.warning(
                        "skill_search_failed",
                        status=response.status_code,
                        error=response.text[:200],
                    )
                    return []

                skills_data = response.json()

                # Filter by categories if multiple provided
                if categories and len(categories) > 1:
                    skills_data = [s for s in skills_data if s.get("category") in categories]

                # Convert to RetrievedSkill objects
                skills = [
                    RetrievedSkill(
                        slug=s["slug"],
                        name=s["name"],
                        category=s["category"],
                        description=s.get("description", ""),
                        content=s.get("content", ""),
                        effectiveness_score=s.get("effectiveness_score", 0.0),
                    )
                    for s in skills_data[:limit]
                ]

                logger.info(
                    "skills_retrieved",
                    task_preview=task[:50],
                    count=len(skills),
                    skills=[s.slug for s in skills],
                )

                return skills

        except httpx.TimeoutException:
            logger.warning("skill_retrieval_timeout", task_preview=task[:50])
            return []
        except Exception as e:
            logger.warning("skill_retrieval_error", error=str(e))
            return []

    async def get_by_slug(self, slug: str) -> Optional[RetrievedSkill]:
        """
        Get a specific skill by slug.

        Args:
            slug: Skill slug (e.g., "websocket-subscription-pattern")

        Returns:
            RetrievedSkill or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.api_base}/skills/by-slug/{slug}")

                if response.status_code == 404:
                    return None

                if response.status_code != 200:
                    logger.warning("skill_get_failed", slug=slug, status=response.status_code)
                    return None

                s = response.json()
                return RetrievedSkill(
                    slug=s["slug"],
                    name=s["name"],
                    category=s["category"],
                    description=s.get("description", ""),
                    content=s.get("content", ""),
                    effectiveness_score=s.get("effectiveness_score", 0.0),
                )

        except Exception as e:
            logger.warning("skill_get_error", slug=slug, error=str(e))
            return None

    async def get_for_persona(self, persona_category: str, limit: int = 3) -> list[RetrievedSkill]:
        """
        Get skills relevant to a persona category.

        Maps persona categories to skill categories:
        - coding -> pattern, architecture
        - assessment -> methodology
        - verification -> methodology, pattern
        - synthesis -> methodology

        Args:
            persona_category: Persona category
            limit: Maximum skills to return

        Returns:
            List of relevant skills
        """
        category_mapping = {
            "coding": ["pattern", "architecture"],
            "assessment": ["methodology"],
            "verification": ["methodology", "pattern"],
            "synthesis": ["methodology"],
            "custom": ["pattern", "methodology"],
        }

        skill_categories = category_mapping.get(persona_category, ["pattern"])

        return await self.find_relevant(
            task=f"{persona_category} tasks",
            categories=skill_categories,
            limit=limit,
        )


def format_skills_for_prompt(skills: list[RetrievedSkill]) -> str:
    """
    Format a list of skills for inclusion in an agent prompt.

    Args:
        skills: List of retrieved skills

    Returns:
        Formatted string to include in prompt
    """
    if not skills:
        return ""

    sections = [
        "## Relevant Skills & Patterns\n",
        "The following skills from the knowledge base may help with this task:\n",
    ]

    for skill in skills:
        sections.append(skill.to_prompt_section())
        sections.append("")  # Blank line between skills

    return "\n".join(sections)
