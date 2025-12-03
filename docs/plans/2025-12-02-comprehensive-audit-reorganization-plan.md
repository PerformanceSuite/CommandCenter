# Comprehensive Audit & Reorganization Plan

**Date**: 2025-12-02
**Status**: Ready for Execution
**Approach**: Hybrid B+C (Document First + Incremental Hub Restructure)

---

## Executive Summary

After several weeks away from active development, this plan provides a structured approach to:
1. **Understand** current state of CommandCenter and VERIA
2. **Document** architecture, relationships, and integration points
3. **Reorganize** incrementally without breaking momentum
4. **Prepare** for next phase of development

**Key Decisions:**
- CommandCenter + VERIA remain **separate projects** with clear API boundaries
- Use **E2B sandboxes** for parallel, isolated audit exploration
- **Keep momentum** - don't over-engineer the reorganization
- Run **GitDiagram** to generate visual architecture maps

---

## Phase 0: E2B Setup (30 minutes)

### Prerequisites

```bash
# Verify E2B credentials in .env
E2B_API_KEY=your_e2b_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GITHUB_TOKEN=your_github_token

# Navigate to agent-sandboxes
cd /Users/danielconnolly/Projects/CommandCenter/tools/agent-sandboxes

# Install dependencies
cd apps/sandbox_workflows
uv sync
```

### Verify Setup

```bash
# Test basic sandbox creation
cd apps/sandbox_fundamentals
uv run python 01_basic_sandbox.py
```

---

## Phase 1: Parallel Audit Execution (2-4 hours)

### Fork Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AUDIT ORCHESTRATOR                        │
│              (Local Claude Code session)                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┐
    ▼             ▼             ▼             ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│ Fork 1 │  │ Fork 2 │  │ Fork 3 │  │ Fork 4 │
│ E2B    │  │ E2B    │  │ E2B    │  │ E2B    │
├────────┤  ├────────┤  ├────────┤  ├────────┤
│GitDiag │  │ Legacy │  │ VERIA  │  │ Code   │
│  Gen   │  │  XML   │  │ Review │  │ Health │
└────────┘  └────────┘  └────────┘  └────────┘
```

### Fork 1: GitDiagram Generation

**Objective**: Generate visual architecture diagrams for both repos

**Commands**:
```bash
# In E2B sandbox
git clone https://github.com/ahmedkhaleel2004/gitdiagram
cd gitdiagram

# Option A: Use their hosted service
# Visit https://gitdiagram.com and paste repo URLs

# Option B: Run locally (requires OpenAI API key)
# Follow gitdiagram README for local setup

# Generate for:
# 1. CommandCenter full repo
# 2. CommandCenter hub/ subdirectory
# 3. VERIA_PLATFORM repo
```

**Output Files**:
- `docs/diagrams/commandcenter-architecture.mmd`
- `docs/diagrams/commandcenter-architecture.png`
- `docs/diagrams/hub-modules.mmd`
- `docs/diagrams/veria-architecture.mmd`

### Fork 2: Legacy XML Analysis

**Objective**: Parse legacy XML exports to understand historical context

**Files to Analyze**:
```
/Users/danielconnolly/Projects/VERIA_PLATFORM/LEGACY_CODE_BASE/
├── legacy_commandcenter.xml     (8.6 MB)
├── legacy_intelligence.xml      (38 MB)
├── legacy_codebase.xml          (76 MB)
├── legacy_codebase_part_a[a-e]  (split files)
├── legacy_intelligence_part_a[a-c]
```

**Analysis Tasks**:
1. Extract file structure and key entities
2. Identify CommandCenter ↔ Intelligence relationships
3. Document intended integration patterns
4. Find deprecated vs still-relevant code paths

**Output File**: `docs/LEGACY_ANALYSIS.md`

### Fork 3: VERIA Platform Audit

**Objective**: Understand current VERIA state and integration points

**Directory**: `/Users/danielconnolly/Projects/VERIA_PLATFORM/`

**Analysis Tasks**:
1. Map current directory structure
2. Identify API endpoints and contracts
3. Find references to CommandCenter
4. Document authentication/authorization model
5. Check `.claude/` for project context

**Key Files to Review**:
- `docs/PROJECT.md`
- `docs/TECHNICAL.md`
- `GEMINI.md`
- `GENKIT_INTEGRATION_SPEC.md`

**Output File**: `docs/VERIA_INTEGRATION.md`

### Fork 4: Code Health Audit

**Objective**: Assess codebase health and identify technical debt

**Scans to Run**:

```bash
# Dependency vulnerabilities
cd hub/frontend && npm audit
cd hub/orchestration && npm audit
cd hub/backend && pip-audit

# Dead code detection
npx knip  # or ts-prune for TypeScript

# TODO/FIXME inventory
grep -rn "TODO\|FIXME" --include="*.ts" --include="*.tsx" --include="*.py" | head -50

# Test coverage
cd hub/backend && pytest --cov=app --cov-report=html
cd hub/frontend && npm run test:coverage

# Bundle size
cd hub/frontend && npm run build && du -sh dist/

# Circular dependencies
npx madge --circular hub/frontend/src
```

**Output File**: `docs/CODE_HEALTH_REPORT.md`

---

## Phase 2: Documentation (Wave 1) - Day 1-2

### Deliverables

| Document | Purpose | Location |
|----------|---------|----------|
| `ARCHITECTURE.md` | Complete codebase map | Root directory |
| `CODEBASE_AUDIT.md` | Consolidated audit findings | `docs/` |
| `VERIA_INTEGRATION.md` | Cross-project API spec | `docs/` |
| `LEGACY_ANALYSIS.md` | Historical context | `docs/` |
| `CODE_HEALTH_REPORT.md` | Technical debt inventory | `docs/` |

### ARCHITECTURE.md Template

```markdown
# CommandCenter Architecture

## Overview
[High-level description]

## Directory Structure
[Output from tree command with annotations]

## Module Map

### Hub (Main Application)
- `hub/orchestration/` - Agent workflow engine
- `hub/frontend/` - React UI
- `hub/backend/` - FastAPI services
- `hub/vislzr/` - Visualization components
- `hub/observability/` - Metrics and tracing

### Core Services
- `backend/` - Legacy backend (→ migrating to hub/core/api)
- `frontend/` - Legacy frontend (→ migrating to hub/core/ui)
- `federation/` - Cross-project coordination service

### Libraries
- `libs/knowledgebeast/` - RAG/knowledge base engine

### Tools
- `tools/agent-sandboxes/` - E2B sandbox integration
- `tools/graphvis/` - Graph visualization utilities

### Infrastructure
- `monitoring/` - Grafana dashboards
- `traefik/` - Reverse proxy config

## Data Flow
[Mermaid diagram from GitDiagram output]

## Integration Points
[VERIA ↔ CommandCenter API boundaries]
```

---

## Phase 3: Reorganization (Wave 2) - Day 3-5

### Target Structure

```
CommandCenter/
├── ARCHITECTURE.md              # NEW
├── hub/
│   ├── modules/                 # NEW: Feature modules
│   │   ├── vislzr/             # Visualization
│   │   ├── orchestration/      # Agent workflows
│   │   ├── observability/      # Metrics/tracing
│   │   └── graph/              # Code graph service
│   ├── core/                    # NEW: Shared infrastructure
│   │   ├── api/                # FastAPI routes
│   │   ├── ui/                 # React components
│   │   └── shared/             # Common utilities
│   ├── frontend/               # Keep (→ imports from core/ui)
│   ├── backend/                # Keep (→ imports from core/api)
│   └── docs/                   # Hub-specific docs
├── federation/                  # Keep (separate service)
├── libs/                        # Keep
├── tools/                       # Keep
├── docs/                        # Project-wide docs
└── [deprecated]/
    ├── backend/                 # Mark deprecated
    ├── frontend/                # Mark deprecated
    └── hub-prototype/           # Archive
```

### Migration Steps

#### Step 3.1: Create Module Structure
```bash
mkdir -p hub/modules
mkdir -p hub/core/{api,ui,shared}
```

#### Step 3.2: Move VISLZR
```bash
# VISLZR is currently scattered across hub/frontend and hub/vislzr
# Consolidate into hub/modules/vislzr/
mv hub/vislzr hub/modules/vislzr
# Update imports in hub/frontend to reference new location
```

#### Step 3.3: Organize Orchestration
```bash
# Already in hub/orchestration - just move under modules
mv hub/orchestration hub/modules/orchestration
```

#### Step 3.4: Create Deprecation Markers

Create `backend/README.md`:
```markdown
# DEPRECATED

This directory contains legacy code being migrated to `hub/core/api/`.

For new development, see:
- `hub/modules/` - Feature modules
- `hub/core/api/` - Shared API infrastructure

Migration status: IN PROGRESS
Target completion: [DATE]
```

#### Step 3.5: Clean Up Cruft
```bash
# Archive hub-prototype
mv hub-prototype docs/archive/hub-prototype-legacy

# Clean worktrees (keep only active ones)
cd .worktrees
ls -la  # Review which are stale
# Remove completed worktrees
```

---

## Phase 4: VERIA Integration Specification - Day 5

### API Boundary Definition

Based on Fork 3 analysis, define:

```yaml
# veria-commandcenter-api.yaml
integration:
  type: "REST API"
  auth: "API Key + JWT"

commandcenter_provides:
  - endpoint: "/api/v1/knowledge/query"
    description: "RAG-powered knowledge search"
  - endpoint: "/api/v1/workflows/trigger"
    description: "Trigger agent workflows"
  - endpoint: "/api/v1/graph/symbols"
    description: "Code symbol lookup"

veria_provides:
  - endpoint: "/api/v1/intelligence/analyze"
    description: "Intelligence analysis"
  - endpoint: "/api/v1/projects"
    description: "Project management"

shared_events:
  - topic: "project.created"
  - topic: "analysis.completed"
  - topic: "workflow.finished"
```

---

## Phase 5: Verification & Next Steps - Day 6

### Verification Checklist

- [ ] All E2B forks completed successfully
- [ ] GitDiagram outputs saved to docs/diagrams/
- [ ] ARCHITECTURE.md written and accurate
- [ ] VERIA_INTEGRATION.md defines clear boundaries
- [ ] CODE_HEALTH_REPORT.md lists actionable items
- [ ] Hub modules structure created
- [ ] Deprecation markers in place
- [ ] No broken imports (run tests)
- [ ] Git history clean (proper commits)

### Success Criteria

| Metric | Target |
|--------|--------|
| Documentation coverage | 100% of major components documented |
| Test pass rate | No regressions from reorganization |
| Build success | All services build cleanly |
| Visual diagrams | At least 2 Mermaid diagrams generated |

### Next Steps After Audit

1. **Resume Phase 7 Graph Service** - Week 3/4 completion
2. **Implement VISLZR enhancements** - GitDiagram + Claude methodology
3. **Build VERIA integration endpoints** - Based on API spec
4. **Address CODE_HEALTH findings** - Prioritized technical debt

---

## Appendix A: E2B Commands Reference

### Start Parallel Forks
```bash
cd tools/agent-sandboxes/apps/sandbox_workflows
uv run obox https://github.com/your/repo \
  --branch main \
  --model sonnet \
  --prompt "Audit task description" \
  --forks 4
```

### Monitor Fork Progress
```bash
# Check sandbox status
uv run python src/main.py sandbox list

# View fork output
uv run python src/main.py exec <sandbox-id> "cat /workspace/output.md"
```

### Collect Results
```bash
# Download results from each fork
uv run python src/main.py files download <sandbox-id> /workspace/output.md ./results/fork-1.md
```

---

## Appendix B: GitDiagram Quick Start

### Option 1: Web Service (Fastest)
1. Visit https://gitdiagram.com
2. Paste GitHub URL
3. Wait for generation
4. Download Mermaid code

### Option 2: Local Execution
```bash
git clone https://github.com/ahmedkhaleel2004/gitdiagram
cd gitdiagram
# Follow their README for local setup
# Requires: Node.js, Python, OpenAI API key
```

### Option 3: In E2B Sandbox
```bash
# Isolate in sandbox for safety
uv run python src/main.py sandbox create
uv run python src/main.py exec <id> "git clone https://github.com/ahmedkhaleel2004/gitdiagram && cd gitdiagram && npm install"
```

---

## Appendix C: Current Directory Analysis

### CommandCenter Structure (as of 2025-12-02)

```
CommandCenter/
├── .agent-coordination/    # Agent task coordination
├── .claude/                # Claude Code config
├── .worktrees/             # Git worktrees (16 total, many stale)
├── backend/                # Legacy FastAPI backend
├── docs/                   # Documentation (71 items)
├── e2e/                    # Playwright E2E tests
├── federation/             # Federation service (Phase 9)
├── frontend/               # Legacy React frontend
├── hub/                    # Main application
│   ├── backend/           # Hub FastAPI
│   ├── docs/              # Hub docs
│   ├── examples/          # Example workflows
│   ├── frontend/          # Hub React UI
│   ├── observability/     # Metrics stack
│   ├── orchestration/     # Agent workflows (Phase 10)
│   ├── scripts/           # Utility scripts
│   └── vislzr/            # Visualization (minimal)
├── hub-prototype/          # Legacy prototype (archive candidate)
├── libs/                   # Shared libraries
│   └── knowledgebeast/    # RAG engine
├── monitoring/             # Grafana dashboards
├── schemas/                # Shared schemas
├── scripts/                # Root scripts
├── snapshots/              # Dev snapshots
├── tools/                  # External tools
│   ├── agent-sandboxes/   # E2B integration
│   └── graphvis/          # Graph visualization
├── traefik/                # Reverse proxy
└── worktree/               # Stale worktree (cleanup)
```

### VERIA Structure (as of 2025-12-02)

```
VERIA_PLATFORM/
├── .claude/                # Claude Code config
├── .genkit/                # Genkit integration
├── .playwright-mcp/        # Playwright MCP
├── .vercel/                # Vercel deployment
├── docs/                   # Documentation
├── LEGACY_CODE_BASE/       # XML exports
│   ├── legacy_commandcenter.xml
│   ├── legacy_intelligence.xml
│   └── legacy_codebase.xml
├── mock-data/              # Test fixtures
├── middleware.ts           # Next.js middleware
├── GEMINI.md              # Gemini integration notes
└── GENKIT_INTEGRATION_SPEC.md
```

---

*Plan created: 2025-12-02*
*Estimated duration: 5-6 days*
*Approach: Hybrid B+C (Document First + Incremental Hub Restructure)*
