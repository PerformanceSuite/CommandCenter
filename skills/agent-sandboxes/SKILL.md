---
name: agent-sandboxes
description: Run parallel Claude Code agents in isolated E2B cloud sandboxes. Use for multi-stream development tasks, comprehensive audits, or when context isolation is needed. Each agent can run Ralph loops for persistence.
---

# Agent Sandboxes (E2B + Claude Code)

Run parallel, isolated Claude Code agents in E2B cloud sandboxes. Each agent has its own context window and can run Ralph loops for persistent tasks.

## Skills Location

**Skills live in the repo at `skills/`** - not at `~/.claude/skills/`.

When an E2B agent clones CommandCenter, skills are available at:
```
./skills/
├── agent-sandboxes/SKILL.md   # This file
├── autonomy/SKILL.md
├── context-management/SKILL.md
├── infrastructure-decisions/SKILL.md
├── project-health/SKILL.md
└── repository-hygiene/SKILL.md
```

Agents should read skills from `./skills/<skill-name>/SKILL.md` relative to repo root.

## ⚠️ COMMON FAILURE MODES (Read First!)

These are the actual failures encountered. Check each before running:

### 1. CLI Syntax Error
```bash
# ❌ WRONG - there is no 'sandbox-fork' subcommand
uv run obox sandbox-fork https://github.com/...

# ✅ CORRECT - repo URL is first positional argument
uv run obox https://github.com/... -p prompt.md
```

### 2. Branch Name with `/` Breaks Logging
Branch names like `feature/skills-native` contain `/` which was interpreted as directory path in log filenames. **Fixed in code** - branches are now sanitized (`/` → `-`).

### 3. System Prompt Template Errors
The system prompt uses Python `.format()`. Any `{...}` in code blocks will be interpreted as placeholders.

```markdown
# ❌ WRONG - Python sees {GITHUB_TOKEN} as placeholder
git remote set-url origin https://${GITHUB_TOKEN}@github.com/...

# ✅ CORRECT - Double braces escape for literal output
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/...
```

Valid placeholders: `{repo_url}`, `{branch}`, `{fork_number}`, `{allowed_directories}`

### 4. Git Push Authentication
**The sandbox is isolated** - no SSH keys, no inherited env vars.

**THREE things must happen:**
1. Token in `.env` file
2. Token passed to sandbox via `env_vars` parameter (done in code)
3. Agent must run: `git remote set-url origin https://$GITHUB_TOKEN@github.com/owner/repo.git`

---

## When to Use

- **Multi-stream development**: Run 4 agents on different features simultaneously
- **Comprehensive audits**: 6 agents for security, performance, docs, tests, etc.
- **Context isolation**: Each agent gets fresh 200k context
- **Persistent parallel work**: Ralph loop in each sandbox

## Prerequisites & API Keys

### Required Keys Location

All keys should be in `~/.config/api-keys/.env.api-keys` (sourced by .zshrc):

```bash
# Check your keys
cat ~/.config/api-keys/.env.api-keys | grep -E "^(ANTHROPIC|E2B|GITHUB)"
```

Expected keys:
```bash
ANTHROPIC_API_KEY=sk-ant-...      # For Claude Code in sandboxes
E2B_API_KEY=e2b_...               # For E2B sandbox management
GITHUB_TOKEN=ghp_...              # For git push/PR operations (needs 'repo' scope)
```

**IMPORTANT**: Use classic PATs (`ghp_...`), NOT OAuth tokens (`gho_...`). OAuth tokens expire and cause push failures.

### Setup Working Directory

```bash
cd ~/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows

# Create .env from your global keys
cat > .env << EOF
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
E2B_API_KEY=${E2B_API_KEY}
GITHUB_TOKEN=${GITHUB_TOKEN}
EOF

# Verify all three are set
cat .env
```

---

## CLI Usage

### Correct Syntax

```bash
cd ~/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows

# ✅ CORRECT - repo URL is positional argument
uv run obox <repo_url> --prompt <prompt> [options]

# ❌ WRONG - no 'sandbox-fork' subcommand
uv run obox sandbox-fork <repo_url>  # THIS WILL FAIL
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--prompt` | `-p` | **Required.** Prompt text or path to .md file |
| `--branch` | `-b` | Git branch to checkout/create |
| `--forks` | `-f` | Number of parallel agents (default: 1) |
| `--model` | `-m` | Model: opus, sonnet, haiku (default: sonnet) |
| `--max-turns` | `-t` | Maximum conversation turns |

### Examples

```bash
# Single agent with inline prompt
uv run obox https://github.com/PerformanceSuite/CommandCenter \
  -p "Add tests for the auth module" \
  -b feature/auth-tests \
  -m sonnet

# Single agent with prompt file
uv run obox https://github.com/PerformanceSuite/CommandCenter \
  -p prompts/my-task.md \
  -b feature/my-task \
  -m sonnet

# Multiple parallel agents (each gets unique branch: feature/audit-1, feature/audit-2, etc.)
uv run obox https://github.com/PerformanceSuite/CommandCenter \
  -p "Audit the codebase and report findings" \
  -b feature/audit \
  -f 3 \
  -m sonnet

# With max turns limit
uv run obox https://github.com/PerformanceSuite/CommandCenter \
  -p prompts/big-task.md \
  -b feature/big-task \
  -m sonnet \
  -t 80
```

---

## Writing Task Prompts

### Template for Tasks That Push to GitHub

```markdown
# Task Title

## CRITICAL: Git Authentication

Before any git push operations, configure authentication:

```bash
git remote set-url origin https://${GITHUB_TOKEN}@github.com/<owner>/<repo>.git
git remote -v  # Verify
```

**You MUST do this before attempting to push.**

---

## Context

<describe the context>

## Your Mission

<describe what to accomplish>

## Branch

Create and work on: `<branch-name>`

## Step-by-Step Implementation

### Step 1: ...

<detailed instructions>

### Step 2: ...

<detailed instructions>

## Verification

```bash
<commands to verify work>
```

## Commit Strategy

1. `type(scope): first commit message`
2. `type(scope): second commit message`

## Push and Create PR

```bash
# Ensure remote uses token (CRITICAL!)
git remote set-url origin https://${GITHUB_TOKEN}@github.com/<owner>/<repo>.git

# Push
git push -u origin <branch-name>
```

## Completion Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Branch pushed to GitHub
```

---

## Parallel Execution Patterns

### Running 4 Streams in Parallel (via Terminal)

```bash
# Create prompts directory
mkdir -p prompts/parallel-tasks

# Create prompt files for each stream
# prompts/parallel-tasks/01-stream-a.md
# prompts/parallel-tasks/02-stream-b.md
# etc.

# Launch in separate terminals (or use osascript)
# Terminal 1:
uv run obox https://github.com/org/repo -p prompts/parallel-tasks/01-stream-a.md -b feature/stream-a -m sonnet

# Terminal 2:
uv run obox https://github.com/org/repo -p prompts/parallel-tasks/02-stream-b.md -b feature/stream-b -m sonnet

# Terminal 3:
uv run obox https://github.com/org/repo -p prompts/parallel-tasks/03-stream-c.md -b feature/stream-c -m sonnet

# Terminal 4:
uv run obox https://github.com/org/repo -p prompts/parallel-tasks/04-stream-d.md -b feature/stream-d -m sonnet
```

### Launching via osascript (from Claude)

```applescript
tell application "Terminal"
    do script "cd /path/to/sandbox_workflows && source .venv/bin/activate && uv run obox https://github.com/org/repo -p prompts/task.md -b feature/branch -m sonnet"
end tell
```

---

## Ralph Loop Inside Sandboxes

Each sandbox agent can use Ralph for persistent tasks:

```markdown
## Workflow
Use Ralph loop for persistence:

/ralph loop "Implement feature X. Run tests after each change. Fix failures before proceeding." \
  --max-iterations 15 \
  --completion-promise "All tests pass"
```

---

## Logs & Debugging

### Log Location

```bash
ls sandbox_agent_working_dir/logs/

# Format: {branch}-fork-{N}-{timestamp}.log
# Also: stream-{a,b,c,d}.log if using tee
```

### Tail Logs in Real-Time

```bash
tail -f sandbox_agent_working_dir/logs/*.log
```

### Common Log Messages

| Message | Meaning |
|---------|---------|
| `could not read Username` | Git auth not configured - token not reaching sandbox |
| `Agent execution completed` | Success, check cost/tokens |
| `ERROR: Command exited with code 128` | Git operation failed |

---

## Troubleshooting

### "Push failed" / "could not read Username"

**Root cause**: Token not reaching sandbox or git remote not configured.

```bash
# 1. Verify token is in .env
grep GITHUB_TOKEN .env

# 2. Verify it's a classic PAT (ghp_), not OAuth (gho_)
# gho_ tokens expire! ghp_ don't (unless you set expiration)

# 3. Verify token works
curl -s -H "Authorization: token $(grep GITHUB_TOKEN .env | cut -d= -f2)" \
  https://api.github.com/user | grep login

# 4. Check if task prompt includes git auth instructions
# The agent MUST run: git remote set-url origin https://${GITHUB_TOKEN}@github.com/...
```

### "Got unexpected extra argument"

**Wrong**: `uv run obox sandbox-fork https://github.com/...`
**Right**: `uv run obox https://github.com/... --prompt ...`

There is no `sandbox-fork` subcommand. The repo URL is the first positional argument.

### "E2B API error"

```bash
# Verify E2B key
grep E2B_API_KEY .env

# Check E2B dashboard for quota: https://e2b.dev/dashboard
```

### Agent Completes But Doesn't Push

1. Check if task prompt includes git auth instructions
2. Check logs for push attempt
3. Agent may have committed but failed to push - work is in sandbox (will be lost when sandbox times out!)

---

## Pre-Flight Checklist

Before running sandboxes, verify:

- [ ] **Working directory**: `cd tools/agent-sandboxes/apps/sandbox_workflows`
- [ ] **Dependencies**: `uv sync`
- [ ] **ANTHROPIC_API_KEY** in `.env`
- [ ] **E2B_API_KEY** in `.env`
- [ ] **GITHUB_TOKEN** in `.env` (classic PAT with 'repo' scope)
- [ ] **Token works**: `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user`
- [ ] **Task prompt includes git auth instructions** (if pushing)
- [ ] **CLI syntax**: `uv run obox <url> -p <prompt>` (no subcommand!)

---

## Cost Tracking

obox reports per-fork costs after completion:
- Input/output tokens
- Cost per agent
- Total run cost

**Typical costs:**
- Simple task (1 agent, 30 turns): ~$0.50-1.00
- Medium task (1 agent, 60 turns): ~$1.00-2.00
- Complex task (1 agent, 100 turns): ~$2.00-4.00
- Parallel assessment (4 agents): ~$4.00-10.00

Review costs before running large parallel jobs.

---

## Files Reference

| File | Purpose |
|------|---------|
| `.env` | API keys (ANTHROPIC, E2B, GITHUB) |
| `src/main.py` | CLI entry point |
| `src/commands/sandbox_fork.py` | Command implementation |
| `src/modules/agents.py` | Agent creation and execution |
| `src/modules/constants.py` | Configuration constants |
| `src/prompts/sandbox_fork_agent_system_prompt.md` | System prompt template |
| `sandbox_agent_working_dir/logs/` | Execution logs |
| `prompts/` | Task prompt files |
