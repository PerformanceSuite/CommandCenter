# Path Traversal via project_dir Parameter

## Status: pending
## Priority: P1 (Critical - Security)
## Issue ID: 001
## Tags: security, code-review, auto-coder

---

## Problem Statement

The `project_dir` field in skill input schemas accepts arbitrary paths without validation. Attackers can provide paths like `../../../etc` to access directories outside project scope.

## Findings

**Source:** security-sentinel agent review of commit ec72af0

**Affected Files:**
- `hub/modules/auto-coder/src/skills/gather_requirements.py:9`
- `hub/modules/auto-coder/src/skills/code_subtask.py:9`

**Vulnerable Code:**
```python
project_dir: str = Field(default=".", description="Project directory path")
```

**Impact:**
- Directory traversal to read/modify files outside project boundaries
- Access to sensitive system files
- Potential for arbitrary file operations

## Proposed Solutions

### Option A: Pydantic Field Validator (Recommended)
Add path validation using Pydantic validator that resolves and checks against allowed base directories.

**Pros:** Clean, reusable, validates at schema level
**Cons:** Need to define allowed base directories
**Effort:** Small
**Risk:** Low

```python
from pydantic import field_validator
import os

ALLOWED_BASE_DIR = os.path.expanduser("~")

@field_validator('project_dir')
@classmethod
def validate_project_dir(cls, v: str) -> str:
    resolved = os.path.realpath(os.path.expanduser(v))
    if not resolved.startswith(ALLOWED_BASE_DIR):
        raise ValueError("project_dir outside allowed boundaries")
    return resolved
```

### Option B: Runtime Validation in Bridge
Validate paths in the bridge layer before passing to external components.

**Pros:** Centralized validation
**Cons:** Validation happens later in flow
**Effort:** Small
**Risk:** Low

## Technical Details

**Affected Components:**
- GatherRequirementsInput model
- CodeSubtaskInput model
- AutoClaudeBridge (downstream)

## Acceptance Criteria

- [ ] project_dir is validated against allowed base directories
- [ ] Path traversal attempts raise ValidationError
- [ ] Resolved paths are used for file operations
- [ ] Tests cover path traversal attack vectors

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-03 | Identified via security-sentinel review | Path validation critical for skills accepting directory paths |

## Resources

- PR: N/A (commit ec72af0 on main)
- OWASP Path Traversal: https://owasp.org/www-community/attacks/Path_Traversal
