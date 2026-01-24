#!/usr/bin/env node

/**
 * AGENT Ownership Consistency Checker
 *
 * Validates that AGENT ownership is used consistently across documents
 * and that the unified ownership model is documented in governance files.
 *
 * Rules:
 * - AGENT is the sole owner in P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md assignments
 * - Constitution and AI policy describe unified AGENT ownership
 *
 * Usage:
 *   node scripts/tools/check-agent-platform.mjs [--mode=warn|fail]
 *
 * Exit codes:
 *   0 - All checks passed or warnings only (WARN mode)
 *   1 - Violations found and FAIL mode enabled
 *   2 - Error running checks
 */

import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const REPO_ROOT = join(__dirname, "../..");
const TODO_PATH = join(REPO_ROOT, "P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md");
// Note: State management is now handled via .repo/policy/QUALITY_GATES.md
const STATE_PATH = join(REPO_ROOT, "docs/archive/governance/state.md");

// Read enforcement mode from environment or default to WARN
const ENFORCEMENT_MODE =
  process.env.AGENT_PLATFORM_ENFORCEMENT ||
  process.argv.find((arg) => arg.startsWith("--mode="))?.split("=")[1] ||
  "warn";

function checkAgentPlatform() {
  console.log("🤖 AGENT Ownership Consistency Checker");
  console.log("=======================================\n");
  console.log(`Enforcement Mode: ${ENFORCEMENT_MODE.toUpperCase()}\n`);

  const violations = [];

  // Check 1: P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md uses unified ownership schema
  console.log(
    "📋 Check 1: P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md Ownership Schema",
  );
  console.log("-------------------------------------");

  if (!existsSync(TODO_PATH)) {
    console.error(
      `❌ P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md not found at: ${TODO_PATH}`,
    );
    violations.push(
      "P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md file not found",
    );
  } else {
    try {
      const todoContent = readFileSync(TODO_PATH, "utf-8");

      // Check for unified ownership schema presence
      if (!todoContent.includes("**Owner**: `AGENT`")) {
        violations.push(
          "P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md missing unified AGENT ownership schema",
        );
        console.error(
          "❌ P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md does not contain unified AGENT ownership schema",
        );
      } else {
        console.log(
          "✅ P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md contains unified AGENT ownership schema",
        );
      }

      // Check for legacy ownership references
      if (
        todoContent.includes("GitHub Agent (Primary)") ||
        todoContent.includes("Codex Agent (Secondary)") ||
        todoContent.includes("Owner: Trevor")
      ) {
        violations.push(
          "P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md contains legacy ownership references",
        );
        console.error(
          "❌ P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md still contains legacy ownership references",
        );
      }

      // Check for Platform field in schema
      if (!todoContent.includes("**Platform**:")) {
        violations.push(
          "P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md schema missing Platform field",
        );
        console.warn(
          "⚠️  P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md schema should include Platform field",
        );
      } else {
        console.log(
          "✅ P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md includes Platform field in schema",
        );
      }
    } catch (error) {
      console.error(
        `❌ Error reading P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md: ${error.message}`,
      );
      violations.push(
        `Error reading P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md: ${error.message}`,
      );
    }
  }

  console.log("");

  // Check 2: Verify constitution has Agent Responsibility Model
  console.log("📜 Check 2: Constitution Has Agent Model");
  console.log("------------------------------------------");

  const constitutionPath = join(REPO_ROOT, ".repo/policy/CONSTITUTION.md");
  if (!existsSync(constitutionPath)) {
    console.error(`❌ Constitution not found at: ${constitutionPath}`);
    violations.push("Constitution file not found");
  } else {
    try {
      const constitutionContent = readFileSync(constitutionPath, "utf-8");

      if (!constitutionContent.includes("Agent Responsibility Model")) {
        violations.push(
          "Constitution missing Agent Responsibility Model section",
        );
        console.error(
          "❌ Constitution does not include Agent Responsibility Model",
        );
      } else {
        console.log("✅ Constitution includes Agent Responsibility Model");
      }

      if (!constitutionContent.includes("Unified AGENT Ownership")) {
        violations.push("Constitution missing Unified AGENT Ownership");
        console.error("❌ Constitution missing Unified AGENT Ownership");
      } else {
        console.log("✅ Constitution defines Unified AGENT Ownership");
      }
    } catch (error) {
      console.error(`❌ Error reading constitution: ${error.message}`);
      violations.push(`Error reading constitution: ${error.message}`);
    }
  }

  console.log("");

  // Check 3: Verify state.md has enforcement toggle
  console.log("📊 Check 3: State.md Enforcement Toggle");
  console.log("----------------------------------------");

  if (!existsSync(STATE_PATH)) {
    console.error(`❌ State.md not found at: ${STATE_PATH}`);
    violations.push("State.md file not found");
  } else {
    try {
      const stateContent = readFileSync(STATE_PATH, "utf-8");

      if (!stateContent.includes("AGENT Ownership Consistency")) {
        violations.push("State.md missing AGENT Ownership Consistency toggle");
        console.error(
          "❌ State.md does not include AGENT Ownership Consistency toggle",
        );
      } else {
        console.log("✅ State.md includes AGENT Ownership Consistency toggle");
      }

      // Check if enforcement mode matches expectation
      if (
        stateContent.includes("AGENT Ownership Consistency") &&
        stateContent.includes("WARN")
      ) {
        console.log(
          "✅ State.md shows WARN mode (as expected for initial rollout)",
        );
      }
    } catch (error) {
      console.error(`❌ Error reading state.md: ${error.message}`);
      violations.push(`Error reading state.md: ${error.message}`);
    }
  }

  console.log("");

  // Check 4: AI contribution policy updated
  console.log("🤖 Check 4: AI Contribution Policy");
  console.log("------------------------------------");

  const aiPolicyPath = join(REPO_ROOT, "docs/ai/ai_contribution_policy.md");
  if (!existsSync(aiPolicyPath)) {
    console.error(`❌ AI contribution policy not found at: ${aiPolicyPath}`);
    violations.push("AI contribution policy file not found");
  } else {
    try {
      const aiPolicyContent = readFileSync(aiPolicyPath, "utf-8");

      if (!aiPolicyContent.includes("Unified AGENT Ownership")) {
        violations.push("AI policy missing Unified AGENT Ownership");
        console.error(
          "❌ AI contribution policy missing Unified AGENT Ownership section",
        );
      } else {
        console.log(
          "✅ AI contribution policy includes Unified AGENT Ownership",
        );
      }
    } catch (error) {
      console.error(
        `❌ Error reading AI contribution policy: ${error.message}`,
      );
      violations.push(`Error reading AI contribution policy: ${error.message}`);
    }
  }

  console.log("");

  // Summary
  console.log("📊 Summary:");
  console.log(`   Checks run: 4`);
  console.log(`   Violations found: ${violations.length}`);
  console.log(`   Enforcement mode: ${ENFORCEMENT_MODE.toUpperCase()}`);

  if (violations.length > 0) {
    console.log("\n⚠️  Violations detected:\n");
    violations.forEach((v, i) => {
      console.log(`   ${i + 1}. ${v}`);
    });

    if (ENFORCEMENT_MODE === "fail") {
      console.error("\n❌ FAILED: AGENT ownership violations detected!");
      console.error("\n📝 Action required:");
      console.error("   1. Review violations listed above");
      console.error(
        "   2. Update P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md to use AGENT-only ownership",
      );
      console.error(
        "   3. Ensure constitution includes Agent Responsibility Model",
      );
      console.error("   4. Ensure state.md has enforcement toggle");
      console.error(
        "   5. Update AI contribution policy with unified ownership guidelines",
      );
      console.error("   6. Commit and push changes");
      console.error(
        "\n   See: docs/governance/constitution.md for full requirements",
      );
      return 1;
    } else {
      console.warn(
        "\n⚠️  WARN MODE: Violations detected but not failing build",
      );
      console.warn("   These will fail once enforcement mode is set to FAIL");
      console.warn("   See: docs/governance/state.md to toggle enforcement");
      return 0;
    }
  }

  console.log("\n✅ All AGENT ownership checks passed!");
  return 0;
}

// Run checker
try {
  const exitCode = checkAgentPlatform();
  process.exit(exitCode);
} catch (error) {
  console.error(`\n❌ Fatal error: ${error.message}`);
  console.error(error.stack);
  process.exit(2);
}
