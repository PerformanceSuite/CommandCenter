# Core Integration

## What's Included

Surgical extraction of backend agent intelligence:

- `agents/` - Planner, Coder, QA Reviewer, QA Fixer implementations
- `prompts/` - Battle-tested system prompts for each agent role
- `core/` - Claude SDK client, security model, auth
- `integrations/` - Graphiti memory, Linear, GitHub integrations
- `spec/` - Spec creation pipeline (Gatherer, Researcher, Writer, Critic)
- `context/` - Project analyzer for dynamic tooling
- `memory/` - Session memory orchestration
- `cli/` - Git worktree management
- `qa/` - QA loop and validation
- `review/` - Code review agents
- `runners/` - Agent execution runners
- `security/` - Security scanning and validation
- `services/` - Service layer components

## What's NOT Included

- Electron frontend (we have VISLZR)
- Their test suite
- CI/CD workflows
- Build scripts

## Usage

See `UPSTREAM_CLAUDE.md` for original documentation.

### Key Entry Points

```python
# Create an agent client
from core.client import create_client

client = create_client(
    project_dir=project_dir,
    spec_dir=spec_dir,
    model="claude-sonnet-4-5-20250929",
    agent_type="coder",  # planner, coder, qa_reviewer, qa_fixer
)

# Run agent session
response = client.create_agent_session(
    name="coder-agent-session",
    starting_message="Implement the feature"
)
```

## Adaptation for The Loop

These components will be wrapped by CommandCenter modules to participate in The Loop:
- DISCOVER: spec (gatherer, researcher)
- VALIDATE: agents (qa_reviewer), spec (critic)
- IMPROVE: agents (planner, coder, qa_fixer)
