# Agent Launch Instructions

## Phase 1: Foundation Agents (Parallel Execution)

Launch all 3 agents simultaneously using Claude Code's Task tool for maximum parallelism.

### Agent 1: MCP Core Infrastructure
**Worktree**: `.agent-worktrees/mcp-core`
**Spec**: `.agent-coordination/agents/agent-1-mcp-core.md`
**Command**:
```bash
cd .agent-worktrees/mcp-core
# Agent works autonomously following agent-1-mcp-core.md
```

### Agent 2: Project Analyzer Service
**Worktree**: `.agent-worktrees/project-analyzer`
**Spec**: `.agent-coordination/agents/agent-2-project-analyzer.md`
**Command**:
```bash
cd .agent-worktrees/project-analyzer
# Agent works autonomously following agent-2-project-analyzer.md
```

### Agent 3: CLI Interface
**Worktree**: `.agent-worktrees/cli-interface`
**Spec**: `.agent-coordination/agents/agent-3-cli-interface.md`
**Command**:
```bash
cd .agent-worktrees/cli-interface
# Agent works autonomously following agent-3-cli-interface.md
```

## Autonomous Agent Workflow

Each agent will:
1. ✅ Read their specification file
2. ✅ Implement all deliverables
3. ✅ Write comprehensive tests
4. ✅ Run linting and type-checking
5. ✅ Self-review against 10/10 rubric
6. ✅ Fix issues until 10/10 achieved
7. ✅ Create PR with detailed description
8. ✅ Update STATUS.json
9. ✅ Mark as ready for coordinator review

## Coordination Protocol

- Agents work independently (no file conflicts in Phase 1)
- Update `.agent-coordination/STATUS.json` at milestones
- Create PR when self-review = 10/10
- Wait for coordinator (Claude) to review and merge
