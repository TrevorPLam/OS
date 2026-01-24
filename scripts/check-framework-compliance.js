#!/usr/bin/env node

/**
 * Framework Compliance Checker
 *
 * Checks if PRs and changes comply with the governance framework requirements.
 * This enforces framework usage and ensures agents are following the rules.
 *
 * Usage:
 *   node .repo/automation/scripts/check-framework-compliance.js \
 *     [--base-ref <ref>] \
 *     [--pr-body <path>] \
 *     [--trace-log <path>]
 *
 * Exit codes:
 *   0 - Compliant
 *   1 - Non-compliant (hard failure)
 *   2 - Warnings (waiverable)
 */

import { readFileSync, existsSync, readdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const REPO_ROOT = join(__dirname, "../../../..");
const HITL_INDEX_PATH = join(REPO_ROOT, ".repo/policy/HITL.md");
const TRACES_DIR = join(REPO_ROOT, ".repo/traces");

// Parse command line arguments
const args = process.argv.slice(2);
let baseRef = "HEAD";
let prBodyPath = null;
let traceLogPath = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--base-ref" && i + 1 < args.length) {
    baseRef = args[i + 1];
    i++;
  } else if (args[i] === "--pr-body" && i + 1 < args.length) {
    prBodyPath = args[i + 1];
    i++;
  } else if (args[i] === "--trace-log" && i + 1 < args.length) {
    traceLogPath = args[i + 1];
    i++;
  }
}

// Get changed files from git
function getChangedFiles(baseRef = "HEAD") {
  try {
    const command = `git diff --name-only ${baseRef} HEAD 2>/dev/null || git diff --name-only origin/${baseRef}...HEAD 2>/dev/null || echo ""`;
    const output = execSync(command, {
      cwd: REPO_ROOT,
      encoding: "utf-8",
    }).trim();
    if (output) {
      return output.split("\n").filter((f) => f.trim());
    }
  } catch (error) {
    // Git not available or not a git repo
  }
  return [];
}

// Check if change requires HITL
function requiresHITL(changedFiles) {
  const securityKeywords = [
    "auth",
    "login",
    "password",
    "credential",
    "token",
    "secret",
    "key",
    "payment",
    "billing",
    "money",
    "charge",
    "subscription",
    "production",
    "deploy",
    "release",
    "schema",
    "migration",
    "oauth",
    "api-key",
    "bearer",
  ];

  const fileContent = changedFiles
    .map((f) => {
      try {
        if (existsSync(join(REPO_ROOT, f))) {
          return readFileSync(join(REPO_ROOT, f), "utf-8").toLowerCase();
        }
      } catch (e) {
        // File might not exist or be binary
      }
      return "";
    })
    .join(" ");

  const fileName = changedFiles.join(" ").toLowerCase();

  for (const keyword of securityKeywords) {
    if (fileContent.includes(keyword) || fileName.includes(keyword)) {
      return true;
    }
  }

  // Check for security trigger file patterns
  const securityPatterns = [
    /\.env/i,
    /config.*production/i,
    /secrets?/i,
    /credentials?/i,
  ];

  for (const pattern of securityPatterns) {
    if (pattern.test(fileName)) {
      return true;
    }
  }

  return false;
}

// Check if HITL items are created when required
function checkHITLCompliance(changedFiles) {
  const errors = [];
  const warnings = [];

  if (requiresHITL(changedFiles)) {
    // Check if HITL index exists and has active items
    if (!existsSync(HITL_INDEX_PATH)) {
      errors.push("HITL required but HITL index not found");
      return { compliant: false, errors, warnings };
    }

    const hitlContent = readFileSync(HITL_INDEX_PATH, "utf-8");

    // Check for active HITL items
    const activeTableMatch = hitlContent.match(/### Active[\s\S]*?(\n###|$)/);
    if (activeTableMatch) {
      const activeTable = activeTableMatch[0];
      const hitlIds = activeTable.match(/HITL-\d+/g) || [];

      if (hitlIds.length === 0) {
        errors.push(
          "HITL required but no active HITL items found. Create HITL item per .repo/policy/HITL.md",
        );
      } else {
        // Check if PR body references HITL items
        if (prBodyPath && existsSync(prBodyPath)) {
          const prBody = readFileSync(prBodyPath, "utf-8");
          const referencedHITLs = prBody.match(/HITL-\d+/g) || [];

          if (referencedHITLs.length === 0) {
            warnings.push(
              "HITL items exist but PR body doesn't reference them. Add HITL references to PR description.",
            );
          }
        }
      }
    } else {
      errors.push("HITL required but HITL index table not found");
    }
  }

  return { compliant: errors.length === 0, errors, warnings };
}

// Check if trace log exists for non-doc changes
function checkTraceLogCompliance(changedFiles) {
  const errors = [];
  const warnings = [];

  const isDocOnlyChange =
    changedFiles.length > 0 &&
    changedFiles.every(
      (f) =>
        f.endsWith(".md") ||
        f.endsWith(".txt") ||
        f.includes("/docs/") ||
        f.includes("/.repo/docs/") ||
        f.includes("/examples/"),
    );

  if (!isDocOnlyChange && changedFiles.length > 0) {
    // Trace log is required for non-doc changes
    if (!traceLogPath || !existsSync(traceLogPath)) {
      // Try to find trace log in traces directory
      if (existsSync(TRACES_DIR)) {
        const traceFiles = readdirSync(TRACES_DIR).filter((f) =>
          f.endsWith(".json"),
        );
        if (traceFiles.length === 0) {
          errors.push(
            "Trace log required for non-documentation changes (Article 2, Principle 24). Create using: node .repo/automation/scripts/create-trace-log.js",
          );
        } else {
          warnings.push(
            "Trace log found in traces directory but not explicitly provided. Consider using --trace-log flag.",
          );
        }
      } else {
        errors.push(
          "Trace log required for non-documentation changes (Article 2, Principle 24). Create using: node .repo/automation/scripts/create-trace-log.js",
        );
      }
    }
  }

  return { compliant: errors.length === 0, errors, warnings };
}

// Check if PR references tasks
function checkTaskCompliance() {
  const errors = [];
  const warnings = [];

  if (prBodyPath && existsSync(prBodyPath)) {
    const prBody = readFileSync(prBodyPath, "utf-8");

    // Check for task references (TASK-XXX or links to TODO files)
    const taskPatterns = [
      /TASK-\d+/i,
      /\[TASK-\d+\]/i,
      /P0TODO|P1TODO|P2TODO|P3TODO/i,
      /TODO\.md/i,
    ];

    const hasTaskRef = taskPatterns.some((pattern) => pattern.test(prBody));

    if (!hasTaskRef) {
      warnings.push(
        "PR body doesn't reference a task. Per Article 5 (Strict Traceability), changes should link to tasks.",
      );
    }
  }

  return { compliant: true, errors, warnings };
}

// Check if filepaths are included in PR
function checkFilepathCompliance() {
  const errors = [];
  const warnings = [];

  if (prBodyPath && existsSync(prBodyPath)) {
    const prBody = readFileSync(prBodyPath, "utf-8");

    // Check for filepath section or inline filepaths
    const hasFilepathSection = /##?\s*(filepaths?|files?|changes?)/i.test(
      prBody,
    );
    const hasInlineFilepaths = /`[^`]+\.(ts|tsx|js|jsx|md|json|yaml|yml)`/.test(
      prBody,
    );

    if (!hasFilepathSection && !hasInlineFilepaths) {
      warnings.push(
        "PR body doesn't include filepaths. Per global rule in PRINCIPLES.md, filepaths are required everywhere.",
      );
    }
  }

  return { compliant: true, errors, warnings };
}

// Main function
function main() {
  console.log("🔍 Framework Compliance Check");
  console.log("==============================\n");

  const changedFiles = getChangedFiles(baseRef);
  const allErrors = [];
  const allWarnings = [];

  console.log(`📝 Changed files: ${changedFiles.length}\n`);

  // 1. Check trace log compliance
  console.log("📋 Checking trace log compliance...");
  const traceResult = checkTraceLogCompliance(changedFiles);
  if (!traceResult.compliant) {
    traceResult.errors.forEach((e) => {
      console.error(`   ❌ ${e}`);
      allErrors.push(e);
    });
  }
  traceResult.warnings.forEach((w) => {
    console.warn(`   ⚠️  ${w}`);
    allWarnings.push(w);
  });
  if (traceResult.compliant && traceResult.warnings.length === 0) {
    console.log("   ✅ Trace log compliance passed\n");
  } else {
    console.log();
  }

  // 2. Check HITL compliance
  console.log("👤 Checking HITL compliance...");
  const hitlResult = checkHITLCompliance(changedFiles);
  if (!hitlResult.compliant) {
    hitlResult.errors.forEach((e) => {
      console.error(`   ❌ ${e}`);
      allErrors.push(e);
    });
  }
  hitlResult.warnings.forEach((w) => {
    console.warn(`   ⚠️  ${w}`);
    allWarnings.push(w);
  });
  if (hitlResult.compliant && hitlResult.warnings.length === 0) {
    console.log("   ✅ HITL compliance passed\n");
  } else {
    console.log();
  }

  // 3. Check task compliance
  console.log("📋 Checking task compliance...");
  const taskResult = checkTaskCompliance();
  taskResult.warnings.forEach((w) => {
    console.warn(`   ⚠️  ${w}`);
    allWarnings.push(w);
  });
  if (taskResult.warnings.length === 0) {
    console.log("   ✅ Task compliance passed\n");
  } else {
    console.log();
  }

  // 4. Check filepath compliance
  console.log("📁 Checking filepath compliance...");
  const filepathResult = checkFilepathCompliance();
  filepathResult.warnings.forEach((w) => {
    console.warn(`   ⚠️  ${w}`);
    allWarnings.push(w);
  });
  if (filepathResult.warnings.length === 0) {
    console.log("   ✅ Filepath compliance passed\n");
  } else {
    console.log();
  }

  // Summary
  console.log("📊 Summary");
  console.log("==========");
  console.log(`Errors: ${allErrors.length}`);
  console.log(`Warnings: ${allWarnings.length}\n`);

  if (allErrors.length > 0) {
    console.error("❌ Framework compliance failed. Fix errors before merging.");
    process.exit(1);
  } else if (allWarnings.length > 0) {
    console.warn("⚠️  Framework compliance warnings. Review recommended.");
    process.exit(2);
  } else {
    console.log("✅ Framework compliance passed!");
    process.exit(0);
  }
}

main();
