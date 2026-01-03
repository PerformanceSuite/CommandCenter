# AutoCoder Module

**Composable Autonomous Coding for CommandCenter**

AutoCoder provides coding capabilities as composable skills that agents can discover, call, and chain together.

## Design Principles

1. **Everything is a building block** - Each skill is independently usable
2. **Agents are primary consumers** - MCP tools first, human UI second
3. **Intent crystallizes over time** - Start with one skill, add more as needed
4. **Discovery over configuration** - Skills API exposes all capabilities
5. **The Loop is optional** - Use full orchestration OR pick individual skills

## Quick Start

```python
from auto_coder.skills import list_skills, get_skill

# Discover available skills
skills = list_skills(category="discover")
print([s.id for s in skills])  # ['gather_requirements', 'research_approach']

# Use a skill directly
skill = get_skill("gather_requirements")()
result = await skill.execute(GatherRequirementsInput(
    task_description="Add user authentication",
    project_dir="."
))

print(result.requirements)
print(result.suggested_next_skills)  # ['research_approach', 'write_spec']
```

## For Agents (MCP Tools)

```
Agent: What coding tools are available?
→ Lists auto_coder_* tools

Agent: Use auto_coder_gather_requirements with {
    "task_description": "Fix the login bug",
    "project_dir": "."
}
← Returns structured requirements + suggested next skills

Agent: Use auto_coder_code_subtask with {
    "subtask": "Fix null check in auth.py",
    "project_dir": "."
}
← Returns implementation result
```

## Skill Categories

| Phase | Skills |
|-------|--------|
| **DISCOVER** | gather_requirements, research_approach |
| **VALIDATE** | critique_spec, review_qa |
| **IMPROVE** | write_spec, plan_implementation, code_subtask, fix_issues |

## Architecture

```
┌─────────────────────────────────────────────┐
│            MCP Tool Layer                   │
│  auto_coder_* tools (one per skill)         │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│           Skills Registry                   │
│  list_skills(), get_skill(), schemas        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│              Bridges                        │
│  auto_claude.py (agent logic)               │
│  sandbox.py (E2B isolation)                 │
└─────────────────────────────────────────────┘
```

## Integration Points

- **Auto-Claude Core**: `integrations/auto-claude-core/`
- **E2B Sandboxes**: `tools/agent-sandboxes/`
- **KnowledgeBeast**: Context for coding tasks
- **Skills API**: Registered for discovery

---

*Part of CommandCenter - The AI Operating System for Knowledge Work*
