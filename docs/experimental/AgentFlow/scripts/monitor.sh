#!/bin/bash

# AgentFlow Monitoring Script
# Real-time monitoring of agent execution

set -e

# Load utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils/colors.sh"
source "$SCRIPT_DIR/utils/functions.sh"

# Configuration
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$PROJECT_ROOT/.agentflow/logs"
REVIEWS_DIR="$PROJECT_ROOT/.agentflow/reviews"
AGENTS_DIR="$PROJECT_ROOT/.agentflow/agents"

# Parse arguments
LIVE_MODE=false
TAIL_LOGS=false
SHOW_METRICS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --live)
            LIVE_MODE=true
            shift
            ;;
        --tail)
            TAIL_LOGS=true
            shift
            ;;
        --metrics)
            SHOW_METRICS=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Functions
show_dashboard() {
    clear
    echo -e "${BOLD_CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║                     AgentFlow Monitoring Dashboard                   ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # System Info
    echo -e "${BOLD}System Information${NC}"
    echo "├─ Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "├─ Project: ${PROJECT_NAME:-Unknown}"
    echo "├─ Uptime: $(calculate_uptime)"
    echo "└─ Status: ${GREEN}Active${NC}"
    echo ""
    
    # Agent Status
    echo -e "${BOLD}Agent Status${NC}"
    show_agents_status
    echo ""
    
    # Review Status
    echo -e "${BOLD}Review Pipeline${NC}"
    show_review_status
    echo ""
    
    # Metrics
    if [ "$SHOW_METRICS" = true ]; then
        echo -e "${BOLD}Performance Metrics${NC}"
        show_metrics
        echo ""
    fi
    
    # Recent Logs
    echo -e "${BOLD}Recent Activity${NC}"
    show_recent_logs
    echo ""
    
    # Controls
    echo -e "${GRAY}Press Ctrl+C to exit | R to refresh | L for logs | M for metrics${NC}"
}

show_agents_status() {
    local agents=$(ls "$AGENTS_DIR"/*.pid 2>/dev/null || true)
    
    if [ -z "$agents" ]; then
        echo "└─ No agents running"
        return
    fi
    
    for pid_file in $agents; do
        local agent=$(basename "$pid_file" .pid)
        local pid=$(cat "$pid_file")
        
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "├─ $agent: ${GREEN}● Running${NC} (PID: $pid)"
            
            # Show progress if available
            local pr_file="$REVIEWS_DIR/${agent}-pr.json"
            if [ -f "$pr_file" ]; then
                local score=$(jq -r '.score' "$pr_file" 2>/dev/null || echo "0")
                local status=$(jq -r '.status' "$pr_file" 2>/dev/null || echo "pending")
                echo "│  └─ Review: $score/10 - $status"
            fi
        else
            echo "├─ $agent: ${YELLOW}● Completed${NC}"
        fi
    done
}

show_review_status() {
    local total=0
    local approved=0
    local pending=0
    local failed=0
    
    for pr_file in "$REVIEWS_DIR"/*-pr.json; do
        [ -f "$pr_file" ] || continue
        
        ((total++))
        local status=$(jq -r '.status' "$pr_file" 2>/dev/null)
        
        case "$status" in
            approved)
                ((approved++))
                ;;
            pending_review)
                ((pending++))
                ;;
            needs_work)
                ((failed++))
                ;;
        esac
    done
    
    echo "├─ Total PRs: $total"
    echo "├─ ${GREEN}Approved: $approved${NC}"
    echo "├─ ${YELLOW}Pending: $pending${NC}"
    echo "└─ ${RED}Failed: $failed${NC}"
    
    # Progress bar
    if [ $total -gt 0 ]; then
        local percent=$((approved * 100 / total))
        echo ""
        echo -n "Progress: ["
        local filled=$((percent / 5))
        for i in $(seq 1 20); do
            if [ $i -le $filled ]; then
                echo -n "█"
            else
                echo -n "░"
            fi
        done
        echo "] $percent%"
    fi
}

show_metrics() {
    # CPU Usage
    local cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo "├─ CPU Usage: ${cpu}%"
    
    # Memory Usage
    local mem=$(free -m | awk 'NR==2{printf "%.1f", $3*100/$2}')
    echo "├─ Memory Usage: ${mem}%"
    
    # Disk Usage
    local disk=$(df -h "$PROJECT_ROOT" | awk 'NR==2{print $5}')
    echo "├─ Disk Usage: $disk"
    
    # Git Stats
    local commits=$(git rev-list --count HEAD 2>/dev/null || echo "0")
    local branches=$(git branch -r | wc -l)
    echo "├─ Git Commits: $commits"
    echo "└─ Git Branches: $branches"
}

show_recent_logs() {
    local recent_logs=$(ls -t "$LOGS_DIR"/*.log 2>/dev/null | head -5)
    
    if [ -z "$recent_logs" ]; then
        echo "└─ No recent logs"
        return
    fi
    
    for log in $recent_logs; do
        local name=$(basename "$log" .log)
        local last_line=$(tail -1 "$log" 2>/dev/null | cut -c1-60)
        echo "├─ $name: $last_line..."
    done
}

calculate_uptime() {
    if [ -f "$LOGS_DIR/.start_time" ]; then
        local start=$(cat "$LOGS_DIR/.start_time")
        local now=$(date +%s)
        local diff=$((now - start))
        printf '%dh %dm %ds' $((diff/3600)) $((diff%3600/60)) $((diff%60))
    else
        echo "N/A"
    fi
}

tail_all_logs() {
    log "Tailing all agent logs..."
    tail -f "$LOGS_DIR"/*.log 2>/dev/null || {
        warning "No logs found"
        exit 0
    }
}

# Main execution
main() {
    if [ "$TAIL_LOGS" = true ]; then
        tail_all_logs
    elif [ "$LIVE_MODE" = true ]; then
        # Live monitoring loop
        while true; do
            show_dashboard
            sleep 5
        done
    else
        # Single dashboard view
        show_dashboard
    fi
}

# Handle keyboard input
if [ "$LIVE_MODE" = true ]; then
    trap 'echo ""; success "Monitoring stopped"; exit 0' INT TERM
fi

# Run main function
main
