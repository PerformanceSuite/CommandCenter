# Verification Test 3: Improve a Skill File

## CRITICAL: Git Authentication

Before any git push operations, run this FIRST:

```bash
git remote set-url origin https://${GITHUB_TOKEN}@github.com/PerformanceSuite/CommandCenter.git
git remote -v  # Verify it shows the token URL
```

**Run this IMMEDIATELY after cloning, before any other git operations.**

---

## Your Task

1. Read the `skills/context-management/SKILL.md` file
2. Try to understand and mentally "use" the skill as if you were an agent following it
3. Document any issues, unclear instructions, or gaps you notice
4. Make concrete improvements to the skill file

## What to Look For

- Are the instructions clear and actionable?
- Are there missing steps or assumptions?
- Is the formatting consistent?
- Are there examples where needed?
- Would an agent know exactly what to do?

## Deliverables

1. Update `skills/context-management/SKILL.md` with your improvements
2. Commit with message: `docs(skills): improve context-management skill clarity`
3. Push to branch

## Verification

```bash
git log -1 --oneline
git diff HEAD~1 --stat
```

Output "TEST 3 COMPLETE" when done.
