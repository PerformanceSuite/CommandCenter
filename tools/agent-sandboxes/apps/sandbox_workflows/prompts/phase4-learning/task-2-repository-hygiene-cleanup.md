# Task: Real Cleanup Using repository-hygiene Skill

## CRITICAL: Git Authentication

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
```

---

## Your Mission

**Real Task**: Clean up the repository root and docs/ following hygiene standards.

**Skill to Use**: Read and follow `skills/repository-hygiene/SKILL.md`

This is a LEARNING task. You must:
1. Actually USE the skill to complete the task
2. Document what WORKED about the skill
3. Document what FAILED or was UNCLEAR
4. Propose IMPROVEMENTS based on your experience

## Branch

`phase4/task-2-repository-hygiene-cleanup`

## Step 1: Read the Skill

```bash
cat skills/repository-hygiene/SKILL.md
```

Read it carefully. This is your guide.

## Step 2: Identify Violations

Follow the skill to find hygiene violations:
- Check root directory for misplaced files
- Check for stale/temporary files
- Run the verification commands from the skill

## Step 3: Execute Cleanup

Move or organize files according to the skill's guidelines:
- Move misplaced scripts to proper locations
- Archive stale documentation
- Clean up temporary files

**Important**: Only make changes you're confident about. Document anything uncertain.

## Step 4: Document Skill Feedback

Create `docs/audits/2026-01-03-hygiene-cleanup-feedback.md`:

```markdown
# Repository Hygiene Cleanup - Skill Feedback

## Changes Made
- [List actual changes]

## Skill Feedback: repository-hygiene

### What Worked Well
- [Specific helpful guidance]

### What Was Unclear or Missing
- [Gaps you encountered]
- [Edge cases not covered]
- [Commands that didn't work as expected]

### Proposed Improvements
- [Specific changes to make the skill better]

### Real-World Issues Encountered
- [Problems the skill didn't anticipate]
```

## Step 5: Commit and Push

```bash
git add -A
git commit -m "chore(hygiene): cleanup using repository-hygiene skill

Includes skill feedback for learning loop"
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git push -u origin phase4/task-2-repository-hygiene-cleanup
```

## Completion Criteria

- [ ] At least one real cleanup action taken
- [ ] Skill feedback document created
- [ ] Honest assessment of skill gaps
- [ ] Branch pushed to GitHub
