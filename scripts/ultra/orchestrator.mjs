#!/usr/bin/env node
/**
 * Intelligent Workflow Orchestrator
 * Orchestrates all automations intelligently, optimizing workflows and preventing conflicts
 */

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { LearningSystem, REPO_ROOT } from "./shared-infrastructure.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const learning = new LearningSystem();

// All automations organized by tier and priority
const automations = {
  tier1: [
    "intelligent-auto-refactor",
    "predictive-bug-detector",
    "intelligent-migration-assistant",
    "auto-api-contract-generator",
    "intelligent-test-data-generator",
  ],
  tier2: [
    "auto-error-recovery",
    "predictive-maintenance",
    "intelligent-dependency-updater",
  ],
  tier3: [
    "semantic-code-search",
    "auto-integration-test-generator",
    "intelligent-code-review-bot",
    "auto-architecture-evolution",
  ],
  tier4: [
    "intelligent-test-coverage-analyzer",
    "auto-performance-profiling",
    "intelligent-refactoring-suggestion",
  ],
  tier5: [
    "self-healing-codebase",
    "autonomous-architecture-evolution",
    "self-optimizing-performance",
    "intelligent-dependency-ecosystem",
    "self-documenting-codebase",
  ],
};

async function runAutomation(name, tier) {
  const scriptPath = path.join(__dirname, `${name}.mjs`);
  
  if (!fs.existsSync(scriptPath)) {
    console.log(`⚠️  Script not found: ${name}`);
    return { success: false, error: "Script not found" };
  }

  try {
    console.log(`\n🚀 Running: ${name}`);
    execSync(`node ${scriptPath}`, {
      cwd: REPO_ROOT,
      stdio: "inherit",
    });
    
    learning.recordOutcome("orchestrator", "run_automation", "success", {
      automation: name,
      tier,
    });
    
    return { success: true };
  } catch (error) {
    console.error(`❌ Error running ${name}:`, error.message);
    learning.recordOutcome("orchestrator", "run_automation", "failure", {
      automation: name,
      tier,
      error: error.message,
    });
    return { success: false, error: error.message };
  }
}

async function optimizeExecutionOrder() {
  // Analyze which automations should run in what order
  // In production, would use ML to optimize based on outcomes
  return {
    sequential: ["predictive-bug-detector", "intelligent-auto-refactor"],
    parallel: ["auto-api-contract-generator", "intelligent-test-data-generator"],
  };
}

async function preventConflicts() {
  // Check for potential conflicts between automations
  // In production, would analyze dependencies and conflicts
  return { conflicts: [] };
}

async function main() {
  console.log("🎼 Intelligent Workflow Orchestrator");
  console.log("====================================\n");

  const args = process.argv.slice(2);
  const tier = args.find((arg) => arg.startsWith("--tier="))?.split("=")[1];
  const automation = args.find((arg) => arg.startsWith("--automation="))?.split("=")[1];
  const all = args.includes("--all");

  if (automation) {
    // Run specific automation
    await runAutomation(automation, "custom");
    return;
  }

  if (tier) {
    // Run all automations in a specific tier
    const tierAutomations = automations[`tier${tier}`] || [];
    console.log(`Running Tier ${tier} automations...\n`);
    
    for (const name of tierAutomations) {
      await runAutomation(name, tier);
    }
    return;
  }

  if (all) {
    // Run all automations in order
    console.log("Running all automations...\n");
    
    for (const [tierName, tierAutomations] of Object.entries(automations)) {
      console.log(`\n📦 ${tierName.toUpperCase()}`);
      console.log("=".repeat(50));
      
      for (const name of tierAutomations) {
        await runAutomation(name, tierName);
      }
    }
    return;
  }

  // Default: Run Phase 1 (Tier 1) automations
  console.log("Running Phase 1 (Tier 1) automations...\n");
  console.log("Use --all to run all automations, --tier=N for specific tier\n");

  for (const name of automations.tier1) {
    await runAutomation(name, "tier1");
  }

  const successRate = learning.getSuccessRate("orchestrator");
  console.log(`\n📊 Orchestrator success rate: ${(successRate * 100).toFixed(1)}%`);
}

main().catch((error) => {
  console.error("❌ Orchestrator error:", error);
  process.exit(1);
});
