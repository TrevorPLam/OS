#!/usr/bin/env node
// /.repo/automation/scripts/check-stale-context.js
// Check for stale context files (older than threshold)
// Usage: node check-stale-context.js [--threshold-days=30] [--warn-only]

const fs = require("fs");
const path = require("path");

// Get repo root
const REPO_ROOT = path.resolve(__dirname, "../../..");
const THRESHOLD_DAYS = parseInt(
  process.env.THRESHOLD_DAYS ||
    process.argv
      .find((arg) => arg.startsWith("--threshold-days="))
      ?.split("=")[1] ||
    "30",
);
const WARN_ONLY = process.argv.includes("--warn-only");

// Colors
const RED = "\x1b[31m";
const YELLOW = "\x1b[33m";
const GREEN = "\x1b[32m";
const RESET = "\x1b[0m";

function findContextFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);

  files.forEach((file) => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (
      stat.isDirectory() &&
      !file.startsWith(".") &&
      file !== "node_modules"
    ) {
      findContextFiles(filePath, fileList);
    } else if (file === ".agent-context.json") {
      fileList.push(filePath);
    }
  });

  return fileList;
}

function checkStaleContextFiles() {
  console.log(
    `Checking for stale context files (threshold: ${THRESHOLD_DAYS} days)...\n`,
  );

  const contextFiles = findContextFiles(REPO_ROOT);
  const thresholdDate = new Date();
  thresholdDate.setDate(thresholdDate.getDate() - THRESHOLD_DAYS);

  const staleFiles = [];
  const missingDateFiles = [];

  contextFiles.forEach((filePath) => {
    try {
      const content = JSON.parse(fs.readFileSync(filePath, "utf8"));
      const stats = fs.statSync(filePath);
      const relativePath = path.relative(REPO_ROOT, filePath);

      // Check if last_verified exists
      if (!content.metrics || !content.metrics.last_verified) {
        missingDateFiles.push({
          path: relativePath,
          lastModified: stats.mtime,
          age: Math.floor(
            (Date.now() - stats.mtime.getTime()) / (1000 * 60 * 60 * 24),
          ),
        });
      } else {
        // Check if last_verified is older than threshold
        const lastVerified = new Date(content.metrics.last_verified);
        if (lastVerified < thresholdDate) {
          const age = Math.floor(
            (Date.now() - lastVerified.getTime()) / (1000 * 60 * 60 * 24),
          );
          staleFiles.push({
            path: relativePath,
            lastVerified: lastVerified,
            age: age,
          });
        }
      }
    } catch (err) {
      console.error(`${RED}Error reading ${filePath}: ${err.message}${RESET}`);
    }
  });

  // Report results
  if (missingDateFiles.length > 0) {
    console.log(
      `${YELLOW}⚠️  Context files missing last_verified date:${RESET}`,
    );
    missingDateFiles.forEach((file) => {
      console.log(`   ${file.path} (last modified: ${file.age} days ago)`);
    });
    console.log();
  }

  if (staleFiles.length > 0) {
    console.log(
      `${YELLOW}⚠️  Stale context files (older than ${THRESHOLD_DAYS} days):${RESET}`,
    );
    staleFiles.forEach((file) => {
      console.log(`   ${file.path} (last verified: ${file.age} days ago)`);
    });
    console.log();
    console.log(
      `   Update with: node .repo/automation/scripts/update-context-verified.js ${staleFiles.map((f) => f.path).join(" ")}`,
    );
    console.log();

    if (!WARN_ONLY) {
      console.log(`${RED}❌ Stale context files detected${RESET}`);
      process.exit(1);
    }
  } else if (missingDateFiles.length === 0) {
    console.log(`${GREEN}✅ All context files are up to date${RESET}`);
  }

  return { staleFiles, missingDateFiles };
}

// CLI usage
if (require.main === module) {
  checkStaleContextFiles();
}

// Export for use as module
module.exports = { checkStaleContextFiles };
