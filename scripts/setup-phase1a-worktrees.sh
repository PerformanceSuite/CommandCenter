#!/bin/bash
# setup-phase1a-worktrees.sh
# Creates isolated worktrees for Phase 1a completion agents

set -e

echo "🚀 Setting up Phase 1a Agent Worktrees"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create worktrees directory if it doesn't exist
mkdir -p worktrees

# Define agents
declare -A AGENTS
AGENTS=(
    ["phase1a-cicd-fixes-agent"]="fix/phase1a-cicd-pipeline"
    ["phase1a-docs-agent"]="feature/ai-dev-tools-ui"
    ["phase1a-git-agent"]="chore/phase1a-coordination-updates"
)

# Check if git is clean
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Warning: Working tree is not clean${NC}"
    echo "Uncommitted changes will be handled by phase1a-docs-agent"
    echo ""
fi

# Create worktrees for each agent
for agent in "${!AGENTS[@]}"; do
    branch="${AGENTS[$agent]}"
    worktree_path="worktrees/$agent"

    echo -e "${GREEN}Creating worktree:${NC} $agent"
    echo "  Branch: $branch"
    echo "  Path: $worktree_path"

    # Check if worktree already exists
    if [ -d "$worktree_path" ]; then
        echo -e "${YELLOW}  ⚠️  Worktree already exists, removing...${NC}"
        git worktree remove "$worktree_path" --force 2>/dev/null || true
    fi

    # Check if branch exists
    if git show-ref --verify --quiet "refs/heads/$branch"; then
        echo "  ℹ️  Branch exists, will reuse"
        git worktree add "$worktree_path" "$branch"
    else
        echo "  ✨ Creating new branch from main"
        git worktree add -b "$branch" "$worktree_path" main
    fi

    echo -e "${GREEN}  ✅ Worktree created${NC}"
    echo ""
done

# Initialize coordination directory if needed
if [ ! -d ".agent-coordination" ]; then
    echo "📁 Creating .agent-coordination directory"
    mkdir -p .agent-coordination
fi

# Update status.json for Phase 1a agents
echo "📝 Updating agent status tracking"
cat > .agent-coordination/phase1a-status.json <<EOF
{
  "phase": "1a",
  "start_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "agents": {
    "phase1a-cicd-fixes-agent": {
      "status": "initialized",
      "worktree": "worktrees/phase1a-cicd-fixes-agent",
      "branch": "fix/phase1a-cicd-pipeline",
      "progress": 0.0,
      "current_task": "Ready to start",
      "priority": "critical",
      "estimated_hours": 2.5,
      "targets": ["PR #18", "PR #19"]
    },
    "phase1a-docs-agent": {
      "status": "initialized",
      "worktree": "worktrees/phase1a-docs-agent",
      "branch": "feature/ai-dev-tools-ui",
      "progress": 0.0,
      "current_task": "Ready to start",
      "priority": "high",
      "estimated_hours": 1.5,
      "targets": ["Uncommitted work", "Documentation"]
    },
    "phase1a-git-agent": {
      "status": "initialized",
      "worktree": "worktrees/phase1a-git-agent",
      "branch": "chore/phase1a-coordination-updates",
      "progress": 0.0,
      "current_task": "Ready to start",
      "priority": "high",
      "estimated_hours": 1.0,
      "targets": ["status.json", "memory.md", "merge-queue.json"]
    },
    "phase1a-validation-agent": {
      "status": "initialized",
      "worktree": "main",
      "branch": "main",
      "progress": 0.0,
      "current_task": "Ready to monitor",
      "priority": "critical",
      "estimated_hours": 2.0,
      "targets": ["Recursive validation", "Auto-merge"]
    }
  },
  "dependencies": {
    "phase1a-docs-agent": [],
    "phase1a-git-agent": [],
    "phase1a-cicd-fixes-agent": [],
    "phase1a-validation-agent": ["phase1a-cicd-fixes-agent", "phase1a-docs-agent", "phase1a-git-agent"]
  },
  "completed": [],
  "failed": [],
  "blocked": []
}
EOF

# Create merge queue
echo "📋 Creating merge queue"
cat > .agent-coordination/phase1a-merge-queue.json <<EOF
{
  "phase": "1a",
  "queue": [
    {
      "pr_number": 19,
      "title": "Phase 1: Security Critical Fixes",
      "priority": 1,
      "merge_after": [],
      "auto_merge": true,
      "conditions": {
        "ci_passing": true,
        "review_score": 10,
        "no_conflicts": true,
        "manual_approval": false
      },
      "reason": "Security fixes block all production MCP deployment"
    },
    {
      "pr_number": 18,
      "title": "Phase 1: VIZTRTR MCP SDK Fixes",
      "priority": 2,
      "merge_after": [19],
      "auto_merge": true,
      "conditions": {
        "ci_passing": true,
        "review_score": 10,
        "no_conflicts": true,
        "manual_approval": false
      },
      "reason": "First production MCP server"
    }
  ],
  "merge_strategy": "squash",
  "auto_delete_branch": true
}
EOF

# Create task definitions
echo "📄 Creating agent task definitions"
mkdir -p .agent-coordination/tasks

cat > .agent-coordination/tasks/phase1a-cicd-fixes.md <<EOF
# Phase 1a: CI/CD Fixes Agent

## Mission
Fix all CI/CD test failures blocking PR #18 and PR #19 merge

## Priority
CRITICAL - Blocks all Phase 1a completion

## Estimated Time
2-3 hours

## Tasks

### 1. Investigate Test Failures (30 min)
- Fetch CI logs: \`gh run view 18304149314 --log-failed\`
- Fetch CI logs: \`gh run view 18304180156 --log-failed\`
- Identify root causes
- Create prioritized fix list

### 2. Fix Frontend Tests (45 min)
- Check new AITools/DevTools components
- Fix TypeScript errors
- Update tests/mocks
- Validate: \`npm test && npm run type-check\`

### 3. Fix Backend Tests (45 min)
- Check new ai_tools/dev_tools routers
- Fix import errors
- Update test fixtures
- Validate: \`pytest -v\`

### 4. Fix Trivy Scans (30 min)
- Run \`trivy fs --severity HIGH,CRITICAL .\`
- Update vulnerable dependencies
- Add .trivyignore if needed

### 5. Push & Validate (30 min)
- Push fixes to PR branches
- Wait for CI
- Recursive validation loop

## Success Criteria
- ✅ All frontend tests passing
- ✅ All backend tests passing
- ✅ Trivy scans clean
- ✅ CI/CD green on both PRs
EOF

cat > .agent-coordination/tasks/phase1a-docs.md <<EOF
# Phase 1a: Documentation Agent

## Mission
Handle uncommitted work and documentation

## Priority
HIGH - Cleanup needed before Phase 1b

## Estimated Time
1-2 hours

## Tasks

### 1. Assess Uncommitted Work (15 min)
- Review 12 uncommitted files
- Categorize: Production vs Experimental
- Make decision: Commit, Branch, or Stash

### 2. Decision Execution (45 min)
**Option A: Production**
- Create feature PR
- Add comprehensive docs
- Include in Phase 1b/1c

**Option B: Experimental**
- Create feature/ai-dev-tools-ui branch
- Commit all work
- Document for future review

**Option C: Stash**
- Stash with clear message
- Document in memory.md

### 3. Update Documentation (30 min)
- Update relevant docs
- Create ADR if production
- Update memory.md

### 4. Clean Working Tree (15 min)
- Ensure git status clean
- Verify no conflicts

## Success Criteria
- ✅ Git working tree clean
- ✅ Decision documented
- ✅ No blocking issues
EOF

cat > .agent-coordination/tasks/phase1a-git-coordination.md <<EOF
# Phase 1a: Git Coordination Agent

## Mission
Update all coordination files with accurate status

## Priority
HIGH - Required for Phase 1b launch

## Estimated Time
1 hour

## Tasks

### 1. Update status.json (15 min)
- Change phase1a_complete to false
- Add ci_status fields
- Add blocking_issues arrays

### 2. Update memory.md (30 min)
- Add Session: Phase 1a CI/CD Fixes
- Correct status (not complete)
- Document failures and actions

### 3. Create merge-queue.json (15 min)
- Define merge order
- Set auto-merge conditions
- Document rationale

## Success Criteria
- ✅ status.json accurate
- ✅ memory.md updated
- ✅ merge-queue.json created
EOF

# Create validation script
echo "🔍 Creating validation script"
cat > .agent-coordination/validate-phase1a.sh <<'EOF'
#!/bin/bash
# validate-phase1a.sh
# Recursive validation script for Phase 1a completion

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Phase 1a Validation"
echo "====================="
echo ""

# Level 1: Unit Validation
echo "Level 1: Unit Validation"
echo "------------------------"

# Check PR #18 CI
PR18_STATUS=$(gh pr view 18 --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS") | .name' | wc -l)
if [ "$PR18_STATUS" -eq 0 ]; then
    echo -e "${GREEN}✅ PR #18 CI passing${NC}"
else
    echo -e "${RED}❌ PR #18 has $PR18_STATUS failing checks${NC}"
    exit 1
fi

# Check PR #19 CI
PR19_STATUS=$(gh pr view 19 --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS") | .name' | wc -l)
if [ "$PR19_STATUS" -eq 0 ]; then
    echo -e "${GREEN}✅ PR #19 CI passing${NC}"
else
    echo -e "${RED}❌ PR #19 has $PR19_STATUS failing checks${NC}"
    exit 1
fi

# Check git status
GIT_STATUS=$(git status --porcelain | wc -l)
if [ "$GIT_STATUS" -eq 0 ]; then
    echo -e "${GREEN}✅ Git working tree clean${NC}"
else
    echo -e "${YELLOW}⚠️  Git has $GIT_STATUS uncommitted files${NC}"
fi

echo ""
echo "Level 2: Integration Validation"
echo "--------------------------------"

# Check coordination files exist
if [ -f ".agent-coordination/phase1a-status.json" ]; then
    echo -e "${GREEN}✅ phase1a-status.json exists${NC}"
else
    echo -e "${RED}❌ phase1a-status.json missing${NC}"
    exit 1
fi

if [ -f ".agent-coordination/phase1a-merge-queue.json" ]; then
    echo -e "${GREEN}✅ phase1a-merge-queue.json exists${NC}"
else
    echo -e "${RED}❌ phase1a-merge-queue.json missing${NC}"
    exit 1
fi

echo ""
echo "Level 3: End-to-End Validation"
echo "-------------------------------"

# Check merge readiness
PR18_MERGEABLE=$(gh pr view 18 --json mergeable -q '.mergeable')
PR19_MERGEABLE=$(gh pr view 19 --json mergeable -q '.mergeable')

if [ "$PR19_MERGEABLE" == "MERGEABLE" ]; then
    echo -e "${GREEN}✅ PR #19 ready to merge${NC}"
else
    echo -e "${RED}❌ PR #19 not mergeable: $PR19_MERGEABLE${NC}"
    exit 1
fi

if [ "$PR18_MERGEABLE" == "MERGEABLE" ]; then
    echo -e "${GREEN}✅ PR #18 ready to merge${NC}"
else
    echo -e "${RED}❌ PR #18 not mergeable: $PR18_MERGEABLE${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 All validations passed!${NC}"
echo ""
echo "Ready to:"
echo "  1. Merge PR #19 (Security)"
echo "  2. Merge PR #18 (VIZTRTR)"
echo "  3. Begin Phase 1b"
EOF

chmod +x .agent-coordination/validate-phase1a.sh

# Create auto-merge script
echo "🤖 Creating auto-merge script"
cat > .agent-coordination/auto-merge-phase1a.sh <<'EOF'
#!/bin/bash
# auto-merge-phase1a.sh
# Automated merge sequence for Phase 1a PRs

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🤖 Phase 1a Auto-Merge Sequence"
echo "================================"
echo ""

# Function to wait for CI
wait_for_ci() {
    local pr_number=$1
    local max_wait=3600  # 1 hour
    local elapsed=0

    while [ $elapsed -lt $max_wait ]; do
        failing=$(gh pr view "$pr_number" --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS") | .name')

        if [ -z "$failing" ]; then
            echo -e "${GREEN}✅ PR #$pr_number CI passed${NC}"
            return 0
        fi

        echo -e "${YELLOW}⏳ Waiting for PR #$pr_number CI... (${elapsed}s elapsed)${NC}"
        echo "   Failing: $failing"
        sleep 60
        elapsed=$((elapsed + 60))
    done

    echo -e "${RED}❌ PR #$pr_number CI timeout${NC}"
    return 1
}

# Step 1: Merge PR #19 (Security)
echo "Step 1: Merging PR #19 (Security Critical Fixes)"
echo "------------------------------------------------"

if wait_for_ci 19; then
    gh pr merge 19 \
        --squash \
        --auto \
        --subject "Phase 1a: Security Critical Fixes 🔒" \
        --body "Automated merge: CWE-306 and CWE-78 fixes ready for production"

    echo -e "${GREEN}✅ PR #19 merge initiated${NC}"
else
    echo -e "${RED}❌ PR #19 CI failed, aborting${NC}"
    exit 1
fi

# Wait for merge to complete
echo "Waiting for PR #19 merge to complete..."
sleep 120

# Step 2: Merge PR #18 (VIZTRTR)
echo ""
echo "Step 2: Merging PR #18 (VIZTRTR MCP SDK Fixes)"
echo "-----------------------------------------------"

if wait_for_ci 18; then
    gh pr merge 18 \
        --squash \
        --auto \
        --subject "Phase 1a: VIZTRTR MCP SDK Fixes - Production Ready" \
        --body "Automated merge: First production MCP server ready to deploy"

    echo -e "${GREEN}✅ PR #18 merge initiated${NC}"
else
    echo -e "${RED}❌ PR #18 CI failed, aborting${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Phase 1a Complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Verify deployments"
echo "  2. Run integration tests"
echo "  3. Launch Phase 1b agents"
EOF

chmod +x .agent-coordination/auto-merge-phase1a.sh

# Print summary
echo ""
echo "======================================"
echo -e "${GREEN}✅ Phase 1a Worktrees Ready!${NC}"
echo "======================================"
echo ""
echo "Worktrees created:"
for agent in "${!AGENTS[@]}"; do
    echo "  - $agent"
done
echo ""
echo "Coordination files:"
echo "  - .agent-coordination/phase1a-status.json"
echo "  - .agent-coordination/phase1a-merge-queue.json"
echo "  - .agent-coordination/tasks/*.md"
echo "  - .agent-coordination/validate-phase1a.sh"
echo "  - .agent-coordination/auto-merge-phase1a.sh"
echo ""
echo "Next steps:"
echo "  1. Launch agents using Claude Code Task tool"
echo "  2. Monitor: watch -n 10 'cat .agent-coordination/phase1a-status.json | jq'"
echo "  3. Validate: bash .agent-coordination/validate-phase1a.sh"
echo "  4. Auto-merge: bash .agent-coordination/auto-merge-phase1a.sh"
echo ""
echo -e "${GREEN}Ready to execute! 🚀${NC}"
