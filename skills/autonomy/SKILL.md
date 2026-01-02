---
name: autonomy
description: Patterns for long-running autonomous agent workflows using Ralph loop, stop hooks, and safety parameters. Use when tasks require persistence beyond a single response cycle, such as TDD loops, complex refactoring, or multi-step implementations.
---

# Autonomous Agentic Workflows

Run long-duration tasks that persist until completion using deterministic control loops.

## Core Concept

LLMs are non-deterministic. Autonomous loops use **deterministic controls** (stop hooks) to steer them toward completion. The stop hook intercepts exit attempts and re-injects the task until success criteria are met.

## When to Use

✅ **Good for:**
- Test-driven development (code → test → fix loop)
- Multi-step task lists (work through todo.md)
- Large refactoring (iterate until tests pass)
- Complex implementations (persist until done)

❌ **Not for:**
- Simple single-response tasks
- Exploratory conversations
- Tasks without clear completion criteria

## Ralph Wiggum Loop

Ralph is the official Anthropic plugin for persistent loops.

### Basic Usage

```bash
cd ~/Projects/YourProject
claude --dangerously-skip-permissions

# Then in Claude Code:
/ralph loop "Your task description" --max-iterations 20 --completion-promise "All tests pass"
```

### Required Parameters (NON-NEGOTIABLE)

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `--max-iterations` | Circuit breaker - prevents infinite loops | `20` |
| `--completion-promise` | Success criteria - when to stop | `"All tests pass"` |

**Never run Ralph without both parameters.** This prevents runaway execution.

### How It Works

1. You start `/ralph loop "task" --max-iterations 20 --completion-promise "done"`
2. Claude works on the task
3. When Claude tries to exit, stop hook intercepts
4. Hook checks: Is `<promise>done</promise>` in output AND true?
5. If no → Re-inject task, increment iteration, continue
6. If yes → Loop ends, task complete
7. If iterations >= max → Loop ends (safety stop)

### Completion Promise Rules

The promise must be:
- **Verifiable** - Can be checked programmatically or obviously
- **Specific** - Not vague ("done" vs "all 47 tests pass")
- **Honest** - Claude must NOT output false promises to escape

```markdown
# Good promises
--completion-promise "All pytest tests pass"
--completion-promise "File docs/AUDIT.md exists with all sections complete"
--completion-promise "Zero TypeScript errors in src/"

# Bad promises
--completion-promise "Task is done"  # Too vague
--completion-promise "I tried my best"  # Not verifiable
```

## Use Case Patterns

### Pattern 1: Test-Driven Development

```bash
/ralph loop "Implement the UserService class. Run pytest after each change. Fix any failures." \
  --max-iterations 30 \
  --completion-promise "All pytest tests pass with 0 failures"
```

Loop: Code → Test → See failures → Fix → Test → Repeat until green.

### Pattern 2: Task List Execution

Create `todo.md`:
```markdown
- [ ] Add user model
- [ ] Add user router
- [ ] Add user tests
- [ ] Update API docs
```

```bash
/ralph loop "Work through todo.md. Mark items complete as you finish them. Commit after each item." \
  --max-iterations 20 \
  --completion-promise "All items in todo.md are checked"
```

### Pattern 3: Large Refactoring

```bash
/ralph loop "Migrate all API endpoints from v1 to v2 format. Run tests after each file." \
  --max-iterations 50 \
  --completion-promise "All endpoints migrated and tests pass"
```

### Pattern 4: Documentation Generation

```bash
/ralph loop "Generate API documentation for all routers in backend/app/routers/. Include examples." \
  --max-iterations 15 \
  --completion-promise "docs/API.md contains documentation for all routers"
```

## Safety Guidelines

### Always Set Limits

| Task Complexity | Suggested max-iterations |
|-----------------|-------------------------|
| Simple fix | 5-10 |
| Medium feature | 15-25 |
| Large refactor | 30-50 |
| Never exceed | 100 |

### Monitor Progress

Ralph creates `.claude/ralph-loop.local.md` with state:
```yaml
---
iteration: 5
max_iterations: 20
completion_promise: "All tests pass"
---
```

### Cancel If Stuck

```bash
/cancel-ralph
```

Or manually: `rm .claude/ralph-loop.local.md`

## Integration with Other Skills

| Skill | Integration |
|-------|-------------|
| **agent-sandboxes** | Use sandboxes for parallel attempts, Ralph for sequential persistence |
| **project-health** | Run health audit as Ralph loop for comprehensive analysis |
| **context-management** | Ralph loops can exhaust context; use selective reading |

## Troubleshooting

### Loop Never Ends
- Check completion promise is achievable
- Verify tests can actually pass
- Look for infinite failure patterns in logs

### Loop Ends Too Early
- Claude may output promise falsely
- Make promise more specific
- Add verification step to promise

### Context Exhaustion
- Lower max-iterations
- Use checkpointing (commit progress)
- Split into smaller loops

## Checklist Before Starting Ralph Loop

- [ ] Clear, verifiable completion promise
- [ ] Reasonable max-iterations set
- [ ] Task is well-defined
- [ ] Tests exist (for TDD loops)
- [ ] Running with `--dangerously-skip-permissions`
- [ ] Monitoring plan (check progress periodically)
