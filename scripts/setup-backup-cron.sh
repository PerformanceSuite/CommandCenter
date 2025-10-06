#!/bin/bash

################################################################################
# Setup Automated Backup Cron Job
#
# This script sets up a daily cron job for automated backups
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "Error: Backup script not found at $BACKUP_SCRIPT"
    exit 1
fi

# Default: Run daily at 2 AM
CRON_SCHEDULE="${BACKUP_CRON_SCHEDULE:-0 2 * * *}"

echo "Setting up automated backup cron job..."
echo "Schedule: $CRON_SCHEDULE (daily at 2 AM by default)"
echo "Script: $BACKUP_SCRIPT"

# Create cron job
CRON_JOB="$CRON_SCHEDULE $BACKUP_SCRIPT >> /var/log/commandcenter-backup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo "Cron job already exists. Updating..."
    (crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT"; echo "$CRON_JOB") | crontab -
else
    echo "Adding new cron job..."
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
fi

echo "Cron job setup completed!"
echo ""
echo "Current crontab:"
crontab -l | grep "$BACKUP_SCRIPT"

echo ""
echo "To view backup logs: tail -f /var/log/commandcenter-backup.log"
echo "To manually run backup: $BACKUP_SCRIPT"

exit 0
