# Task: Add Real-World Assessment Examples to Project Health Skill

## CRITICAL: Git Authentication

Before any git push operations, configure authentication:

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git remote -v  # Verify
```

**You MUST do this before attempting to push.**

---

## Context

The project-health skill at `skills/project-health/SKILL.md` has good methodology but lacks concrete examples of actual assessments with real findings.

## Your Mission

Enhance the skill with:
1. **2-3 complete assessment examples** showing actual outputs
2. **Sample health reports** from different project types
3. **Before/After cleanup comparisons**
4. **Common patterns** discovered during assessments

## Branch

Create and work on: `phase3/task-3-project-health-examples`

## Implementation

1. Read the current skill: `skills/project-health/SKILL.md`
2. Add "## Example Assessments" section with:
   - Example 1: Fresh project with minimal cleanup needed
   - Example 2: Stale project with significant debt
   - Example 3: Project mid-development with mixed state
3. Add "## Sample Health Reports" with complete example output
4. Add "## Common Patterns" section documenting typical findings
5. Add "## Cleanup Scripts" with ready-to-use commands

## Verification

```bash
cat skills/project-health/SKILL.md | wc -l  # Should grow by 100+ lines
```

## Commit

```bash
git add skills/project-health/SKILL.md
git commit -m "docs(skills): add real-world assessment examples to project-health skill"
```

## Push

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git push -u origin phase3/task-3-project-health-examples
```

## Completion Criteria

- [ ] 2+ complete assessment examples
- [ ] Sample health reports included
- [ ] Common patterns documented
- [ ] Branch pushed to GitHub
