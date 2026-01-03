#!/bin/bash
# check-agents.sh
# Quick check of all agent statuses

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Agent Status Quick Check"
echo "========================"
echo ""

for i in 1 2 3; do
    status_file=".agent-coordination/agent${i}-status.txt"

    if [ -f "$status_file" ]; then
        # Extract key info
        agent_name=$(grep "^Agent:" "$status_file" | cut -d: -f2 | xargs)
        status=$(grep "^Status:" "$status_file" | cut -d: -f2 | xargs)

        # Check if complete
        if echo "$status" | grep -qi "complete\|success"; then
            echo -e "${GREEN}✅ Agent $i:${NC} $agent_name"
            echo "   Status: $status"
        else
            echo -e "${YELLOW}⏳ Agent $i:${NC} $agent_name"
            echo "   Status: $status"
        fi

        # Show last few lines
        echo "   Last Update:"
        tail -3 "$status_file" | sed 's/^/     /'
        echo ""
    else
        echo -e "${RED}❌ Agent $i:${NC} Not started (no status file)"
        echo ""
    fi
done

echo "========================"
echo "For detailed status: bash .agent-coordination/validation-dashboard.sh"
