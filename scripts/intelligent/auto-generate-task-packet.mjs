#!/usr/bin/env node
// Auto-generate task packet JSON from code changes
// Usage: node scripts/intelligent/auto-generate-task-packet.mjs [--task-id TASK-XXX] [--base-ref main]

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const TASK_ID = process.argv.find((arg) => arg.startsWith("--task-id="))?.split("=")[1];
const BASE_REF = process.argv.find((arg) => arg.startsWith("--base-ref="))?.split("=")[1] || "main";
const DRY_RUN = process.argv.includes("--dry-run");

function detectChangeType(changedFiles, diffContent) {
  const files = changedFiles.join(" ").toLowerCase();
  const diff = diffContent.toLowerCase();

  // Security changes
  if (files.includes("auth") || files.includes("security") || files.includes("payment") || diff.includes("password") || diff.includes("secret") || diff.includes("token")) {
    return "security";
  }

  // API changes
  if (files.includes("api/") || files.includes("routes") || files.includes("endpoint") || files.includes("openapi")) {
    return "api_change";
  }

  // Cross-module (check for cross-feature imports)
  if (diff.includes("from 'packages/features/") && diff.match(/from 'packages\/features\/\w+\//g)?.length > 1) {
    return "cross_module";
  }

  // Feature changes
  if (files.includes("feature") || files.includes("screen") || files.includes("component")) {
    return "feature";
  }

  // Default to non_doc_change
  return "non_doc_change";
}

function getAffectedModules(changedFiles) {
  const modules = new Set();

  for (const file of changedFiles) {
    // Extract module from path
    const moduleMatch = file.match(/packages\/features\/(\w+)\//);
    if (moduleMatch) {
      modules.add(moduleMatch[1]);
    }

    // Check apps
    if (file.startsWith("apps/api/")) modules.add("api");
    if (file.startsWith("apps/mobile/")) modules.add("mobile");
    if (file.startsWith("apps/web/")) modules.add("web");
  }

  return Array.from(modules);
}

function getRequiredArtifacts(changeType) {
  const requirements = {
    feature: ["task_packet", "trace_log", "tests"],
    api_change: ["task_packet", "adr", "trace_log", "openapi_update"],
    security: ["hitl", "trace_log", "security_tests"],
    cross_module: ["adr", "task_packet", "trace_log"],
    non_doc_change: ["agent_log", "trace_log", "reasoning_summary"],
  };

  return requirements[changeType] || [];
}

function analyzeCodeChanges(baseRef) {
  try {
    const changedFiles = execSync(`git diff --name-only ${baseRef}...HEAD`, { encoding: "utf8", cwd: REPO_ROOT })
      .trim()
      .split("\n")
      .filter(Boolean);

    const diffContent = execSync(`git diff ${baseRef}...HEAD`, { encoding: "utf8", cwd: REPO_ROOT });

    const changeType = detectChangeType(changedFiles, diffContent);
    const affectedModules = getAffectedModules(changedFiles);
    const requiredArtifacts = getRequiredArtifacts(changeType);

    // Count lines changed
    const stats = execSync(`git diff --stat ${baseRef}...HEAD`, { encoding: "utf8", cwd: REPO_ROOT });
    const additionsMatch = stats.match(/(\d+)\s+insertion/);
    const deletionsMatch = stats.match(/(\d+)\s+deletion/);
    const additions = additionsMatch ? parseInt(additionsMatch[1]) : 0;
    const deletions = deletionsMatch ? parseInt(deletionsMatch[1]) : 0;

    return {
      changedFiles,
      changeType,
      affectedModules,
      requiredArtifacts,
      additions,
      deletions,
      totalChanges: additions + deletions,
    };
  } catch (e) {
    console.error("Error analyzing changes:", e.message);
    return null;
  }
}

function generateTaskPacket(taskId, analysis) {
  const timestamp = new Date().toISOString();
  const packetPath = path.join(REPO_ROOT, ".repo/tasks/packets", `${taskId}-packet.json`);

  const packet = {
    task_id: taskId,
    generated_at: timestamp,
    change_type: analysis.changeType,
    affected_modules: analysis.affectedModules,
    files_modified: analysis.changedFiles,
    change_summary: {
      additions: analysis.additions,
      deletions: analysis.deletions,
      total_changes: analysis.totalChanges,
      file_count: analysis.changedFiles.length,
    },
    required_artifacts: analysis.requiredArtifacts,
    artifacts_status: {},
    verification: {
      tests_passing: null,
      coverage_met: null,
      lint_passing: null,
      type_check_passing: null,
    },
    risks: [],
    rollback_plan: "",
    notes: "Auto-generated task packet. Please review and complete.",
  };

  // Initialize artifact status
  for (const artifact of analysis.requiredArtifacts) {
    packet.artifacts_status[artifact] = "pending";
  }

  return { packet, packetPath };
}

function main() {
  console.log("📦 Auto-Generating Task Packet\n");

  if (!TASK_ID) {
    console.error("❌ Task ID required. Use --task-id=TASK-XXX");
    process.exit(1);
  }

  console.log(`📋 Task: ${TASK_ID}`);
  console.log(`🔍 Analyzing changes from ${BASE_REF}...\n`);

  const analysis = analyzeCodeChanges(BASE_REF);
  if (!analysis) {
    console.error("❌ Failed to analyze code changes");
    process.exit(1);
  }

  console.log(`   Change Type: ${analysis.changeType}`);
  console.log(`   Affected Modules: ${analysis.affectedModules.join(", ") || "None"}`);
  console.log(`   Files Changed: ${analysis.changedFiles.length}`);
  console.log(`   Lines: +${analysis.additions} -${analysis.deletions}`);
  console.log(`   Required Artifacts: ${analysis.requiredArtifacts.join(", ")}\n`);

  const { packet, packetPath } = generateTaskPacket(TASK_ID, analysis);

  if (DRY_RUN) {
    console.log("[DRY RUN] Would create:");
    console.log(JSON.stringify(packet, null, 2));
    return;
  }

  // Ensure directory exists
  const packetDir = path.dirname(packetPath);
  if (!fs.existsSync(packetDir)) {
    fs.mkdirSync(packetDir, { recursive: true });
  }

  // Check if packet already exists
  if (fs.existsSync(packetPath)) {
    console.log(`⚠️  Task packet already exists: ${packetPath}`);
    console.log("   Use --force to overwrite");
    return;
  }

  fs.writeFileSync(packetPath, JSON.stringify(packet, null, 2) + "\n");
  console.log(`✅ Task packet created: ${packetPath}`);
  console.log("\n📝 Next steps:");
  console.log("   1. Review and complete artifact status");
  console.log("   2. Add risks and rollback plan");
  console.log("   3. Update verification status");
}

main();
