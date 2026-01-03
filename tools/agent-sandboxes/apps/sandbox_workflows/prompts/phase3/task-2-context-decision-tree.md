# Task: Add Decision Tree and Examples to Context Management Skill

## CRITICAL: Git Authentication

Before any git push operations, configure authentication:

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git remote -v  # Verify
```

**You MUST do this before attempting to push.**

---

## Context

The context-management skill at `skills/context-management/SKILL.md` has good strategies but lacks:
- A quick decision flowchart for choosing strategies
- Concrete before/after examples of each optimization
- Real numbers showing token savings

## Your Mission

Enhance the skill with:
1. **Visual decision flowchart** (ASCII art) for strategy selection
2. **Before/After examples** for each strategy showing exact token counts
3. **Quick reference card** for common scenarios
4. **Real session logs** showing optimization in action

## Branch

Create and work on: `phase3/task-2-context-decision-tree`

## Implementation

1. Read the current skill: `skills/context-management/SKILL.md`
2. Add "## Quick Decision Flowchart" near the top with ASCII diagram
3. For each strategy, add concrete before/after:
   ```
   Strategy 1: Thinking Suppression
   Before: Response with thinking = 3,500 tokens
   After: Response without thinking = 1,200 tokens
   Savings: 2,300 tokens (66%)
   ```
4. Add "## Quick Reference Card" table
5. Add "## Real Session Example" showing a full optimization session

## Verification

```bash
cat skills/context-management/SKILL.md | grep -c "tokens"  # Should increase significantly
```

## Commit

```bash
git add skills/context-management/SKILL.md
git commit -m "docs(skills): add decision tree and examples to context-management skill"
```

## Push

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git push -u origin phase3/task-2-context-decision-tree
```

## Completion Criteria

- [ ] Decision flowchart added
- [ ] Before/after examples with token counts
- [ ] Quick reference card added
- [ ] Branch pushed to GitHub
