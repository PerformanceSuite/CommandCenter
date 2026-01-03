# Exception Handling Too Broad in MCP Provider

## Status: pending
## Priority: P2 (Important)
## Issue ID: 007
## Tags: code-quality, security, code-review, auto-coder

---

## Problem Statement

The MCP provider catches bare `Exception` and returns full exception messages. This masks programming errors and potentially discloses sensitive information.

## Findings

**Source:** kieran-python-reviewer, security-sentinel

**Affected Files:**
- `hub/modules/auto-coder/src/mcp/provider.py:50-55`

**Code:**
```python
try:
    input_data = input_model(**arguments)
    result = await skill.execute(input_data)
    return {"success": True, "result": result.model_dump()}
except Exception as e:
    return {"success": False, "error": str(e)}  # Exposes internal details
```

## Proposed Solutions

### Option A: Separate Validation from Execution Errors (Recommended)

**Pros:** Distinguishes error types, better debugging
**Cons:** More code
**Effort:** Small
**Risk:** Low

```python
from pydantic import ValidationError

try:
    input_data = input_model(**arguments)
except ValidationError as e:
    return {"success": False, "error": f"Invalid input: {e}", "validation_errors": e.errors()}

try:
    result = await skill.execute(input_data)
    return {"success": True, "result": result.model_dump()}
except Exception as e:
    logging.exception(f"Skill {skill_id} execution failed")
    return {"success": False, "error": "Skill execution failed", "error_code": "EXEC_001"}
```

## Acceptance Criteria

- [ ] ValidationError handled separately from execution errors
- [ ] Full exceptions logged server-side
- [ ] Generic error messages returned to clients

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-03 | Identified via code reviews | Separate error types for better handling |
