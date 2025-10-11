#!/bin/bash

# Git helper functions for AgentFlow

# Check if we're in a git repository
is_git_repo() {
    git rev-parse --git-dir &> /dev/null
}

# Get current branch name
current_branch() {
    git rev-parse --abbrev-ref HEAD 2>/dev/null
}

# Check if branch exists
branch_exists() {
    local branch=$1
    git show-ref --verify --quiet "refs/heads/$branch"
}

# Check if worktree exists
worktree_exists() {
    local path=$1
    git worktree list | grep -q "$path"
}

# Create worktree safely
create_worktree() {
    local branch=$1
    local path=$2
    
    # Remove existing worktree if it exists
    if worktree_exists "$path"; then
        git worktree remove "$path" --force 2>/dev/null || true
    fi
    
    # Delete branch if it exists
    if branch_exists "$branch"; then
        git branch -D "$branch" 2>/dev/null || true
    fi
    
    # Create new worktree
    git worktree add -b "$branch" "$path"
}

# Check for uncommitted changes
has_changes() {
    [ -n "$(git status --porcelain)" ]
}

# Commit all changes
commit_all() {
    local message=$1
    git add -A
    git commit -m "$message"
}

# Push branch to origin
push_branch() {
    local branch=${1:-$(current_branch)}
    git push origin "$branch" 2>/dev/null || {
        git push --set-upstream origin "$branch"
    }
}

# Get file changes between branches
get_changes() {
    local base=${1:-main}
    local head=${2:-HEAD}
    git diff --name-only "$base...$head"
}

# Get commit count between branches
get_commit_count() {
    local base=${1:-main}
    local head=${2:-HEAD}
    git rev-list --count "$base..$head"
}

# Check if branch is up to date with main
is_up_to_date() {
    local branch=${1:-$(current_branch)}
    local behind=$(git rev-list --count "$branch..main")
    [ "$behind" -eq 0 ]
}

# Merge branch with strategy
merge_branch() {
    local branch=$1
    local strategy=${2:-merge}
    
    case "$strategy" in
        squash)
            git merge --squash "$branch"
            ;;
        merge)
            git merge --no-ff "$branch"
            ;;
        rebase)
            git checkout "$branch"
            git rebase main
            git checkout main
            git merge --ff-only "$branch"
            ;;
        *)
            error "Unknown merge strategy: $strategy"
            return 1
            ;;
    esac
}

# Clean up merged branches
cleanup_branches() {
    git branch --merged main | grep -v "main\|master" | xargs -r git branch -d
}

# Get PR-style diff
get_pr_diff() {
    local branch=$1
    local base=${2:-main}
    
    echo "## Branch: $branch"
    echo "## Base: $base"
    echo "## Files changed: $(git diff --name-only "$base...$branch" | wc -l)"
    echo "## Insertions: $(git diff --stat "$base...$branch" | tail -1 | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+' || echo 0)"
    echo "## Deletions: $(git diff --stat "$base...$branch" | tail -1 | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' || echo 0)"
    echo ""
    git diff "$base...$branch"
}

# Cherry-pick commits
cherry_pick_range() {
    local start=$1
    local end=$2
    git cherry-pick "${start}..${end}"
}

# Stash operations
stash_changes() {
    local message=${1:-"AgentFlow auto-stash"}
    git stash push -m "$message"
}

pop_stash() {
    git stash pop
}

# Get git config value
get_git_config() {
    local key=$1
    git config --get "$key"
}

# Set git config value
set_git_config() {
    local key=$1
    local value=$2
    git config "$key" "$value"
}

# Check if remote exists
remote_exists() {
    local remote=${1:-origin}
    git remote | grep -q "^$remote$"
}

# Add remote if not exists
add_remote() {
    local name=$1
    local url=$2
    
    if ! remote_exists "$name"; then
        git remote add "$name" "$url"
    fi
}

# Export functions
export -f is_git_repo current_branch branch_exists
export -f worktree_exists create_worktree
export -f has_changes commit_all push_branch
export -f get_changes get_commit_count is_up_to_date
export -f merge_branch cleanup_branches get_pr_diff
export -f cherry_pick_range stash_changes pop_stash
export -f get_git_config set_git_config
export -f remote_exists add_remote
