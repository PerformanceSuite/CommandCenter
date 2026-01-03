# SandboxBridge Stub Methods Return None

## Status: fixed
## Priority: P1 (Critical)
## Issue ID: 003
## Tags: code-quality, code-review, auto-coder

---

## Problem Statement

All methods in SandboxBridge contain only `pass` statements, returning `None` instead of declared types. Code expecting sandbox isolation runs without it, creating a false sense of security.

## Findings

**Source:** kieran-python-reviewer, architecture-strategist, simplicity-reviewer

**Affected Files:**
- `hub/modules/auto-coder/src/bridges/sandbox.py:15-37`

**Vulnerable Code:**
```python
async def create_sandbox(self, repo_url: str, branch: str) -> str:
    pass  # Returns None, not str as declared

async def run_coder(self, sandbox_id: str, subtask: str, context: dict | None = None) -> dict:
    pass  # Returns None, not dict as declared
```

**Impact:**
- Return type violations (None instead of str/dict)
- Silent failures when sandbox expected
- Code using sandbox_id will receive None

## Proposed Solutions

### Option A: Raise NotImplementedError (Recommended)
Replace `pass` with explicit NotImplementedError.

**Pros:** Fail-fast, clear intent
**Cons:** Breaks code that calls these methods
**Effort:** Small
**Risk:** Low

```python
async def create_sandbox(self, repo_url: str, branch: str) -> str:
    raise NotImplementedError("E2B sandbox integration not yet implemented")
```

### Option B: Delete File Entirely
Remove SandboxBridge until implementation exists (per simplicity-reviewer).

**Pros:** No dead code, YAGNI compliance
**Cons:** Loses placeholder for future implementation
**Effort:** Small
**Risk:** Low

### Option C: Return Stub Values with Logging
Return empty/stub values but log warnings.

**Pros:** Doesn't break callers
**Cons:** Hides missing functionality
**Effort:** Small
**Risk:** Medium

## Technical Details

**Affected Components:**
- CodeSubtaskSkill.execute() when sandbox_id provided
- Any future code expecting sandbox isolation

## Acceptance Criteria

- [ ] No methods silently return None
- [ ] Either NotImplementedError or remove file
- [ ] If keeping stubs, document clearly in docstrings

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-03 | Identified via multiple reviewers | Stub methods should fail explicitly |

## Resources

- YAGNI principle
