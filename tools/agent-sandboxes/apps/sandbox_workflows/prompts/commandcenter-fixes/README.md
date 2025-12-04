# CommandCenter Audit Fixes

Parallel E2B sandbox prompts for fixing P0/P1 issues identified in the 2025-12-04 audit.

## Fix Prompts

| Priority | File | Description | Branch |
|----------|------|-------------|--------|
| P0-1 | `p0-1-output-schema-validation.md` | Add Zod validation to Dagger executor | `fix/p0-output-schema-validation` |
| P0-2 | `p0-2-task-persistence.md` | Replace in-memory tasks with Redis | `fix/p0-task-persistence` |
| P0-3 | `p0-3-multi-tenant-audit.md` | Complete multi-tenant isolation | `fix/p0-multi-tenant-isolation` |
| P1-1 | `p1-1-typescript-strict.md` | Enable TS strict mode | `fix/p1-typescript-strict` |
| P1-2 | `p1-2-github-circuit-breaker.md` | Add circuit breaker to GitHub API | `fix/p1-github-circuit-breaker` |

## Execution

### Run All P0 Fixes in Parallel (3 forks)
```bash
cd /Users/danielconnolly/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows

# P0-1: Output Schema Validation
uv run obox sandbox-fork https://github.com/PerformanceSuite/CommandCenter \
  --branch main \
  --prompt ./prompts/commandcenter-fixes/p0-1-output-schema-validation.md \
  --model sonnet \
  --forks 1

# P0-2: Task Persistence
uv run obox sandbox-fork https://github.com/PerformanceSuite/CommandCenter \
  --branch main \
  --prompt ./prompts/commandcenter-fixes/p0-2-task-persistence.md \
  --model sonnet \
  --forks 1

# P0-3: Multi-Tenant Isolation
uv run obox sandbox-fork https://github.com/PerformanceSuite/CommandCenter \
  --branch main \
  --prompt ./prompts/commandcenter-fixes/p0-3-multi-tenant-audit.md \
  --model sonnet \
  --forks 1
```

### Run P1 Fixes
```bash
# P1-1: TypeScript Strict
uv run obox sandbox-fork https://github.com/PerformanceSuite/CommandCenter \
  --branch main \
  --prompt ./prompts/commandcenter-fixes/p1-1-typescript-strict.md \
  --model sonnet \
  --forks 1

# P1-2: Circuit Breaker
uv run obox sandbox-fork https://github.com/PerformanceSuite/CommandCenter \
  --branch main \
  --prompt ./prompts/commandcenter-fixes/p1-2-github-circuit-breaker.md \
  --model sonnet \
  --forks 1
```

## Post-Execution Workflow

After E2B agents complete, branches should be pushed to origin. Then:

1. **Fetch branches locally**:
   ```bash
   cd /Users/danielconnolly/Projects/CommandCenter
   git fetch origin
   ```

2. **Create PRs using compounding-engineering review**:
   ```bash
   # For each branch
   gh pr create --base main --head fix/p0-output-schema-validation \
     --title "fix(orchestration): Add Zod output schema validation" \
     --body "P0 fix from 2025-12-04 audit. See docs/plans/2025-12-04-audit-implementation-plan.md"
   ```

3. **Run code review**:
   ```
   /compounding-engineering:workflows:review fix/p0-output-schema-validation
   ```

4. **Merge after approval**

## Expected Branches After Execution

- `fix/p0-output-schema-validation`
- `fix/p0-task-persistence`
- `fix/p0-multi-tenant-isolation`
- `fix/p1-typescript-strict`
- `fix/p1-github-circuit-breaker`
