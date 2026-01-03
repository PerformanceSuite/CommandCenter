# Task: Add Cross-Reference Guide Between Skills

## CRITICAL: Git Authentication

Before any git push operations, configure authentication:

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git remote -v  # Verify
```

**You MUST do this before attempting to push.**

---

## Context

The skills in `skills/` work together but there's no guide explaining how they combine for different workflows.

## Your Mission

Create a new skill that serves as a cross-reference guide showing how skills combine for real workflows.

## Branch

Create and work on: `phase3/task-5-skill-cross-references`

## Implementation

1. Create new directory: `skills/skill-combinations/`
2. Create `skills/skill-combinations/SKILL.md` with:
   - Skills overview table
   - Workflow combinations (e.g., "Large Refactoring" = autonomy + context-management + project-health)
   - Decision matrix: "I want to do X" → "Use skills Y, Z"
   - Anti-patterns: skills that shouldn't be combined
3. Include 3-4 complete workflow examples showing skill combinations

## Structure

```markdown
---
name: skill-combinations
description: Guide for combining skills into effective workflows
---

# Skill Combinations Guide

## Available Skills Matrix

| Skill | Category | When to Use |
|-------|----------|-------------|
| autonomy | Execution | Long-running tasks |
| context-management | Optimization | Always |
| project-health | Assessment | Before major work |
| ...

## Workflow Recipes

### Recipe 1: Large Feature Implementation
Skills: brainstorming → writing-plans → autonomy + context-management
...

### Recipe 2: Comprehensive Project Audit
Skills: project-health → agent-sandboxes (parallel) → autonomy (cleanup)
...
```

## Verification

```bash
ls skills/skill-combinations/SKILL.md  # Should exist
cat skills/skill-combinations/SKILL.md | wc -l  # Should be 100+ lines
```

## Commit

```bash
git add skills/skill-combinations/
git commit -m "docs(skills): add skill-combinations cross-reference guide"
```

## Push

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git push -u origin phase3/task-5-skill-cross-references
```

## Completion Criteria

- [ ] New skill-combinations directory created
- [ ] Skills matrix included
- [ ] 3+ workflow recipes documented
- [ ] Branch pushed to GitHub
