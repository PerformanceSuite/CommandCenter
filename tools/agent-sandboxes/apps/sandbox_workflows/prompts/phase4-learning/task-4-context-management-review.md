# Task: Large Review Using context-management Skill

## CRITICAL: Git Authentication

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
```

---

## Your Mission

**Real Task**: Review and summarize the entire `backend/app/routers/` directory.

**Skill to Use**: Read and follow `skills/context-management/SKILL.md`

This is a LEARNING task. The context-management skill is about handling large tasks efficiently. You must:
1. Read and understand the context-management skill
2. Apply its strategies while reviewing many files
3. Document what WORKED about the skill guidance
4. Document what FAILED or was UNCLEAR
5. Propose IMPROVEMENTS based on your experience

## Branch

`phase4/task-4-context-management-review`

## Step 1: Read the Skill

```bash
cat skills/context-management/SKILL.md
```

Understand the strategies for managing context during large tasks.

## Step 2: Plan Your Review

The routers directory has many files. Plan how to review them efficiently:
```bash
ls -la backend/app/routers/
wc -l backend/app/routers/*.py
```

## Step 3: Execute Review Using Skill Strategies

Apply context-management strategies:
- Use selective reading (grep before full reads)
- Summarize as you go (don't re-read)
- Track your "mental" token usage

Create `docs/reviews/2026-01-03-routers-summary.md` with:
- Summary of each router's purpose
- Key endpoints
- Patterns observed

## Step 4: Document Skill Feedback

At the END of your review document, add:

```markdown
## Skill Feedback: context-management

### Strategies I Used
- [Which strategies from the skill did you actually apply?]

### What Worked Well
- [Specific techniques that helped]

### What Was Unclear or Missing
- [Gaps in the skill for this type of task]
- [Strategies that didn't apply or were confusing]

### Proposed Improvements
- [How to make the skill more actionable]

### Token Efficiency
- Estimated tokens if I read everything fully: X
- Estimated tokens using skill strategies: Y
- Was the skill guidance worth following?
```

## Step 5: Commit and Push

```bash
git add docs/reviews/
git commit -m "docs(routers): summary review using context-management skill

Includes skill feedback for learning loop"
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git push -u origin phase4/task-4-context-management-review
```

## Completion Criteria

- [ ] Routers summary document created
- [ ] At least 5 routers summarized
- [ ] Skill feedback section completed
- [ ] Branch pushed to GitHub
