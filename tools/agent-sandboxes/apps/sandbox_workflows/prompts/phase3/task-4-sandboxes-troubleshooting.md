# Task: Add Troubleshooting Scenarios to Agent Sandboxes Skill

## CRITICAL: Git Authentication

Before any git push operations, configure authentication:

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git remote -v  # Verify
```

**You MUST do this before attempting to push.**

---

## Context

The agent-sandboxes skill at `skills/agent-sandboxes/SKILL.md` documents failures but needs more detailed troubleshooting scenarios with exact error messages and solutions.

## Your Mission

Enhance the skill with:
1. **5+ troubleshooting scenarios** with exact error messages
2. **Diagnostic commands** for each failure type
3. **Step-by-step recovery procedures**
4. **Success/failure log comparisons**

## Branch

Create and work on: `phase3/task-4-sandboxes-troubleshooting`

## Implementation

1. Read the current skill: `skills/agent-sandboxes/SKILL.md`
2. Expand "## Troubleshooting" section with detailed scenarios:
   - Scenario: Token authentication failures (with exact git errors)
   - Scenario: E2B sandbox timeout
   - Scenario: Agent completes but work is lost
   - Scenario: Context exhaustion mid-task
   - Scenario: Parallel agent conflicts
3. Add "## Diagnostic Commands" section
4. Add "## Log Analysis Guide" showing how to read agent logs
5. Add "## Recovery Playbook" with step-by-step procedures

## Verification

```bash
cat skills/agent-sandboxes/SKILL.md | grep -c "Scenario\|Error\|Fix"  # Should be 10+
```

## Commit

```bash
git add skills/agent-sandboxes/SKILL.md
git commit -m "docs(skills): add troubleshooting scenarios to agent-sandboxes skill"
```

## Push

```bash
git remote set-url origin https://${{GITHUB_TOKEN}}@github.com/PerformanceSuite/CommandCenter.git
git push -u origin phase3/task-4-sandboxes-troubleshooting
```

## Completion Criteria

- [ ] 5+ troubleshooting scenarios documented
- [ ] Diagnostic commands added
- [ ] Recovery procedures included
- [ ] Branch pushed to GitHub
