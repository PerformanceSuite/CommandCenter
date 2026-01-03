# Auto-Claude Integration Plan

**Date**: 2026-01-03
**Status**: ✅ Extraction Complete
**Approach**: Surgical Extraction (Option C)

## Objective

Integrate Auto-Claude's autonomous multi-agent coding framework into CommandCenter to:
1. Accelerate CommandCenter development using Auto-Claude's battle-tested agent patterns
2. Add an "AutoCoder" capability as a CommandCenter module
3. Adopt their Graphiti memory system to enhance KnowledgeBeast/Wander

## Source Repository

- **Repo**: https://github.com/AndyMik90/Auto-Claude
- **Branch**: develop
- **License**: AGPL-3.0 (keep isolated, maintain attribution)
- **Stars**: 5.1k (mature, battle-tested)

## What We're Extracting

### ✅ Include (Backend Intelligence)
| Directory | Purpose | Value to CommandCenter |
|-----------|---------|----------------------|
| `agents/` | Planner, Coder, QA Reviewer, QA Fixer | Core agent loop patterns |
| `prompts/` | System prompts for each agent role | Battle-tested prompt engineering |
| `core/` | Client, security, auth | Claude SDK patterns, security model |
| `integrations/` | Graphiti memory, Linear, GitHub | Memory layer for Wander |
| `spec_agents/` | Gatherer, Researcher, Writer, Critic | Spec creation pipeline |
| `context/` | Project analyzer | Dynamic tooling detection |
| `memory/` | Session memory manager | Cross-session context |
| `cli/` | Worktree management | Git isolation patterns |

### ❌ Skip (We Have Alternatives)
| Directory | Reason |
|-----------|--------|
| `apps/frontend/` | We have VISLZR |
| `.github/` | Our own CI/CD |
| `tests/` | We'll write CommandCenter-specific tests |
| `scripts/` | Our own build tools |

## Target Structure

```
CommandCenter/
├── integrations/
│   └── auto-claude-core/          # ← Extracted components
│       ├── agents/
│       ├── prompts/
│       ├── core/
│       ├── integrations/
│       ├── spec_agents/
│       ├── context/
│       ├── memory/
│       ├── cli/
│       ├── requirements.txt
│       ├── .env.example
│       ├── UPSTREAM_CLAUDE.md     # Their CLAUDE.md for reference
│       └── README.md              # Our integration notes
```

## Integration with The Loop

```
Auto-Claude Agents    →    CommandCenter Mapping
─────────────────────────────────────────────────
Spec Gatherer         →    DISCOVER (Wander)
Spec Researcher       →    DISCOVER (Research Hub)
Spec Writer           →    VALIDATE (AI Arena)
Planner               →    IMPROVE (planning)
Coder                 →    IMPROVE (implementation)
QA Reviewer           →    VALIDATE (verification)
QA Fixer              →    IMPROVE (iteration)
Graphiti Memory       →    KnowledgeBeast enhancement
```

---

## Claude Code Prompt

Copy everything below the line and paste into Claude Code:

---

```
# Auto-Claude Integration Task

## Context
I'm integrating Auto-Claude (https://github.com/AndyMik90/Auto-Claude) into CommandCenter. We're doing a surgical extraction - only the backend agent intelligence, not their Electron frontend.

## Task
Execute this integration plan:

### Step 1: Clone and Extract
```bash
# Clone to temp location
git clone --depth 1 --branch develop https://github.com/AndyMik90/Auto-Claude.git /tmp/auto-claude-temp

# Create integration directory
mkdir -p /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core
```

### Step 2: Copy Core Components
```bash
cd /tmp/auto-claude-temp/apps/backend

# Copy agent intelligence
cp -r agents /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/
cp -r prompts /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/
cp -r core /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/
cp -r integrations /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/
cp -r spec_agents /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/
cp -r context /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/
cp -r memory /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/
cp -r cli /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/

# Copy config files
cp requirements.txt /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/
cp .env.example /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/

# Copy their CLAUDE.md as reference
cp /tmp/auto-claude-temp/CLAUDE.md /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/UPSTREAM_CLAUDE.md
```

### Step 3: Create Integration README
Create `/Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/README.md`:

```markdown
# Auto-Claude Core Integration

**Source**: https://github.com/AndyMik90/Auto-Claude
**Extracted**: 2026-01-03
**License**: AGPL-3.0 (upstream)

## What's Included

Surgical extraction of Auto-Claude's backend agent intelligence:

- `agents/` - Planner, Coder, QA Reviewer, QA Fixer implementations
- `prompts/` - Battle-tested system prompts for each agent role
- `core/` - Claude SDK client, security model, auth
- `integrations/` - Graphiti memory, Linear, GitHub integrations
- `spec_agents/` - Spec creation pipeline (Gatherer, Researcher, Writer, Critic)
- `context/` - Project analyzer for dynamic tooling
- `memory/` - Session memory orchestration
- `cli/` - Git worktree management

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
- DISCOVER: spec_agents (gatherer, researcher)
- VALIDATE: agents (qa_reviewer), spec_agents (critic)
- IMPROVE: agents (planner, coder, qa_fixer)

## Attribution

This code is derived from Auto-Claude by AndyMik90, licensed under AGPL-3.0.
```

### Step 4: Cleanup
```bash
rm -rf /tmp/auto-claude-temp
```

### Step 5: Verify Structure
```bash
ls -la /Users/danielconnolly/Projects/CommandCenter/integrations/auto-claude-core/
```

Expected output:
```
agents/
cli/
context/
core/
integrations/
memory/
prompts/
spec_agents/
.env.example
README.md
requirements.txt
UPSTREAM_CLAUDE.md
```

### Step 6: Git Add (but don't commit yet)
```bash
cd /Users/danielconnolly/Projects/CommandCenter
git add integrations/auto-claude-core/
git status
```

## Success Criteria
- [ ] All directories extracted successfully
- [ ] README.md created with attribution
- [ ] No Electron frontend code included
- [ ] Files staged for commit

## What's Next (Don't Do Yet)
After I verify the extraction:
1. Create a CommandCenter wrapper module at `hub/modules/auto-coder/`
2. Adapt agents to participate in The Loop
3. Wire Graphiti memory to KnowledgeBeast
4. Test by having agents work on VISLZR Sprint 3
```

---

## Post-Extraction Next Steps

After running the Claude Code prompt:

1. **Verify extraction** - Check the structure matches expected
2. **Review prompts/** - Their battle-tested prompts are gold
3. **Study `core/client.py`** - Understand their SDK integration
4. **Examine `integrations/graphiti/`** - This could replace/enhance KB's graph layer
5. **Create wrapper module** - `hub/modules/auto-coder/` to expose as CommandCenter capability
6. **Dogfood it** - Use Auto-Claude agents to help build VISLZR

## References

- [Auto-Claude README](https://github.com/AndyMik90/Auto-Claude)
- [Their CLAUDE.md](https://github.com/AndyMik90/Auto-Claude/blob/develop/CLAUDE.md) - Comprehensive architecture docs
- [Situational Awareness Doc](../SituationalAwareness.rtf) - Why autonomous coding matters now
