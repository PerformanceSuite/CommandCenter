# Unsafe sys.path Manipulation

## Status: pending
## Priority: P1 (Critical - Security)
## Issue ID: 002
## Tags: security, code-review, auto-coder

---

## Problem Statement

The code unconditionally inserts paths into `sys.path` at module load time using magic parent traversal numbers. This creates fragile dependencies and potential code injection vectors.

## Findings

**Source:** security-sentinel, architecture-strategist reviews of commit ec72af0

**Affected Files:**
- `hub/modules/auto-coder/src/bridges/auto_claude.py:6-8`
- `hub/modules/auto-coder/src/adapters/base.py:10-11` (no existence check!)

**Vulnerable Code:**
```python
AUTO_CLAUDE_PATH = Path(__file__).parents[4] / "integrations" / "auto-claude-core"
if AUTO_CLAUDE_PATH.exists():
    sys.path.insert(0, str(AUTO_CLAUDE_PATH))
```

**Impact:**
- If attacker creates malicious module at expected path, code execution
- sys.path.insert(0, ...) prioritizes injected path over system packages
- Magic number `parents[4]` is fragile and breaks on restructuring
- adapters/base.py has no existence check at all

## Proposed Solutions

### Option A: Proper Package Installation (Recommended)
Make `auto-claude-core` an installable package and use standard imports.

**Pros:** Clean, standard Python, no path manipulation
**Cons:** Requires package restructuring
**Effort:** Medium
**Risk:** Low

```bash
pip install -e ../integrations/auto-claude-core
```

### Option B: Configuration-Based Path
Use environment variable or configuration file for external paths.

**Pros:** Explicit, configurable
**Cons:** Still manipulates sys.path
**Effort:** Small
**Risk:** Medium

### Option C: Integrity Verification
Verify path contents before importing (marker files, hashes).

**Pros:** Can be added to existing pattern
**Cons:** Doesn't fix fragility
**Effort:** Small
**Risk:** Medium

## Technical Details

**Affected Components:**
- AutoClaudeBridge
- adapters/base.py
- Any module that imports from auto-claude-core

## Acceptance Criteria

- [ ] No unconditional sys.path manipulation
- [ ] Path existence verified before modification
- [ ] Either use proper package installation OR add integrity checks
- [ ] Magic parent numbers replaced with configuration

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-03 | Identified via security + architecture reviews | sys.path manipulation is a code smell |

## Resources

- Python Packaging Guide: https://packaging.python.org/
