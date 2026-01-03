# Task: Multi-Step Task Using autonomy Skill

## CRITICAL: Git Authentication

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
```

---

## Your Mission

**Real Task**: Add missing docstrings to `backend/app/services/rag_service.py`

**Skill to Use**: Read and follow `skills/autonomy/SKILL.md`

This is a LEARNING task. The autonomy skill is about persistent, multi-step work. You must:
1. Read and understand the autonomy skill
2. Apply its patterns to this multi-step task
3. Document what WORKED about the skill guidance
4. Document what FAILED or was UNCLEAR
5. Propose IMPROVEMENTS based on your experience

## Branch

`phase4/task-3-autonomy-docstrings`

## Step 1: Read the Skill

```bash
cat skills/autonomy/SKILL.md
```

Understand when and how to use persistent workflows.

## Step 2: Assess the Task

Check the RAG service for missing docstrings:
```bash
cat backend/app/services/rag_service.py | head -100
```

Count functions/methods missing docstrings.

## Step 3: Execute Iteratively

Following the autonomy skill's guidance on multi-step work:
- Add docstrings one function at a time
- Verify each change
- Track your progress

**Note**: You're NOT using Ralph loop (that requires special setup). Instead, apply the PRINCIPLES from the autonomy skill - iteration, verification, persistence.

## Step 4: Document Skill Feedback

Create `docs/audits/2026-01-03-autonomy-skill-feedback.md`:

```markdown
# Autonomy Skill Feedback - Docstring Task

## Task Summary
- Functions found without docstrings: X
- Docstrings added: Y

## Skill Feedback: autonomy

### Did the Skill Apply?
- Was this task appropriate for autonomy patterns? Why/why not?

### What Worked Well
- [Specific guidance that helped]

### What Was Unclear or Missing
- [Gaps for non-Ralph persistent work]
- [Missing guidance for this type of task]

### Proposed Improvements
- [How to make the skill more useful]

### Key Insight
- [One thing you learned about when autonomy patterns help]
```

## Step 5: Commit and Push

```bash
git add backend/app/services/rag_service.py docs/audits/
git commit -m "docs(rag): add docstrings using autonomy skill patterns

Includes skill feedback for learning loop"
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git push -u origin phase4/task-3-autonomy-docstrings
```

## Completion Criteria

- [ ] At least 3 docstrings added
- [ ] Skill feedback document created
- [ ] Honest assessment of skill applicability
- [ ] Branch pushed to GitHub
