#!/bin/bash
#
# Cron script for checking and sending stale deal reminders (DEAL-6)
#
# Add to crontab:
# # Check for stale deals and send reminders daily at 9 AM
# 0 9 * * * /path/to/repo/scripts/check_stale_deals.sh >> /var/log/stale_deals.log 2>&1
#

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root
cd "$PROJECT_ROOT/src" || exit 1

# Activate virtual environment if it exists
if [ -f "../venv/bin/activate" ]; then
    source "../venv/bin/activate"
fi

# Set DJANGO_SETTINGS_MODULE if not already set
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings}"

# Step 1: Check and mark stale deals
echo "[$(date)] Checking for stale deals..."
python manage.py shell -c "
from modules.crm.deal_rotting_alerts import check_and_mark_stale_deals
marked = check_and_mark_stale_deals()
print(f'Marked {marked} deals as stale')
"

# Step 2: Send reminders (remove --dry-run in production)
echo "[$(date)] Sending stale deal reminders..."
python manage.py send_stale_deal_reminders --dry-run

echo "[$(date)] Stale deal check completed"
