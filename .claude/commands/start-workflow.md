---
description: Start an agent workflow for multi-agent coordination
---

# Start Workflow

You are tasked with starting an agent workflow for parallel or phased development.

## Command Format

```
/start-workflow <workflow-type> [agents...]
```

## Arguments

- `workflow-type`: Type of workflow (parallel, sequential, phased, or template name)
- `agents`: List of agents to include (optional for templates)

## Your Task

1. **Parse workflow request**
   - Identify workflow type
   - Get list of agents (from arguments or template)
   - Validate agent names

2. **Load or create workflow**
   - If using template: Load from `.commandcenter/.agent-coordination/workflows/templates/`
   - If custom: Create new workflow definition
   - Validate workflow structure

3. **Set up git worktrees**
   - Create worktree for each agent
   - Create branches (feature/<agent-name>)
   - Copy task definitions to worktrees

4. **Initialize agent coordination**
   - Update `mcp-status.json` with agent statuses
   - Set up dependencies in `dependencies.json`
   - Create merge queue in `merge-queue.json`

5. **Start agents**
   - For each agent in workflow:
     - Create worktree
     - Set initial status to "pending"
     - Copy task definition
     - Log initialization

6. **Provide monitoring instructions**
   - Show how to check progress
   - Explain review process
   - Guide on PR creation

## Workflow Templates

Available templates:

- `parallel-improvement`: Run security, backend, frontend, testing, docs agents in parallel
- `phased-development`: Execute MCP infrastructure in 4 phases
- `sequential-feature`: Build feature step-by-step
- `hotfix-workflow`: Quick bugfix and test
- `quality-audit`: Comprehensive quality review

## Example Usage

```bash
# Start parallel improvement workflow
/start-workflow parallel-improvement

# Start custom parallel workflow
/start-workflow parallel security-agent backend-agent frontend-agent

# Start phased MCP development
/start-workflow phased-development
```

## Expected Output

After starting workflow:

1. **Worktrees created**: `worktrees/<agent-name>/`
2. **Branches created**: `feature/<agent-name>`
3. **Status tracking**: `.agent-coordination/mcp-status.json` updated
4. **Progress monitoring**: Instructions provided

## Success Criteria

- [ ] Workflow type validated
- [ ] Agents identified and validated
- [ ] Git worktrees created successfully
- [ ] Branches created for each agent
- [ ] Agent status tracking initialized
- [ ] Dependencies configured
- [ ] Monitoring instructions provided
- [ ] Workflow marked as "running"

Begin the workflow start process now.
