# Silent ImportError Swallowing in Bridges

## Status: fixed
## Priority: P1 (High)
## Issue ID: 005
## Tags: code-quality, code-review, auto-coder

---

## Problem Statement

ImportError exceptions are silently caught and ignored in the bridge layer. When `gather_requirements` returns a stub result, there's no indication whether Auto-Claude was unavailable vs. had an import error.

## Findings

**Source:** kieran-python-reviewer, pattern-recognition-specialist

**Affected Files:**
- `hub/modules/auto-coder/src/bridges/auto_claude.py:29-30, 53-54`

**Code:**
```python
except ImportError:
    pass  # Silent failure - no logging
```

## Proposed Solutions

### Option A: Log the Exception (Recommended)

**Pros:** Aids debugging, no behavior change
**Cons:** Adds logging dependency
**Effort:** Small
**Risk:** Low

```python
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f"Auto-Claude not available: {e}")
```

### Option B: Add Flag to Output
Include a flag in output indicating fallback was used.

**Pros:** Caller knows source of data
**Cons:** Changes output schema
**Effort:** Medium
**Risk:** Medium

## Acceptance Criteria

- [ ] No silent exception swallowing
- [ ] ImportErrors logged at appropriate level
- [ ] Fallback behavior is observable

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-03 | Identified via code reviews | Silent exceptions hide debugging info |
