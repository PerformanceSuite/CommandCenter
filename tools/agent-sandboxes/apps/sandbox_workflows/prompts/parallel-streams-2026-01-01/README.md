# Parallel Execution Streams - January 1, 2026

These prompts run in parallel with Sprint 6b (Document Intelligence Integration).

## Streams Overview

| Stream | Agent | Branch | Est. Time | Est. Cost |
|--------|-------|--------|-----------|-----------|
| A: Multi-tenant Fix | 1 agent | `fix/multi-tenant-isolation` | 2-3 hrs | ~$2-3 |
| B: Skills Foundation | 1 agent | `feature/skills-native` | 3-4 hrs | ~$3-4 |
| C: AlertManager | 1 agent | `feature/alertmanager-deploy` | 1-2 hrs | ~$1-2 |
| D: Doc Archival | 1 agent | `chore/doc-cleanup` | 1-2 hrs | ~$1-2 |

**Total estimated cost: ~$7-11**

## Quick Start

```bash
cd ~/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows

# Verify environment
cat .env | grep -E "^(ANTHROPIC|E2B|GITHUB)"

# Run all 4 streams in parallel
./prompts/parallel-streams-2026-01-01/run-all.sh

# Or run individually
uv run obox https://github.com/PerformanceSuite/CommandCenter \
  -p prompts/parallel-streams-2026-01-01/01-multi-tenant-fix.md \
  -b main -m sonnet -t 80
```

## After Completion

1. Review each PR on GitHub
2. Run tests locally: `cd backend && uv run pytest`
3. Merge in order: A → B → C → D (or as ready)
4. Delete branches after merge

## Dependencies

- Stream B (Skills) benefits from Stream A (multi-tenant) but can proceed independently
- All streams are independent of Sprint 6b
- Stream D (Doc Archival) creates clean target for 6b concept extraction
