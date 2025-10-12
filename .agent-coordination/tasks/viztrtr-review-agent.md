# VIZTRTR System Review Agent - Task Definition

**Mission:** Comprehensive review of VIZTRTR UI/UX analysis system and all dependencies
**Worktree:** worktrees/viztrtr-review-agent
**Branch:** review/viztrtr-system
**Estimated Time:** 14 hours
**Dependencies:** None (Phase 0 - Pre-MCP Review)

---

## System Overview

**VIZTRTR Location:** `/Users/danielconnolly/Projects/VIZTRTR`

**Core Technology Stack:**
- TypeScript 5.6
- Node.js 18+
- Puppeteer 23.0+ (headless Chrome)
- Chrome DevTools Protocol (chrome-devtools-mcp)
- Anthropic Claude (vision analysis)
- Google Gemini (optional)
- OpenAI (optional)

**Key Dependencies:**
1. **Puppeteer** - Headless browser automation and screenshots
2. **chrome-devtools-mcp** - Chrome DevTools integration
3. **@anthropic-ai/sdk** - Claude Opus 4 vision analysis
4. **Sharp** - Image processing
5. **fluent-ffmpeg** - Video processing
6. **@modelcontextprotocol/sdk** - MCP SDK already integrated!

**Agent System:**
- OrchestratorAgent - Coordinates improvements
- ReflectionAgent - Analyzes iteration outcomes
- VerificationAgent - Validates changes
- IterationMemoryManager - Learns from past attempts

---

## Tasks Checklist

### Task 1: Review Core Orchestrator & Agent System (3 hours)
- [ ] Read `/Users/danielconnolly/Projects/VIZTRTR/src/core/orchestrator.ts`
- [ ] Analyze OrchestratorAgent implementation
- [ ] Review ReflectionAgent logic
- [ ] Check VerificationAgent validation
- [ ] Analyze agent coordination and communication
- [ ] Review iteration loop and stopping conditions
- [ ] Check 8-dimension scoring system
- [ ] Verify memory system integration

**Focus Areas:**
- Agent coordination reliability
- Iteration convergence (target: 8.5+/10 score)
- Memory learning effectiveness
- Scoring accuracy and consistency
- Error recovery in agent failures

---

### Task 2: Review Puppeteer & Screenshot Capture (2 hours)
- [ ] Read `/Users/danielconnolly/Projects/VIZTRTR/src/plugins/capture-puppeteer.ts`
- [ ] Check Puppeteer configuration and browser launch
- [ ] Verify screenshot quality and consistency
- [ ] Analyze headless browser stability
- [ ] Review viewport configuration
- [ ] Check resource cleanup (browser instances)
- [ ] Test screenshot capture under various conditions
- [ ] Verify Sharp image processing pipeline

**Critical Checks:**
- Browser instance leaks (memory leaks)
- Screenshot consistency across runs
- Headless rendering accuracy
- Performance under concurrent captures
- Error handling for unresponsive pages

---

### Task 3: Review Chrome DevTools Integration (2 hours)
- [ ] Read chrome-devtools-mcp usage
- [ ] Check DevTools Protocol implementation
- [ ] Verify performance metrics collection
- [ ] Analyze accessibility audit integration
- [ ] Review network inspection capabilities
- [ ] Check console log capture
- [ ] Verify DOM manipulation safety

**DevTools Features:**
- Performance profiling
- Accessibility audits
- Network analysis
- Console monitoring
- DOM inspection
- Resource tracking

---

### Task 4: Review Vision Analysis & AI Integration (3 hours)
- [ ] Read `/Users/danielconnolly/Projects/VIZTRTR/src/plugins/vision-claude.ts`
- [ ] Analyze Claude Opus 4 vision prompts
- [ ] Review image encoding and API calls
- [ ] Check multi-provider support (Google, OpenAI)
- [ ] Verify API error handling and retries
- [ ] Analyze cost optimization strategies
- [ ] Review scoring prompt engineering
- [ ] Test vision analysis accuracy

**AI Integration:**
- Prompt quality for design critique
- Vision API reliability
- Cost per iteration estimate
- Multi-model fallback
- Rate limiting and quotas
- Response parsing robustness

---

### Task 5: Review Memory & Learning System (2 hours)
- [ ] Read `/Users/danielconnolly/Projects/VIZTRTR/src/memory/IterationMemoryManager.ts`
- [ ] Analyze memory persistence strategy
- [ ] Check failed attempt tracking
- [ ] Review successful strategy storage
- [ ] Verify cross-run learning
- [ ] Analyze memory retrieval efficiency
- [ ] Check memory cleanup and limits
- [ ] Test memory-guided iteration improvements

**Memory System:**
- Persistence format and location
- Memory retrieval accuracy
- Learning effectiveness over runs
- Memory bloat prevention
- Cross-project memory isolation

---

### Task 6: Review Code Implementation Plugin (1 hour)
- [ ] Read `/Users/danielconnolly/Projects/VIZTRTR/src/plugins/implementation-claude.ts`
- [ ] Check code generation quality
- [ ] Verify safe code application
- [ ] Review code validation before apply
- [ ] Analyze undo/rollback mechanisms
- [ ] Check file system safety
- [ ] Verify no destructive operations without confirmation

**Safety Checks:**
- No accidental file deletions
- Backup before modifications
- Code validation before apply
- Rollback mechanisms
- User confirmation for destructive ops

---

### Task 7: Review MCP SDK Integration (1 hour)
- [ ] Check `@modelcontextprotocol/sdk` usage
- [ ] Analyze existing MCP patterns
- [ ] Verify MCP server compatibility
- [ ] Review MCP tool definitions
- [ ] Check MCP resource providers
- [ ] Analyze stdio transport readiness

**MCP Readiness:**
- Already uses MCP SDK! (major advantage)
- Check if ready for server mode
- Verify tool/resource architecture
- Check async compatibility

---

## Review Checklist

### Code Quality
- [ ] TypeScript strict mode enabled
- [ ] Type safety comprehensive
- [ ] Error handling robust
- [ ] Logging sufficient for debugging
- [ ] No API keys hardcoded
- [ ] Configuration externalized

### Testing
- [ ] Unit tests present (check tests/ directory)
- [ ] Integration tests exist
- [ ] End-to-end tests for orchestration
- [ ] Vision analysis mocks for testing
- [ ] Screenshot capture tests

### Documentation
- [ ] API documentation complete
- [ ] Configuration options documented
- [ ] Scoring system explained
- [ ] Agent architecture documented
- [ ] Usage examples accurate

### MCP Integration Readiness
- [ ] Can run headless (no UI required)
- [ ] Clean TypeScript API for programmatic use
- [ ] Async/await throughout
- [ ] Already uses @modelcontextprotocol/sdk
- [ ] Tool definitions adaptable to MCP
- [ ] Resource providers ready

---

## Review Output Format

Create: `/Users/danielconnolly/Projects/CommandCenter/VIZTRTR_REVIEW.md`

**Structure:**
```markdown
# VIZTRTR System Review

## Executive Summary
- Overall Status: ✅ Production Ready / ⚠️ Needs Work / ❌ Not Ready
- Critical Issues: [count]
- Medium Issues: [count]
- MCP Integration Readiness: [score]/10
- **Already Uses MCP SDK**: ✅ Yes / ❌ No

## Core Orchestrator & Agent System
### Findings
- [Issue 1]: Description
- [Issue 2]: Description

### Recommendations
- [Fix 1]
- [Fix 2]

## Puppeteer & Screenshot Capture
[Same structure]

## Chrome DevTools Integration
[Same structure]

## Vision Analysis & AI Integration
[Same structure]

## Memory & Learning System
[Same structure]

## Code Implementation Plugin
[Same structure]

## MCP SDK Integration
[Same structure]

## 8-Dimension Scoring System
- Visual Hierarchy: [analysis]
- Typography: [analysis]
- Color & Contrast: [analysis]
- Spacing & Layout: [analysis]
- Accessibility: [analysis]
- Responsiveness: [analysis]
- Performance: [analysis]
- User Experience: [analysis]

## MCP Integration Blockers
- [Blocker 1 if any]
- [Blocker 2 if any]

## Recommended Actions
1. [Priority 1 fix]
2. [Priority 2 fix]
...

## Test Results
- Unit tests: PASS/FAIL
- Integration tests: PASS/FAIL
- End-to-end tests: PASS/FAIL
- Vision analysis accuracy: [score]

## Approval for MCP Wrapping
- [ ] Yes - Ready to wrap as MCP
- [ ] No - Fix issues first

### If No, Required Fixes:
1. [Critical fix 1]
2. [Critical fix 2]

## MCP Advantages
- Already uses @modelcontextprotocol/sdk
- Agent architecture maps to MCP tools
- Headless operation ready
- [Other advantages]
```

---

## Success Criteria

- [ ] All 7 tasks completed
- [ ] Comprehensive review document created
- [ ] All critical issues identified
- [ ] MCP integration blockers documented
- [ ] Agent system reliability verified
- [ ] Puppeteer stability confirmed
- [ ] Vision analysis accuracy validated
- [ ] Clear go/no-go decision on MCP wrapping
- [ ] Recommended fixes prioritized

---

**Reference Documents:**
- `/Users/danielconnolly/Projects/VIZTRTR/README.md`
- `/Users/danielconnolly/Projects/VIZTRTR/package.json`
- `/Users/danielconnolly/Projects/VIZTRTR/docs/`
- VIZTRTR source code
- Chrome DevTools Protocol documentation
- Anthropic Vision API documentation
