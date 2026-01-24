#!/usr/bin/env node
/**
 * check-changelog-and-logs.js
 * Hard block commit if changelog or logs are missing when required
 *
 * Exit codes:
 * - 0: All checks passed
 * - 1: Hard failure (changelog or logs missing)
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const RED = "\x1b[31m";
const GREEN = "\x1b[32m";
const YELLOW = "\x1b[33m";
const RESET = "\x1b[0m";

let hasErrors = false;

function logError(msg) {
  console.error(`${RED}❌ ERROR: ${msg}${RESET}`);
  hasErrors = true;
}

function logSuccess(msg) {
  console.log(`${GREEN}✅ ${msg}${RESET}`);
}

function logInfo(msg) {
  console.log(`${YELLOW}ℹ️  ${msg}${RESET}`);
}

/**
 * Get list of staged files
 */
function getStagedFiles() {
  try {
    const output = execSync("git diff --cached --name-only", {
      encoding: "utf8",
    });
    return output
      .trim()
      .split("\n")
      .filter((f) => f.length > 0);
  } catch (err) {
    return [];
  }
}

/**
 * Determine change type from staged files
 * Returns: 'feature' | 'api_change' | 'security' | 'cross_module' | 'non_doc_change' | 'doc_only' | null
 */
function determineChangeType(stagedFiles) {
  const files = stagedFiles.join(" ").toLowerCase();

  // Security triggers
  if (
    files.includes("auth") ||
    files.includes("security") ||
    files.includes("payment") ||
    files.includes("credential") ||
    files.includes("secret") ||
    files.match(/apps\/api.*(auth|security|payment)/)
  ) {
    return "security";
  }

  // API changes
  if (
    files.includes("packages/contracts") ||
    files.includes("apps/api/routes") ||
    files.includes("openapi") ||
    files.includes("api/endpoint")
  ) {
    return "api_change";
  }

  // Cross-module (check for imports across modules)
  // This is harder to detect from file paths alone, but we can check for shared/utilities
  if (
    files.includes("packages/shared") ||
    files.includes("packages/utilities") ||
    (files.includes("apps/mobile") && files.includes("apps/api"))
  ) {
    return "cross_module";
  }

  // Features (user-facing changes)
  if (
    files.includes("apps/mobile/screens") ||
    files.includes("apps/mobile/components") ||
    files.includes("apps/mobile/hooks") ||
    files.match(/apps\/mobile.*(screen|component|hook)/)
  ) {
    return "feature";
  }

  // Check if only docs
  const nonDocFiles = stagedFiles.filter(
    (f) =>
      !f.includes("docs/") &&
      !f.includes(".md") &&
      !f.includes(".repo/") &&
      !f.includes("CHANGELOG.md") &&
      !f.includes("README.md"),
  );

  if (nonDocFiles.length === 0) {
    return "doc_only";
  }

  // Default to non_doc_change for other code changes
  return "non_doc_change";
}

/**
 * Check if CHANGELOG.md was modified in this commit
 */
function checkChangelogUpdated() {
  try {
    const stagedFiles = getStagedFiles();
    return stagedFiles.includes("CHANGELOG.md");
  } catch (err) {
    return false;
  }
}

/**
 * Check if trace log exists for this change
 * Looks for trace logs in .repo/traces/ that might be related
 */
function checkTraceLogExists() {
  try {
    // Get current branch or commit message to infer task ID
    let taskId = null;
    try {
      const branch = execSync("git rev-parse --abbrev-ref HEAD", {
        encoding: "utf8",
      }).trim();
      const taskMatch = branch.match(/TASK-(\d+)/i);
      if (taskMatch) {
        taskId = `TASK-${taskMatch[1]}`;
      }
    } catch (err) {
      // No branch info
    }

    // Check if any trace logs exist in staged files
    const stagedFiles = getStagedFiles();
    const hasTraceLog = stagedFiles.some(
      (f) => f.includes(".repo/traces/") && f.endsWith(".json"),
    );

    if (hasTraceLog) {
      return true;
    }

    // Check if trace log directory has recent files
    const tracesDir = ".repo/traces";
    if (fs.existsSync(tracesDir)) {
      const files = fs
        .readdirSync(tracesDir)
        .filter((f) => f.endsWith(".json"));
      if (taskId) {
        // Check for task-specific trace log
        const taskTrace = files.find((f) => f.includes(taskId));
        if (taskTrace) {
          return true;
        }
      }
      // If trace logs exist but none for this task, warn
      if (files.length > 0) {
        logInfo(
          `Trace logs exist but none found for current task. Consider creating one.`,
        );
      }
    }

    return false;
  } catch (err) {
    return false;
  }
}

/**
 * Check if agent log exists for this change
 */
function checkAgentLogExists() {
  try {
    // Check if any agent logs exist in staged files
    const stagedFiles = getStagedFiles();
    const hasAgentLog = stagedFiles.some(
      (f) => f.includes(".repo/logs/") && f.endsWith(".json"),
    );

    if (hasAgentLog) {
      return true;
    }

    // Check if agent log directory has recent files
    const logsDir = ".repo/logs";
    if (fs.existsSync(logsDir)) {
      const files = fs.readdirSync(logsDir).filter((f) => f.endsWith(".json"));
      if (files.length > 0) {
        logInfo(
          `Agent logs exist but none found for current change. Consider creating one.`,
        );
      }
    }

    return false;
  } catch (err) {
    return false;
  }
}

/**
 * Check user-facing file patterns
 */
function isUserFacingChange(stagedFiles) {
  const userFacingPatterns = [
    /^apps\/mobile\//,
    /^apps\/api\/routes\//,
    /^packages\/contracts\//,
  ];

  const internalPatterns = [
    /\.test\./,
    /\.spec\./,
    /^\.repo\//,
    /^docs\/(development|architecture)/,
  ];

  for (const file of stagedFiles) {
    // Skip internal files
    if (internalPatterns.some((p) => p.test(file))) {
      continue;
    }

    // Check if user-facing
    if (userFacingPatterns.some((p) => p.test(file))) {
      return true;
    }
  }

  return false;
}

/**
 * Main check function
 */
function main() {
  console.log("\n🔍 Checking changelog and logs...\n");

  const stagedFiles = getStagedFiles();

  if (stagedFiles.length === 0) {
    logInfo("No staged files. Skipping checks.");
    process.exit(0);
  }

  // Determine change type
  const changeType = determineChangeType(stagedFiles);
  logInfo(`Detected change type: ${changeType || "unknown"}`);

  // Check changelog requirements
  const requiresChangelog = ["feature", "api_change", "security"].includes(
    changeType,
  );
  const isUserFacing = isUserFacingChange(stagedFiles);

  if (requiresChangelog || (changeType === "cross_module" && isUserFacing)) {
    const changelogUpdated = checkChangelogUpdated();
    if (!changelogUpdated) {
      logError(
        `CHANGELOG.md must be updated for ${changeType} changes.\n` +
          `  Please add an entry to CHANGELOG.md describing the change.`,
      );
    } else {
      logSuccess("CHANGELOG.md updated");
    }
  } else {
    logInfo("CHANGELOG.md update not required for this change type");
  }

  // Check log requirements (for non-doc changes)
  if (changeType && changeType !== "doc_only") {
    const traceLogExists = checkTraceLogExists();
    const agentLogExists = checkAgentLogExists();

    // Per procedures.json: non_doc_change requires both trace log and agent log
    // Other change types may require trace log
    if (changeType === "non_doc_change") {
      if (!traceLogExists) {
        logError(
          `Trace log required for non_doc_change.\n` +
            `  Create a trace log in .repo/traces/ following AGENT_TRACE_SCHEMA.json`,
        );
      } else {
        logSuccess("Trace log found");
      }

      if (!agentLogExists) {
        logError(
          `Agent log required for non_doc_change.\n` +
            `  Create an agent log in .repo/logs/ following AGENT_LOG_TEMPLATE.md`,
        );
      } else {
        logSuccess("Agent log found");
      }
    } else if (
      ["feature", "api_change", "security", "cross_module"].includes(changeType)
    ) {
      // These change types require trace log
      if (!traceLogExists) {
        logError(
          `Trace log required for ${changeType} changes.\n` +
            `  Create a trace log in .repo/traces/ following AGENT_TRACE_SCHEMA.json`,
        );
      } else {
        logSuccess("Trace log found");
      }
    }
  } else {
    logInfo("Logs not required for doc-only changes");
  }

  // Final result
  console.log("");
  if (hasErrors) {
    console.error(
      `${RED}❌ Commit blocked: Missing required changelog or logs${RESET}\n`,
    );
    console.error("To bypass (not recommended): git commit --no-verify");
    process.exit(1);
  } else {
    logSuccess("All checks passed. Proceeding with commit.");
    process.exit(0);
  }
}

// Run checks
main();
