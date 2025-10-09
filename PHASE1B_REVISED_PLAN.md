# Phase 1b REVISED: Focus on CommandCenter Core (No MCP Yet)

**Reality Check:** Based on Phase 0 findings, skip MCP integration until foundations are solid.

**Date:** 2025-10-09
**Strategy:** Fix CommandCenter's critical issues, make it production-ready standalone
**Timeline:** 3-4 weeks → 1 week parallelized

---

## Executive Decision: Skip MCP for Now

### Why No MCP Yet?

**VIZTRTR (8.5/10):**
- ✅ Nearly ready BUT
- ❌ PR #18 is just MCP SDK import fixes (2-3h work)
- ❌ Still experimental, not core to CommandCenter
- **Decision:** Fix and keep as standalone tool, MCP later

**KnowledgeBeast (3/10):**
- ❌ NOT a RAG system (uses keyword matching, not vectors!)
- ❌ No collection isolation (all projects share data)
- ❌ Needs 4-6 weeks of fundamental redesign
- **Decision:** Don't wrap broken system, fix it first

**CommandCenter (6/10):**
- ❌ Database has NO project isolation
- ❌ Redis keys collide between projects
- ❌ ChromaDB single collection (data leakage!)
- **Decision:** THIS is the priority - make CommandCenter actually useful

---

## Phase 1b: CommandCenter Production Readiness

**Goal:** Make CommandCenter a solid R&D knowledge base WITHOUT MCP dependency

### Core Issues to Fix (21 hours → 5 hours parallelized)

#### 1. Database Isolation (CRITICAL)
**Problem:** All tables share data across projects - massive security issue
**Impact:** Can't run multiple projects safely
**Fix Time:** 12 hours

#### 2. Redis Namespacing (CRITICAL)
**Problem:** Cache collisions between projects
**Impact:** Wrong data returned to wrong project
**Fix Time:** 3 hours

#### 3. ChromaDB Per-Project Collections (CRITICAL)
**Problem:** Single collection = knowledge base returns wrong project's data
**Impact:** Research findings leak between projects
**Fix Time:** 4 hours

#### 4. Project Context Middleware (HIGH)
**Problem:** No way to identify which project is being accessed
**Impact:** Can't enforce isolation even after database fixes
**Fix Time:** 2 hours

---

## Phase 1b Agent Assignments (Parallel)

### Agent 1: Database Isolation Agent (12 hours)
**Branch:** `feature/database-isolation`
**Priority:** CRITICAL

**Tasks:**
1. Create `Project` model
   - id, name, owner, created_at, updated_at
   - Unique constraint on (owner, name)

2. Add `project_id` foreign key to ALL tables:
   - ✅ repositories
   - ✅ technologies
   - ✅ research_tasks
   - ✅ knowledge_entries
   - ✅ webhooks
   - ✅ rate_limits

3. Create Alembic migration
   - Add project_id columns
   - Create foreign keys
   - Add indexes on project_id
   - Migration script for existing data (assign to default project)

4. Update all SQLAlchemy queries
   - Add `.filter(model.project_id == project_id)` everywhere
   - Update create operations to include project_id
   - Add project_id validation

5. Update all routers
   - Extract project_id from request context
   - Pass to service layer
   - Validate project access

**Success Criteria:**
- All queries filtered by project_id
- Impossible to access other project's data
- Migration runs cleanly
- All tests pass

---

### Agent 2: Redis & Cache Agent (3 hours)
**Branch:** `feature/redis-namespacing`
**Priority:** CRITICAL

**Tasks:**
1. Update RedisService class
   - Add project_id to all key generation
   - Pattern: `project:{project_id}:{key_type}:{identifier}`
   - Examples:
     - `project:123:repo:owner/name`
     - `project:123:rate_limit:github_api`

2. Update all cache calls
   - Pass project_id to Redis operations
   - Update cache invalidation to use project prefix

3. Add cache isolation tests
   - Verify project A can't access project B's cache
   - Test cache invalidation per-project

**Success Criteria:**
- All Redis keys namespaced by project
- Cache isolation verified
- No cross-project cache leaks

---

### Agent 3: ChromaDB Multi-Collection Agent (4 hours)
**Branch:** `feature/chromadb-collections`
**Priority:** CRITICAL

**Tasks:**
1. Update RAGService
   - Change from single collection to per-project collections
   - Collection name pattern: `knowledge_project_{project_id}`
   - Create collection on first use per project

2. Update knowledge endpoints
   - Pass project_id to RAG operations
   - Create/use project-specific collection

3. Add collection management
   - List collections per project
   - Delete collection when project deleted
   - Migrate existing embeddings to default project collection

4. Update tests
   - Test multi-collection isolation
   - Verify queries only search project's collection

**Success Criteria:**
- Each project has own ChromaDB collection
- Knowledge queries isolated by project
- No cross-project knowledge leaks

---

### Agent 4: Project Context Agent (2 hours)
**Branch:** `feature/project-context`
**Priority:** HIGH

**Tasks:**
1. Create ProjectContextMiddleware
   - Extract project_id from:
     - Request header: `X-Project-ID`
     - JWT token claim: `project_id`
     - Query parameter: `?project_id=123` (fallback)
   - Attach to request.state.project_id

2. Add project validation
   - Verify user has access to project
   - Return 403 if unauthorized
   - Log all project access attempts

3. Update auth system
   - Add project_id to JWT tokens
   - Add user-project relationship table
   - Implement project access control

4. Add project selector to frontend
   - Dropdown in header
   - Persist selection in localStorage
   - Send in X-Project-ID header on all requests

**Success Criteria:**
- All requests have project context
- Unauthorized access blocked
- Frontend can switch projects
- All services use project_id

---

## Parallel Execution Strategy

### Week 1: All 4 Agents in Parallel

```
Day 1-3: Development Phase
├── Agent 1: Database schema changes + migrations
├── Agent 2: Redis namespacing
├── Agent 3: ChromaDB collections
└── Agent 4: Project context middleware

Day 4: Integration Phase
├── Merge Agent 4 first (middleware foundation)
├── Merge Agent 2 (Redis namespacing)
├── Merge Agent 3 (ChromaDB collections)
└── Merge Agent 1 last (database - most complex)

Day 5: Testing & Validation
├── Integration tests across all changes
├── Multi-project smoke tests
├── Performance testing
└── Security validation
```

**Timeline:**
- Sequential: 21 hours (3 days)
- Parallel: 12 hours max (Agent 1) = 1.5 days
- With reviews/testing: 5 days total

---

## What We're NOT Doing (For Now)

### ❌ MCP Server Development
- Wait until foundations solid
- KnowledgeBeast needs 4-6 weeks first
- VIZTRTR separate tool, not core
- Focus on core CommandCenter value

### ❌ VIZTRTR Integration
- Keep as standalone tool
- PR #18 fixes are fine but not priority
- Can integrate later when stable

### ❌ AgentFlow Coordinator
- Config/prompts are excellent
- Execution layer needs rebuild (1-2 weeks)
- Not blocking CommandCenter usefulness

### ❌ Additional Features
- AI Tools UI (experimental branch)
- Dev Tools Hub (experimental branch)
- Keep focused on core R&D knowledge base

---

## What Makes CommandCenter Useful (After Phase 1b)

### ✅ Multi-Project Support
- Run multiple R&D projects safely
- Complete data isolation
- No cross-project leaks

### ✅ Knowledge Base (RAG)
- Per-project knowledge collections
- Semantic search within project
- Document ingestion per project

### ✅ Tech Radar
- Track technologies per project
- Domain-specific categorization
- Status tracking (adopt/trial/assess/hold)

### ✅ Research Task Management
- Track research items per project
- Link to technologies and repositories
- Priority and status management

### ✅ GitHub Integration
- Repository tracking per project
- Commit history analysis
- Webhook support

### ✅ Secure & Isolated
- Project-level data isolation
- Encrypted GitHub tokens
- Rate limiting
- Security headers

---

## Success Criteria for Phase 1b

### Must Have (CRITICAL):
- [x] Database: All tables have project_id
- [x] Database: All queries filtered by project
- [x] Redis: All keys namespaced by project
- [x] ChromaDB: Per-project collections
- [x] Middleware: Project context on all requests
- [x] Auth: Project access control
- [x] Frontend: Project selector
- [x] Tests: Multi-project isolation verified

### Nice to Have (Can defer):
- [ ] Project CRUD UI
- [ ] Project settings page
- [ ] Project member management
- [ ] Project-level analytics

---

## Phase 1c: Polish & Production (Week 2)

**After Phase 1b foundations solid:**

### Security Hardening (6 hours)
- MCP authentication (for future)
- Command injection sanitization
- Path traversal prevention
- API key rotation

### Performance Optimization (4 hours)
- Database query optimization
- Redis connection pooling
- ChromaDB query performance
- Frontend bundle optimization

### Production Deployment (4 hours)
- Docker compose production config
- Environment variable management
- Backup/restore procedures
- Monitoring dashboards

### Documentation (6 hours)
- Multi-project setup guide
- API documentation updates
- Architecture diagrams
- Deployment guide

**Total Phase 1c:** 20 hours → 1 week with review/testing

---

## Revised Roadmap

### Phase 1a: ✅ In Progress (CI fixes)
- Fix CI/CD failures
- Merge PRs #18 and #19
- Git working tree clean
- **Duration:** 4-6 hours

### Phase 1b: Database Isolation (THIS PHASE)
- Multi-project data isolation
- Redis namespacing
- ChromaDB per-project collections
- Project context middleware
- **Duration:** 5 days (21h parallelized to 12h + testing)

### Phase 1c: Polish & Production
- Security hardening
- Performance optimization
- Production deployment
- Documentation
- **Duration:** 1 week

### Phase 2-4: Advanced Features (Defer for now)
- KnowledgeBeast redesign (4-6 weeks when ready)
- VIZTRTR production (when stable)
- AgentFlow execution layer (1-2 weeks when needed)
- MCP integration (after foundations proven)

---

## Key Decisions

### ✅ DO Focus On:
1. **CommandCenter Core:** Make the R&D knowledge base actually work
2. **Multi-Project Isolation:** CRITICAL security and usability issue
3. **Solid Foundations:** Database, cache, knowledge base integrity
4. **Production Ready:** Deploy what works, iterate later

### ❌ DON'T Focus On (Yet):
1. **MCP Integration:** Underlying systems not ready
2. **KnowledgeBeast MCP:** Needs fundamental redesign first
3. **VIZTRTR MCP:** Nice-to-have, not core value
4. **AgentFlow Coordinator:** Execution layer needs rebuild
5. **Experimental Features:** AI Tools UI can wait

---

## Why This Approach?

### Phase 0 Findings Were Clear:
- **VIZTRTR:** 8.5/10 but not core to CommandCenter
- **KnowledgeBeast:** 3/10 - broken, needs major work
- **CommandCenter:** 6/10 - database isolation BLOCKS everything
- **MCP Security:** 7/10 - not ready for production

### Building on Broken Foundations = Waste
- Would wrap fake RAG system (KnowledgeBeast)
- Would deploy with data leakage (CommandCenter database)
- Would spend weeks on MCP while core broken

### Fix Core First = Real Value
- CommandCenter becomes actually useful for R&D
- Multi-project support = real deployment possibility
- Solid foundation = MCP later when ready
- Proven value = easier to justify additional work

---

## Next Steps After Phase 1a Complete

1. **Review Phase 1b Plan** (this document)
2. **Create 4 agent task definitions** (database, redis, chromadb, context)
3. **Setup worktrees for Phase 1b**
4. **Launch 4 agents in parallel**
5. **5 days later: CommandCenter production ready!**

---

**Status:** Plan Complete ✅
**Focus:** Core CommandCenter value, not MCP integration yet
**Timeline:** Phase 1b (1 week) + Phase 1c (1 week) = 2 weeks to production
**MCP:** Phase 2+ after foundations proven solid
