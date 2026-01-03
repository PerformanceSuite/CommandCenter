# Task: Real Decision Using infrastructure-decisions Skill

## CRITICAL: Git Authentication

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
```

---

## Your Mission

**Real Task**: Evaluate whether the test infrastructure should use Dagger or Docker Compose.

**Skill to Use**: Read and follow `skills/infrastructure-decisions/SKILL.md`

This is a LEARNING task. You must:
1. Read and understand the infrastructure-decisions skill
2. Apply its decision matrix to a REAL question
3. Document what WORKED about the skill guidance
4. Document what FAILED or was UNCLEAR
5. Propose IMPROVEMENTS based on your experience

## Branch

`phase4/task-5-infrastructure-decision`

## Step 1: Read the Skill

```bash
cat skills/infrastructure-decisions/SKILL.md
```

Understand the decision framework.

## Step 2: Gather Context

Examine the current test setup:
```bash
ls -la backend/tests/
cat backend/tests/conftest.py | head -50
ls docker-compose*.yml
cat docker-compose.yml | head -50
```

## Step 3: Apply the Decision Matrix

Using the skill's decision matrix, evaluate:
- Does the test suite need custom images?
- Does it need testing matrices?
- Does it need programmatic control?
- What's the team familiarity?

## Step 4: Document Your Decision

Create `docs/decisions/2026-01-03-test-infrastructure-decision.md`:

```markdown
# Test Infrastructure Decision: Dagger vs Docker Compose

## Context
[What you learned about current test setup]

## Decision Matrix Application

| Criteria | Current State | Dagger? | Compose? |
|----------|---------------|---------|----------|
| Custom images needed | ... | ... | ... |
| Testing matrix | ... | ... | ... |
| Programmatic control | ... | ... | ... |
| Team familiarity | ... | ... | ... |
| CI/CD integration | ... | ... | ... |

## Recommendation
[Your decision based on the matrix]

## Skill Feedback: infrastructure-decisions

### Did the Matrix Help?
- Was the decision matrix useful for this real question?

### What Worked Well
- [Specific guidance that helped]

### What Was Unclear or Missing
- [Gaps when applying to real decisions]
- [Criteria that were hard to evaluate]

### Proposed Improvements
- [How to make the skill more actionable]

### Confidence Level
- How confident are you in this decision? Why?
```

## Step 5: Commit and Push

```bash
git add docs/decisions/
git commit -m "docs(infra): test infrastructure decision using infrastructure-decisions skill

Includes skill feedback for learning loop"
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git push -u origin phase4/task-5-infrastructure-decision
```

## Completion Criteria

- [ ] Decision document created with real analysis
- [ ] Decision matrix actually applied
- [ ] Skill feedback section completed
- [ ] Branch pushed to GitHub
