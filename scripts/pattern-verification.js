#!/usr/bin/env node
// /.repo/automation/scripts/pattern-verification.js
// Basic pattern verification - checks if pattern files exist and are referenced
// Usage: node pattern-verification.js [--warn-only]

const fs = require("fs");
const path = require("path");

// Get repo root
const REPO_ROOT = path.resolve(__dirname, "../../..");
const WARN_ONLY = process.argv.includes("--warn-only");

// Colors
const YELLOW = "\x1b[33m";
const GREEN = "\x1b[32m";
const RESET = "\x1b[0m";

function findPatternFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);

  files.forEach((file) => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (
      stat.isDirectory() &&
      !file.startsWith(".") &&
      file !== "node_modules"
    ) {
      findPatternFiles(filePath, fileList);
    } else if (file === "PATTERNS.md") {
      fileList.push(filePath);
    }
  });

  return fileList;
}

function checkPatternFiles() {
  console.log("Checking pattern files...\n");

  const patternFiles = findPatternFiles(REPO_ROOT);
  const issues = [];

  patternFiles.forEach((filePath) => {
    const relativePath = path.relative(REPO_ROOT, filePath);
    const dir = path.dirname(filePath);
    const dirName = path.basename(dir);

    try {
      const content = fs.readFileSync(filePath, "utf8");

      // Check if pattern file has content
      if (content.trim().length < 100) {
        issues.push({
          file: relativePath,
          issue: "Pattern file is very short (may be incomplete)",
        });
      }

      // Check if corresponding .AGENT.md references it
      const agentMdPath = path.join(dir, ".AGENT.md");
      if (fs.existsSync(agentMdPath)) {
        const agentContent = fs.readFileSync(agentMdPath, "utf8");
        if (
          !agentContent.includes("PATTERNS.md") &&
          !agentContent.includes("patterns")
        ) {
          issues.push({
            file: relativePath,
            issue: "Pattern file exists but not referenced in .AGENT.md",
          });
        }
      }

      // Check if corresponding .agent-context.json references it
      const contextPath = path.join(dir, ".agent-context.json");
      if (fs.existsSync(contextPath)) {
        const contextContent = JSON.parse(fs.readFileSync(contextPath, "utf8"));
        if (
          !contextContent.patterns ||
          Object.keys(contextContent.patterns).length === 0
        ) {
          issues.push({
            file: relativePath,
            issue:
              "Pattern file exists but .agent-context.json has no patterns field",
          });
        }
      }
    } catch (err) {
      issues.push({
        file: relativePath,
        issue: `Error reading file: ${err.message}`,
      });
    }
  });

  if (issues.length > 0) {
    console.log(`${YELLOW}⚠️  Pattern file issues found:${RESET}`);
    issues.forEach((issue) => {
      console.log(`   ${issue.file}: ${issue.issue}`);
    });
    console.log();

    if (!WARN_ONLY) {
      process.exit(1);
    }
  } else {
    console.log(`${GREEN}✅ Pattern files are properly configured${RESET}`);
  }

  return issues;
}

// CLI usage
if (require.main === module) {
  checkPatternFiles();
}

// Export for use as module
module.exports = { checkPatternFiles };
