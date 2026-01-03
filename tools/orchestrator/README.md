# Long-Running Agent Orchestrator

Autonomous agent orchestration for overnight development work.

## Quick Start

```bash
# 1. Navigate to orchestrator
cd ~/Projects/CommandCenter/tools/orchestrator

# 2. Check status
python main.py --mode status

# 3. Run single task (test)
python main.py --mode once

# 4. Run overnight (continuous)
python main.py --mode continuous
```

## How It Works

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   TASKS     │────▶│   ORCHESTRATOR   │────▶│  E2B SANDBOXES  │
│  (YAML)     │     │   (Long-Running) │     │  (Short-Lived)  │
└─────────────┘     └────────┬─────────┘     └────────┬────────┘
                             │                        │
                             │                        │ Creates PRs
                             │                        │ Writes Skills
                             ▼                        ▼
                    ┌─────────────────────────────────────────┐
                    │          PERSISTENCE LAYER              │
                    │  Skills Store │ Cost Budget │ Git PRs   │
                    └─────────────────────────────────────────┘
```

## Directory Structure

```
tools/orchestrator/
├── main.py              # Orchestrator entry point
├── task_queue.py        # YAML-based task queue
├── skills_store.py      # Skills read/write
├── cost_budget.py       # Daily cost tracking
├── tasks/
│   ├── pending/         # Tasks waiting to run
│   ├── running/         # Currently executing
│   ├── completed/       # Finished tasks
│   └── failed/          # Failed tasks
└── README.md
```

## Task Format

```yaml
id: unique-task-id
type: implementation
title: "Human-readable task title"
priority: 1  # Lower = higher priority
depends_on:
  - other-task-id

context:
  plan_file: "docs/plans/some-plan.md"
  repo: "https://github.com/org/repo"
  branch: "feature/branch-name"

skills_required:
  - frontend-design
  - context-management

agent_config:
  model: sonnet  # or opus, haiku
  max_turns: 100
  max_cost_usd: 10.00

on_completion:
  create_pr: true
  update_skill: "learned-skill-name"  # Optional
  trigger_next:
    - dependent-task-id
```

## CLI Usage

```bash
# Show status (tasks, budget, skills)
python main.py --mode status

# Process one task and exit
python main.py --mode once

# Process all pending tasks
python main.py --mode batch

# Run continuously (overnight)
python main.py --mode continuous

# With custom budget
python main.py --budget 100.0
```

## Running Overnight

### Option 1: tmux (Recommended)

```bash
tmux new -s orchestrator
cd ~/Projects/CommandCenter/tools/orchestrator
python main.py
# Detach: Ctrl-B then D
# Reattach: tmux attach -t orchestrator
```

### Option 2: nohup

```bash
nohup python main.py > orchestrator.log 2>&1 &
```

## Cost Control

- Default daily budget: $50
- Each task has `max_cost_usd` limit
- Orchestrator pauses when budget exhausted
- Budget resets at midnight UTC

## Skills Learning

When tasks complete successfully:
1. High-confidence patterns → `~/.claude/skills/learned/`
2. Low-confidence patterns → `~/.claude/skills/pending/` for review

## Pre-Loaded Tasks: Wander Mind Map

The orchestrator comes with 4 tasks for implementing Wander:

1. `wander-001`: Create TypeScript types
2. `wander-002`: Create custom nodes (depends on 001)
3. `wander-003`: Create custom edges (depends on 001)
4. `wander-004`: Create main component (depends on 002, 003)

Tasks 002 and 003 run in parallel after 001 completes.

## The Bootstrap Loop

```
Night 1: Agents complete tasks → Learn patterns
Night 2: Future agents read improved skills → Work faster
Night 3: Quality compounds → Less human intervention
...
Result: Self-improving development system
```
