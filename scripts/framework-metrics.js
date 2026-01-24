#!/usr/bin/env node

/**
 * Framework Metrics Generator
 *
 * Generates metrics and reports on framework compliance and usage.
 * Helps track adoption and identify areas for improvement.
 *
 * Usage:
 *   node .repo/automation/scripts/framework-metrics.js [--output <path>]
 *
 * Exit codes:
 *   0 - Success
 *   1 - Error
 */

import {
  readFileSync,
  existsSync,
  readdirSync,
  statSync,
  writeFileSync,
} from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const REPO_ROOT = join(__dirname, "../../../..");
const HITL_INDEX_PATH = join(REPO_ROOT, ".repo/policy/HITL.md");
const HITL_ITEMS_DIR = join(REPO_ROOT, ".repo/hitl");
const TRACES_DIR = join(REPO_ROOT, ".repo/traces");
const WAIVERS_DIR = join(REPO_ROOT, ".repo/waivers");
const ADR_DIR = join(REPO_ROOT, ".repo/docs/adr");

// Parse command line arguments
const args = process.argv.slice(2);
let outputPath = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--output" && i + 1 < args.length) {
    outputPath = args[i + 1];
    i++;
  }
}

// Count HITL items
function countHITLItems() {
  const stats = {
    active: 0,
    pending: 0,
    inProgress: 0,
    blocked: 0,
    completed: 0,
    superseded: 0,
    total: 0,
  };

  if (!existsSync(HITL_INDEX_PATH)) {
    return stats;
  }

  const content = readFileSync(HITL_INDEX_PATH, "utf-8");

  // Parse active table
  const activeMatch = content.match(/### Active[\s\S]*?(\n###|$)/);
  if (activeMatch) {
    const activeTable = activeMatch[0];
    const rows = activeTable
      .split("\n")
      .filter((line) => line.includes("|") && !line.includes("---"));
    stats.active = rows.length - 1; // Subtract header row

    // Count by status
    for (const row of rows) {
      if (row.includes("|Pending|")) stats.pending++;
      if (row.includes("|In Progress|")) stats.inProgress++;
      if (row.includes("|Blocked|")) stats.blocked++;
      if (row.includes("|Completed|")) stats.completed++;
      if (row.includes("|Superseded|")) stats.superseded++;
    }
  }

  // Count archived
  const archivedMatch = content.match(/### Archived[\s\S]*?$/);
  if (archivedMatch) {
    const archivedTable = archivedMatch[0];
    const rows = archivedTable
      .split("\n")
      .filter((line) => line.includes("|") && !line.includes("---"));
    stats.total = rows.length - 1; // Subtract header row
  }

  // Count item files
  if (existsSync(HITL_ITEMS_DIR)) {
    const files = readdirSync(HITL_ITEMS_DIR).filter((f) => f.endsWith(".md"));
    stats.total = Math.max(stats.total, files.length);
  }

  return stats;
}

// Count trace logs
function countTraceLogs() {
  const stats = {
    total: 0,
    recent: 0, // Last 30 days
    oldest: null,
    newest: null,
  };

  if (!existsSync(TRACES_DIR)) {
    return stats;
  }

  const files = readdirSync(TRACES_DIR).filter((f) => f.endsWith(".json"));
  stats.total = files.length;

  const now = Date.now();
  const thirtyDaysAgo = now - 30 * 24 * 60 * 60 * 1000;

  for (const file of files) {
    const filePath = join(TRACES_DIR, file);
    const stat = statSync(filePath);
    const mtime = stat.mtimeMs;

    if (!stats.oldest || mtime < stats.oldest) {
      stats.oldest = mtime;
    }
    if (!stats.newest || mtime > stats.newest) {
      stats.newest = mtime;
    }

    if (mtime > thirtyDaysAgo) {
      stats.recent++;
    }
  }

  return stats;
}

// Count waivers
function countWaivers() {
  const stats = {
    active: 0,
    expired: 0,
    total: 0,
  };

  if (!existsSync(WAIVERS_DIR)) {
    return stats;
  }

  const files = readdirSync(WAIVERS_DIR).filter((f) => f.endsWith(".md"));
  stats.total = files.length;

  const now = new Date();

  for (const file of files) {
    try {
      const content = readFileSync(join(WAIVERS_DIR, file), "utf-8");
      const expirationMatch = content.match(
        /Expiration:\s*(\d{4}-\d{2}-\d{2})/,
      );

      if (expirationMatch) {
        const expiration = new Date(expirationMatch[1]);
        if (expiration > now) {
          stats.active++;
        } else {
          stats.expired++;
        }
      } else {
        stats.active++; // No expiration = active
      }
    } catch (e) {
      // Skip invalid files
    }
  }

  return stats;
}

// Count ADRs
function countADRs() {
  const stats = {
    total: 0,
  };

  if (existsSync(ADR_DIR)) {
    const files = readdirSync(ADR_DIR).filter((f) => f.endsWith(".md"));
    stats.total = files.length;
  }

  return stats;
}

// Generate report
function generateReport() {
  const hitlStats = countHITLItems();
  const traceStats = countTraceLogs();
  const waiverStats = countWaivers();
  const adrStats = countADRs();

  const report = {
    generated: new Date().toISOString(),
    hitl: hitlStats,
    traces: traceStats,
    waivers: waiverStats,
    adrs: adrStats,
    compliance: {
      traceLogsPerChange:
        traceStats.total > 0
          ? "✅ Trace logs being created"
          : "❌ No trace logs found",
      hitlUsage:
        hitlStats.active > 0
          ? "✅ HITL items being used"
          : "⚠️  No active HITL items",
      waiverUsage:
        waiverStats.active > 0
          ? "⚠️  Active waivers exist"
          : "✅ No active waivers",
      adrUsage:
        adrStats.total > 0 ? "✅ ADRs being created" : "ℹ️  No ADRs yet",
    },
  };

  return report;
}

// Format report as markdown
function formatMarkdown(report) {
  let md = "# Framework Metrics Report\n\n";
  md += `**Generated:** ${new Date(report.generated).toLocaleString()}\n\n`;
  md += "---\n\n";

  md += "## HITL Items\n\n";
  md += `- **Active:** ${report.hitl.active}\n`;
  md += `- **Pending:** ${report.hitl.pending}\n`;
  md += `- **In Progress:** ${report.hitl.inProgress}\n`;
  md += `- **Blocked:** ${report.hitl.blocked}\n`;
  md += `- **Completed:** ${report.hitl.completed}\n`;
  md += `- **Total:** ${report.hitl.total}\n\n`;

  md += "## Trace Logs\n\n";
  md += `- **Total:** ${report.traces.total}\n`;
  md += `- **Recent (30 days):** ${report.traces.recent}\n`;
  if (report.traces.oldest) {
    md += `- **Oldest:** ${new Date(report.traces.oldest).toLocaleDateString()}\n`;
    md += `- **Newest:** ${new Date(report.traces.newest).toLocaleDateString()}\n`;
  }
  md += "\n";

  md += "## Waivers\n\n";
  md += `- **Active:** ${report.waivers.active}\n`;
  md += `- **Expired:** ${report.waivers.expired}\n`;
  md += `- **Total:** ${report.waivers.total}\n\n`;

  md += "## ADRs\n\n";
  md += `- **Total:** ${report.adrs.total}\n\n`;

  md += "## Compliance Status\n\n";
  md += `- **Trace Logs:** ${report.compliance.traceLogsPerChange}\n`;
  md += `- **HITL Usage:** ${report.compliance.hitlUsage}\n`;
  md += `- **Waiver Usage:** ${report.compliance.waiverUsage}\n`;
  md += `- **ADR Usage:** ${report.compliance.adrUsage}\n\n`;

  md += "---\n\n";
  md += "*Generated by framework-metrics.js*\n";

  return md;
}

// Main function
function main() {
  console.log("📊 Generating Framework Metrics...\n");

  const report = generateReport();
  const markdown = formatMarkdown(report);

  if (outputPath) {
    writeFileSync(outputPath, markdown, "utf-8");
    console.log(`✅ Report written to: ${outputPath}`);

    // Also output JSON for programmatic use
    const jsonPath = outputPath.replace(/\.md$/, ".json");
    writeFileSync(jsonPath, JSON.stringify(report, null, 2), "utf-8");
    console.log(`✅ JSON data written to: ${jsonPath}`);
  } else {
    console.log(markdown);
  }

  process.exit(0);
}

main();
