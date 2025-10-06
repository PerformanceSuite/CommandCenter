#!/bin/bash

################################################################################
# Command Center Restore Script
#
# This script restores backups created by backup.sh
#
# Usage:
#   ./restore.sh [TIMESTAMP]
#
# If no timestamp is provided, the most recent backup will be used.
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
COMPOSE_PROJECT="${COMPOSE_PROJECT_NAME:-commandcenter}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Parse arguments
TIMESTAMP=${1:-""}

if [ -z "$TIMESTAMP" ]; then
    log "No timestamp provided, finding most recent backup..."

    # Find most recent PostgreSQL backup
    LATEST_BACKUP=$(find "$BACKUP_DIR/postgres" -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -rn | head -1 | cut -d' ' -f2-)

    if [ -z "$LATEST_BACKUP" ]; then
        error "No backups found in $BACKUP_DIR/postgres"
        exit 1
    fi

    # Extract timestamp from filename
    TIMESTAMP=$(basename "$LATEST_BACKUP" | sed 's/commandcenter_\(.*\)\.sql\.gz/\1/')
    log "Found backup with timestamp: $TIMESTAMP"
fi

# Verify backup files exist
POSTGRES_BACKUP="${BACKUP_DIR}/postgres/commandcenter_${TIMESTAMP}.sql.gz"
RAG_BACKUP="${BACKUP_DIR}/rag/rag_storage_${TIMESTAMP}.tar.gz"
REDIS_BACKUP="${BACKUP_DIR}/redis/redis_${TIMESTAMP}.rdb.gz"

if [ ! -f "$POSTGRES_BACKUP" ]; then
    error "PostgreSQL backup not found: $POSTGRES_BACKUP"
    exit 1
fi

log "Using backup timestamp: $TIMESTAMP"
log "PostgreSQL backup: $POSTGRES_BACKUP"
[ -f "$RAG_BACKUP" ] && log "RAG backup: $RAG_BACKUP"
[ -f "$REDIS_BACKUP" ] && log "Redis backup: $REDIS_BACKUP"

# Confirmation prompt
echo ""
warning "WARNING: This will overwrite existing data!"
read -p "Are you sure you want to restore from backup $TIMESTAMP? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log "Restore cancelled"
    exit 0
fi

################################################################################
# PostgreSQL Restore
################################################################################
log "Restoring PostgreSQL database..."

# Drop existing database and recreate
docker exec "${COMPOSE_PROJECT}_db" psql -U commandcenter -c "DROP DATABASE IF EXISTS commandcenter;"
docker exec "${COMPOSE_PROJECT}_db" psql -U commandcenter -c "CREATE DATABASE commandcenter;"

# Restore from backup
if gunzip -c "$POSTGRES_BACKUP" | docker exec -i "${COMPOSE_PROJECT}_db" psql -U commandcenter commandcenter; then
    log "PostgreSQL restore completed successfully"
else
    error "PostgreSQL restore failed!"
    exit 1
fi

################################################################################
# RAG Storage Restore
################################################################################
if [ -f "$RAG_BACKUP" ]; then
    log "Restoring RAG storage..."

    RAG_VOLUME=$(docker volume inspect "${COMPOSE_PROJECT}_rag_storage" --format '{{.Mountpoint}}' 2>/dev/null || echo "")

    if [ -n "$RAG_VOLUME" ]; then
        # Clear existing data
        docker run --rm -v "${COMPOSE_PROJECT}_rag_storage:/data" alpine sh -c "rm -rf /data/*"

        # Restore backup
        if tar -xzf "$RAG_BACKUP" -C "$RAG_VOLUME"; then
            log "RAG storage restore completed successfully"
        else
            error "RAG storage restore failed!"
            exit 1
        fi
    else
        warning "RAG storage volume not found, skipping..."
    fi
else
    warning "RAG backup not found, skipping..."
fi

################################################################################
# Redis Restore
################################################################################
if [ -f "$REDIS_BACKUP" ]; then
    log "Restoring Redis data..."

    # Stop Redis to restore
    docker exec "${COMPOSE_PROJECT}_redis" redis-cli SHUTDOWN NOSAVE || true
    sleep 2

    # Restore dump.rdb
    if gunzip -c "$REDIS_BACKUP" | docker cp - "${COMPOSE_PROJECT}_redis:/data/dump.rdb"; then
        # Restart Redis
        docker restart "${COMPOSE_PROJECT}_redis"
        sleep 5
        log "Redis restore completed successfully"
    else
        warning "Redis restore failed, continuing..."
    fi
else
    warning "Redis backup not found, skipping..."
fi

################################################################################
# Summary
################################################################################
log "Restore completed successfully!"
log "Restored from backup: $TIMESTAMP"

exit 0
