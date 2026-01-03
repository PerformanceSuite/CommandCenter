# Task: Add Real-World Examples to Autonomy Skill

## CRITICAL: Git Authentication

Before any git push operations, configure authentication:

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git remote -v  # Verify
```

**You MUST do this before attempting to push.**

---

## Context

The autonomy skill at `skills/autonomy/SKILL.md` explains Ralph loops but lacks concrete real-world examples showing exactly what outputs/logs look like during execution.

## Your Mission

Enhance the autonomy skill with:
1. **3-5 real-world examples** with actual command outputs
2. **Edge case handling** - what happens when things go wrong
3. **Before/After comparisons** showing state changes
4. **Log snippets** showing what successful/failed loops look like

## Branch

Create and work on: `phase3/task-1-autonomy-examples`

## Implementation

1. Read the current skill: `skills/autonomy/SKILL.md`
2. Add a new section: "## Real-World Examples"
3. Include examples like:
   - TDD loop showing actual pytest output between iterations
   - Task list completion showing todo.md updates
   - Failed loop showing what "stuck" looks like
   - Recovery from context exhaustion
4. Add "## What Success Looks Like" section with sample logs
5. Add "## What Failure Looks Like" section with warning signs

## Verification

```bash
cat skills/autonomy/SKILL.md | grep -c "Example"  # Should be 5+
```

## Commit

```bash
git add skills/autonomy/SKILL.md
git commit -m "docs(skills): add real-world examples to autonomy skill"
```

## Push

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git push -u origin phase3/task-1-autonomy-examples
```

## Completion Criteria

- [ ] 3+ detailed real-world examples added
- [ ] Edge case handling documented
- [ ] Sample log outputs included
- [ ] Branch pushed to GitHub
