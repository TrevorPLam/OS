#!/usr/bin/env node
// /.repo/automation/scripts/agent-logger.js
// Agent interaction logging SDK
// Usage: const logger = require('./agent-logger.js');

const fs = require("fs");
const path = require("path");

// Get repo root (assumes script is in .repo/automation/scripts/)
const REPO_ROOT = path.resolve(__dirname, "../../..");
const LOGS_DIR = path.join(REPO_ROOT, ".agent-logs");
const INTERACTIONS_DIR = path.join(LOGS_DIR, "interactions");
const ERRORS_DIR = path.join(LOGS_DIR, "errors");
const METRICS_DIR = path.join(LOGS_DIR, "metrics");

// Ensure directories exist
[INTERACTIONS_DIR, ERRORS_DIR, METRICS_DIR].forEach((dir) => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

/**
 * Log an agent interaction
 * @param {Object} entry - Log entry object
 * @param {string} entry.agent - Agent name (e.g., "Auto")
 * @param {string} entry.action - Action performed (e.g., "read_file", "search_replace")
 * @param {string} [entry.file] - File path (relative to repo root)
 * @param {number} [entry.duration_ms] - Duration in milliseconds
 * @param {boolean} entry.success - Whether action succeeded
 * @param {Object} [entry.context] - Additional context (task, folder, etc.)
 * @param {string} [entry.error] - Error message if failed
 */
function logInteraction(entry) {
  const timestamp = new Date().toISOString();
  const logEntry = {
    timestamp,
    agent: entry.agent || "Auto",
    action: entry.action,
    file: entry.file || null,
    duration_ms: entry.duration_ms || null,
    success: entry.success !== undefined ? entry.success : true,
    context: entry.context || {},
    ...(entry.error && { error: entry.error }),
  };

  // Write to interactions log (JSONL format)
  const today = new Date().toISOString().split("T")[0];
  const logFile = path.join(INTERACTIONS_DIR, `${today}.jsonl`);

  try {
    fs.appendFileSync(logFile, JSON.stringify(logEntry) + "\n", "utf8");
  } catch (err) {
    // Graceful degradation: log to stderr but don't throw
    // This ensures workflow continues even if logging fails
    console.error(`[WARNING] Failed to write interaction log: ${err.message}`);
    // Try to log error (but don't fail if this also fails)
    try {
      logError({
        agent: entry.agent || "Auto",
        action: "log_interaction",
        error: `Failed to write interaction log: ${err.message}`,
        context: { original_entry: logEntry },
      });
    } catch {
      // If error logging also fails, just continue
    }
  }
}

/**
 * Log an error
 * @param {Object} entry - Error log entry
 * @param {string} entry.agent - Agent name
 * @param {string} entry.action - Action that failed
 * @param {string} entry.error - Error message
 * @param {Object} [entry.context] - Additional context
 */
function logError(entry) {
  const timestamp = new Date().toISOString();
  const errorEntry = {
    timestamp,
    agent: entry.agent || "Auto",
    action: entry.action || "unknown",
    error: entry.error,
    context: entry.context || {},
  };

  // Write to errors log
  const today = new Date().toISOString().split("T")[0];
  const errorFile = path.join(ERRORS_DIR, `${today}.jsonl`);

  try {
    fs.appendFileSync(errorFile, JSON.stringify(errorEntry) + "\n", "utf8");
  } catch (err) {
    // Last resort: write to stderr
    console.error(`CRITICAL: Failed to write error log: ${err.message}`);
    console.error(`Original error: ${JSON.stringify(errorEntry)}`);
  }
}

/**
 * Generate daily metrics from interaction logs
 * @param {string} [date] - Date in YYYY-MM-DD format (defaults to today)
 * @returns {Object} Metrics object
 */
function generateMetrics(date) {
  const targetDate = date || new Date().toISOString().split("T")[0];
  const logFile = path.join(INTERACTIONS_DIR, `${targetDate}.jsonl`);

  if (!fs.existsSync(logFile)) {
    return {
      date: targetDate,
      total_interactions: 0,
      successful: 0,
      failed: 0,
      success_rate: 0,
      avg_duration_ms: 0,
      actions: {},
      errors: [],
    };
  }

  const lines = fs
    .readFileSync(logFile, "utf8")
    .split("\n")
    .filter((line) => line.trim());

  const entries = lines
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    })
    .filter((entry) => entry !== null);

  const metrics = {
    date: targetDate,
    total_interactions: entries.length,
    successful: 0,
    failed: 0,
    success_rate: 0,
    total_duration_ms: 0,
    avg_duration_ms: 0,
    actions: {},
    errors: [],
  };

  entries.forEach((entry) => {
    if (entry.success) {
      metrics.successful++;
    } else {
      metrics.failed++;
      if (entry.error) {
        metrics.errors.push({
          action: entry.action,
          error: entry.error,
          file: entry.file,
        });
      }
    }

    if (entry.duration_ms) {
      metrics.total_duration_ms += entry.duration_ms;
    }

    if (!metrics.actions[entry.action]) {
      metrics.actions[entry.action] = {
        count: 0,
        successful: 0,
        failed: 0,
        total_duration_ms: 0,
      };
    }
    metrics.actions[entry.action].count++;
    if (entry.success) {
      metrics.actions[entry.action].successful++;
    } else {
      metrics.actions[entry.action].failed++;
    }
    if (entry.duration_ms) {
      metrics.actions[entry.action].total_duration_ms += entry.duration_ms;
    }
  });

  if (metrics.total_interactions > 0) {
    metrics.success_rate = metrics.successful / metrics.total_interactions;
    metrics.avg_duration_ms =
      metrics.total_duration_ms / metrics.total_interactions;
  }

  // Calculate averages for each action
  Object.keys(metrics.actions).forEach((action) => {
    const actionData = metrics.actions[action];
    if (actionData.count > 0) {
      actionData.avg_duration_ms =
        actionData.total_duration_ms / actionData.count;
      actionData.success_rate = actionData.successful / actionData.count;
    }
  });

  return metrics;
}

/**
 * Write metrics to file
 * @param {string} [date] - Date in YYYY-MM-DD format (defaults to today)
 */
function writeMetrics(date) {
  const targetDate = date || new Date().toISOString().split("T")[0];
  const metrics = generateMetrics(targetDate);
  const metricsFile = path.join(METRICS_DIR, `${targetDate}.json`);

  try {
    fs.writeFileSync(metricsFile, JSON.stringify(metrics, null, 2), "utf8");
    return metrics;
  } catch (err) {
    console.error(`Failed to write metrics: ${err.message}`);
    return null;
  }
}

/**
 * Clean up old logs (keep last N days)
 * @param {number} daysToKeep - Number of days to keep (default: 30)
 */
function cleanupOldLogs(daysToKeep = 30) {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);

  [INTERACTIONS_DIR, ERRORS_DIR, METRICS_DIR].forEach((dir) => {
    if (!fs.existsSync(dir)) return;

    const files = fs.readdirSync(dir);
    files.forEach((file) => {
      const filePath = path.join(dir, file);
      const stats = fs.statSync(filePath);
      if (stats.mtime < cutoffDate) {
        try {
          fs.unlinkSync(filePath);
        } catch (err) {
          console.error(
            `Failed to delete old log file ${filePath}: ${err.message}`,
          );
        }
      }
    });
  });
}

// CLI usage
if (require.main === module) {
  const command = process.argv[2];

  if (command === "metrics") {
    const date = process.argv[3];
    const metrics = writeMetrics(date);
    if (metrics) {
      console.log(JSON.stringify(metrics, null, 2));
    }
  } else if (command === "cleanup") {
    const days = parseInt(process.argv[3]) || 30;
    cleanupOldLogs(days);
    console.log(`Cleaned up logs older than ${days} days`);
  } else {
    console.log("Usage:");
    console.log(
      "  node agent-logger.js metrics [date]  - Generate and write metrics",
    );
    console.log(
      "  node agent-logger.js cleanup [days] - Clean up old logs (default: 30 days)",
    );
  }
}

// Export for use as module
module.exports = {
  logInteraction,
  logError,
  generateMetrics,
  writeMetrics,
  cleanupOldLogs,
};
