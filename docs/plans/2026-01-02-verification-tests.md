# Verification Test Cases
*Run these before scaling to parallel agents*

## Test 1: Skill Reading

```bash
cd ~/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows

uv run obox sandbox-fork https://github.com/dconnolly-slalom/CommandCenter \
  --prompt "Read ~/.claude/skills/agent-sandboxes/SKILL.md and summarize what it teaches in 3 bullet points. Then exit." \
  --branch main \
  --model sonnet \
  -t 20
```

**Pass criteria**: Accurate 3-bullet summary
**Time budget**: 2 minutes

## Test 2: Small Code Change

```bash
uv run obox sandbox-fork https://github.com/dconnolly-slalom/CommandCenter \
  --prompt "Add a one-line docstring to the first function in backend/app/main.py that lacks one. Commit with message 'docs: add docstring'. Push to branch test/docstring-addition." \
  --branch main \
  --model sonnet \
  -t 30
```

**Pass criteria**: Valid commit, correct docstring, pushed
**Time budget**: 5 minutes

## Test 3: Skill Improvement

```bash
uv run obox sandbox-fork https://github.com/dconnolly-slalom/CommandCenter \
  --prompt "Try to follow the agent-sandboxes skill to run a simple task. Document any unclear instructions or missing info. Create a PR with improvements to the SKILL.md file." \
  --branch main \
  --model sonnet \
  -t 50
```

**Pass criteria**: PR with meaningful improvements
**Time budget**: 10 minutes

## Scoring

| Test | Pass | Partial | Fail |
|------|------|---------|------|
| 1: Read skill | Accurate summary | Minor errors | Can't find/read |
| 2: Code change | Valid commit pushed | Commit but errors | No commit |
| 3: Skill improve | Useful PR | PR but trivial | No PR |

**Proceed to Phase 2 only if**: All 3 tests pass or partial
