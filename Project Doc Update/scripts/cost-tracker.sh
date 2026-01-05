#!/usr/bin/env bash
# scripts/cost-tracker.sh - Track AI session costs
set -euo pipefail

echo "[cost-tracker] Starting cost calculation..."

# Constants
CLAUDE_RATE=0.000003  # $3 per million tokens
COPILOT_MONTHLY=10.00  # $10/month flat rate

# Cost tracking file
COST_FILE=".ai-cost-tracker.json"

# Initialize cost file if it doesn't exist
if [[ ! -f "$COST_FILE" ]]; then
    echo "[cost-tracker] Initializing cost tracking file..."
    cat > "$COST_FILE" << 'EOF'
{
  "rolling_30_day_total": 0.0,
  "sessions": [],
  "monthly_budget": 100.0,
  "alert_threshold": 10.0
}
EOF
fi

# Parse PROJECT_STATUS.md YAML header
if [[ ! -f "PROJECT_STATUS.md" ]]; then
    echo "[cost-tracker] ERROR: PROJECT_STATUS.md not found"
    exit 1
fi

# Extract tokens_this_session using Python
TOKENS=$(python3 -c "
import yaml
import re

with open('PROJECT_STATUS.md', 'r') as f:
    content = f.read()

# Extract YAML frontmatter
match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
if match:
    yaml_content = match.group(1)
    data = yaml.safe_load(yaml_content)
    print(data.get('tokens_this_session', 0))
else:
    print(0)
")

# Calculate session cost
SESSION_COST=$(echo "$TOKENS * $CLAUDE_RATE" | bc -l 2>/dev/null || echo "0")
SESSION_COST=$(printf "%.2f" "$SESSION_COST")

echo "[cost-tracker] Session tokens: $TOKENS"
echo "[cost-tracker] Session cost: \$$SESSION_COST"

# Update PROJECT_STATUS.md with new cost
python3 -c "
import yaml
import re
from datetime import datetime

with open('PROJECT_STATUS.md', 'r') as f:
    content = f.read()

# Extract YAML frontmatter
match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
if match:
    yaml_content = match.group(1)
    rest_content = match.group(2)
    
    data = yaml.safe_load(yaml_content)
    
    # Update fields
    data['session_cost_usd'] = float('$SESSION_COST')
    data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Calculate budget remaining
    monthly_budget = 100.0  # Default monthly budget
    total_spent = data.get('total_spent_this_month', 0) + float('$SESSION_COST')
    data['total_spent_this_month'] = total_spent
    
    budget_remaining = ((monthly_budget - total_spent) / monthly_budget) * 100
    data['budget_estimate_remaining'] = f'{max(0, budget_remaining):.0f}%'
    
    # Write back to file
    new_yaml = '---\n' + yaml.dump(data, default_flow_style=False, sort_keys=False) + '---\n'
    
    with open('PROJECT_STATUS.md', 'w') as f:
        f.write(new_yaml + rest_content)
    
    print(f'[cost-tracker] Updated PROJECT_STATUS.md: ${SESSION_COST} spent, {data[\"budget_estimate_remaining\"]} remaining')
else:
    print('[cost-tracker] ERROR: Could not parse PROJECT_STATUS.md')
"

# Update rolling cost tracker
python3 -c "
import json
from datetime import datetime, timedelta

# Load cost file
with open('$COST_FILE', 'r') as f:
    tracker = json.load(f)

# Add current session
session_data = {
    'date': datetime.utcnow().isoformat(),
    'tokens': $TOKENS,
    'cost': float('$SESSION_COST'),
    'agent': 'claude-code-v4'
}

tracker['sessions'].append(session_data)

# Remove sessions older than 30 days
cutoff_date = datetime.utcnow() - timedelta(days=30)
tracker['sessions'] = [
    s for s in tracker['sessions'] 
    if datetime.fromisoformat(s['date'].replace('Z', '+00:00')) > cutoff_date
]

# Calculate rolling total
tracker['rolling_30_day_total'] = sum(s['cost'] for s in tracker['sessions'])

# Save updated tracker
with open('$COST_FILE', 'w') as f:
    json.dump(tracker, f, indent=2)

print(f'[cost-tracker] Updated $COST_FILE: 30-day total = ${tracker[\"rolling_30_day_total\"]:.2f}')

# Check alert threshold
if tracker['rolling_30_day_total'] > tracker['alert_threshold']:
    print(f'[cost-tracker] ⚠️  ALERT: 30-day spending (${tracker[\"rolling_30_day_total\"]:.2f}) exceeds threshold')
"

echo "[cost-tracker] Cost tracking complete"