# Remove Unused Fields from SkillMetadata

## Status: pending
## Priority: P3 (Nice-to-have)
## Issue ID: 008
## Tags: simplification, code-review, auto-coder, yagni

---

## Problem Statement

SkillMetadata contains several fields that are not used anywhere: `examples`, `depends_on`, and `category` (redundant with `phase`). This adds boilerplate without value.

## Findings

**Source:** code-simplicity-reviewer

**Affected Files:**
- `hub/modules/auto-coder/src/skills/base.py:18, 22-23`
- All skill implementations (examples blocks)

**Unused Fields:**
- `examples`: 15+ lines per skill, never consumed
- `depends_on`: Always empty list, no dependency resolution code
- `category`: Maps 1:1 with phase (redundant)

## Proposed Solutions

### Option A: Remove Unused Fields (Recommended)

**Pros:** ~30 LOC reduction, simpler mental model
**Cons:** Minor breaking change to metadata structure
**Effort:** Small
**Risk:** Low

Simplified SkillMetadata:
```python
@dataclass
class SkillMetadata:
    id: str
    name: str
    description: str
    phase: str  # DISCOVER, VALIDATE, IMPROVE
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
```

## Acceptance Criteria

- [ ] Remove examples, depends_on, category from SkillMetadata
- [ ] Update all skill metadata() implementations
- [ ] Estimated ~30 LOC reduction

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-01-03 | Identified via simplicity-reviewer | YAGNI - remove until needed |
