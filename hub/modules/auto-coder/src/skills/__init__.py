"""
AutoCoder Skills - Composable coding capabilities.

Each skill is:
- Independently usable
- Discoverable via list_skills()
- Callable via MCP tools
- Composable with other skills

Usage:
    from auto_coder.skills import list_skills, get_skill

    # Discovery
    skills = list_skills(category="discover")

    # Get and use a skill
    skill_cls = get_skill("gather_requirements")
    skill = skill_cls()
    result = await skill.execute(input_data)
"""

from .base import (
    Skill,
    SkillMetadata,
    register_skill,
    get_skill,
    list_skills,
    get_skill_schema,
)

# Import all skills to trigger registration
from . import gather_requirements
from . import code_subtask
# Add more as they're created:
# from . import research_approach
# from . import write_spec
# from . import critique_spec
# from . import plan_implementation
# from . import review_qa
# from . import fix_issues

__all__ = [
    "Skill",
    "SkillMetadata",
    "register_skill",
    "get_skill",
    "list_skills",
    "get_skill_schema",
]
