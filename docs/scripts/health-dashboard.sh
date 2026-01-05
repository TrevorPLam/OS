#!/usr/bin/env bash
# scripts/health-dashboard.sh - Generate governance health metrics
set -euo pipefail

echo "[health-dashboard] Generating governance health metrics..."

# Check if GOVERNANCE_HEALTH.md exists
if [[ ! -f "docs/GOVERNANCE_HEALTH.md" ]]; then
    echo "[health-dashboard] WARNING: docs/GOVERNANCE_HEALTH.md not found"
    exit 1
fi

# Parse GOVERNANCE_HEALTH.md and calculate metrics
python3 -c "
import re
from datetime import datetime, timedelta
from collections import Counter

# Read governance health log
with open('docs/GOVERNANCE_HEALTH.md', 'r') as f:
    content = f.read()

# Extract entries
entries = re.findall(r'### (\\d{4}-\\d{2}-\\d{2}) — ([^\\n]+).*?Severity: (low|medium|high|critical).*?Detected By: ([^\\n]+)', content, re.DOTALL)

violations = []
detection_methods = []
severities = []

for date, title, severity, detected_by in entries:
    violations.append({
        'date': datetime.strptime(date, '%Y-%m-%d'),
        'title': title.strip(),
        'severity': severity,
        'detected_by': detected_by.strip()
    })
    detection_methods.append(detected_by.strip())
    severities.append(severity)

# Calculate metrics
now = datetime.now()
week_ago = now - timedelta(days=7)

# Violations this week
this_week_violations = [v for v in violations if v['date'] >= week_ago]
violations_this_week = len(this_week_violations)

# Most common violation type
severity_counts = Counter(severities)
most_common_severity = severity_counts.most_common(1)[0][0] if severity_counts else 'none'

# Detection method effectiveness
detection_counts = Counter(detection_methods)
most_effective_detection = detection_counts.most_common(1)[0][0] if detection_counts else 'none'

# Trend calculation (compare last 7 days vs previous 7 days)
two_weeks_ago = now - timedelta(days=14)
last_week = [v for v in violations if week_ago <= v['date'] < now]
previous_week = [v for v in violations if two_weeks_ago <= v['date'] < week_ago]

last_week_count = len(last_week)
previous_week_count = len(previous_week)

if previous_week_count == 0:
    trend = '↑ Increasing' if last_week_count > 0 else '→ Stable'
elif last_week_count < previous_week_count:
    trend = '↓ Decreasing'
elif last_week_count > previous_week_count:
    trend = '↑ Increasing'
else:
    trend = '→ Stable'

# Generate metrics section
metrics = f'''\n
---\n
📊 Health Metrics (Auto-Generated {now.strftime('%Y-%m-%d %H:%M')})\n\n• Violations this week: {violations_this_week}\n• Most common severity: {most_common_severity}\n• Trend: {trend} (was {previous_week_count} last week)\n• Top detection method: {most_effective_detection}\n• Total violations recorded: {len(violations)}\n\n### Violation Categories\n\n| Category | Count | Percentage |\n|----------|-------|------------|\n| Naming convention | {severities.count('low')} | {severities.count('low')/len(severities)*100:.1f}% |\n| Security | {severities.count('medium')} | {severities.count('medium')/len(severities)*100:.1f}% |\n| Coupling | {severities.count('high')} | {severities.count('high')/len(severities)*100:.1f}% |\n| Critical | {severities.count('critical')} | {severities.count('critical')/len(severities)*100:.1f}% |\n\n### Prevention Effectiveness\n\n| Detection Method | Violations Caught | Effectiveness |\n|------------------|-------------------|---------------|\n| Pre-commit hooks | {detection_counts.get('pre-commit', 0)} | {detection_counts.get('pre-commit', 0)/len(violations)*100:.1f}% |\n| ai-audit | {detection_counts.get('ai-audit', 0)} | {detection_counts.get('ai-audit', 0)/len(violations)*100:.1f}% |\n| CI | {detection_counts.get('CI', 0)} | {detection_counts.get('CI', 0)/len(violations)*100:.1f}% |\n| Reviewer | {detection_counts.get('reviewer', 0)} | {detection_counts.get('reviewer', 0)/len(violations)*100:.1f}% |\n'''

# Append metrics to GOVERNANCE_HEALTH.md
with open('docs/GOVERNANCE_HEALTH.md', 'r') as f:
    health_content = f.read()

# Remove existing metrics section if present
health_content = re.sub(r'\\n---\\n\\n📊 Health Metrics.*', '', health_content, flags=re.DOTALL)

# Add new metrics
with open('docs/GOVERNANCE_HEALTH.md', 'w') as f:
    f.write(health_content + metrics)

print(f'[health-dashboard] ✅ Health metrics updated in docs/GOVERNANCE_HEALTH.md')
print(f'[health-dashboard] Violations this week: {violations_this_week}')
print(f'[health-dashboard] Trend: {trend}')
"

echo "[health-dashboard] Health dashboard generation complete"