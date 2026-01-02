#!/bin/bash
# Active Directory Synchronization Cron Script
#
# AD-4: Scheduled synchronization script for cron jobs.
#
# Add to crontab for scheduled AD sync:
#
# Hourly sync (every hour at minute 5):
# 5 * * * * /path/to/sync_ad_cron.sh hourly
#
# Daily sync (every day at 2 AM):
# 0 2 * * * /path/to/sync_ad_cron.sh daily
#
# Weekly sync (every Sunday at 3 AM):
# 0 3 * * 0 /path/to/sync_ad_cron.sh weekly

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
MANAGE_PY="$PROJECT_DIR/src/manage.py"

# Sync schedule (default: scheduled)
SYNC_SCHEDULE="${1:-scheduled}"

# Log file
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/ad_sync_$(date +%Y%m%d).log"

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if Django settings are configured
if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    export DJANGO_SETTINGS_MODULE="config.settings"
fi

log "Starting AD sync ($SYNC_SCHEDULE schedule)"

# Activate virtual environment if it exists
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    log "Activating virtual environment"
    source "$PROJECT_DIR/.venv/bin/activate"
fi

# Run AD sync
log "Running: python $MANAGE_PY sync_ad"

if python "$MANAGE_PY" sync_ad >> "$LOG_FILE" 2>&1; then
    log "AD sync completed successfully"
    exit 0
else
    log "ERROR: AD sync failed"
    exit 1
fi
