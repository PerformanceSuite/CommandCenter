---
description: Show status of all active agents and workflows
---

# Agent Status

You are tasked with displaying the current status of all active agents and workflows.

## Your Task

1. **Load agent status data**
   - Read `.agent-coordination/mcp-status.json`
   - Parse agent information
   - Check for any errors or blockers

2. **Generate status report**
   - Show overall progress (percentage)
   - List agents by status (pending, in_progress, completed, failed)
   - Display current task for each active agent
   - Show review scores
   - Highlight any blockers or dependencies

3. **Display workflow status**
   - Read workflow files from `.agent-coordination/workflows/`
   - Show active workflows
   - Display workflow type and agents involved

4. **Show git status**
   - List worktrees and their branches
   - Show PR status for completed agents
   - Highlight merge conflicts if any

5. **Provide actionable insights**
   - Suggest next steps
   - Identify blocked agents
   - Recommend which agents to review
   - Highlight agents ready for PR creation

## Status Display Format

```
=== CommandCenter Agent Status ===

Overall Progress: 75% (6/8 agents completed)

Completed Agents (6):
  ✓ security-agent         [10/10] PR #1 merged
  ✓ backend-agent          [10/10] PR #2 merged
  ✓ frontend-agent         [10/10] PR #3 merged
  ✓ rag-agent              [10/10] PR #4 merged
  ✓ testing-agent          [10/10] PR #5 merged
  ✓ docs-agent             [10/10] PR #6 merged

In Progress (2):
  ⚙ github-agent           [45%] Implementing webhooks... [8/10]
  ⚙ devops-agent           [30%] Setting up monitoring... [6/10]

Pending (0):

Failed (0):

Blocked (0):

=== Active Workflows ===

1. parallel-improvement (running)
   - Type: parallel
   - Agents: 8
   - Progress: 75%

=== Recommendations ===

- Review github-agent (score 8/10, needs improvement)
- Review devops-agent (score 6/10, needs improvement)
- All completed agents have been merged to main
```

## Additional Information

Include:

- Estimated completion time for remaining agents
- Test status for each agent
- Any merge conflicts detected
- Dependencies that are blocking agents
- Recent commits in agent branches

## Success Criteria

- [ ] Status data loaded successfully
- [ ] All agents accounted for
- [ ] Progress percentages calculated
- [ ] Review scores displayed
- [ ] Blockers identified
- [ ] Actionable recommendations provided
- [ ] Git and PR status shown
- [ ] Clear, formatted output

Display the agent status now.
