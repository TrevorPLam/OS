#!/usr/bin/env node

/**
 * Traceability Checker
 *
 * Validates that features are properly traced through the development lifecycle:
 * Feature → PRD → ADR → Modules → APIs → Schemas → Tests → Runbooks → Dashboards
 *
 * Initially runs in WARN-ONLY mode (does not fail builds).
 * Mode can be toggled to FAIL via docs/governance/state.md or environment variable.
 *
 * Usage:
 *   node scripts/tools/check-traceability.mjs
 *   TRACEABILITY_ENFORCEMENT=fail node scripts/tools/check-traceability.mjs
 *
 * Exit codes:
 *   0 - All checks passed OR warnings only (warn mode)
 *   1 - Violations found and enforcement mode is FAIL
 */

import { readFileSync, existsSync, readdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const REPO_ROOT = join(__dirname, "../..");
const TRACEABILITY_PATH = join(REPO_ROOT, "docs/traceability_matrix.md");
// Note: State management is now handled via .repo/policy/QUALITY_GATES.md
// This script may need updates to work with new governance structure
const STATE_PATH = join(REPO_ROOT, "docs/archive/governance/state.md");
const OPENAPI_PATH = join(REPO_ROOT, "docs/apis/openapi/openapi.yaml");

// Determine enforcement mode
function getEnforcementMode() {
  // 1. Check environment variable first
  if (process.env.TRACEABILITY_ENFORCEMENT) {
    return process.env.TRACEABILITY_ENFORCEMENT.toLowerCase();
  }

  // 2. Read from state.md if it exists
  if (existsSync(STATE_PATH)) {
    try {
      const stateContent = readFileSync(STATE_PATH, "utf-8");
      // Look for: | **Traceability Matrix** | `WARN` | or | `FAIL` |
      const match = stateContent.match(
        /\*\*Traceability Matrix\*\*.*?`(WARN|FAIL)`/i,
      );
      if (match) {
        return match[1].toLowerCase();
      }
    } catch (error) {
      console.warn(
        `⚠️  Could not read enforcement mode from state.md: ${error.message}`,
      );
    }
  }

  // 3. Default to warn
  return "warn";
}

function checkTraceability() {
  console.log("🔍 Traceability Checker");
  console.log("=======================\n");

  const enforcementMode = getEnforcementMode();
  console.log(`📋 Enforcement mode: ${enforcementMode.toUpperCase()}`);

  if (enforcementMode === "warn") {
    console.log("   (Violations will log warnings but not fail the build)\n");
  } else {
    console.log("   (Violations will fail the build)\n");
  }

  // Check if traceability matrix exists
  if (!existsSync(TRACEABILITY_PATH)) {
    console.error(`❌ Traceability matrix not found at: ${TRACEABILITY_PATH}`);
    if (enforcementMode === "fail") {
      return 1;
    }
    console.warn("⚠️  Continuing in warn-only mode...\n");
    return 0;
  }

  console.log(`📖 Reading traceability matrix from: ${TRACEABILITY_PATH}\n`);
  const matrixContent = readFileSync(TRACEABILITY_PATH, "utf-8");

  const violations = [];

  // Parse the matrix table
  const lines = matrixContent.split("\n");
  const tableLines = lines.filter(
    (line) => line.trim().startsWith("|") && !line.includes("---"),
  );

  if (tableLines.length === 0) {
    violations.push({
      type: "empty_matrix",
      message: "Traceability matrix is empty (no table rows found)",
    });
  } else {
    // Skip header row
    const dataRows = tableLines.slice(1);
    console.log(`   Found ${dataRows.length} row(s) in matrix\n`);

    // Check for TODO markers
    const todoCount = (matrixContent.match(/TODO/gi) || []).length;
    if (todoCount > 0) {
      console.log(`   ℹ️  Matrix contains ${todoCount} TODO marker(s)\n`);
    }
  }

  // Check if OpenAPI was modified without traceability update
  // (This would be done by checking git diff in CI, simplified here)
  if (existsSync(OPENAPI_PATH)) {
    console.log("✅ OpenAPI spec exists");
    // TODO: In CI, check if openapi.yaml changed in current PR
    // If so, verify traceability_matrix.md was also updated
  }

  // Check for common issues
  const issueChecks = [
    {
      pattern: /\|\s*\|\s*\|/,
      message: "Empty cells detected in traceability matrix",
      type: "empty_cells",
    },
    {
      pattern: /Feature.*TODO.*TODO/,
      message: "Rows with multiple TODOs should be completed",
      type: "incomplete_rows",
    },
  ];

  for (const check of issueChecks) {
    if (check.pattern.test(matrixContent)) {
      violations.push({
        type: check.type,
        message: check.message,
      });
    }
  }

  // Report violations
  if (violations.length > 0) {
    console.log("⚠️  Traceability Issues Found:\n");
    violations.forEach((v, i) => {
      console.log(`   ${i + 1}. [${v.type}] ${v.message}`);
    });
    console.log("");

    if (enforcementMode === "fail") {
      console.error("❌ FAILED: Traceability violations found in FAIL mode\n");
      console.error("📝 Action required:");
      console.error(
        "   1. Review and fix issues in docs/traceability_matrix.md",
      );
      console.error("   2. Ensure all features are properly traced");
      console.error("   3. Replace TODOs with actual links/references");
      console.error("   4. Commit and push changes\n");
      return 1;
    } else {
      console.warn("⚠️  Warnings logged (warn-only mode - build will pass)\n");
      console.warn("📝 Recommended actions:");
      console.warn("   - Gradually complete TODOs in traceability matrix");
      console.warn("   - Add traceability rows for new features");
      console.warn("   - When matrix is >80% complete, toggle to FAIL mode\n");
      return 0;
    }
  }

  console.log("✅ Traceability checks passed\n");
  return 0;
}

// Run checker
const exitCode = checkTraceability();
process.exit(exitCode);
