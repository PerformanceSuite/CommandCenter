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
