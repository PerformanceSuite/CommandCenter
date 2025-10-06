#!/bin/bash

################################################################################
# Command Center Backup Script
#
# This script performs automated backups of:
# - PostgreSQL database
# - RAG storage (ChromaDB and documents)
# - Redis data (optional)
#
# Features:
# - Compressed backups with timestamps
# - 30-day retention policy
# - Error handling and logging
# - Support for local and remote storage
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${BACKUP_DIR}/backup.log"

# Docker compose project name
COMPOSE_PROJECT="${COMPOSE_PROJECT_NAME:-commandcenter}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"/{postgres,rag,redis}
mkdir -p "$(dirname "$LOG_FILE")"

log "Starting backup process..."

################################################################################
# PostgreSQL Backup
################################################################################
log "Backing up PostgreSQL database..."

POSTGRES_BACKUP_FILE="${BACKUP_DIR}/postgres/commandcenter_${TIMESTAMP}.sql.gz"

if docker exec "${COMPOSE_PROJECT}_db" pg_dump -U commandcenter commandcenter | gzip > "$POSTGRES_BACKUP_FILE"; then
    BACKUP_SIZE=$(du -h "$POSTGRES_BACKUP_FILE" | cut -f1)
    log "PostgreSQL backup completed: ${POSTGRES_BACKUP_FILE} (${BACKUP_SIZE})"
else
    error "PostgreSQL backup failed!"
    exit 1
fi

################################################################################
# RAG Storage Backup
################################################################################
log "Backing up RAG storage..."

RAG_BACKUP_FILE="${BACKUP_DIR}/rag/rag_storage_${TIMESTAMP}.tar.gz"

# Get the RAG storage volume path
RAG_VOLUME=$(docker volume inspect "${COMPOSE_PROJECT}_rag_storage" --format '{{.Mountpoint}}' 2>/dev/null || echo "")

if [ -n "$RAG_VOLUME" ] && [ -d "$RAG_VOLUME" ]; then
    if tar -czf "$RAG_BACKUP_FILE" -C "$RAG_VOLUME" .; then
        BACKUP_SIZE=$(du -h "$RAG_BACKUP_FILE" | cut -f1)
        log "RAG storage backup completed: ${RAG_BACKUP_FILE} (${BACKUP_SIZE})"
    else
        error "RAG storage backup failed!"
        exit 1
    fi
else
    warning "RAG storage volume not found, skipping..."
fi

################################################################################
# Redis Backup (Optional)
################################################################################
log "Backing up Redis data..."

REDIS_BACKUP_FILE="${BACKUP_DIR}/redis/redis_${TIMESTAMP}.rdb.gz"

if docker exec "${COMPOSE_PROJECT}_redis" redis-cli BGSAVE; then
    # Wait for BGSAVE to complete
    sleep 5

    # Copy the RDB file
    if docker cp "${COMPOSE_PROJECT}_redis:/data/dump.rdb" - | gzip > "$REDIS_BACKUP_FILE"; then
        BACKUP_SIZE=$(du -h "$REDIS_BACKUP_FILE" | cut -f1)
        log "Redis backup completed: ${REDIS_BACKUP_FILE} (${BACKUP_SIZE})"
    else
        warning "Redis backup failed, continuing..."
    fi
else
    warning "Redis BGSAVE failed, skipping Redis backup..."
fi

################################################################################
# Cleanup Old Backups
################################################################################
log "Cleaning up backups older than ${RETENTION_DAYS} days..."

# Count backups before cleanup
TOTAL_BEFORE=$(find "$BACKUP_DIR" -type f -name "*.gz" -o -name "*.tar.gz" | wc -l)

# Remove old backups
find "$BACKUP_DIR/postgres" -name "*.sql.gz" -type f -mtime "+${RETENTION_DAYS}" -delete
find "$BACKUP_DIR/rag" -name "*.tar.gz" -type f -mtime "+${RETENTION_DAYS}" -delete
find "$BACKUP_DIR/redis" -name "*.rdb.gz" -type f -mtime "+${RETENTION_DAYS}" -delete

# Count backups after cleanup
TOTAL_AFTER=$(find "$BACKUP_DIR" -type f -name "*.gz" -o -name "*.tar.gz" | wc -l)
DELETED=$((TOTAL_BEFORE - TOTAL_AFTER))

if [ $DELETED -gt 0 ]; then
    log "Removed ${DELETED} old backup(s)"
else
    log "No old backups to remove"
fi

################################################################################
# Backup Summary
################################################################################
log "Backup completed successfully!"
log "Backup location: ${BACKUP_DIR}"
log "Total backups: ${TOTAL_AFTER}"

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "Total backup size: ${TOTAL_SIZE}"

################################################################################
# Optional: Upload to Remote Storage
################################################################################
# Uncomment and configure for remote backup storage (S3, Google Cloud Storage, etc.)
#
# Example for AWS S3:
# if command -v aws &> /dev/null; then
#     log "Uploading backups to S3..."
#     aws s3 sync "$BACKUP_DIR" "s3://your-bucket-name/commandcenter-backups/" \
#         --exclude "*" \
#         --include "postgres/*_${TIMESTAMP}.sql.gz" \
#         --include "rag/*_${TIMESTAMP}.tar.gz" \
#         --include "redis/*_${TIMESTAMP}.rdb.gz"
#     log "S3 upload completed"
# fi

# Example for Google Cloud Storage:
# if command -v gsutil &> /dev/null; then
#     log "Uploading backups to Google Cloud Storage..."
#     gsutil -m rsync -r "$BACKUP_DIR" "gs://your-bucket-name/commandcenter-backups/"
#     log "GCS upload completed"
# fi

exit 0
