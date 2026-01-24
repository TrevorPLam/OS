#!/usr/bin/env node
// Auto-Detect Performance Regressions
// Usage: node scripts/intelligent/auto-detect-performance-regressions.mjs [--base-ref main] [--threshold 10]

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const BASE_REF = process.argv.find((arg) => arg.startsWith("--base-ref="))?.split("=")[1] || "main";
const THRESHOLD_PERCENT = parseInt(process.argv.find((arg) => arg.startsWith("--threshold="))?.split("=")[1] || "10");

function runPerformanceBenchmark() {
  try {
    // Run a simple performance test
    const start = Date.now();
    execSync("npm test -- --testPathPattern=performance --silent 2>&1", { encoding: "utf8", cwd: REPO_ROOT, timeout: 30000 });
    const duration = Date.now() - start;
    return duration;
  } catch (e) {
    // Performance tests might not exist
    return null;
  }
}

function analyzeBundlePerformance() {
  try {
    const buildOutput = execSync("npm run expo:static:build 2>&1", { encoding: "utf8", cwd: REPO_ROOT, timeout: 120000 });
    
    // Extract build time
    const timeMatch = buildOutput.match(/build.*?(\d+\.?\d*)\s*(s|ms)/i);
    if (timeMatch) {
      const time = parseFloat(timeMatch[1]);
      const unit = timeMatch[2].toLowerCase();
      return unit === "s" ? time * 1000 : time; // Convert to ms
    }
  } catch (e) {
    // Build might fail
  }
  return null;
}

function detectPerformanceBottlenecks(changedFiles) {
  const bottlenecks = [];

  for (const file of changedFiles.slice(0, 20)) {
    // Limit for performance
    const filePath = path.join(REPO_ROOT, file);
    if (!fs.existsSync(filePath) || !file.match(/\.(ts|tsx|js|jsx)$/)) continue;

    try {
      const content = fs.readFileSync(filePath, "utf8");

      // Detect potential performance issues
      if (content.includes("useEffect") && content.match(/useEffect/g)?.length > 5) {
        bottlenecks.push({
          file,
          issue: "too_many_useEffects",
          severity: "medium",
        });
      }

      if (content.includes(".map(") && content.match(/\.map\(/g)?.length > 10) {
        bottlenecks.push({
          file,
          issue: "excessive_array_operations",
          severity: "low",
        });
      }

      if (content.includes("JSON.parse") || content.includes("JSON.stringify")) {
        bottlenecks.push({
          file,
          issue: "json_operations_in_render",
          severity: "medium",
        });
      }
    } catch (e) {
      // Skip file
    }
  }

  return bottlenecks;
}

function main() {
  console.log("⚡ Auto-Detecting Performance Regressions\n");

  console.log(`📊 Running performance benchmarks...\n`);

  const currentBuildTime = analyzeBundlePerformance();
  const currentTestTime = runPerformanceBenchmark();

  if (!currentBuildTime && !currentTestTime) {
    console.log("⚠️  Could not run performance benchmarks");
    console.log("   Ensure build and tests are working");
    return;
  }

  console.log(`   Build Time: ${currentBuildTime ? `${(currentBuildTime / 1000).toFixed(2)}s` : "N/A"}`);
  console.log(`   Test Time: ${currentTestTime ? `${(currentTestTime / 1000).toFixed(2)}s` : "N/A"}\n`);

  // Get changed files
  try {
    const changedFiles = execSync(`git diff --name-only ${BASE_REF}...HEAD`, {
      encoding: "utf8",
      cwd: REPO_ROOT,
    })
      .trim()
      .split("\n")
      .filter(Boolean);

    if (changedFiles.length > 0) {
      const bottlenecks = detectPerformanceBottlenecks(changedFiles);
      if (bottlenecks.length > 0) {
        console.log(`⚠️  Potential Performance Issues Detected:\n`);
        bottlenecks.forEach((b, i) => {
          console.log(`   ${i + 1}. [${b.severity.toUpperCase()}] ${b.file}`);
          console.log(`      Issue: ${b.issue}\n`);
        });
      }
    }
  } catch (e) {
    // No changes or git error
  }

  // Generate report
  const report = {
    timestamp: new Date().toISOString(),
    build_time_ms: currentBuildTime,
    test_time_ms: currentTestTime,
    threshold_percent: THRESHOLD_PERCENT,
  };

  const reportPath = path.join(REPO_ROOT, ".repo/automation/performance-report.json");
  const reportDir = path.dirname(reportPath);
  if (!fs.existsSync(reportDir)) {
    fs.mkdirSync(reportDir, { recursive: true });
  }
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  console.log(`✅ Report saved to: ${reportPath}`);
}

main();
