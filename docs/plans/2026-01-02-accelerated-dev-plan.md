# Accelerated Development Plan
*2026-01-02 - Living Document*

## Philosophy (Corrected)

**NOT**: Long-running overnight agents
**YES**: Wide + Bite-sized + Verified

- Go as wide as possible (max parallel worktrees/sandboxes)
- Bite-sized pieces only (verifiable, observable)
- First verify agents can actually work before scaling

## The Verification Loop (Must Prove First)

Can an agent in an E2B sandbox actually:
1. Read a skill file
2. Follow its instructions
3. Complete a small task correctly
4. Write back improvements to the skill

**Until this loop is verified, scaling is premature.**

## Phase 1: Verify Basic Agent Capability

### Test 1: Can agent read and follow a skill?
- Task: "Read the agent-sandboxes skill, summarize it"
- Success: Accurate summary
- Time: ~2 min

### Test 2: Can agent complete a small coding task?
- Task: "Add a docstring to function X in file Y"
- Success: Valid commit with correct change
- Time: ~5 min

### Test 3: Can agent improve a skill file?
- Task: "Try to use skill X, document any issues you hit, propose improvements"
- Success: Meaningful skill update PR
- Time: ~10 min

## Phase 2: Parallel Execution (After Verification)

Once Phase 1 passes:
- 3-6 parallel worktrees
- Each agent gets one bite-sized task
- All results observable before next batch

## Infrastructure Needed

- [ ] E2B sandbox working (have it)
- [ ] Skills readable by agents (have it)
- [ ] Git commit/PR flow (have it)
- [ ] Task queue for bite-sized work (need it)
- [ ] Results dashboard (need it)

## Next Action

Run Test 1 right now.
