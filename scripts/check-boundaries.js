#!/usr/bin/env node
// /.repo/automation/scripts/check-boundaries.js
// Boundary checking script - wraps lint-imports for agent use
// Usage: node check-boundaries.js [--fail-on-violations]

const { execSync } = require("child_process");
const path = require("path");

// Get repo root
const REPO_ROOT = path.resolve(__dirname, "../../..");
const IMPORTLINTER_CONFIG = path.join(REPO_ROOT, ".importlinter");

// Colors
const RED = "\x1b[31m";
const YELLOW = "\x1b[33m";
const GREEN = "\x1b[32m";
const RESET = "\x1b[0m";

function commandExists(cmd) {
  try {
    execSync(`which ${cmd} 2>/dev/null || where ${cmd} 2>/dev/null`, {
      stdio: "ignore",
    });
    return true;
  } catch {
    return false;
  }
}

function checkBoundaries(failOnViolations = false) {
  console.log("Checking module boundaries...\n");

  // Check if import-linter is installed
  if (!commandExists("lint-imports")) {
    console.error(`${RED}❌ ERROR: lint-imports not found${RESET}`);
    console.error("Install with: pip install import-linter==2.0");
    process.exit(1);
  }

  // Check if config file exists
  const fs = require("fs");
  if (!fs.existsSync(IMPORTLINTER_CONFIG)) {
    console.error(
      `${RED}❌ ERROR: .importlinter config file not found${RESET}`,
    );
    console.error(`Expected at: ${IMPORTLINTER_CONFIG}`);
    process.exit(1);
  }

  try {
    // Run lint-imports
    const result = execSync(`lint-imports --config "${IMPORTLINTER_CONFIG}"`, {
      encoding: "utf8",
      cwd: REPO_ROOT,
      stdio: "pipe",
    });

    console.log(result);
    console.log(`${GREEN}✅ Boundary check passed${RESET}`);
    return { success: true, violations: [] };
  } catch (e) {
    const output = e.stdout || e.stderr || e.message;
    console.error(`${RED}❌ Boundary violations detected:${RESET}\n`);
    console.error(output);

    // Try to parse violations from output
    const violations = [];
    const lines = output.split("\n");
    let currentViolation = null;

    for (const line of lines) {
      if (line.includes("Broken contract:") || line.includes("Contract")) {
        if (currentViolation) {
          violations.push(currentViolation);
        }
        currentViolation = { contract: line.trim(), imports: [] };
      } else if (line.includes("->") && currentViolation) {
        currentViolation.imports.push(line.trim());
      }
    }
    if (currentViolation) {
      violations.push(currentViolation);
    }

    if (failOnViolations) {
      console.error(
        `\n${RED}Hard gate failure: Boundary violations must be fixed or waived${RESET}`,
      );
      console.error("See: .repo/policy/BOUNDARIES.md for boundary rules");
      console.error("See: .repo/policy/QUALITY_GATES.md for waiver process");
      process.exit(1);
    }

    return { success: false, violations };
  }
}

// CLI usage
if (require.main === module) {
  const failOnViolations = process.argv.includes("--fail-on-violations");
  const result = checkBoundaries(failOnViolations);
  process.exit(result.success ? 0 : 1);
}

// Export for use as module
module.exports = { checkBoundaries };
