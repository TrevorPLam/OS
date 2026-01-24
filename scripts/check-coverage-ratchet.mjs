#!/usr/bin/env node
/**
 * Check coverage on New Code only (Ratchet approach)
 * Ensures ≥ 90% coverage on lines changed in PR
 */

import { execSync } from "child_process";
import { readFileSync } from "fs";

const COVERAGE_THRESHOLD = 90; // 90% minimum
const BASE_BRANCH = process.env.BASE_REF || "main";

function getChangedFiles() {
  try {
    const output = execSync(`git diff --name-only ${BASE_BRANCH}...HEAD`, {
      encoding: "utf-8",
    });
    return output.trim().split("\n").filter(Boolean);
  } catch (error) {
    console.error("Error getting changed files:", error.message);
    return [];
  }
}

function getChangedLines(file) {
  try {
    const output = execSync(`git diff ${BASE_BRANCH}...HEAD -- ${file}`, {
      encoding: "utf-8",
    });
    const addedLines = [];
    let currentLine = 0;

    output.split("\n").forEach((line) => {
      if (line.startsWith("@@")) {
        const match = line.match(/\+(\d+)/);
        if (match) currentLine = parseInt(match[1]) - 1;
      } else if (line.startsWith("+") && !line.startsWith("+++")) {
        currentLine++;
        addedLines.push(currentLine);
      } else if (!line.startsWith("-") && !line.startsWith("\\")) {
        currentLine++;
      }
    });

    return addedLines;
  } catch (error) {
    return [];
  }
}

function parseCoverageReport() {
  try {
    // Try to read coverage-summary.json (Jest format)
    const coverage = JSON.parse(
      readFileSync("coverage/coverage-summary.json", "utf-8"),
    );
    return coverage;
  } catch (error) {
    console.error(
      "Coverage report not found. Run tests with --coverage first.",
    );
    return null;
  }
}

function checkNewCodeCoverage() {
  const changedFiles = getChangedFiles();
  const codeFiles = changedFiles.filter(
    (f) =>
      /\.(ts|tsx|js|jsx|mjs)$/.test(f) &&
      !f.includes("test") &&
      !f.includes("spec"),
  );

  if (codeFiles.length === 0) {
    console.log("✅ No code files changed, skipping coverage check");
    return true;
  }

  console.log(`\n📊 Checking coverage on ${codeFiles.length} changed file(s):`);
  codeFiles.forEach((f) => console.log(`  - ${f}`));

  const coverage = parseCoverageReport();
  if (!coverage) {
    return false;
  }

  let totalLines = 0;
  let coveredLines = 0;

  codeFiles.forEach((file) => {
    const fileCoverage = coverage[file];
    if (fileCoverage && fileCoverage.lines) {
      const changedLines = getChangedLines(file);
      changedLines.forEach((lineNum) => {
        totalLines++;
        if (fileCoverage.lines[lineNum] > 0) {
          coveredLines++;
        }
      });
    }
  });

  if (totalLines === 0) {
    console.log("✅ No executable lines changed");
    return true;
  }

  const coveragePercent = (coveredLines / totalLines) * 100;
  console.log(
    `\n📈 New Code Coverage: ${coveragePercent.toFixed(1)}% (${coveredLines}/${totalLines} lines)`,
  );

  if (coveragePercent < COVERAGE_THRESHOLD) {
    console.error(
      `\n❌ Coverage ${coveragePercent.toFixed(1)}% is below threshold of ${COVERAGE_THRESHOLD}%`,
    );
    console.error("   Add tests for new code or increase coverage");
    return false;
  }

  console.log(
    `✅ Coverage ${coveragePercent.toFixed(1)}% meets threshold of ${COVERAGE_THRESHOLD}%`,
  );
  return true;
}

if (!checkNewCodeCoverage()) {
  process.exit(1);
}
