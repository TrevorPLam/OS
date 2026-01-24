#!/usr/bin/env node

/**
 * Trace Log Generator
 *
 * Creates a trace log following AGENT_TRACE_SCHEMA.json format.
 * This automates trace log creation for agents following the three-pass workflow.
 *
 * Usage:
 *   node .repo/automation/scripts/create-trace-log.js \
 *     --intent "Add feature X" \
 *     --files "file1.ts,file2.ts" \
 *     --commands "npm test,npm run lint" \
 *     --evidence "Tests passed,Lint clean" \
 *     [--hitl "HITL-0001"] \
 *     [--unknowns "API endpoint unclear"] \
 *     [--output .repo/traces/trace-{timestamp}.json]
 *
 * Exit codes:
 *   0 - Success
 *   1 - Error
 */

import { writeFileSync, existsSync, mkdirSync, readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const REPO_ROOT = join(__dirname, "../../../..");
const TRACES_DIR = join(REPO_ROOT, ".repo/traces");
const TRACE_SCHEMA_PATH = join(
  REPO_ROOT,
  ".repo/templates/AGENT_TRACE_SCHEMA.json",
);

// Parse command line arguments
const args = process.argv.slice(2);
let intent = null;
let files = [];
let commands = [];
let evidence = [];
let hitl = [];
let unknowns = [];
let outputPath = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--intent" && i + 1 < args.length) {
    intent = args[i + 1];
    i++;
  } else if (args[i] === "--files" && i + 1 < args.length) {
    files = args[i + 1]
      .split(",")
      .map((f) => f.trim())
      .filter(Boolean);
    i++;
  } else if (args[i] === "--commands" && i + 1 < args.length) {
    commands = args[i + 1]
      .split(",")
      .map((c) => c.trim())
      .filter(Boolean);
    i++;
  } else if (args[i] === "--evidence" && i + 1 < args.length) {
    evidence = args[i + 1]
      .split(",")
      .map((e) => e.trim())
      .filter(Boolean);
    i++;
  } else if (args[i] === "--hitl" && i + 1 < args.length) {
    hitl = args[i + 1]
      .split(",")
      .map((h) => h.trim())
      .filter(Boolean);
    i++;
  } else if (args[i] === "--unknowns" && i + 1 < args.length) {
    unknowns = args[i + 1]
      .split(",")
      .map((u) => u.trim())
      .filter(Boolean);
    i++;
  } else if (args[i] === "--output" && i + 1 < args.length) {
    outputPath = args[i + 1];
    i++;
  }
}

// Validate required fields
if (!intent) {
  console.error("❌ Error: --intent is required");
  console.error("\nUsage:");
  console.error("  node create-trace-log.js --intent 'Add feature X' \\");
  console.error("    --files 'file1.ts,file2.ts' \\");
  console.error("    --commands 'npm test,npm run lint' \\");
  console.error("    --evidence 'Tests passed,Lint clean'");
  process.exit(1);
}

// Ensure traces directory exists
if (!existsSync(TRACES_DIR)) {
  mkdirSync(TRACES_DIR, { recursive: true });
}

// Generate output path if not provided
if (!outputPath) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const taskId = process.env.TASK_ID || "unknown";
  outputPath = join(TRACES_DIR, `trace-${taskId}-${timestamp}.json`);
}

// Create trace log object
const traceLog = {
  intent,
  files: files.length > 0 ? files : [],
  commands: commands.length > 0 ? commands : [],
  evidence: evidence.length > 0 ? evidence : [],
  hitl: hitl.length > 0 ? hitl : [],
  unknowns: unknowns.length > 0 ? unknowns : [],
};

// Validate against schema (basic check)
const schema = JSON.parse(readFileSync(TRACE_SCHEMA_PATH, "utf-8"));
const requiredFields = schema.required || [];

for (const field of requiredFields) {
  if (!(field in traceLog)) {
    console.error(`❌ Error: Missing required field '${field}'`);
    process.exit(1);
  }
}

// Write trace log
try {
  writeFileSync(outputPath, JSON.stringify(traceLog, null, 2) + "\n", "utf-8");
  console.log("✅ Trace log created:");
  console.log(`   ${outputPath}`);
  console.log(`\n📋 Summary:`);
  console.log(`   Intent: ${intent}`);
  console.log(`   Files: ${files.length}`);
  console.log(`   Commands: ${commands.length}`);
  console.log(`   Evidence: ${evidence.length}`);
  if (hitl.length > 0) {
    console.log(`   HITL items: ${hitl.join(", ")}`);
  }
  if (unknowns.length > 0) {
    console.log(`   Unknowns: ${unknowns.join(", ")}`);
  }
} catch (error) {
  console.error(`❌ Error writing trace log: ${error.message}`);
  process.exit(1);
}
