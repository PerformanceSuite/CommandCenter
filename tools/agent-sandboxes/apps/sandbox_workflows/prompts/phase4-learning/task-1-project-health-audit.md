# Task: Real Audit Using project-health Skill

## CRITICAL: Git Authentication

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
```

---

## Your Mission

**Real Task**: Conduct a health audit of `backend/app/services/` directory.

**Skill to Use**: Read and follow `skills/project-health/SKILL.md`

This is a LEARNING task. You must:
1. Actually USE the skill to complete the task
2. Document what WORKED about the skill
3. Document what FAILED or was UNCLEAR
4. Propose IMPROVEMENTS based on your experience

## Branch

`phase4/task-1-project-health-audit`

## Step 1: Read the Skill

```bash
cat skills/project-health/SKILL.md
```

Read it carefully. This is your guide.

## Step 2: Execute the Audit

Follow the project-health skill to audit `backend/app/services/`:
- Run the commands it suggests
- Follow its assessment phases
- Generate findings

## Step 3: Document Your Findings

Create `docs/audits/2026-01-03-services-health-audit.md` with:
- Audit results following the skill's template
- What you discovered about the services

## Step 4: Document Skill Feedback

At the END of your audit file, add a section:

```markdown
## Skill Feedback: project-health

### What Worked Well
- [List specific things that helped]

### What Was Unclear or Missing
- [List gaps, confusing instructions, missing examples]

### Proposed Improvements
- [Specific changes you'd make to the skill]

### Time/Effort Assessment
- Estimated time following skill: X minutes
- Would have been faster/slower without skill: Y
```

## Step 5: Commit and Push

```bash
git add docs/audits/
git commit -m "audit(services): health assessment using project-health skill

Includes skill feedback for learning loop"
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git push -u origin phase4/task-1-project-health-audit
```

## Completion Criteria

- [ ] Audit document created with real findings
- [ ] Skill feedback section completed honestly
- [ ] Branch pushed to GitHub
