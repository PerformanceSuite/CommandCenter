# Parameter 'input' Shadows Python Built-in

## Status: fixed
## Priority: P1 (High)
## Issue ID: 004
## Tags: code-quality, code-review, auto-coder

---

## Problem Statement

The `execute()` method uses `input` as a parameter name, which shadows Python's built-in `input()` function. This is a linting error and can cause subtle bugs.

## Findings

**Source:** kieran-python-reviewer

**Affected Files:**
- `hub/modules/auto-coder/src/skills/base.py:44`
- `hub/modules/auto-coder/src/skills/gather_requirements.py:69`
- `hub/modules/auto-coder/src/skills/code_subtask.py:67`

**Code:**
```python
async def execute(self, input: T_Input, context: dict | None = None) -> T_Output:
```

## Proposed Solutions

### Option A: Rename to skill_input (Recommended)

**Pros:** Clear, descriptive, no shadowing
**Cons:** Breaking change for any subclasses
**Effort:** Small
**Risk:** Low

```python
async def execute(self, skill_input: T_Input, context: dict | None = None) -> T_Output:
```

### Option B: Rename to params

**Pros:** Short, common pattern
**Cons:** Less descriptive
**Effort:** Small
**Risk:** Low

## Acceptance Criteria

- [ ] No parameter named `input` in codebase
- [ ] Linting passes without shadowing warnings
- [ ] All subclasses updated

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-03 | Identified via kieran-python-reviewer | Avoid shadowing built-ins |
