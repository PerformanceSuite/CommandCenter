# Phase 1 Agent: VIZTRTR MCP SDK Fixes

**Agent Name:** phase1-viztrtr-fixes-agent
**Branch:** phase1/viztrtr-mcp-sdk-fixes
**Estimated Time:** 3 hours
**Priority:** CRITICAL - Quick Win
**Blocks:** VIZTRTR production deployment

---

## Mission

Fix VIZTRTR's MCP SDK import paths and re-enable hybrid scoring to make it production-ready. VIZTRTR is 85% ready and already uses `@modelcontextprotocol/sdk` v1.19.1 - this agent completes the final 15%.

---

## Context from Phase 0 Review

**VIZTRTR Review Score:** 8.5/10 - Near Ready

**Critical Issues Found (2 - both easy):**
1. 🔧 MCP SDK import paths broken (1-2 hours fix)
2. 🔧 Hybrid scoring disabled (30 min fix - depends on #1)

**Major Strengths:**
- ✅ Already uses `@modelcontextprotocol/sdk` v1.19.1
- ✅ 7 sophisticated agents (Orchestrator, Reflection, Verification, etc.)
- ✅ Memory system learns from failed attempts
- ✅ Production-grade validation (effort limits, backups, rollback)
- ✅ Extended thinking (2000-3000 token budgets)
- ✅ 291 test files

**From VIZTRTR_REVIEW.md:**
- Location: `/Users/danielconnolly/Projects/VIZTRTR`
- Technologies: TypeScript 5.6, Node.js 18+, Puppeteer, Chrome DevTools
- Dependencies: @modelcontextprotocol/sdk, @anthropic-ai/sdk, puppeteer, sharp

---

## Tasks

### Task 1: Fix MCP SDK Import Paths (1-2 hours)

**Goal:** Update all import statements to use correct `@modelcontextprotocol/sdk` paths

**Steps:**
1. Search for all MCP SDK imports:
   ```bash
   cd /Users/danielconnolly/Projects/VIZTRTR
   grep -r "from.*@modelcontextprotocol" --include="*.ts" --include="*.tsx"
   grep -r "import.*@modelcontextprotocol" --include="*.ts" --include="*.tsx"
   ```

2. Identify broken import paths (likely using old paths like `@modelcontextprotocol/server` instead of `@modelcontextprotocol/sdk`)

3. Check package.json to confirm SDK version:
   ```bash
   cat package.json | grep "@modelcontextprotocol/sdk"
   ```

4. Fix all import paths to match SDK v1.19.1 API:
   - Correct paths based on SDK documentation
   - Update any deprecated imports
   - Ensure all MCP types are imported correctly

5. Run TypeScript compiler to verify:
   ```bash
   npm run type-check
   ```

6. Run tests to ensure nothing broke:
   ```bash
   npm test
   ```

**Expected Issues:**
- Import paths may reference old SDK structure
- Some imports may use deprecated types
- Need to verify against SDK v1.19.1 API

**Success Criteria:**
- [ ] All MCP SDK imports use correct paths
- [ ] TypeScript compilation succeeds with no MCP-related errors
- [ ] All existing tests pass

---

### Task 2: Re-enable Hybrid Scoring (30 minutes)

**Goal:** Re-enable hybrid scoring system that was disabled (depends on MCP SDK imports)

**Steps:**
1. Search for hybrid scoring implementation:
   ```bash
   grep -r "hybrid.*scor" --include="*.ts" --include="*.tsx"
   grep -r "scoring" src/ --include="*.ts" | grep -i hybrid
   ```

2. Find why it was disabled:
   - Check for commented-out code
   - Look for feature flags
   - Check git history if needed

3. Re-enable hybrid scoring:
   - Uncomment or re-enable the feature
   - Ensure it integrates with fixed MCP SDK imports
   - Verify configuration is correct

4. Test hybrid scoring:
   ```bash
   npm test -- --grep "hybrid.*scor"
   ```

5. Validate in integration test:
   - Run a full VIZTRTR analysis cycle
   - Verify hybrid scoring is applied
   - Check that scores are calculated correctly

**Expected Issues:**
- May have been disabled due to MCP SDK import issues
- Could require configuration updates
- May need test updates

**Success Criteria:**
- [ ] Hybrid scoring is re-enabled
- [ ] Scoring tests pass
- [ ] Integration test shows correct scoring

---

### Task 3: Full Integration Test (30 minutes)

**Goal:** Run complete VIZTRTR iteration cycle to validate all fixes

**Steps:**
1. Start VIZTRTR server:
   ```bash
   npm run dev
   ```

2. Run a complete analysis cycle:
   - Screenshot capture
   - Vision analysis
   - Agent orchestration
   - Memory system update
   - Code implementation
   - Verification

3. Monitor for:
   - MCP SDK errors
   - Import errors
   - Scoring calculation issues
   - Agent communication problems

4. Check logs for warnings/errors:
   ```bash
   # Review logs for any MCP-related issues
   grep -i "error" logs/*.log | grep -i mcp
   grep -i "warn" logs/*.log | grep -i mcp
   ```

5. Verify extended thinking is working:
   - Check token budgets (2000-3000)
   - Verify reflection agent runs
   - Confirm verification agent completes

**Expected Issues:**
- May discover additional import issues
- Performance issues if scoring is heavy
- Agent coordination timing issues

**Success Criteria:**
- [ ] Complete iteration cycle succeeds
- [ ] No MCP SDK errors in logs
- [ ] Hybrid scoring produces valid results
- [ ] All 7 agents function correctly
- [ ] Memory system persists learning

---

### Task 4: Production Readiness Check (30 minutes)

**Goal:** Validate VIZTRTR is production-ready

**Steps:**
1. Run full test suite:
   ```bash
   npm test
   npm run test:integration
   ```

2. Check test coverage:
   ```bash
   npm run test:coverage
   ```

3. Verify production configurations:
   - Environment variables documented
   - Docker setup validated
   - Resource limits appropriate
   - Error handling robust

4. Security check:
   - Review Puppeteer sandbox settings
   - Verify API key handling
   - Check for exposed secrets
   - Validate input sanitization

5. Performance validation:
   - Memory usage acceptable
   - Response times reasonable
   - No resource leaks
   - Cleanup working correctly

6. Create production deployment checklist:
   - Document environment requirements
   - List configuration variables
   - Note any operational concerns
   - Specify monitoring requirements

**Success Criteria:**
- [ ] All tests pass (291 test files)
- [ ] Test coverage > 80%
- [ ] No security vulnerabilities found
- [ ] Performance metrics acceptable
- [ ] Production deployment checklist created

---

### Task 5: Documentation Update (30 minutes)

**Goal:** Update documentation to reflect MCP SDK fixes and production readiness

**Steps:**
1. Update README.md:
   - Note MCP SDK version (v1.19.1)
   - Document import path changes
   - Explain hybrid scoring re-enablement
   - Add production deployment section

2. Update VIZTRTR_REVIEW.md status:
   - Change score from 8.5/10 to 10/10
   - Mark critical issues as ✅ FIXED
   - Update MCP integration readiness
   - Add production deployment date

3. Create VIZTRTR_MCP_PRODUCTION_READY.md:
   - Document all fixes applied
   - List production deployment steps
   - Include monitoring recommendations
   - Note known limitations (if any)

4. Update Phase 0 documents:
   - Mark VIZTRTR as production-ready in PHASE0_CONSOLIDATED_FINDINGS.md
   - Update PHASE0_COMPLETE.md with VIZTRTR success
   - Add to success metrics

**Success Criteria:**
- [ ] README.md updated
- [ ] VIZTRTR_REVIEW.md updated (10/10)
- [ ] VIZTRTR_MCP_PRODUCTION_READY.md created
- [ ] Phase 0 documents updated

---

### Task 6: Commit and PR (30 minutes)

**Goal:** Create clean commit and PR for review

**Steps:**
1. Review all changes:
   ```bash
   git status
   git diff
   ```

2. Create atomic commits:
   ```bash
   git add [files with MCP SDK import fixes]
   git commit -m "fix: Update MCP SDK import paths to v1.19.1 API"

   git add [files with hybrid scoring]
   git commit -m "feat: Re-enable hybrid scoring system"

   git add [tests and documentation]
   git commit -m "docs: Update VIZTRTR production readiness documentation"
   ```

3. Push branch:
   ```bash
   git push -u origin phase1/viztrtr-mcp-sdk-fixes
   ```

4. Create PR using coordination-agent.sh workflow:
   - Title: "Phase 1: VIZTRTR MCP SDK Fixes - Production Ready"
   - Body: Comprehensive summary of fixes
   - Link to VIZTRTR_REVIEW.md
   - Note this completes Phase 1 for VIZTRTR

5. Self-review (aim for 10/10):
   - All tests pass
   - Documentation complete
   - No regressions
   - Production-ready

**PR Body Template:**
```markdown
# Phase 1: VIZTRTR MCP SDK Fixes - Production Ready

## Summary
Fixes the final 15% of VIZTRTR to make it production-ready. VIZTRTR was already 85% ready from Phase 0 review.

## Changes
- ✅ Fixed MCP SDK import paths (v1.19.1 API)
- ✅ Re-enabled hybrid scoring system
- ✅ Full integration test cycle validated
- ✅ Production readiness confirmed (10/10)

## Test Results
- All 291 test files pass
- Integration test cycle complete
- No MCP SDK errors
- Hybrid scoring functional

## Phase 0 → Phase 1
**Before:** 8.5/10 (Near Ready)
**After:** 10/10 (Production Ready)

## Time Estimate vs Actual
- Estimated: 3 hours
- Actual: [FILL IN]

## Next Steps
- Merge this PR
- Deploy VIZTRTR as first MCP server in production
- Use as template for other MCP servers

## Links
- Phase 0 Review: VIZTRTR_REVIEW.md
- Consolidated Findings: PHASE0_CONSOLIDATED_FINDINGS.md
- Production Ready Doc: VIZTRTR_MCP_PRODUCTION_READY.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Success Criteria:**
- [ ] Clean atomic commits
- [ ] PR created with comprehensive summary
- [ ] Self-review score: 10/10
- [ ] Ready for merge

---

## Definition of Done

- [ ] All MCP SDK import paths fixed and validated
- [ ] Hybrid scoring re-enabled and tested
- [ ] Full integration test cycle passes
- [ ] All 291 test files pass
- [ ] Production readiness validated
- [ ] Documentation updated
- [ ] PR created and self-reviewed (10/10)
- [ ] VIZTRTR ready for production deployment

---

## Success Metrics

**Time:** 3 hours (1-2h imports + 30m scoring + 30m integration + 30m production check + 30m docs + 30m PR)
**Tests:** 291 test files must pass
**Score:** 8.5/10 → 10/10
**Impact:** First MCP server ready for production

---

## Notes

- VIZTRTR is the **quickest win** in Phase 1
- Already uses MCP SDK - just needs import fixes
- This validates the entire MCP approach
- Success here builds confidence for other systems
- Use VIZTRTR as template for future MCP servers

---

**Priority:** 🔴 CRITICAL - Quick Win
**Blocking:** Production deployment of first MCP server
**Dependencies:** None - can start immediately
