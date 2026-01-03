# Enhanced Multi-Agent Coordination Strategy

**Version**: 2.0
**Date**: 2025-10-12
**Based On**: AgentFlow architecture + CommandCenter proven patterns

---

## Executive Summary

This document defines an enhanced parallel agent execution strategy that combines:
- **AgentFlow's proven architectural patterns** (prompts, configuration, coordination logic)
- **File-based coordination mechanism** (the missing piece AgentFlow designed but didn't implement)
- **CommandCenter's working implementations** (proven in Session 18 with 8 agents)
- **Checkpoint-based execution** (safer than true parallel, enables iteration)

**Goal**: Enable 3 Phase 1 agents (MCP Core, Project Analyzer, CLI) to work in coordinated parallel fashion with real-time conflict detection and integration validation.

---

## Core Architecture

### Coordination via Shared State Files

All agent coordination happens through structured files that agents read/write:

```
.agent-coordination/
├── STATUS.json                           # Real-time agent progress
├── COMMUNICATION.md                      # Async message board
├── contracts/                            # Interface contracts (read-only for agents)
│   ├── mcp-server-interface.ts          # Agent 1 must implement
│   ├── project-analyzer-interface.ts     # Agent 2 must implement
│   ├── cli-interface.ts                  # Agent 3 must implement
│   └── CONTRACTS.md                      # Contract documentation
├── checkpoints/                          # Progress snapshots
│   ├── agent-1-checkpoint-1.json        # After 2 hours work
│   ├── agent-1-checkpoint-2.json        # After 4 hours work
│   └── ...
├── feedback/                             # Coordinator feedback to agents
│   ├── agent-1-feedback.md              # Issues found in Agent 1's work
│   ├── agent-2-feedback.md              # Issues found in Agent 2's work
│   └── integration-report.md            # Cross-agent issues
└── prompts/                              # AgentFlow templates
    ├── base.md                           # Agent instruction template
    ├── review.md                         # Review rubric
    └── coordinate.md                     # Coordination logic
```

### STATUS.json Structure

```json
{
  "session_id": "session-20-mcp-phase1",
  "started_at": "2025-10-12T10:00:00Z",
  "current_phase": "checkpoint-1",
  "agents": {
    "agent-1-mcp-core": {
      "status": "in_progress",
      "branch": "agent/mcp-core-infrastructure",
      "worktree": ".agent-worktrees/mcp-core",
      "checkpoint": 1,
      "progress_percent": 40,
      "last_commit": "abc123",
      "files_changed": 12,
      "tests_passing": 18,
      "tests_total": 54,
      "blocks": [],
      "needs_from_others": [],
      "exports_ready": ["MCPServer", "JSONRPCHandler"]
    },
    "agent-2-project-analyzer": {
      "status": "in_progress",
      "branch": "agent/project-analyzer-service",
      "worktree": ".agent-worktrees/project-analyzer",
      "checkpoint": 1,
      "progress_percent": 35,
      "last_commit": "def456",
      "files_changed": 15,
      "tests_passing": 12,
      "tests_total": 40,
      "blocks": ["waiting for Agent 1 MCPServer stub"],
      "needs_from_others": ["MCPServer.register_provider"],
      "exports_ready": ["ProjectAnalyzer", "DependencyParser"]
    },
    "agent-3-cli-interface": {
      "status": "in_progress",
      "branch": "agent/cli-interface",
      "worktree": ".agent-worktrees/cli-interface",
      "checkpoint": 1,
      "progress_percent": 45,
      "last_commit": "ghi789",
      "files_changed": 8,
      "tests_passing": 20,
      "tests_total": 37,
      "blocks": [],
      "needs_from_others": ["ProjectAnalyzer.analyze"],
      "exports_ready": ["CLIApp", "analyze_command"]
    }
  },
  "conflicts": [],
  "integration_status": "pending_checkpoint_1_merge"
}
```

### COMMUNICATION.md Structure

```markdown
# Agent Communication Log

**Session**: session-20-mcp-phase1
**Last Updated**: 2025-10-12T12:30:00Z

---

## Checkpoint 1 Messages

### [12:15] Agent 1 (MCP Core) → All
**Status**: Exported `MCPServer` class with `register_provider` method
**Location**: `backend/app/mcp/server.py:15-45`
**Signature**:
```python
def register_provider(self, provider: ResourceProvider) -> None:
    """Register a resource provider with the MCP server."""
```
**Note**: Agent 2 and 3 can now import this

---

### [12:20] Agent 2 (Project Analyzer) → Agent 1
**Question**: Does `MCPServer.register_provider` support async providers?
**Context**: My `ProjectAnalyzer` needs to do async filesystem operations
**Blocking**: No (using sync stub for now)

---

### [12:25] Agent 1 → Agent 2
**Answer**: Yes, supports both sync and async. Check if provider has `__aenter__`
**Reference**: `backend/app/mcp/server.py:32-38`

---

### [12:30] Coordinator → All
**Integration Test Result**: PASS (18/18 tests)
**Conflicts Detected**: None
**Action**: Continue to checkpoint 2
**Merge Status**: Checkpoint 1 merged to integration branch `integration/phase1-checkpoint1`
```

---

## Execution Phases

### Phase 0: Contract Creation (30 minutes, Claude)

**Before any agents start**, I create the interface contracts:

1. **Define exact interfaces each agent must implement**
   ```typescript
   // contracts/mcp-server-interface.ts
   export interface MCPServer {
     register_provider(provider: ResourceProvider): void;
     handle_request(request: JSONRPCRequest): Promise<JSONRPCResponse>;
     start(): Promise<void>;
     stop(): Promise<void>;
   }

   export interface ResourceProvider {
     provide_resources(): Resource[];
     get_resource(uri: string): Promise<ResourceData>;
   }
   ```

2. **Create stubs for dependencies**
   ```python
   # contracts/stubs/mcp_server_stub.py
   """Stub implementation - Agent 2/3 use this until Agent 1 completes"""
   class MCPServerStub:
       def register_provider(self, provider):
           print(f"STUB: Would register {provider}")
   ```

3. **Document contracts in CONTRACTS.md**
   - What each interface does
   - Parameter types and return values
   - Usage examples
   - Which agent implements what

4. **Initialize coordination files**
   - Empty STATUS.json with agent placeholders
   - Empty COMMUNICATION.md with headers
   - Empty feedback/ directory

**Output**: All 3 agents have clear contracts, no ambiguity, can work independently

---

### Phase 1: Checkpoint Execution (Agents work in 2-hour sprints)

**Checkpoint 1 (2 hours):**

1. **Launch all 3 agents simultaneously** (via Task tool)

   Each agent receives:
   - Their specification (`.agent-coordination/agents/agent-X.md`)
   - Contract interfaces (`contracts/`)
   - Agent base prompt (`prompts/base.md`)
   - Checkpoint 1 scope: "First 40% of deliverables"
   - Instructions to:
     - Work in their worktree
     - Commit every 30 minutes
     - Update STATUS.json after each commit
     - Post questions to COMMUNICATION.md
     - Use stubs for dependencies not yet available

2. **Agents work independently for 2 hours**

   Each agent:
   - Implements against contracts
   - Uses stubs for missing dependencies
   - Writes tests as they go
   - Updates STATUS.json: `progress_percent`, `last_commit`, `tests_passing`
   - If blocked, writes to COMMUNICATION.md and continues other work

3. **After 2 hours, agents return their results**

---

### Phase 2: Coordinator Review (30 minutes, Claude)

**I act as coordinator agent**, following `prompts/coordinate.md` logic:

1. **Read STATUS.json** - Understand what each agent accomplished

2. **Check COMMUNICATION.md** - See if agents had questions or blockers

3. **Create integration branch**
   ```bash
   git checkout -b integration/phase1-checkpoint1
   git merge agent/mcp-core-infrastructure --no-commit
   git merge agent/project-analyzer-service --no-commit
   git merge agent/cli-interface --no-commit
   ```

4. **Run integration tests**
   ```bash
   cd .agent-worktrees/integration-test
   pytest backend/tests/integration/ -v
   ```

5. **Detect conflicts**
   - File-level conflicts (git merge conflicts)
   - Interface mismatches (contract violations)
   - Test failures (integration breaks)

6. **Generate feedback reports**

   For each agent, create `feedback/agent-X-feedback.md`:
   ```markdown
   # Agent 1 Feedback - Checkpoint 1

   ## Overall: ✅ PASS

   **Progress**: 40% (on target)
   **Tests**: 18/54 passing (33%, on track)
   **Conflicts**: None
   **Contract Compliance**: ✅ Pass

   ## Issues

   ### Issue 1: Missing async support in provider registration
   - **Location**: `backend/app/mcp/server.py:25`
   - **Problem**: Agent 2 needs async providers, current impl only sync
   - **Fix**: Add async detection: `if inspect.iscoroutinefunction(provider.provide_resources)`
   - **Priority**: P1 (blocking Agent 2 checkpoint 2)

   ## What's Working Well
   - JSON-RPC protocol implementation is clean
   - Test coverage excellent (18/18 passing)
   - Code quality high

   ## Next Checkpoint
   Continue with deliverables 3-5 from your spec.
   ```

7. **Write integration report** (`feedback/integration-report.md`)

8. **Update STATUS.json**
   - Mark checkpoint 1 complete
   - Set `current_phase: "checkpoint-2"`
   - Update any blockers

---

### Phase 3: Agent Iteration (If needed, 1 hour)

**If coordinator found critical issues:**

1. **Launch affected agents again** with:
   - Their checkpoint 1 code (already committed)
   - Feedback report from coordinator
   - Instruction: "Fix issues in feedback before continuing"

2. **Agents fix issues, re-commit**

3. **Coordinator re-tests integration**

4. **Proceed to checkpoint 2 when passes**

**If no critical issues:**
- Proceed directly to checkpoint 2

---

### Phase 4: Repeat for Checkpoints 2-3

**Checkpoint 2** (2 hours): Deliverables 3-5 (next 40%)
**Checkpoint 3** (2 hours): Deliverables 6-7 (final 20% + polish)

After checkpoint 3:
- All agents at 100%
- Full integration test passes
- Ready for final review and merge

---

### Phase 5: Final Integration & Merge (1 hour, Claude)

1. **Create final integration branch**
   ```bash
   git checkout main
   git checkout -b integration/phase1-complete
   # Merge all 3 agents in dependency order
   git merge agent/mcp-core-infrastructure --squash
   git merge agent/project-analyzer-service --squash
   git merge agent/cli-interface --squash
   ```

2. **Run full test suite**
   ```bash
   make test-backend
   # All tests must pass
   ```

3. **Run end-to-end validation**
   ```bash
   # Test the full workflow
   commandcenter analyze ~/Projects/test-project
   # Should work end-to-end
   ```

4. **Merge to main if all pass**
   ```bash
   git checkout main
   git merge integration/phase1-complete --squash
   git commit -m "feat: Implement Phase 1 MCP infrastructure

   - MCP Core: JSON-RPC protocol, server, providers (54 tests)
   - Project Analyzer: 8 parsers, tech detection (40 tests)
   - CLI Interface: Click CLI, analyze command (37 tests)

   All agents: 10/10 review score, 131/131 tests passing

   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

5. **Clean up worktrees**
   ```bash
   git worktree remove .agent-worktrees/mcp-core
   git worktree remove .agent-worktrees/project-analyzer
   git worktree remove .agent-worktrees/cli-interface
   git branch -d agent/mcp-core-infrastructure
   git branch -d agent/project-analyzer-service
   git branch -d agent/cli-interface
   ```

---

## Conflict Resolution Strategies

### Strategy 1: Same File, Different Sections
**Detection**: Git merge shows conflicts in same file
**Resolution**:
1. Check if changes are in different functions/classes
2. If yes, auto-resolve by keeping both changes
3. If no, use coordination logic:
   - Infrastructure changes win over feature changes
   - Earlier agent (by dependency) wins over later agent
   - Flag for manual review if ambiguous

### Strategy 2: Interface Mismatches
**Detection**: Agent 2 expects `async def foo()` but Agent 1 provided `def foo()`
**Resolution**:
1. Check contract - which is correct?
2. If contract says async, Agent 1 must fix
3. If contract ambiguous, prefer async (more flexible)
4. Update contract to clarify

### Strategy 3: Integration Test Failures
**Detection**: Individual agent tests pass, but integration test fails
**Resolution**:
1. Identify which agents' interaction is failing
2. Check COMMUNICATION.md for assumptions
3. Create feedback report for both agents
4. Re-launch iteration phase

### Strategy 4: Circular Dependencies
**Detection**: Agent 1 needs Agent 2's export, Agent 2 needs Agent 1's export
**Resolution**:
1. Identify the circular dependency in STATUS.json `needs_from_others`
2. One agent must use stub/interface
3. Update contracts to break circle
4. Flag as critical issue, may need re-architecture

---

## Success Criteria

### Checkpoint-Level Success
- ✅ All agents report progress ≥ target (40%, 80%, 100%)
- ✅ Tests passing for completed deliverables
- ✅ No merge conflicts (or resolved automatically)
- ✅ Integration tests pass
- ✅ STATUS.json shows no critical blockers

### Phase-Level Success
- ✅ All checkpoints complete
- ✅ Full test suite passes (131/131 tests)
- ✅ End-to-end workflow works
- ✅ Code quality: linters pass, types check
- ✅ All contracts fully implemented
- ✅ No "STUB" markers in final code

### Project-Level Success
- ✅ `commandcenter analyze ~/Projects/test-project` works
- ✅ Detects technologies correctly
- ✅ Outputs analysis results
- ✅ All 3 agents' code merged to main
- ✅ Documentation complete

---

## Risk Mitigation

### Risk 1: Agents Diverge Too Much
**Symptom**: Checkpoint 1 integration has major conflicts
**Mitigation**: Contracts are very explicit, agents can't deviate
**Fallback**: Coordinator feedback forces alignment at checkpoint 1

### Risk 2: Agent Gets Stuck
**Symptom**: Agent reports same progress % for 2 commits
**Mitigation**: Agents instructed to skip blockers, use stubs
**Fallback**: Coordinator sees `blocks: [...]` in STATUS.json, provides guidance

### Risk 3: Integration Tests Fail
**Symptom**: Individual tests pass, integration fails
**Mitigation**: Agents test against stubs that match contracts
**Fallback**: Iteration phase fixes integration issues

### Risk 4: Contract Ambiguity
**Symptom**: Agent 1 and 2 interpret contract differently
**Mitigation**: Contracts include usage examples, type annotations
**Fallback**: First checkpoint catches this, coordinator clarifies contract

### Risk 5: Checkpoint Takes Too Long
**Symptom**: Agent not done after 2 hours
**Mitigation**: Checkpoints are scoped to be achievable in 2 hours
**Fallback**: Agent reports progress, continues in next checkpoint

---

## Timeline

### Session 20 (This Session)
- [x] Phase 0: Create contracts (30 min) - **TODAY**
- [ ] Phase 1: Checkpoint 1 execution (2 hours)
- [ ] Phase 2: Coordinator review (30 min)
- [ ] Phase 3: Iteration if needed (1 hour)

**Total**: 4-5 hours (1 session)

### Session 21
- [ ] Phase 1: Checkpoint 2 execution (2 hours)
- [ ] Phase 2: Coordinator review (30 min)
- [ ] Phase 3: Iteration if needed (1 hour)

**Total**: 3.5-4.5 hours

### Session 22
- [ ] Phase 1: Checkpoint 3 execution (2 hours)
- [ ] Phase 2: Coordinator review (30 min)
- [ ] Phase 5: Final integration & merge (1 hour)

**Total**: 3.5 hours

**Total Time**: 11-14 hours across 3 sessions (vs 24-36 hours sequential)

---

## Comparison: Enhanced Coordination vs Sequential

### Sequential (Option B)
- ✅ Simple, proven
- ✅ No coordination complexity
- ❌ 24-36 hours total (3x longer)
- ❌ Agent 3 waits for Agent 1 & 2 to finish
- ❌ No parallel testing

### Enhanced Coordination (This Strategy)
- ✅ 11-14 hours total (40% faster)
- ✅ Agents work simultaneously
- ✅ Early conflict detection
- ✅ Continuous integration testing
- ⚠️ More complex (but managed via files)
- ⚠️ Requires coordinator role (but automated via prompts)

---

## Implementation Checklist

### Pre-Execution (30 min)
- [ ] Copy AgentFlow prompts to `.agent-coordination/prompts/`
- [ ] Create interface contracts in `contracts/`
- [ ] Generate stubs for dependencies
- [ ] Write CONTRACTS.md documentation
- [ ] Initialize STATUS.json
- [ ] Initialize COMMUNICATION.md
- [ ] Create feedback/ directory

### Checkpoint 1 (3-4 hours)
- [ ] Launch 3 agents with checkpoint 1 specs
- [ ] Agents work for 2 hours
- [ ] Coordinator reviews integration
- [ ] Generate feedback reports
- [ ] Iteration if needed

### Checkpoint 2 (3-4 hours)
- [ ] Launch 3 agents with checkpoint 2 specs + feedback
- [ ] Agents work for 2 hours
- [ ] Coordinator reviews integration
- [ ] Generate feedback reports
- [ ] Iteration if needed

### Checkpoint 3 (3.5 hours)
- [ ] Launch 3 agents with checkpoint 3 specs
- [ ] Agents work for 2 hours
- [ ] Coordinator reviews integration
- [ ] Final merge to main
- [ ] Cleanup worktrees

---

## Next Steps

1. **Review this spec** - Ensure the strategy makes sense
2. **Phase 0: Create contracts** - I'll create all interface definitions
3. **Launch Checkpoint 1** - Start the 3 agents
4. **Coordinate** - I'll act as coordinator between checkpoints

**Ready to proceed with Phase 0?**
