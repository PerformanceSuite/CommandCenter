# AutoCoder Skills

Composable autonomous coding capabilities for CommandCenter agents.

## Philosophy

Each skill is a **building block**, not a monolithic service:
- Independently callable via MCP tools
- Discoverable via Skills API
- Composable in any order
- Optional Loop orchestration

## Available Skills

### DISCOVER Phase
| Skill | Description | Depends On |
|-------|-------------|------------|
| `gather_requirements` | Extract structured requirements from task | - |
| `research_approach` | Research technical approaches | gather_requirements |

### VALIDATE Phase
| Skill | Description | Depends On |
|-------|-------------|------------|
| `critique_spec` | Self-critique with ultrathink | write_spec |
| `review_qa` | QA review against acceptance criteria | code_subtask |

### IMPROVE Phase
| Skill | Description | Depends On |
|-------|-------------|------------|
| `write_spec` | Create spec document | gather_requirements |
| `plan_implementation` | Create subtask plan | write_spec |
| `code_subtask` | Implement one subtask | - (can run standalone) |
| `fix_issues` | Fix QA-reported issues | review_qa |

## MCP Tools

Each skill is exposed as: `auto_coder_{skill_id}`

```
# List available tools
GET /mcp/tools

# Call a tool
POST /mcp/tools/auto_coder_gather_requirements
{"task_description": "Add auth", "project_dir": "."}
```

## Composability Patterns

### Quick Fix (skip discovery)
```
code_subtask → review_qa → [fix_issues if needed]
```

### Full Loop
```
gather_requirements → research_approach → write_spec → critique_spec
→ plan_implementation → code_subtask (parallel) → review_qa → fix_issues
```

### Research Only
```
gather_requirements → research_approach
```

## Output Hints

Each skill output includes `suggested_next_skills` to guide composition:
```json
{
  "requirements": [...],
  "suggested_next_skills": ["research_approach", "write_spec"]
}
```
