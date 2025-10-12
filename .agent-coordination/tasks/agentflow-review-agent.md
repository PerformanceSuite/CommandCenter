# AgentFlow Multi-Agent System Review Agent - Task Definition

**Mission:** Comprehensive review of AgentFlow orchestration system (from memory.md session notes)
**Worktree:** worktrees/agentflow-review-agent
**Branch:** review/agentflow-system
**Estimated Time:** 10 hours
**Dependencies:** None (Phase 0 - Pre-MCP Review)

---

## System Overview

**AgentFlow Status:** Referenced in memory.md but need to locate actual implementation

**Known Features (from session notes):**
- 15+ specialized agents (core, quality, specialized types)
- Git worktree strategy for parallel execution
- Review system with 10/10 scoring
- Coordination mechanisms
- agents.json configuration
- default.json workflow configuration
- Prompt templates (base.md, review.md, coordinate.md)

**Files Mentioned:**
- `AgentFlow/README.md`
- `AgentFlow/CLAUDE.md`
- `AgentFlow/config/agents.json`
- `AgentFlow/config/default.json`
- `AgentFlow/prompts/base.md`
- `AgentFlow/prompts/review.md`
- `AgentFlow/prompts/coordinate.md`
- `AgentFlow/scripts/setup.sh`
- `AgentFlow/scripts/agentflow.sh`

---

## Tasks Checklist

### Task 1: Locate and Analyze AgentFlow System (2 hours)
- [ ] Search for AgentFlow in user's Projects directory
- [ ] If not found, check if it's integrated into CommandCenter already
- [ ] Read README.md for system overview
- [ ] Read CLAUDE.md for development guidelines
- [ ] Understand agent orchestration architecture
- [ ] Document actual file structure

**Search Locations:**
- ~/Projects/AgentFlow
- ~/Projects/CommandCenter/AgentFlow
- ~/Projects/agent-flow
- Check git repositories

---

### Task 2: Review Agent Definitions & Configuration (2 hours)
- [ ] Read `agents.json` - 15+ agent definitions
- [ ] Analyze agent types (core, quality, specialized)
- [ ] Check agent task assignments
- [ ] Review agent dependency graph
- [ ] Verify agent isolation mechanisms
- [ ] Check agent communication protocol
- [ ] Analyze agent spawning logic

**Agent Types to Review:**
- Core agents (orchestrator, coordinator)
- Quality agents (review, testing, docs)
- Specialized agents (security, backend, frontend, etc.)

---

### Task 3: Review Git Worktree Strategy (2 hours)
- [ ] Analyze worktree creation and management
- [ ] Check branch isolation
- [ ] Review merge coordination
- [ ] Verify conflict resolution strategy
- [ ] Check cleanup processes
- [ ] Analyze parallel execution safety
- [ ] Review PR creation automation

**Git Workflow:**
- Worktree setup scripts
- Branch naming conventions
- Merge queue management
- Conflict detection and resolution
- Cleanup after merge

---

### Task 4: Review Scoring & Review System (1 hour)
- [ ] Read `prompts/review.md` - review rubric
- [ ] Analyze 10/10 scoring criteria
- [ ] Check iteration logic (improve until 10/10)
- [ ] Review feedback incorporation
- [ ] Verify review objectivity
- [ ] Check for score inflation prevention
- [ ] Analyze review agent prompts

**Scoring System:**
- Dimensions evaluated
- Scoring rubric clarity
- Iteration limits
- Failure handling
- Review consistency

---

### Task 5: Review Coordination & Communication (2 hours)
- [ ] Read `prompts/coordinate.md`
- [ ] Analyze inter-agent communication
- [ ] Check status tracking system
- [ ] Review dependency management
- [ ] Verify deadlock prevention
- [ ] Analyze coordination agent role
- [ ] Check event notification system

**Coordination Mechanisms:**
- Status files (JSON)
- Dependency graph
- Merge queue
- Agent messaging
- Event system

---

### Task 6: Review Scripts & Automation (1 hour)
- [ ] Analyze `setup.sh` - initialization
- [ ] Review `agentflow.sh` - orchestrator
- [ ] Check error handling in scripts
- [ ] Verify idempotency
- [ ] Review cleanup scripts
- [ ] Analyze monitoring capabilities
- [ ] Check integration with CommandCenter

**Scripts to Review:**
- setup.sh (worktree initialization)
- agentflow.sh (main orchestrator)
- monitoring scripts
- cleanup scripts
- utility scripts

---

## Review Checklist

### Architecture
- [ ] Agent orchestration sound
- [ ] Git worktree strategy robust
- [ ] Dependency management correct
- [ ] Communication protocol reliable
- [ ] Coordination logic deadlock-free

### Code Quality
- [ ] Shell scripts follow best practices
- [ ] Error handling comprehensive
- [ ] Logging sufficient
- [ ] No hardcoded paths or secrets
- [ ] Scripts are idempotent

### Testing
- [ ] Test coverage for agents
- [ ] Integration tests present
- [ ] Git operations tested
- [ ] Coordination logic validated

### Documentation
- [ ] Architecture documented
- [ ] Agent definitions clear
- [ ] Configuration options explained
- [ ] Usage examples accurate
- [ ] Troubleshooting guide present

### MCP Integration Readiness
- [ ] Can be wrapped as MCP orchestrator
- [ ] Agent spawning compatible with MCP
- [ ] Status tracking adaptable
- [ ] Configuration JSON compatible
- [ ] Prompts reusable in MCP

---

## Review Output Format

Create: `/Users/danielconnolly/Projects/CommandCenter/AGENTFLOW_REVIEW.md`

**Structure:**
```markdown
# AgentFlow Multi-Agent System Review

## Executive Summary
- Overall Status: ✅ Production Ready / ⚠️ Needs Work / ❌ Not Ready
- Critical Issues: [count]
- Medium Issues: [count]
- MCP Integration Readiness: [score]/10
- System Location: [path]

## System Architecture
### Agent Orchestration
- [Analysis of orchestration design]

### Git Worktree Strategy
- [Analysis of parallel execution]

### Findings
- [Issue 1]: Description
- [Issue 2]: Description

### Recommendations
- [Fix 1]
- [Fix 2]

## Agent Definitions & Configuration
[Same structure]

## Git Worktree Strategy
[Same structure]

## Scoring & Review System
[Same structure]

## Coordination & Communication
[Same structure]

## Scripts & Automation
[Same structure]

## Integration with CommandCenter
- Current integration status
- Compatibility analysis
- Integration points
- Required adaptations

## MCP Integration Blockers
- [Blocker 1 if any]
- [Blocker 2 if any]

## Recommended Actions
1. [Priority 1 fix]
2. [Priority 2 fix]
...

## Reusability Assessment
- Prompts: [Can reuse X%]
- Configuration: [Can reuse X%]
- Scripts: [Can adapt X%]
- Agent definitions: [Can reuse X%]

## Approval for MCP Wrapping
- [ ] Yes - Ready to wrap as MCP
- [ ] No - Fix issues first

### If No, Required Fixes:
1. [Critical fix 1]
2. [Critical fix 2]
```

---

## Success Criteria

- [ ] AgentFlow system located and analyzed
- [ ] All 6 tasks completed
- [ ] Comprehensive review document created
- [ ] All critical issues identified
- [ ] MCP integration blockers documented
- [ ] Reusability of components assessed
- [ ] Integration with CommandCenter analyzed
- [ ] Clear go/no-go decision on MCP wrapping
- [ ] Recommended fixes prioritized

---

**Reference Documents:**
- `.claude/memory.md` (Session 2 notes)
- AgentFlow system files (once located)
- CommandCenter agent coordination system
- Git worktree documentation
