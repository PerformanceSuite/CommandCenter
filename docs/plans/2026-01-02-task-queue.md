# Bite-Sized Task Queue
*Small, verifiable units of work for parallel agents*

## Task Format

```yaml
id: task-001
type: docstring|test|refactor|skill-update
target: path/to/file.py
description: "Add docstring to function X"
time_budget: 5min
branch: task/task-001
verification: "pytest path/to/test.py passes"
```

## Example Queue (Start Small)

### Batch 1: Documentation (3 parallel)
- task-001: Add docstring to backend/app/main.py:create_app
- task-002: Add docstring to backend/app/core/config.py:Settings
- task-003: Add docstring to backend/app/api/deps.py:get_db

### Batch 2: Tests (3 parallel)
- task-004: Add test for settings validation
- task-005: Add test for db connection retry
- task-006: Add test for health endpoint

### Batch 3: Skill Updates (2 parallel)
- task-007: Improve agent-sandboxes skill clarity
- task-008: Add troubleshooting section to autonomy skill

## Execution Pattern

```
1. Pick batch (3-6 tasks)
2. Spawn parallel agents (one per task)
3. Wait for all to complete (timeout: 10min)
4. Review results (human or synthesis agent)
5. Merge passing PRs
6. Log failures for analysis
7. Next batch
```

## Key Constraints

- Max task time: 10 minutes
- Max tasks per batch: 6
- Human review before merge (initially)
- No dependencies between tasks in same batch
