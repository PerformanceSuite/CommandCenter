#!/bin/bash

# Utility functions for AgentFlow

# Logging functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

debug() {
    if [ "${DEBUG:-0}" = "1" ]; then
        echo -e "${GRAY}[DEBUG]${NC} $1"
    fi
}

# Banner function
banner() {
    local text="$1"
    local width=60
    local padding=$(( (width - ${#text}) / 2 ))
    
    echo -e "${BOLD_CYAN}"
    echo "╔$(printf '═%.0s' $(seq 1 $width))╗"
    echo "║$(printf ' %.0s' $(seq 1 $padding))$text$(printf ' %.0s' $(seq 1 $((width - padding - ${#text}))))║"
    echo "╚$(printf '═%.0s' $(seq 1 $width))╝"
    echo -e "${NC}"
}

# Progress bar
progress_bar() {
    local current=$1
    local total=$2
    local width=50
    local percent=$((current * 100 / total))
    local filled=$((current * width / total))
    
    printf "\r["
    printf "%-${width}s" "$(printf '#%.0s' $(seq 1 $filled))"
    printf "] %d%%" $percent
}

# Spinner
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Confirm action
confirm() {
    local prompt="${1:-Are you sure?}"
    local response
    
    read -r -p "$(echo -e "${YELLOW}$prompt [y/N]: ${NC}")" response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Create backup
backup_file() {
    local file=$1
    if [ -f "$file" ]; then
        local backup="${file}.backup.$(date +%Y%m%d-%H%M%S)"
        cp "$file" "$backup"
        debug "Created backup: $backup"
    fi
}

# JSON operations
json_get() {
    local file=$1
    local path=$2
    jq -r "$path" "$file" 2>/dev/null
}

json_set() {
    local file=$1
    local path=$2
    local value=$3
    local temp=$(mktemp)
    jq "$path = $value" "$file" > "$temp" && mv "$temp" "$file"
}

# File operations
safe_mkdir() {
    local dir=$1
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        debug "Created directory: $dir"
    fi
}

safe_rm() {
    local file=$1
    if confirm "Delete $file?"; then
        rm -rf "$file"
        debug "Deleted: $file"
    fi
}

# Process management
is_process_running() {
    local pid=$1
    ps -p "$pid" > /dev/null 2>&1
}

kill_process_tree() {
    local pid=$1
    local children=$(ps -o pid= --ppid "$pid")
    
    for child in $children; do
        kill_process_tree "$child"
    done
    
    kill -TERM "$pid" 2>/dev/null
}

# Network operations
wait_for_port() {
    local host=$1
    local port=$2
    local timeout=${3:-30}
    local elapsed=0
    
    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ $elapsed -ge $timeout ]; then
            return 1
        fi
        sleep 1
        ((elapsed++))
    done
    return 0
}

# String operations
trim() {
    echo "$1" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

to_lowercase() {
    echo "$1" | tr '[:upper:]' '[:lower:]'
}

to_uppercase() {
    echo "$1" | tr '[:lower:]' '[:upper:]'
}

# Array operations
array_contains() {
    local needle=$1
    shift
    local item
    for item in "$@"; do
        [[ "$item" == "$needle" ]] && return 0
    done
    return 1
}

array_join() {
    local delimiter=$1
    shift
    local first=1
    for item in "$@"; do
        if [ $first -eq 1 ]; then
            printf "%s" "$item"
            first=0
        else
            printf "%s%s" "$delimiter" "$item"
        fi
    done
}

# Time operations
timestamp() {
    date +%Y%m%d-%H%M%S
}

epoch() {
    date +%s
}

duration() {
    local start=$1
    local end=${2:-$(epoch)}
    local diff=$((end - start))
    printf '%dh %dm %ds' $((diff/3600)) $((diff%3600/60)) $((diff%60))
}

# Validation functions
validate_email() {
    local email=$1
    [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]
}

validate_url() {
    local url=$1
    [[ "$url" =~ ^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$ ]]
}

validate_json() {
    local file=$1
    jq empty "$file" 2>/dev/null
}

# Export all functions
export -f log error success warning info debug
export -f banner progress_bar spinner
export -f command_exists confirm backup_file
export -f json_get json_set
export -f safe_mkdir safe_rm
export -f is_process_running kill_process_tree
export -f wait_for_port
export -f trim to_lowercase to_uppercase
export -f array_contains array_join
export -f timestamp epoch duration
export -f validate_email validate_url validate_json
