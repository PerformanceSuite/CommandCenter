# Local Worktree Agents

*Replace GitHub clone with local worktrees for E2B sandboxes*

## Problem

Current E2B flow:
1. Agent clones repo from GitHub
2. No access to local config/skills (fixed with skills in repo)
3. Slow startup (full clone each time)
4. Must push to GitHub to get changes out

## Solution

Use git worktrees instead:

```
CommandCenter/
├── .worktrees/           # Agent working directories
│   ├── agent-1/          # Worktree for agent 1
│   ├── agent-2/          # Worktree for agent 2
│   └── ...
├── skills/               # Shared skills (already done)
└── ...
```

## Benefits

1. **Instant startup** - no clone, just checkout
2. **Shared skills** - all agents see same skills/
3. **Local commits** - no GitHub round-trip needed
4. **Parallel isolation** - each worktree is independent
5. **Easy cleanup** - `git worktree remove`

## Implementation

### Step 1: Worktree Manager Script

Create `tools/agent-sandboxes/worktree-manager.sh`:

```bash
#!/bin/bash
# Create a worktree for an agent task

TASK_ID=$1
BRANCH_NAME="agent/${TASK_ID}"
WORKTREE_PATH=".worktrees/${TASK_ID}"

# Create branch and worktree
git worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH" main

echo "Worktree ready at $WORKTREE_PATH"
```

### Step 2: Update obox to Use Local Mode

Add `--local` flag to obox:

```bash
uv run obox --local \
  -p "Add docstring to main.py" \
  -t 20
```

When `--local`:
- Skip GitHub clone
- Create worktree in `.worktrees/`
- Run agent in worktree directory
- On completion, agent commits to branch
- Orchestrator can merge or create PR

### Step 3: Agent Handoff Pattern

```
1. Orchestrator creates worktree + branch
2. Agent runs in worktree
3. Agent commits changes
4. Orchestrator reviews diff
5. If good: merge to main
6. Cleanup worktree
```

## File Changes Needed

| File | Change |
|------|--------|
| `tools/agent-sandboxes/apps/sandbox_workflows/src/obox/cli.py` | Add `--local` flag |
| `tools/agent-sandboxes/apps/sandbox_workflows/src/obox/local_executor.py` | New: local worktree execution |
| `tools/agent-sandboxes/worktree-manager.sh` | New: worktree lifecycle |
| `.gitignore` | Add `.worktrees/` |

## Migration

1. Keep E2B/GitHub mode for remote execution
2. Add local mode as new option
3. Default to local for single-machine work
4. Use E2B for true parallel (multiple machines)

## Commands After Implementation

```bash
# Local parallel agents (same machine, worktrees)
uv run obox --local -p "task" -f 3

# Remote parallel agents (E2B sandboxes, GitHub)
uv run obox https://github.com/... -p "task" -f 3
```
