# AutoCoder Module

**Autonomous Coding through The Loop**

AutoCoder wraps Auto-Claude's multi-agent coding framework for CommandCenter, enabling autonomous software development that participates in The Loop.

## Overview

```
DISCOVER -> VALIDATE -> IMPROVE -> DISCOVER...
    |          |          |
 Gatherer   Critic    Planner
 Researcher   QA      Coder
                      Fixer
```

## Quick Start

```bash
# From hub/modules/auto-coder/
uv sync

# Create a coding task
uv run auto-coder create "Add user authentication to the API"

# Check status
uv run auto-coder status <task-id>

# Approve and merge
uv run auto-coder approve <task-id>
```

## API

```bash
# Create task
curl -X POST http://localhost:8000/api/auto-coder/tasks \
  -H "Content-Type: application/json" \
  -d '{"description": "Add rate limiting", "complexity": "standard"}'

# Check status
curl http://localhost:8000/api/auto-coder/tasks/<task-id>
```

## Architecture

### The Loop Adapters

| Adapter | Phase | Auto-Claude Agents |
|---------|-------|-------------------|
| `DiscoverAdapter` | DISCOVER | gatherer, researcher |
| `ValidateAdapter` | VALIDATE | critic, qa_reviewer |
| `ImproveAdapter` | IMPROVE | writer, planner, coder, qa_fixer |

### Integration Points

- **E2B Sandboxes**: Uses `tools/agent-sandboxes/` for isolated execution
- **KnowledgeBeast**: Fetches context for coding tasks
- **Graphiti Memory**: Cross-session insights from Auto-Claude

## Configuration

```bash
# Required
ANTHROPIC_API_KEY=your-key
E2B_API_KEY=your-key

# Optional
GRAPHITI_ENABLED=true
AUTO_CODER_MODEL=claude-sonnet-4-5-20250929
```

## Dogfooding

Use AutoCoder to improve CommandCenter itself:

```bash
uv run auto-coder create "Implement VISLZR Sprint 3 mind map nodes" \
  --project /Users/danielconnolly/Projects/CommandCenter \
  --complexity complex \
  --parallel 3
```

## Dependencies

- `integrations/auto-claude-core/` - Auto-Claude agent intelligence
- `tools/agent-sandboxes/` - E2B sandbox infrastructure
- `backend/` - CommandCenter API integration

## Module Structure

```
hub/modules/auto-coder/
├── pyproject.toml          # Package configuration
├── README.md               # This file
├── src/
│   ├── adapters/           # Loop phase adapters
│   │   ├── base.py         # BaseAdapter, LoopContext
│   │   ├── discover.py     # DISCOVER phase
│   │   ├── validate.py     # VALIDATE phase
│   │   └── improve.py      # IMPROVE phase
│   ├── orchestrator/       # Task orchestration
│   │   └── task_manager.py # The Loop orchestration
│   ├── api/                # REST API (TODO)
│   └── cli/                # CLI commands (TODO)
├── prompts/                # CommandCenter-adapted prompts
└── tests/                  # Test suite
```

---

*Part of CommandCenter - The AI Operating System for Knowledge Work*
