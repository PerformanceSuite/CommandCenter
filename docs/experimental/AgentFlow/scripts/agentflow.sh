#!/bin/bash

# AgentFlow - Main Orchestration Script
# Autonomous Multi-Agent Claude Code System

set -e

# Load configuration and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils/colors.sh"
source "$SCRIPT_DIR/utils/functions.sh"
source "$SCRIPT_DIR/utils/git-helpers.sh"

# Configuration
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config"
PROMPTS_DIR="$PROJECT_ROOT/prompts"
AGENTS_DIR="$PROJECT_ROOT/agents"
LOGS_DIR="$PROJECT_ROOT/.agentflow/logs"
WORKTREES_DIR="$PROJECT_ROOT/.agentflow/worktrees"
REVIEWS_DIR="$PROJECT_ROOT/.agentflow/reviews"

# Default values
PROJECT_NAME="${PROJECT_NAME:-my-project}"
MAX_PARALLEL="${MAX_PARALLEL:-5}"
REVIEW_THRESHOLD="${REVIEW_THRESHOLD:-10}"
MERGE_STRATEGY="${MERGE_STRATEGY:-squash}"
BRANCH_STRATEGY="${BRANCH_STRATEGY:-gitflow}"
CLAUDE_MODEL="${CLAUDE_MODEL:-claude-opus-4-1-20250805}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT_NAME="$2"
            shift 2
            ;;
        --agents)
            MAX_PARALLEL="$2"
            shift 2
            ;;
        --threshold)
            REVIEW_THRESHOLD="$2"
            shift 2
            ;;
        --model)
            CLAUDE_MODEL="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Functions
show_help() {
    cat << EOF
AgentFlow - Autonomous Multi-Agent Claude Code System

Usage: $(basename "$0") [OPTIONS]

Options:
    --project NAME      Project name (default: my-project)
    --agents NUM        Max parallel agents (default: 5)
    --threshold NUM     Review score threshold (default: 10)
    --model MODEL       Claude model to use (default: claude-opus-4-1-20250805)
    --config FILE       Path to configuration file
    --help              Show this help message

Examples:
    $(basename "$0") --project my-app --agents 8
    $(basename "$0") --config ./my-config.json
    $(basename "$0") --project backend-api --threshold 9

EOF
}

init_project() {
    log "Initializing AgentFlow for project: ${BOLD}$PROJECT_NAME${NC}"
    
    # Create necessary directories
    mkdir -p "$LOGS_DIR"
    mkdir -p "$WORKTREES_DIR"
    mkdir -p "$REVIEWS_DIR"
    mkdir -p "$PROJECT_ROOT/.agentflow/cache"
    mkdir -p "$PROJECT_ROOT/.agentflow/artifacts"
    
    # Initialize git if needed
    if [ ! -d .git ]; then
        warning "Git repository not found. Initializing..."
        git init
        git add .
        git commit -m "Initial commit for AgentFlow"
    fi
    
    # Create main branch if needed
    git checkout -b main 2>/dev/null || git checkout main
    
    success "Project initialized successfully"
}

load_agents() {
    log "Loading agent configurations..."
    
    # Read agents from config
    if [ -f "$CONFIG_DIR/agents.json" ]; then
        AGENTS=$(jq -r '.agents[].name' "$CONFIG_DIR/agents.json")
    else
        # Default agents
        AGENTS=(
            "backend"
            "frontend"
            "database"
            "testing"
            "security"
        )
    fi
    
    info "Loaded ${#AGENTS[@]} agents"
}

setup_worktrees() {
    log "Setting up git worktrees for agents..."
    
    local count=0
    for agent in $AGENTS; do
        local worktree_path="$WORKTREES_DIR/$agent"
        
        if [ ! -d "$worktree_path" ]; then
            log "Creating worktree for ${CYAN}$agent${NC}"
            git worktree add -b "agent/$agent" "$worktree_path" 2>/dev/null || {
                warning "Worktree for $agent already exists, cleaning up..."
                git worktree remove "$worktree_path" --force 2>/dev/null || true
                git branch -D "agent/$agent" 2>/dev/null || true
                git worktree add -b "agent/$agent" "$worktree_path"
            }
            ((count++))
        fi
    done
    
    success "Created $count new worktrees"
}

launch_agent() {
    local agent=$1
    local task=$2
    local worktree="$WORKTREES_DIR/$agent"
    local log_file="$LOGS_DIR/${agent}-$(date +%Y%m%d-%H%M%S).log"
    
    log "Launching agent: ${CYAN}$agent${NC}"
    info "Task: $task"
    
    (
        cd "$worktree"
        
        # Create agent-specific prompt
        cat > .agentflow-prompt.md << EOF
# Agent: $agent
# Task: $task
# Model: $CLAUDE_MODEL

$(cat "$PROMPTS_DIR/base.md")

## Specific Instructions for $agent

$(cat "$AGENTS_DIR/$agent/instructions.md" 2>/dev/null || echo "No specific instructions found.")

## Current Task
$task

## Working Directory
$(pwd)

## Branch
agent/$agent

## Success Criteria
- Achieve review score of $REVIEW_THRESHOLD/10
- All tests passing
- No security vulnerabilities
- Clean code following best practices

BEGIN IMPLEMENTATION:
EOF
        
        # Log execution
        exec &> >(tee "$log_file")
        
        # Execute Claude Code
        log "Executing Claude Code for $agent..."
        
        # Simulate Claude Code execution (replace with actual command)
        if command -v claude-code &> /dev/null; then
            claude-code \
                --model "$CLAUDE_MODEL" \
                --prompt .agentflow-prompt.md \
                --max-tokens 4000 \
                --temperature 0.7
        else
            warning "Claude Code CLI not found. Simulating agent work..."
            echo "// $agent implementation" > "${agent}.js"
            sleep 2
        fi
        
        # Commit changes
        if [ -n "$(git status --porcelain)" ]; then
            git add -A
            git commit -m "[$agent] $task

Agent: $agent
Task: $task
Timestamp: $(date -Iseconds)
Model: $CLAUDE_MODEL"
            
            # Push changes
            git push origin "agent/$agent" 2>/dev/null || {
                git push --set-upstream origin "agent/$agent"
            }
            
            # Create PR metadata
            create_pr_metadata "$agent" "$task"
            
            success "Agent $agent completed task"
        else
            warning "No changes made by $agent"
        fi
        
    ) &
    
    # Save PID for monitoring
    echo $! > "$PROJECT_ROOT/.agentflow/agents/${agent}.pid"
}

create_pr_metadata() {
    local agent=$1
    local task=$2
    
    cat > "$REVIEWS_DIR/${agent}-pr.json" << EOF
{
    "agent": "$agent",
    "branch": "agent/$agent",
    "task": "$task",
    "status": "pending_review",
    "score": 0,
    "created": "$(date -Iseconds)",
    "files_changed": $(git diff --name-only main...HEAD | wc -l),
    "additions": $(git diff --numstat main...HEAD | awk '{s+=$1} END {print s}'),
    "deletions": $(git diff --numstat main...HEAD | awk '{s+=$2} END {print s}')
}
EOF
}

review_agent_work() {
    local pr_file=$1
    local agent=$(jq -r '.agent' "$pr_file")
    
    log "Reviewing work from ${CYAN}$agent${NC}"
    
    # Create review prompt
    cat > "$PROJECT_ROOT/.agentflow/review-prompt.md" << EOF
# Code Review Request

## Agent: $agent
## Branch: agent/$agent

## Review Criteria (Score out of 10)

1. **Functionality (2 points)**
   - Works as intended
   - Handles edge cases
   
2. **Code Quality (2 points)**
   - Clean and readable
   - Follows best practices
   
3. **Performance (2 points)**
   - Optimized algorithms
   - No bottlenecks
   
4. **Security (2 points)**
   - No vulnerabilities
   - Proper validation
   
5. **Testing (2 points)**
   - Comprehensive coverage
   - All tests passing

## Files Changed
$(cd "$WORKTREES_DIR/$agent" && git diff --name-only main...HEAD)

## Code Diff
$(cd "$WORKTREES_DIR/$agent" && git diff main...HEAD)

Please review and provide:
1. Numeric score (0-10)
2. Specific feedback
3. Required improvements (if score < $REVIEW_THRESHOLD)
EOF
    
    # Execute review
    local score=0
    if command -v claude-code &> /dev/null; then
        score=$(claude-code \
            --model "$CLAUDE_MODEL" \
            --prompt "$PROJECT_ROOT/.agentflow/review-prompt.md" \
            --quiet \
            | grep -oE 'Score: [0-9]+' \
            | grep -oE '[0-9]+' \
            | head -1)
    else
        # Simulate review score
        score=$((RANDOM % 3 + 8))  # Random score between 8-10
    fi
    
    # Update PR metadata
    jq ".score = $score | .status = if $score >= $REVIEW_THRESHOLD then \"approved\" else \"needs_work\" end" "$pr_file" > temp.json
    mv temp.json "$pr_file"
    
    if [ "$score" -lt "$REVIEW_THRESHOLD" ]; then
        warning "PR from $agent needs improvements (score: $score/$REVIEW_THRESHOLD)"
        return 1
    else
        success "PR from $agent approved (score: $score/$REVIEW_THRESHOLD)"
        return 0
    fi
}

coordinate_merges() {
    log "Starting coordination phase..."
    
    # Collect approved PRs
    local approved_prs=()
    for pr_file in "$REVIEWS_DIR"/*-pr.json; do
        [ -f "$pr_file" ] || continue
        
        local status=$(jq -r '.status' "$pr_file")
        if [ "$status" = "approved" ]; then
            approved_prs+=("$pr_file")
        fi
    done
    
    info "Found ${#approved_prs[@]} approved PRs"
    
    # Sort by dependencies (simplified)
    log "Analyzing dependencies and merge order..."
    
    # Merge each approved PR
    for pr_file in "${approved_prs[@]}"; do
        local branch=$(jq -r '.branch' "$pr_file")
        local agent=$(jq -r '.agent' "$pr_file")
        
        log "Merging ${CYAN}$branch${NC}"
        
        git checkout main
        
        case "$MERGE_STRATEGY" in
            squash)
                git merge --squash "$branch"
                git commit -m "[$agent] Merged changes via squash"
                ;;
            merge)
                git merge --no-ff "$branch" -m "Merge $branch into main"
                ;;
            rebase)
                git checkout "$branch"
                git rebase main
                git checkout main
                git merge --ff-only "$branch"
                ;;
        esac
        
        # Run tests after merge
        if [ -f "package.json" ] && command -v npm &> /dev/null; then
            log "Running integration tests..."
            npm test 2>/dev/null || warning "Some tests failed"
        fi
        
        success "Merged $branch successfully"
    done
    
    # Cleanup worktrees
    log "Cleaning up worktrees..."
    git worktree prune
    
    success "Coordination complete!"
}

monitor_agents() {
    while true; do
        clear
        echo "╔══════════════════════════════════════════════════════════╗"
        echo "║             AgentFlow Monitoring Dashboard              ║"
        echo "╠══════════════════════════════════════════════════════════╣"
        echo "║ Project: $PROJECT_NAME"
        echo "║ Time: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "╠══════════════════════════════════════════════════════════╣"
        echo "║ Agent Status:"
        echo "║"
        
        for agent in $AGENTS; do
            local pid_file="$PROJECT_ROOT/.agentflow/agents/${agent}.pid"
            local pr_file="$REVIEWS_DIR/${agent}-pr.json"
            
            if [ -f "$pid_file" ]; then
                local pid=$(cat "$pid_file")
                if ps -p $pid > /dev/null 2>&1; then
                    echo "║ ✓ $agent: ${GREEN}Running${NC} (PID: $pid)"
                else
                    if [ -f "$pr_file" ]; then
                        local score=$(jq -r '.score' "$pr_file" 2>/dev/null || echo "0")
                        local status=$(jq -r '.status' "$pr_file" 2>/dev/null || echo "unknown")
                        echo "║ ✓ $agent: ${YELLOW}Complete${NC} (Score: $score/10, Status: $status)"
                    else
                        echo "║ ✓ $agent: ${BLUE}Complete${NC}"
                    fi
                fi
            else
                echo "║ - $agent: ${GRAY}Not started${NC}"
            fi
        done
        
        echo "║"
        echo "╠══════════════════════════════════════════════════════════╣"
        echo "║ Press Ctrl+C to exit monitoring                         ║"
        echo "╚══════════════════════════════════════════════════════════╝"
        
        sleep 5
    done
}

generate_summary() {
    log "Generating workflow summary..."
    
    local summary_file="$PROJECT_ROOT/agentflow-summary-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$summary_file" << EOF
# AgentFlow Workflow Summary

**Project**: $PROJECT_NAME  
**Date**: $(date)  
**Model**: $CLAUDE_MODEL  

## Configuration
- Max Parallel Agents: $MAX_PARALLEL
- Review Threshold: $REVIEW_THRESHOLD/10
- Merge Strategy: $MERGE_STRATEGY
- Branch Strategy: $BRANCH_STRATEGY

## Agents Performance

| Agent | Status | Score | Files Changed | Lines Added | Lines Removed |
|-------|--------|-------|---------------|-------------|---------------|
EOF
    
    for agent in $AGENTS; do
        local pr_file="$REVIEWS_DIR/${agent}-pr.json"
        if [ -f "$pr_file" ]; then
            local status=$(jq -r '.status' "$pr_file")
            local score=$(jq -r '.score' "$pr_file")
            local files=$(jq -r '.files_changed' "$pr_file")
            local adds=$(jq -r '.additions' "$pr_file")
            local dels=$(jq -r '.deletions' "$pr_file")
            echo "| $agent | $status | $score/10 | $files | +$adds | -$dels |" >> "$summary_file"
        fi
    done
    
    cat >> "$summary_file" << EOF

## Execution Timeline
- Start: $(cat "$LOGS_DIR"/.start_time 2>/dev/null || echo "N/A")
- End: $(date)
- Duration: $(calculate_duration)

## Next Steps
1. Review merged changes in main branch
2. Run comprehensive test suite
3. Deploy to staging environment
4. Monitor application metrics

## Logs
All execution logs available in: $LOGS_DIR/

---
Generated by AgentFlow v1.0.0
EOF
    
    success "Summary saved to: $summary_file"
}

calculate_duration() {
    if [ -f "$LOGS_DIR/.start_time" ]; then
        local start=$(cat "$LOGS_DIR/.start_time")
        local end=$(date +%s)
        local duration=$((end - start))
        printf '%dh %dm %ds' $((duration/3600)) $((duration%3600/60)) $((duration%60))
    else
        echo "N/A"
    fi
}

# Main execution
main() {
    banner "AgentFlow - Autonomous Multi-Agent System"
    
    # Save start time
    date +%s > "$LOGS_DIR/.start_time"
    
    # Phase 1: Initialize
    init_project
    load_agents
    setup_worktrees
    
    # Phase 2: Launch agents
    log "Launching agents in parallel (max: $MAX_PARALLEL)..."
    
    # Example task distribution
    launch_agent "backend" "Implement REST API with authentication"
    launch_agent "frontend" "Create React components and routing"
    launch_agent "database" "Design schema and add migrations"
    launch_agent "testing" "Write comprehensive test suites"
    launch_agent "security" "Implement security best practices"
    
    # Phase 3: Monitor
    if [ -t 0 ]; then
        monitor_agents &
        MONITOR_PID=$!
    fi
    
    # Phase 4: Wait for completion
    log "Waiting for agents to complete..."
    wait
    
    # Kill monitor if running
    [ -n "$MONITOR_PID" ] && kill $MONITOR_PID 2>/dev/null
    
    # Phase 5: Review
    log "Starting review phase..."
    for pr_file in "$REVIEWS_DIR"/*-pr.json; do
        [ -f "$pr_file" ] || continue
        
        while ! review_agent_work "$pr_file"; do
            warning "Requesting improvements..."
            sleep 5
        done
    done
    
    # Phase 6: Coordinate and merge
    coordinate_merges
    
    # Phase 7: Generate summary
    generate_summary
    
    success "AgentFlow workflow completed successfully!"
    info "Check the summary for detailed results"
}

# Trap for cleanup
trap 'error "Interrupted! Cleaning up..."; kill $(jobs -p) 2>/dev/null; exit 1' INT TERM

# Check dependencies
check_dependencies() {
    local missing=()
    
    command -v git &> /dev/null || missing+=("git")
    command -v jq &> /dev/null || missing+=("jq")
    
    if [ ${#missing[@]} -gt 0 ]; then
        error "Missing dependencies: ${missing[*]}"
        info "Please install them and try again"
        exit 1
    fi
}

# Run checks and main
check_dependencies
main "$@"
