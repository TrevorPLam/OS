#!/bin/bash
# generate-dashboard.sh
# Generates an HTML dashboard from metrics
#
# Usage: ./scripts/generate-dashboard.sh [output-file]
#   output-file: Path to HTML file (default: .repo/dashboard.html)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OUTPUT_FILE="${1:-.repo/dashboard.html}"

# Generate metrics in JSON format
METRICS_JSON=$(./scripts/generate-metrics.sh json)

# Extract values (using basic parsing since we control the format)
TODAY=$(date +%Y-%m-%d)

# Create HTML dashboard
cat > "$OUTPUT_FILE" <<'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Governance Framework Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #7f8c8d;
            font-size: 14px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #2c3e50;
            font-size: 18px;
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #ecf0f1;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-label {
            color: #7f8c8d;
        }
        .metric-value {
            font-weight: bold;
            color: #2c3e50;
        }
        .metric-value.high {
            color: #27ae60;
        }
        .metric-value.medium {
            color: #f39c12;
        }
        .metric-value.low {
            color: #e74c3c;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            transition: width 0.3s ease;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-pending {
            background: #fff3cd;
            color: #856404;
        }
        .status-completed {
            background: #d4edda;
            color: #155724;
        }
        .status-active {
            background: #d1ecf1;
            color: #0c5460;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 12px;
        }
        .refresh-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 10px;
        }
        .refresh-btn:hover {
            background: #2980b9;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Governance Framework Dashboard</h1>
            <div class="subtitle">Generated: <span id="timestamp"></span></div>
            <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
        </header>

        <div class="grid">
            <div class="card">
                <h2>📋 Tasks</h2>
                <div class="metric">
                    <span class="metric-label">Active (TODO)</span>
                    <span class="metric-value" id="todo-count">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Backlog</span>
                    <span class="metric-value" id="backlog-count">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Archived</span>
                    <span class="metric-value" id="archive-count">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total</span>
                    <span class="metric-value high" id="total-tasks">-</span>
                </div>
            </div>

            <div class="card">
                <h2>🎯 Backlog by Priority</h2>
                <div class="metric">
                    <span class="metric-label">P0 (Critical)</span>
                    <span class="metric-value low" id="p0-count">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">P1 (High)</span>
                    <span class="metric-value medium" id="p1-count">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">P2 (Medium)</span>
                    <span class="metric-value" id="p2-count">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">P3 (Low)</span>
                    <span class="metric-value" id="p3-count">-</span>
                </div>
            </div>

            <div class="card">
                <h2>👤 HITL Items</h2>
                <div class="metric">
                    <span class="metric-label">Active</span>
                    <span class="metric-value" id="hitl-active">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Pending</span>
                    <span class="metric-value medium" id="hitl-pending">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Completed</span>
                    <span class="metric-value high" id="hitl-completed">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Files</span>
                    <span class="metric-value" id="hitl-total">-</span>
                </div>
            </div>

            <div class="card">
                <h2>📝 Waivers</h2>
                <div class="metric">
                    <span class="metric-label">Active</span>
                    <span class="metric-value" id="waiver-active">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Expired</span>
                    <span class="metric-value low" id="waiver-expired">-</span>
                </div>
            </div>

            <div class="card">
                <h2>📦 Artifacts</h2>
                <div class="metric">
                    <span class="metric-label">Trace Logs</span>
                    <span class="metric-value" id="trace-count">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Agent Logs</span>
                    <span class="metric-value" id="log-count">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">ADRs</span>
                    <span class="metric-value" id="adr-count">-</span>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Dashboard generated by governance framework | Run <code>./scripts/generate-dashboard.sh</code> to regenerate</p>
        </div>
    </div>

    <script>
        // Parse metrics JSON and populate dashboard
        const metrics = JSON.parse(`METRICS_PLACEHOLDER`);

        // Update timestamp
        document.getElementById('timestamp').textContent = metrics.date || new Date().toLocaleString();

        // Tasks
        document.getElementById('todo-count').textContent = metrics.tasks.todo || 0;
        document.getElementById('backlog-count').textContent = metrics.tasks.backlog || 0;
        document.getElementById('archive-count').textContent = metrics.tasks.archive || 0;
        document.getElementById('total-tasks').textContent =
            (metrics.tasks.todo || 0) + (metrics.tasks.backlog || 0) + (metrics.tasks.archive || 0);

        // Priorities
        document.getElementById('p0-count').textContent = metrics.tasks.by_priority.p0 || 0;
        document.getElementById('p1-count').textContent = metrics.tasks.by_priority.p1 || 0;
        document.getElementById('p2-count').textContent = metrics.tasks.by_priority.p2 || 0;
        document.getElementById('p3-count').textContent = metrics.tasks.by_priority.p3 || 0;

        // HITL
        document.getElementById('hitl-active').textContent = metrics.hitl.active || 0;
        document.getElementById('hitl-pending').textContent = metrics.hitl.pending || 0;
        document.getElementById('hitl-completed').textContent = metrics.hitl.completed || 0;
        document.getElementById('hitl-total').textContent = metrics.hitl.total || 0;

        // Waivers
        document.getElementById('waiver-active').textContent = metrics.waivers.active || 0;
        document.getElementById('waiver-expired').textContent = metrics.waivers.expired || 0;

        // Artifacts
        document.getElementById('trace-count').textContent = metrics.artifacts.trace_logs || 0;
        document.getElementById('log-count').textContent = metrics.artifacts.agent_logs || 0;
        document.getElementById('adr-count').textContent = metrics.artifacts.adrs || 0;
    </script>
</body>
</html>
EOF

# Replace placeholder with actual JSON
# Use Python for safe JSON embedding
python3 <<PYTHON_SCRIPT
import json
import re

metrics_json = '''$METRICS_JSON'''

# Read the HTML file
with open('$OUTPUT_FILE', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Escape JSON for JavaScript
escaped_json = json.dumps(json.loads(metrics_json))

# Replace placeholder
html_content = html_content.replace('METRICS_PLACEHOLDER', escaped_json)

# Write back
with open('$OUTPUT_FILE', 'w', encoding='utf-8') as f:
    f.write(html_content)
PYTHON_SCRIPT

echo "✅ Dashboard generated: $OUTPUT_FILE"
echo "Open in browser: file://$(realpath "$OUTPUT_FILE")"
