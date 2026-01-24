#!/usr/bin/env node

/**
 * Security Pattern Scanner
 *
 * Scans codebase for forbidden security patterns defined in SECURITY_BASELINE.md.
 *
 * Usage:
 *   node .repo/automation/scripts/check-security-patterns.js [--path <path>]
 *
 * Exit codes:
 *   0 - No violations found
 *   1 - Violations found
 */

import { readFileSync, existsSync, readdirSync, statSync } from "fs";
import { join, dirname, relative } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const REPO_ROOT = join(__dirname, "../../../..");
const SECURITY_BASELINE_PATH = join(
  REPO_ROOT,
  ".repo/policy/SECURITY_BASELINE.md",
);

// File extensions to scan
const SCAN_EXTENSIONS = [
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".json",
  ".yaml",
  ".yml",
  ".env",
  ".env.example",
];

// Files/directories to ignore
const IGNORE_PATTERNS = [
  "node_modules",
  ".git",
  ".expo",
  "dist",
  "build",
  "coverage",
  ".repo/traces",
  ".repo/hitl",
  ".repo/waivers",
  "package-lock.json",
  "yarn.lock",
];

// Parse forbidden patterns from SECURITY_BASELINE.md
function getForbiddenPatterns() {
  if (!existsSync(SECURITY_BASELINE_PATH)) {
    throw new Error(`Security baseline not found: ${SECURITY_BASELINE_PATH}`);
  }

  const content = readFileSync(SECURITY_BASELINE_PATH, "utf-8");

  // Extract patterns array from markdown
  const patternsMatch = content.match(/Forbidden patterns list:\s*\[(.*?)\]/s);
  if (!patternsMatch) {
    throw new Error(
      "Could not find forbidden patterns in SECURITY_BASELINE.md",
    );
  }

  // Parse JSON array from the match (handles both comma-separated and newline-separated)
  const patternsStr = patternsMatch[1];
  // Split by comma or newline, then clean up
  const patterns = patternsStr
    .split(/[,\n]/)
    .map((p) => p.trim().replace(/^"|"$/g, ""))
    .filter((p) => p && !p.match(/^\s*$/)); // Filter out empty strings

  if (patterns.length === 0) {
    throw new Error("No patterns found in SECURITY_BASELINE.md");
  }

  return patterns.map((pattern) => new RegExp(pattern, "i"));
}

// Check if file should be ignored
function shouldIgnore(filePath) {
  const relativePath = relative(REPO_ROOT, filePath);
  return IGNORE_PATTERNS.some((pattern) => relativePath.includes(pattern));
}

// Get file extension
function getExtension(filePath) {
  const ext = filePath.substring(filePath.lastIndexOf("."));
  return ext.toLowerCase();
}

// Scan a single file
function scanFile(filePath, patterns) {
  const violations = [];

  try {
    const content = readFileSync(filePath, "utf-8");
    const lines = content.split("\n");

    patterns.forEach((pattern, index) => {
      lines.forEach((line, lineNum) => {
        if (pattern.test(line)) {
          violations.push({
            file: relative(REPO_ROOT, filePath),
            line: lineNum + 1,
            pattern: index + 1,
            content: line.trim().substring(0, 100), // First 100 chars
          });
        }
      });
    });
  } catch (error) {
    // Skip files that can't be read (binary, etc.)
  }

  return violations;
}

// Recursively scan directory
function scanDirectory(dirPath, patterns, allViolations = []) {
  if (!existsSync(dirPath)) {
    return allViolations;
  }

  const entries = readdirSync(dirPath);

  for (const entry of entries) {
    const fullPath = join(dirPath, entry);

    if (shouldIgnore(fullPath)) {
      continue;
    }

    const stat = statSync(fullPath);

    if (stat.isDirectory()) {
      scanDirectory(fullPath, patterns, allViolations);
    } else if (stat.isFile()) {
      const ext = getExtension(fullPath);
      if (SCAN_EXTENSIONS.includes(ext)) {
        const violations = scanFile(fullPath, patterns);
        allViolations.push(...violations);
      }
    }
  }

  return allViolations;
}

// Main function
function main() {
  console.log("🔒 Security Pattern Scanner");
  console.log("===========================\n");

  try {
    const patterns = getForbiddenPatterns();
    console.log(`📋 Loaded ${patterns.length} forbidden pattern(s)\n`);

    const scanPath = process.argv.includes("--path")
      ? process.argv[process.argv.indexOf("--path") + 1]
      : REPO_ROOT;

    console.log(`🔍 Scanning: ${scanPath}\n`);

    const violations = scanDirectory(scanPath, patterns);

    if (violations.length > 0) {
      console.error(`❌ Found ${violations.length} violation(s):\n`);

      violations.forEach((v) => {
        console.error(`  File: ${v.file}:${v.line}`);
        console.error(`  Pattern: ${v.pattern}`);
        console.error(`  Content: ${v.content}`);
        console.error("");
      });

      console.error(
        "⚠️  Security violation detected. Review and remove secrets/tokens.",
      );
      process.exit(1);
    } else {
      console.log("✅ No security violations found");
      process.exit(0);
    }
  } catch (error) {
    console.error(`❌ Error: ${error.message}`);
    process.exit(1);
  }
}

main();
