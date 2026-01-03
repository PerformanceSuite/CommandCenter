# MCP Provider Missing Output Schema

## Status: pending
## Priority: P2 (Important)
## Issue ID: 006
## Tags: agent-native, code-review, auto-coder

---

## Problem Statement

The MCP provider's `list_tools()` exposes `input_schema` but NOT `output_schema`. Agents cannot know what shape of data to expect from a skill without separate introspection.

## Findings

**Source:** agent-native-reviewer

**Affected Files:**
- `hub/modules/auto-coder/src/mcp/provider.py:16-31`

**Current Code:**
```python
tools.append({
    "name": f"auto_coder_{skill_meta.id}",
    "description": skill_meta.description,
    "input_schema": skill_meta.input_schema.model_json_schema(),
    # Missing: output_schema
})
```

## Proposed Solutions

### Option A: Add output_schema to Tools (Recommended)

**Pros:** Complete schema information
**Cons:** Slightly larger response
**Effort:** Small
**Risk:** Low

```python
tools.append({
    "name": f"auto_coder_{skill_meta.id}",
    "description": skill_meta.description,
    "input_schema": skill_meta.input_schema.model_json_schema(),
    "output_schema": skill_meta.output_schema.model_json_schema(),  # ADD
})
```

## Acceptance Criteria

- [ ] output_schema included in list_tools() response
- [ ] Agents can plan skill chains with schema knowledge

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-03 | Identified via agent-native-reviewer | Agents need full schema visibility |
