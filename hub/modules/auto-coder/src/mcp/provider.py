"""MCP Tool Provider - exposes skills as MCP tools for agents."""
from typing import Any
from ..skills import list_skills, get_skill


class AutoCoderMCPProvider:
    """
    Exposes all registered skills as MCP tools.

    Each skill becomes a tool named: auto_coder_{skill_id}

    Agents can discover tools and call them directly without
    going through the Loop orchestrator.
    """

    def list_tools(self) -> list[dict]:
        """List all available tools (one per skill)."""
        tools = []
        for skill_meta in list_skills():
            tools.append({
                "name": f"auto_coder_{skill_meta.id}",
                "description": skill_meta.description,
                "input_schema": skill_meta.input_schema.model_json_schema(),
                "metadata": {
                    "category": skill_meta.category,
                    "phase": skill_meta.phase,
                    "depends_on": skill_meta.depends_on,
                    "examples": skill_meta.examples,
                }
            })
        return tools

    async def call_tool(self, name: str, arguments: dict) -> dict[str, Any]:
        """Execute a skill by tool name."""
        # Extract skill ID from tool name
        if not name.startswith("auto_coder_"):
            return {"error": f"Unknown tool format: {name}"}

        skill_id = name.replace("auto_coder_", "")
        skill_cls = get_skill(skill_id)

        if not skill_cls:
            available = [s.id for s in list_skills()]
            return {"error": f"Unknown skill: {skill_id}", "available": available}

        # Instantiate and execute
        skill = skill_cls()
        input_model = skill_cls.metadata().input_schema

        try:
            input_data = input_model(**arguments)
            result = await skill.execute(input_data)
            return {"success": True, "result": result.model_dump()}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton for easy import
mcp_provider = AutoCoderMCPProvider()
