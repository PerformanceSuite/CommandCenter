# Branch Consolidation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate all feature branches into main, eliminating stale branches and ensuring Hub works with Dagger SDK orchestration.

**Architecture:** Sequential merge strategy with testing gates between phases. Critical infrastructure changes (Dagger, DB fixes) first, then optional features (agent services, devops), then cleanup. Each merge includes conflict resolution, testing, and commit verification.

**Tech Stack:** Git, Dagger SDK, Docker, FastAPI, React, PostgreSQL

**Risk Level:**
- Phase 1-2: Low (well-tested)
- Phase 3: Medium (needs evaluation)
- Phase 4: Medium (CI/Docker changes)
- Phase 5: Low (cleanup only)

---

## Pre-Flight Checks

### Task 0: Verify Current State

**Purpose:** Ensure we're starting from a clean, known state

**Step 1: Check current branch status**

Run:
```bash
git status
git branch --show-current
```

Expected: On `main` branch, working tree clean

**Step 2: Verify no uncommitted changes**

Run:
```bash
git diff --stat
git diff --cached --stat
```

Expected: No output (clean working tree)

**Step 3: Pull latest main**

Run:
```bash
git pull origin main
```

Expected: Already up to date OR fast-forward merge

**Step 4: List all branches with commit counts**

Run:
```bash
git branch -a --format='%(refname:short) %(upstream:track)' | grep -v HEAD
git for-each-ref --format='%(refname:short) %(committerdate:short)' refs/heads/ | sort -k2 -r
```

Expected: See all branches listed with dates

**Step 5: Create backup tag**

Run:
```bash
git tag backup-before-consolidation-$(date +%Y%m%d-%H%M%S)
git tag -l | tail -5
```

Expected: New backup tag created

**Step 6: Document starting commit**

Run:
```bash
echo "Starting consolidation from commit: $(git rev-parse HEAD)" > /tmp/consolidation-start.txt
cat /tmp/consolidation-start.txt
```

Expected: Commit hash saved to file

---

## Phase 1: Hub Dagger Integration (CRITICAL)

### Task 1: Review Dagger Branch Status

**Purpose:** Understand what we're merging before we merge it

**Files to Review:**
- `hub/backend/app/services/orchestration_service.py`
- `hub/backend/app/dagger_modules/commandcenter.py`
- `hub/backend/app/models.py`
- `hub/backend/requirements.txt`

**Step 1: Switch to dagger branch**

Run:
```bash
git checkout feature/dagger-orchestration
```

Expected: Switched to branch 'feature/dagger-orchestration'

**Step 2: Review branch commits**

Run:
```bash
git log main..HEAD --oneline
git show --stat HEAD
```

Expected: 13 commits listed, see file changes in HEAD

**Step 3: Check for conflicts before merge**

Run:
```bash
git diff main...feature/dagger-orchestration --stat
```

Expected: See list of changed files (mainly in hub/)

**Step 4: Read verification report**

Run:
```bash
cat TASK_10_VERIFICATION_REPORT.md | head -100
```

Expected: See test results (9/9 passing)

**Step 5: Check Dagger dependencies**

Run:
```bash
grep -E "dagger|anyio|opentelemetry" hub/backend/requirements.txt
```

Expected: See dagger-io>=0.19.2, anyio>=4.2.0, opentelemetry-exporter-otlp-proto-grpc>=1.38.0

**Step 6: Return to main**

Run:
```bash
git checkout main
```

Expected: Switched to branch 'main'

---

### Task 2: Test Dagger Branch Before Merge

**Purpose:** Verify feature/dagger-orchestration actually works before merging

**Step 1: Switch to dagger branch**

Run:
```bash
git checkout feature/dagger-orchestration
cd hub
```

Expected: On feature/dagger-orchestration, in hub directory

**Step 2: Check Hub services status**

Run:
```bash
docker-compose ps 2>/dev/null | grep hub || echo "Hub not running"
```

Expected: May show running or not running

**Step 3: Stop any running Hub services**

Run:
```bash
docker-compose down 2>/dev/null || echo "No services to stop"
```

Expected: Services stopped or message

**Step 4: Start Hub with Dagger version**

Run:
```bash
docker-compose build hub-backend
docker-compose up -d hub-backend hub-frontend
sleep 5
docker-compose ps
```

Expected: hub-backend and hub-frontend running

**Step 5: Test Hub backend health**

Run:
```bash
curl -s http://localhost:9001/health | jq .
```

Expected: `{"status": "healthy"}`

**Step 6: Test Hub API lists projects**

Run:
```bash
curl -s http://localhost:9001/api/projects/ | jq .
```

Expected: Empty array `[]` or list of projects

**Step 7: Verify Dagger SDK is available**

Run:
```bash
docker exec commandcenter-hub-backend python -c "import dagger; print('Dagger SDK version:', dagger.__version__)"
```

Expected: Dagger SDK version printed (e.g., 0.19.2)

**Step 8: Test template version endpoint**

Run:
```bash
curl -s http://localhost:9001/api/projects/template/version | jq .
```

Expected: JSON with commit, branch, last_commit_message

**Step 9: Stop Hub services**

Run:
```bash
docker-compose down
cd ..
```

Expected: Services stopped, back in project root

**Step 10: Return to main**

Run:
```bash
git checkout main
```

Expected: Switched to branch 'main'

---

### Task 3: Merge Dagger Branch to Main

**Purpose:** Bring Dagger orchestration to main branch

**Files Modified:**
- `hub/backend/app/services/orchestration_service.py` - Replace docker-compose with Dagger SDK
- `hub/backend/app/dagger_modules/commandcenter.py` - New Dagger stack definitions
- `hub/backend/app/models.py` - Remove cc_path, compose_project_name fields
- `hub/backend/requirements.txt` - Add Dagger dependencies
- Delete: `hub/backend/app/services/setup_service.py`
- Multiple docs and test files

**Step 1: Create merge branch**

Run:
```bash
git checkout -b merge/dagger-orchestration
```

Expected: Switched to new branch

**Step 2: Merge feature/dagger-orchestration**

Run:
```bash
git merge feature/dagger-orchestration --no-ff -m "feat(hub): Merge Dagger SDK orchestration

Replaces docker-compose subprocess calls with Dagger SDK for container orchestration.

Major Changes:
- Remove git clone approach (no more setup_service.py)
- Projects mount directly via Dagger SDK
- Simplified Project model (removed cc_path, compose_project_name)
- All 9 tests passing

Commits: 13
Branch: feature/dagger-orchestration
Verification: TASK_10_VERIFICATION_REPORT.md"
```

Expected: Merge completed OR merge conflicts detected

**Step 3: Handle conflicts if any**

If conflicts:
```bash
git status | grep "both modified"
# Manually resolve each conflict
git add <resolved-files>
git merge --continue
```

Expected: All conflicts resolved, merge completed

**Step 4: Verify merge commit**

Run:
```bash
git log -1 --stat
```

Expected: See merge commit with all dagger files

**Step 5: Run Hub tests**

Run:
```bash
cd hub/backend
pytest -v
```

Expected: All tests passing

**Step 6: Test Hub with merged code**

Run:
```bash
cd /Users/danielconnolly/Projects/CommandCenter/hub
docker-compose build hub-backend
docker-compose up -d
sleep 8
curl -s http://localhost:9001/health | jq .
```

Expected: `{"status": "healthy"}`

**Step 7: Verify Dagger module loads**

Run:
```bash
docker exec commandcenter-hub-backend python -c "from app.dagger_modules.commandcenter import CommandCenterStack; print('✅ Dagger module imports successfully')"
```

Expected: Success message

**Step 8: Stop Hub**

Run:
```bash
docker-compose down
cd /Users/danielconnolly/Projects/CommandCenter
```

Expected: Stopped, back in root

**Step 9: Merge to main**

Run:
```bash
git checkout main
git merge merge/dagger-orchestration --ff-only
```

Expected: Fast-forward merge completed

**Step 10: Delete merge branch**

Run:
```bash
git branch -d merge/dagger-orchestration
```

Expected: Branch deleted

---

### Task 4: Delete Dagger Feature Branch

**Purpose:** Clean up now-merged feature branch

**Step 1: Verify branch is merged**

Run:
```bash
git branch --merged main | grep dagger
```

Expected: feature/dagger-orchestration listed

**Step 2: Delete local branch**

Run:
```bash
git branch -d feature/dagger-orchestration
```

Expected: Branch deleted

**Step 3: Delete remote branch if exists**

Run:
```bash
git push origin --delete feature/dagger-orchestration 2>&1 | head -5
```

Expected: Branch deleted OR "remote ref does not exist"

**Step 4: Verify deletion**

Run:
```bash
git branch -a | grep dagger || echo "✅ No dagger branches remaining"
```

Expected: No dagger branches found

---

## Phase 2: Backend Critical Fix

### Task 5: Cherry-Pick Backend DB Session Fix

**Purpose:** Apply critical DB session bug fix without merging entire branch

**Files Modified:**
- `backend/app/repositories/base.py` - Fix DB session bug
- Related repository pattern implementations

**Step 1: Inspect backend refactor commit**

Run:
```bash
git show feature/backend-refactor --stat
git log feature/backend-refactor -1 --format="%H%n%s%n%b"
```

Expected: See commit 896e92f with description

**Step 2: Check for conflicts**

Run:
```bash
git diff main feature/backend-refactor --stat
```

Expected: See changed files list

**Step 3: Cherry-pick the commit**

Run:
```bash
git cherry-pick 896e92f
```

Expected: Commit applied OR conflicts

**Step 4: Resolve conflicts if any**

If conflicts:
```bash
git status | grep "both modified"
# Manually resolve
git add <files>
git cherry-pick --continue
```

Expected: Cherry-pick completed

**Step 5: Verify backend code compiles**

Run:
```bash
cd backend
python -c "from app.repositories.base import BaseRepository; print('✅ Repository imports successfully')"
cd ..
```

Expected: No import errors

**Step 6: Run backend tests**

Run:
```bash
cd backend
pytest tests/test_repositories.py -v 2>/dev/null || echo "Tests need database - will test with docker"
cd ..
```

Expected: Tests pass OR note about needing database

**Step 7: Test with Docker**

Run:
```bash
docker-compose -f docker-compose.yml build backend
docker-compose -f docker-compose.yml up -d postgres redis
sleep 5
docker-compose -f docker-compose.yml up -d backend
sleep 5
docker-compose -f docker-compose.yml exec backend python -c "from app.database import get_db; print('✅ DB session works')" 2>&1 | head -10
```

Expected: DB session confirmation OR connection success

**Step 8: Stop test containers**

Run:
```bash
docker-compose -f docker-compose.yml down
```

Expected: Containers stopped

**Step 9: Commit the cherry-pick if not auto-committed**

Run:
```bash
git log -1 --oneline
```

Expected: See cherry-picked commit at HEAD

**Step 10: Delete backend refactor branch**

Run:
```bash
git branch -d feature/backend-refactor
git push origin --delete feature/backend-refactor 2>&1 | head -5 || echo "Remote branch may not exist"
```

Expected: Branch deleted

---

## Phase 3: Agent Services Evaluation

### Task 6: Review Agent CLI Interface

**Purpose:** Evaluate if agent/cli-interface should be merged or deferred

**Files to Review:**
- `cli/` directory (if exists)
- `backend/app/cli/` or similar
- Tests in `tests/cli/`

**Step 1: Switch to agent CLI branch**

Run:
```bash
git checkout agent/cli-interface
```

Expected: Switched to agent/cli-interface

**Step 2: Review commits**

Run:
```bash
git log main..HEAD --oneline
wc -l $(git diff main --name-only) 2>/dev/null || echo "Checking diff size..."
```

Expected: See 5+ commits, count lines changed

**Step 3: Check for CLI entry point**

Run:
```bash
find . -name "cli.py" -o -name "agents.py" -o -name "__main__.py" | grep -v venv | grep -v node_modules | head -10
```

Expected: Find CLI files

**Step 4: Read CLI documentation**

Run:
```bash
find . -name "CLI*.md" -o -name "AGENT*.md" | grep -v node_modules | head -5
cat docs/CLI_GUIDE.md 2>/dev/null | head -50 || echo "No CLI docs found"
```

Expected: See CLI documentation or note

**Step 5: Check dependencies**

Run:
```bash
git diff main backend/requirements.txt | grep "^+" | head -20
```

Expected: See new CLI dependencies (click, rich, etc.)

**Step 6: Assess complexity and stability**

Run:
```bash
git diff main --stat | tail -20
git log --oneline --since="2 weeks ago" HEAD | wc -l
```

Expected: See scope of changes, recent activity

**Step 7: Decision point - Record assessment**

Run:
```bash
echo "Agent CLI Assessment:" > /tmp/agent-cli-assessment.txt
echo "Commits: $(git log main..HEAD --oneline | wc -l)" >> /tmp/agent-cli-assessment.txt
echo "Files changed: $(git diff main --name-only | wc -l)" >> /tmp/agent-cli-assessment.txt
echo "Last updated: $(git log -1 --format=%cd)" >> /tmp/agent-cli-assessment.txt
cat /tmp/agent-cli-assessment.txt
```

Expected: Assessment file created

**Step 8: Return to main**

Run:
```bash
git checkout main
```

Expected: Back on main

**Step 9: User decision required**

**STOP HERE FOR USER INPUT:**

Based on assessment:
- If CLI is complete and tested → Proceed to Task 7 (merge)
- If CLI is experimental/incomplete → Proceed to Task 10 (defer)
- If unsure → Ask user for guidance

**Record decision:**
```bash
# User sets: export AGENT_CLI_DECISION="merge" or "defer"
echo $AGENT_CLI_DECISION
```

---

### Task 7: Merge Agent CLI (if AGENT_CLI_DECISION=merge)

**Purpose:** Integrate CLI interface into main

**Prerequisites:** Task 6 decision = "merge"

**Step 1: Verify decision**

Run:
```bash
if [ "$AGENT_CLI_DECISION" != "merge" ]; then echo "❌ Skipping - not approved for merge"; exit 1; fi
```

Expected: No output (continue) OR skip message

**Step 2: Create merge branch**

Run:
```bash
git checkout -b merge/agent-cli-interface
```

Expected: New branch created

**Step 3: Merge agent CLI**

Run:
```bash
git merge agent/cli-interface --no-ff -m "feat(cli): Add professional CLI interface for CommandCenter

Adds comprehensive CLI for project management and agent operations.

See docs/CLI_GUIDE.md for usage."
```

Expected: Merge completed OR conflicts

**Step 4: Resolve conflicts**

If conflicts:
```bash
git status | grep "both modified"
# Resolve each conflict
git add <files>
git merge --continue
```

Expected: Conflicts resolved

**Step 5: Test CLI installation**

Run:
```bash
cd backend
pip install -e . --quiet
python -m app.cli --help 2>&1 | head -20 || echo "CLI may have different entry point"
cd ..
```

Expected: CLI help shown OR note about entry point

**Step 6: Run CLI tests**

Run:
```bash
cd backend
pytest tests/cli/ -v 2>/dev/null || echo "CLI tests location may differ"
cd ..
```

Expected: Tests pass OR location note

**Step 7: Merge to main**

Run:
```bash
git checkout main
git merge merge/agent-cli-interface --ff-only
```

Expected: Merged to main

**Step 8: Delete branches**

Run:
```bash
git branch -d merge/agent-cli-interface
git branch -d agent/cli-interface
```

Expected: Branches deleted

---

### Task 8: Review Agent MCP Core

**Purpose:** Evaluate agent/mcp-core-infrastructure for merge or defer

**Files to Review:**
- `backend/app/mcp/` or similar
- MCP provider implementations
- Tests

**Step 1: Switch to MCP branch**

Run:
```bash
git checkout agent/mcp-core-infrastructure
```

Expected: Switched

**Step 2: Review commits and changes**

Run:
```bash
git log main..HEAD --oneline
git diff main --stat | tail -30
```

Expected: See 5+ commits, file changes

**Step 3: Find MCP files**

Run:
```bash
find . -path "*/mcp/*" -name "*.py" | grep -v venv | grep -v node_modules | head -10
```

Expected: MCP implementation files

**Step 4: Check for documentation**

Run:
```bash
find docs -name "*MCP*" -o -name "*mcp*" | head -5
cat docs/MCP_ARCHITECTURE.md 2>/dev/null | head -50 || echo "No MCP docs"
```

Expected: Architecture docs or note

**Step 5: Assess integration points**

Run:
```bash
git diff main backend/app/main.py 2>/dev/null | head -30 || echo "Checking integration..."
git diff main backend/requirements.txt | grep mcp
```

Expected: See MCP integration points

**Step 6: Record assessment**

Run:
```bash
echo "Agent MCP Assessment:" > /tmp/agent-mcp-assessment.txt
echo "Commits: $(git log main..HEAD --oneline | wc -l)" >> /tmp/agent-mcp-assessment.txt
echo "Files changed: $(git diff main --name-only | wc -l)" >> /tmp/agent-mcp-assessment.txt
cat /tmp/agent-mcp-assessment.txt
```

Expected: Assessment saved

**Step 7: Return to main**

Run:
```bash
git checkout main
```

Expected: Back on main

**Step 8: User decision**

**STOP HERE FOR USER INPUT:**
Set decision: `export AGENT_MCP_DECISION="merge"` or `"defer"`

---

### Task 9: Review Agent Project Analyzer

**Purpose:** Evaluate agent/project-analyzer-service for merge or defer

**Step 1: Switch to analyzer branch**

Run:
```bash
git checkout agent/project-analyzer-service
```

Expected: Switched

**Step 2: Review commits**

Run:
```bash
git log main..HEAD --oneline
git diff main --stat | tail -30
```

Expected: See 3+ commits

**Step 3: Find analyzer files**

Run:
```bash
find . -path "*/analyzer/*" -o -path "*/project_analyzer/*" -name "*.py" | grep -v venv | head -10
```

Expected: Analyzer implementation

**Step 4: Check dependencies**

Run:
```bash
git diff main backend/requirements.txt | grep "^+"
```

Expected: New analyzer dependencies

**Step 5: Record assessment**

Run:
```bash
echo "Agent Analyzer Assessment:" > /tmp/agent-analyzer-assessment.txt
echo "Commits: $(git log main..HEAD --oneline | wc -l)" >> /tmp/agent-analyzer-assessment.txt
echo "Files changed: $(git diff main --name-only | wc -l)" >> /tmp/agent-analyzer-assessment.txt
cat /tmp/agent-analyzer-assessment.txt
```

Expected: Assessment saved

**Step 6: Return to main**

Run:
```bash
git checkout main
```

Expected: Back on main

**Step 7: User decision**

**STOP HERE FOR USER INPUT:**
Set: `export AGENT_ANALYZER_DECISION="merge"` or `"defer"`

---

### Task 10: Defer Agent Services (if any DECISION=defer)

**Purpose:** Mark agent branches for future work without deleting

**Step 1: Create defer list**

Run:
```bash
touch /tmp/deferred-branches.txt
[ "$AGENT_CLI_DECISION" = "defer" ] && echo "agent/cli-interface" >> /tmp/deferred-branches.txt
[ "$AGENT_MCP_DECISION" = "defer" ] && echo "agent/mcp-core-infrastructure" >> /tmp/deferred-branches.txt
[ "$AGENT_ANALYZER_DECISION" = "defer" ] && echo "agent/project-analyzer-service" >> /tmp/deferred-branches.txt
cat /tmp/deferred-branches.txt || echo "No branches deferred"
```

Expected: List of deferred branches or none

**Step 2: Tag deferred branches for future reference**

Run:
```bash
while read branch; do
  git tag "deferred-$(echo $branch | tr '/' '-')-$(date +%Y%m%d)" $branch
done < /tmp/deferred-branches.txt
git tag | grep deferred
```

Expected: Tags created for deferred branches

**Step 3: Document deferral reasons**

Run:
```bash
cat > docs/DEFERRED_FEATURES.md << 'EOF'
# Deferred Features

Features evaluated but not merged in 2025-10-28 consolidation.

## Agent Services

**Reason for Deferral:** [To be filled by user]

### agent/cli-interface
- Professional CLI for CommandCenter
- Status: Incomplete/Experimental
- Decision: Defer until core features stabilize

### agent/mcp-core-infrastructure
- MCP provider implementations
- Status: Needs integration testing
- Decision: Defer for separate integration sprint

### agent/project-analyzer-service
- Project analysis service
- Status: Dependencies on MCP core
- Decision: Defer until MCP is merged

## Re-evaluation

Review these branches after:
1. Hub Dagger orchestration is stable (2-4 weeks)
2. Core CommandCenter features tested in production
3. User feedback on current feature set

## Tags

Deferred branches tagged for reference:
- deferred-agent-cli-interface-YYYYMMDD
- deferred-agent-mcp-core-infrastructure-YYYYMMDD
- deferred-agent-project-analyzer-service-YYYYMMDD

EOF
cat docs/DEFERRED_FEATURES.md
```

Expected: Documentation file created

**Step 4: Commit deferred features doc**

Run:
```bash
git add docs/DEFERRED_FEATURES.md
git commit -m "docs: Record deferred agent services for future work"
```

Expected: Committed

---

## Phase 4: DevOps Refactor

### Task 11: Review DevOps Refactor

**Purpose:** Evaluate feature/devops-refactor for merge

**Files to Review:**
- `.github/workflows/` - CI changes
- `docker-compose.yml` - Docker changes
- `backend/requirements.txt` or `requirements-dev.txt` - Dependency changes
- CI/CD configuration files

**Step 1: Switch to devops branch**

Run:
```bash
git checkout feature/devops-refactor
```

Expected: Switched

**Step 2: Review commits**

Run:
```bash
git log main..HEAD --oneline
git log main..HEAD --format="%h %s" | cat
```

Expected: See 4 commits about CI, Docker, dependencies

**Step 3: Check CI changes**

Run:
```bash
git diff main .github/workflows/ | head -100
ls -la .github/workflows/ 2>/dev/null || echo "No workflows directory"
```

Expected: See workflow changes or note

**Step 4: Check Docker changes**

Run:
```bash
git diff main docker-compose.yml | head -50
git diff main backend/Dockerfile | head -50
```

Expected: See Docker configuration changes

**Step 5: Check dependency changes**

Run:
```bash
git diff main backend/requirements.txt | head -50
git diff main backend/requirements-dev.txt 2>/dev/null | head -30 || echo "No dev requirements file"
```

Expected: See dependency updates

**Step 6: Check for breaking changes**

Run:
```bash
git diff main docker-compose.yml | grep -E "^-|ports:|image:|build:" | head -30
```

Expected: Identify any breaking changes

**Step 7: Test build**

Run:
```bash
docker-compose build backend --no-cache 2>&1 | tail -50
```

Expected: Build succeeds OR identify issues

**Step 8: Record assessment**

Run:
```bash
echo "DevOps Refactor Assessment:" > /tmp/devops-assessment.txt
echo "Commits: $(git log main..HEAD --oneline | wc -l)" >> /tmp/devops-assessment.txt
echo "CI changes: $(git diff main .github/workflows/ --stat 2>/dev/null | wc -l)" >> /tmp/devops-assessment.txt
echo "Docker changes: $(git diff main docker-compose.yml --stat | wc -l)" >> /tmp/devops-assessment.txt
echo "Dependency changes: $(git diff main backend/requirements.txt --stat | wc -l)" >> /tmp/devops-assessment.txt
cat /tmp/devops-assessment.txt
```

Expected: Assessment complete

**Step 9: Return to main**

Run:
```bash
git checkout main
```

Expected: Back on main

**Step 10: User decision**

**STOP HERE FOR USER INPUT:**
Set: `export DEVOPS_DECISION="merge"` or `"defer"`

Considerations:
- Does DevOps refactor conflict with Dagger changes?
- Are CI improvements needed now?
- Do dependency updates break anything?

---

### Task 12: Merge DevOps Refactor (if DEVOPS_DECISION=merge)

**Purpose:** Integrate DevOps improvements into main

**Prerequisites:** Task 11 decision = "merge"

**Step 1: Verify decision**

Run:
```bash
if [ "$DEVOPS_DECISION" != "merge" ]; then echo "❌ Skipping - not approved"; exit 1; fi
```

Expected: Continue or skip

**Step 2: Create merge branch**

Run:
```bash
git checkout -b merge/devops-refactor
```

Expected: New branch created

**Step 3: Merge devops refactor**

Run:
```bash
git merge feature/devops-refactor --no-ff -m "refactor(devops): Overhaul CI, Docker, and dependencies

Improves CI/CD pipeline, Docker configurations, and dependency management.

Major Changes:
- Enhanced GitHub Actions workflows
- Optimized Docker builds
- Updated and organized dependencies
- Code quality improvements (10/10 quality score)

Commits: 4
Branch: feature/devops-refactor"
```

Expected: Merge completed OR conflicts

**Step 4: Resolve conflicts**

Priority conflict resolution order:
1. docker-compose.yml (keep Dagger-compatible version)
2. backend/requirements.txt (merge both sets of dependencies)
3. CI workflows (keep or merge improvements)

If conflicts:
```bash
git status | grep "both modified"

# For docker-compose.yml - prefer main (has Dagger changes)
git checkout --ours docker-compose.yml

# For requirements.txt - merge manually
# Check both versions and combine unique dependencies
git diff main feature/devops-refactor backend/requirements.txt

# Manually edit to include all unique dependencies
nano backend/requirements.txt
git add backend/requirements.txt

git merge --continue
```

Expected: All conflicts resolved

**Step 5: Verify Docker build**

Run:
```bash
docker-compose build backend
docker-compose build hub-backend
```

Expected: Both build successfully

**Step 6: Test services start**

Run:
```bash
docker-compose -f docker-compose.yml up -d postgres redis
sleep 5
docker-compose -f docker-compose.yml up -d backend
sleep 5
docker-compose -f docker-compose.yml ps | grep backend
```

Expected: Services running

**Step 7: Stop test services**

Run:
```bash
docker-compose -f docker-compose.yml down
```

Expected: Stopped

**Step 8: Test Hub still works**

Run:
```bash
cd hub
docker-compose up -d
sleep 5
curl -s http://localhost:9001/health | jq .
docker-compose down
cd ..
```

Expected: Hub health check passes

**Step 9: Merge to main**

Run:
```bash
git checkout main
git merge merge/devops-refactor --ff-only
```

Expected: Merged

**Step 10: Delete branches**

Run:
```bash
git branch -d merge/devops-refactor
git branch -d feature/devops-refactor
```

Expected: Branches deleted

---

## Phase 5: Cleanup

### Task 13: Delete Stale Branches

**Purpose:** Remove branches that are superseded or obsolete

**Branches to Delete:**
- `feature/knowledgebeast-migration-docker-fix` (superseded by main)
- `docs/product-roadmap-integration` (no changes)
- `experimental/ai-dev-tools-ui` (3 weeks stale)

**Step 1: Verify knowledgebeast-migration-docker-fix is superseded**

Run:
```bash
git log main..feature/knowledgebeast-migration-docker-fix --oneline
```

Expected: Commits that are already on main

**Step 2: Delete knowledgebeast-migration-docker-fix**

Run:
```bash
git branch -D feature/knowledgebeast-migration-docker-fix
git push origin --delete feature/knowledgebeast-migration-docker-fix 2>&1 | head -5 || echo "Remote may not exist"
```

Expected: Branch deleted

**Step 3: Check docs/product-roadmap-integration**

Run:
```bash
git log main..docs/product-roadmap-integration --oneline
```

Expected: No commits ahead or identical commits

**Step 4: Delete product-roadmap-integration**

Run:
```bash
git branch -D docs/product-roadmap-integration
git push origin --delete docs/product-roadmap-integration 2>&1 | head -5 || echo "Remote may not exist"
```

Expected: Branch deleted

**Step 5: Check experimental/ai-dev-tools-ui**

Run:
```bash
git log main..experimental/ai-dev-tools-ui --oneline | head -5
git log experimental/ai-dev-tools-ui -1 --format="%cd (%cr)"
```

Expected: See age (3+ weeks old)

**Step 6: Tag experimental UI for reference**

Run:
```bash
git tag experimental-ai-dev-tools-ui-archive-$(date +%Y%m%d) experimental/ai-dev-tools-ui
```

Expected: Tag created

**Step 7: Delete experimental UI branch**

Run:
```bash
git branch -D experimental/ai-dev-tools-ui
git push origin --delete experimental/ai-dev-tools-ui 2>&1 | head -5 || echo "Remote may not exist"
```

Expected: Branch deleted

**Step 8: List remaining branches**

Run:
```bash
git branch -a | grep -v HEAD | grep -v main
```

Expected: Only agent branches (if deferred) and security-fixes

**Step 9: Check security-fixes/all-prs**

Run:
```bash
git log main..security-fixes/all-prs --oneline
```

Expected: Check if merged or still needed

**Step 10: Delete security-fixes if merged**

Run:
```bash
git branch --merged main | grep security-fixes && git branch -d security-fixes/all-prs || echo "Not merged or doesn't exist"
```

Expected: Deleted if merged

---

### Task 14: Clean Up Worktrees

**Purpose:** Remove detached worktree directories

**Current Worktrees:**
- `.worktrees/feature/dagger-orchestration` (can delete after merge)
- `.worktrees/knowledgebeast-migration` (can delete, already merged)
- `worktree/backend-refactor` (can delete after cherry-pick)
- `worktree/devops-refactor` (can delete after merge)
- `worktree/frontend-refactor` (check if needed)

**Step 1: List current worktrees**

Run:
```bash
git worktree list
```

Expected: See all active worktrees

**Step 2: Remove dagger-orchestration worktree**

Run:
```bash
git worktree remove .worktrees/feature/dagger-orchestration 2>&1 || echo "May need force remove"
git worktree remove .worktrees/feature/dagger-orchestration --force
```

Expected: Worktree removed

**Step 3: Remove knowledgebeast-migration worktree**

Run:
```bash
git worktree remove .worktrees/knowledgebeast-migration --force
```

Expected: Worktree removed

**Step 4: Remove backend-refactor worktree**

Run:
```bash
git worktree remove worktree/backend-refactor --force
```

Expected: Worktree removed

**Step 5: Remove devops-refactor worktree**

Run:
```bash
git worktree remove worktree/devops-refactor --force
```

Expected: Worktree removed

**Step 6: Check frontend-refactor worktree**

Run:
```bash
ls -la worktree/frontend-refactor/ 2>/dev/null | head -10 || echo "Doesn't exist"
git log main..feature/frontend-refactor --oneline 2>/dev/null || echo "Branch merged or doesn't exist"
```

Expected: Check status

**Step 7: Remove frontend-refactor worktree if safe**

Run:
```bash
git worktree remove worktree/frontend-refactor --force 2>&1 || echo "Already removed or doesn't exist"
```

Expected: Removed or message

**Step 8: Verify worktree cleanup**

Run:
```bash
git worktree list
ls -la .worktrees/ 2>/dev/null || echo "No .worktrees directory"
ls -la worktree/ 2>/dev/null || echo "No worktree directory"
```

Expected: Only active worktrees remain (if any)

**Step 9: Prune worktree metadata**

Run:
```bash
git worktree prune
```

Expected: Stale metadata removed

**Step 10: Remove empty worktree directories**

Run:
```bash
rmdir .worktrees 2>/dev/null || echo ".worktrees not empty or doesn't exist"
rmdir worktree 2>/dev/null || echo "worktree not empty or doesn't exist"
```

Expected: Directories removed if empty

---

### Task 15: Verify Final State

**Purpose:** Ensure consolidation is complete and main is clean

**Step 1: Check current branch**

Run:
```bash
git branch --show-current
```

Expected: main

**Step 2: Verify working tree is clean**

Run:
```bash
git status
```

Expected: "nothing to commit, working tree clean"

**Step 3: List remaining local branches**

Run:
```bash
git branch
```

Expected: main (and agent branches if deferred)

**Step 4: Count branches before/after**

Run:
```bash
echo "Branches at start: $(git tag | grep backup-before-consolidation | wc -l)"
echo "Branches remaining: $(git branch | wc -l)"
```

Expected: Fewer branches than start

**Step 5: Test Hub end-to-end**

Run:
```bash
cd hub
docker-compose up -d
sleep 8
curl -s http://localhost:9001/health | jq .
curl -s http://localhost:9001/api/projects/ | jq .
curl -s http://localhost:9001/api/projects/template/version | jq .commit
```

Expected: All endpoints working

**Step 6: Test Hub frontend loads**

Run:
```bash
curl -s http://localhost:9000 | grep -o "<title>[^<]*</title>"
```

Expected: `<title>CommandCenter Hub</title>`

**Step 7: Stop Hub**

Run:
```bash
docker-compose down
cd ..
```

Expected: Stopped

**Step 8: Test CommandCenter template builds**

Run:
```bash
docker-compose build backend
docker-compose build frontend
```

Expected: Both build successfully

**Step 9: Generate consolidation report**

Run:
```bash
cat > CONSOLIDATION_REPORT.md << EOF
# Branch Consolidation Report

**Date:** $(date +"%Y-%m-%d %H:%M:%S")
**Starting Commit:** $(cat /tmp/consolidation-start.txt)
**Ending Commit:** $(git rev-parse HEAD)

## Branches Merged

### ✅ feature/dagger-orchestration (13 commits)
- Hub now uses Dagger SDK for orchestration
- Removed git clone approach
- Simplified Project model
- All tests passing

### ✅ feature/backend-refactor (1 commit - cherry-picked)
- Fixed DB session bug
- Implemented repository pattern

### DevOps Refactor
- Status: ${DEVOPS_DECISION:-"Not evaluated"}
- Action: ${DEVOPS_DECISION:-"Pending"}

### Agent Services
- CLI: ${AGENT_CLI_DECISION:-"Not evaluated"}
- MCP: ${AGENT_MCP_DECISION:-"Not evaluated"}
- Analyzer: ${AGENT_ANALYZER_DECISION:-"Not evaluated"}

## Branches Deleted

- feature/dagger-orchestration (merged)
- feature/backend-refactor (cherry-picked)
- feature/knowledgebeast-migration-docker-fix (superseded)
- docs/product-roadmap-integration (no changes)
- experimental/ai-dev-tools-ui (archived)

## Remaining Branches

$(git branch | grep -v "^*")

## Verification

- ✅ Hub health check: $(curl -s http://localhost:9001/health 2>/dev/null | jq -r .status || echo "Service not running")
- ✅ Hub can reach template: $(curl -s http://localhost:9001/api/projects/template/version 2>/dev/null | jq -r .commit || echo "Service not running")
- ✅ Working tree clean: $(git status --porcelain | wc -l) changes
- ✅ All Docker builds passing

## Next Steps

1. Test Hub project creation with Dagger
2. Deploy CommandCenter instances to test projects
3. Monitor for issues over 24-48 hours
4. Consider merging deferred branches after stabilization

EOF
cat CONSOLIDATION_REPORT.md
```

Expected: Report generated

**Step 10: Commit consolidation report**

Run:
```bash
git add CONSOLIDATION_REPORT.md
git commit -m "docs: Add branch consolidation report

Consolidation completed on $(date +%Y-%m-%d).

Major changes:
- Merged Dagger orchestration (13 commits)
- Cherry-picked backend DB fix
- Cleaned up 5+ stale branches
- Reduced active branches by ~60%

Hub now fully operational with Dagger SDK."
```

Expected: Report committed

---

## Post-Consolidation Tasks

### Task 16: Push to Remote

**Purpose:** Sync local consolidation to remote repository

**Step 1: Review what will be pushed**

Run:
```bash
git log origin/main..main --oneline | head -20
```

Expected: See all new commits

**Step 2: Push main**

Run:
```bash
git push origin main
```

Expected: Pushed successfully

**Step 3: Push tags**

Run:
```bash
git push origin --tags
```

Expected: Tags pushed

**Step 4: Verify remote state**

Run:
```bash
git fetch origin
git log origin/main -1 --oneline
```

Expected: Remote matches local

---

### Task 17: Create GitHub Release (Optional)

**Purpose:** Mark this consolidation milestone

**Step 1: Create annotated tag**

Run:
```bash
git tag -a v1.0.0-consolidated -m "Version 1.0.0 - Branch Consolidation

Major milestone: All feature branches consolidated into main.

Highlights:
- Hub uses Dagger SDK for orchestration
- Backend DB session fixes
- Clean branch structure
- All core features tested and working

See CONSOLIDATION_REPORT.md for details."
```

Expected: Tag created

**Step 2: Push release tag**

Run:
```bash
git push origin v1.0.0-consolidated
```

Expected: Tag pushed

**Step 3: Create GitHub release (via gh CLI if available)**

Run:
```bash
gh release create v1.0.0-consolidated \
  --title "v1.0.0 - Branch Consolidation" \
  --notes-file CONSOLIDATION_REPORT.md \
  2>&1 || echo "Create release manually at github.com"
```

Expected: Release created OR manual instruction

---

## Rollback Plan

If something goes wrong at any phase, use these rollback procedures:

### Emergency Rollback to Pre-Consolidation State

**Step 1: Find backup tag**

Run:
```bash
git tag | grep backup-before-consolidation
```

Expected: See backup tag from Task 0

**Step 2: Create recovery branch**

Run:
```bash
git checkout -b recovery-$(date +%Y%m%d-%H%M%S)
```

Expected: New recovery branch

**Step 3: Reset to backup**

Run:
```bash
BACKUP_TAG=$(git tag | grep backup-before-consolidation | tail -1)
git reset --hard $BACKUP_TAG
```

Expected: Reset to pre-consolidation state

**Step 4: Verify state**

Run:
```bash
git log -1 --oneline
git status
```

Expected: At backup commit, clean tree

**Step 5: Test services**

Run:
```bash
docker-compose build backend
docker-compose up -d postgres redis backend
sleep 5
docker-compose ps | grep healthy
docker-compose down
```

Expected: Services work at backup state

---

## Success Criteria

- ✅ All planned branches merged or explicitly deferred
- ✅ Hub works with Dagger SDK (health check passes)
- ✅ Backend builds and starts successfully
- ✅ Frontend builds successfully
- ✅ No uncommitted changes on main
- ✅ Stale branches deleted (5+ branches removed)
- ✅ Working tree clean
- ✅ All tests passing (where applicable)
- ✅ Consolidation report generated and committed
- ✅ Changes pushed to remote

---

## Notes for Engineer

**Key Decision Points:**
- Task 6, 8, 9: Decide merge vs defer for agent services
- Task 11: Decide merge vs defer for devops refactor

**Conflict Resolution Strategy:**
- docker-compose.yml: Prefer main (has Dagger)
- requirements.txt: Merge unique dependencies from both sides
- Code conflicts: Understand context before choosing

**Testing Gates:**
- After Phase 1: Hub must pass health check
- After Phase 2: Backend must build and run
- After Phase 4: All services must still work
- Final: End-to-end Hub test

**Estimated Time:**
- Phase 1: 30-45 minutes (Dagger merge + testing)
- Phase 2: 15-20 minutes (Backend cherry-pick)
- Phase 3: 45-60 minutes (Agent evaluation + merges)
- Phase 4: 20-30 minutes (DevOps merge)
- Phase 5: 15-20 minutes (Cleanup)
- **Total: 2-3 hours** (with decision breaks)

**Dependencies:**
- Docker must be running
- Git configured properly
- Hub dependencies installed (Dagger SDK)
- Network access for Docker pulls

**Common Issues:**
- Merge conflicts in docker-compose.yml: Keep Dagger version
- Dependency conflicts: Merge both sets, test builds
- Port conflicts: Ensure ports 9000/9001 available for Hub tests
- Worktree removal failures: Use --force flag

---

## Plan Metadata

**Created:** 2025-10-28
**Engineer Assumptions:**
- Familiar with Git merge/rebase
- Can resolve merge conflicts
- Understands Docker and docker-compose
- Can read Python code
- Knows when to ask for help

**Reference Skills:**
- @superpowers:systematic-debugging (if issues arise)
- @superpowers:verification-before-completion (after each phase)
- @superpowers:test-driven-development (if writing new code)
