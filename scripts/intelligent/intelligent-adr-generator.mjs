#!/usr/bin/env node
// Intelligent ADR Auto-Generation with context, options, and consequences
// Usage: node scripts/intelligent/intelligent-adr-generator.mjs [--trigger cross_module|api_change|schema] [--force]

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const TRIGGER = process.argv.find((arg) => arg.startsWith("--trigger="))?.split("=")[1];
const FORCE = process.argv.includes("--force");

function detectADRTriggers() {
  try {
    const changedFiles = execSync("git diff --name-only HEAD~1 HEAD", { encoding: "utf8", cwd: REPO_ROOT })
      .trim()
      .split("\n")
      .filter(Boolean);

    const diffContent = execSync("git diff HEAD~1 HEAD", { encoding: "utf8", cwd: REPO_ROOT });

    const triggers = [];

    // Check for cross-module imports
    const crossModuleMatch = diffContent.match(/from ['"]packages\/features\/(\w+)\//g);
    if (crossModuleMatch && new Set(crossModuleMatch.map((m) => m.match(/\/(\w+)\//)?.[1])).size > 1) {
      triggers.push({
        type: "cross_module",
        description: "Cross-module imports detected",
        modules: Array.from(new Set(crossModuleMatch.map((m) => m.match(/\/(\w+)\//)?.[1]).filter(Boolean))),
      });
    }

    // Check for API changes
    if (changedFiles.some((f) => f.includes("api/") || f.includes("routes") || f.includes("endpoint"))) {
      triggers.push({
        type: "api_change",
        description: "API contract changes detected",
        files: changedFiles.filter((f) => f.includes("api/") || f.includes("routes")),
      });
    }

    // Check for schema changes
    if (changedFiles.some((f) => f.includes("schema") || f.includes("migration") || f.includes("drizzle"))) {
      triggers.push({
        type: "schema",
        description: "Database schema changes detected",
        files: changedFiles.filter((f) => f.includes("schema") || f.includes("migration")),
      });
    }

    return triggers;
  } catch (e) {
    return [];
  }
}

function analyzeAffectedModules(triggers) {
  const modules = new Set();
  for (const trigger of triggers) {
    if (trigger.modules) {
      trigger.modules.forEach((m) => modules.add(m));
    }
    if (trigger.files) {
      trigger.files.forEach((f) => {
        const match = f.match(/packages\/features\/(\w+)\//);
        if (match) modules.add(match[1]);
      });
    }
  }
  return Array.from(modules);
}

function getPastADRs() {
  const adrDir = path.join(REPO_ROOT, "docs/adr");
  if (!fs.existsSync(adrDir)) return [];

  const adrs = [];
  const files = fs.readdirSync(adrDir).filter((f) => f.endsWith(".md"));
  for (const file of files.slice(0, 10)) {
    // Read last 10 ADRs for pattern learning
    const content = fs.readFileSync(path.join(adrDir, file), "utf8");
    const decisionMatch = content.match(/## Decision\s*\n\s*(.+?)(?=\n##|$)/s);
    if (decisionMatch) {
      adrs.push({ file, decision: decisionMatch[1].trim() });
    }
  }
  return adrs;
}

function generateDecisionDrivers(triggers, modules) {
  const drivers = [];

  if (triggers.some((t) => t.type === "cross_module")) {
    drivers.push("Need to share functionality across modules");
    drivers.push("Maintain module boundaries while enabling collaboration");
  }

  if (triggers.some((t) => t.type === "api_change")) {
    drivers.push("API contract evolution requirements");
    drivers.push("Backward compatibility concerns");
  }

  if (triggers.some((t) => t.type === "schema")) {
    drivers.push("Database schema evolution needs");
    drivers.push("Data migration requirements");
  }

  if (modules.length > 1) {
    drivers.push(`Multiple modules affected: ${modules.join(", ")}`);
  }

  return drivers;
}

function generateOptions(triggerType) {
  const options = [];

  if (triggerType === "cross_module") {
    options.push({
      name: "Shared Package/Utility",
      pros: ["Reusable code", "Single source of truth", "Easier maintenance"],
      cons: ["Additional dependency", "Potential over-coupling"],
    });
    options.push({
      name: "Event-Based Communication",
      pros: ["Loose coupling", "Scalable", "Async communication"],
      cons: ["More complex", "Harder to debug"],
    });
    options.push({
      name: "Direct Import with ADR",
      pros: ["Simple", "Explicit dependencies"],
      cons: ["Tighter coupling", "Requires ADR documentation"],
    });
  }

  if (triggerType === "api_change") {
    options.push({
      name: "Versioned API",
      pros: ["Backward compatible", "Gradual migration"],
      cons: ["More endpoints to maintain", "Complexity"],
    });
    options.push({
      name: "Breaking Change",
      pros: ["Clean API", "Simpler long-term"],
      cons: ["Requires client updates", "Migration needed"],
    });
  }

  return options;
}

function getNextADRNumber() {
  const adrDir = path.join(REPO_ROOT, "docs/adr");
  if (!fs.existsSync(adrDir)) {
    fs.mkdirSync(adrDir, { recursive: true });
    return 1;
  }

  const files = fs.readdirSync(adrDir).filter((f) => f.match(/^ADR-\d+\.md$/));
  if (files.length === 0) return 1;

  const numbers = files.map((f) => parseInt(f.match(/ADR-(\d+)\.md/)?.[1] || "0")).filter((n) => !isNaN(n));
  return numbers.length > 0 ? Math.max(...numbers) + 1 : 1;
}

function generateADR(triggers, modules) {
  const adrNumber = getNextADRNumber();
  const adrId = `ADR-${adrNumber.toString().padStart(4, "0")}`;
  const adrPath = path.join(REPO_ROOT, "docs/adr", `${adrId}.md`);

  const primaryTrigger = TRIGGER || triggers[0]?.type || "cross_module";
  const decisionDrivers = generateDecisionDrivers(triggers, modules);
  const options = generateOptions(primaryTrigger);

  const template = `# ${adrId}: [Decision Title - Please Fill In]

**Status:** Proposed  
**Date:** ${new Date().toISOString().split("T")[0]}  
**Context:** ${triggers.map((t) => t.description).join("; ")}

## Context

${triggers.map((t) => `- ${t.description}`).join("\n")}

This ADR was auto-generated from detected triggers. Please complete the decision details below.

## Decision Drivers

${decisionDrivers.map((d) => `- ${d}`).join("\n")}

## Considered Options

${options
  .map(
    (opt, i) => `### Option ${i + 1}: ${opt.name}

**Pros:**
${opt.pros.map((p) => `- ${p}`).join("\n")}

**Cons:**
${opt.cons.map((c) => `- ${c}`).join("\n")}`,
  )
  .join("\n\n")}

## Decision

[Chosen option and rationale - **REQUIRED**]

## Consequences

### Positive
- [To be filled based on chosen option]

### Negative
- [To be filled based on chosen option]

## Modules Affected

${modules.map((m) => `- ${m}`).join("\n")}

## Boundary Impact

[Describe impact on module boundaries - **REQUIRED for cross-module changes**]

## Migration Notes

[If applicable, describe migration steps]

## HITL Items

- [List related HITL items if any]

## Notes

- Auto-generated on ${new Date().toISOString()}
- Review and complete all sections marked as **REQUIRED**
- Link this ADR in PR description
`;

  return { adrId, adrPath, template };
}

function main() {
  console.log("🧠 Intelligent ADR Generator\n");

  const triggers = TRIGGER ? [{ type: TRIGGER, description: `Manual trigger: ${TRIGGER}` }] : detectADRTriggers();

  if (triggers.length === 0 && !TRIGGER) {
    console.log("✅ No ADR triggers detected");
    return;
  }

  console.log(`🔍 Detected triggers:`);
  triggers.forEach((t) => console.log(`   - ${t.description}`));

  const modules = analyzeAffectedModules(triggers);
  console.log(`📦 Affected modules: ${modules.join(", ") || "None"}\n`);

  const { adrId, adrPath, template } = generateADR(triggers, modules);

  if (fs.existsSync(adrPath) && !FORCE) {
    console.log(`⚠️  ADR already exists: ${adrPath}`);
    console.log("   Use --force to overwrite");
    return;
  }

  fs.writeFileSync(adrPath, template);
  console.log(`✅ ADR generated: ${adrPath}`);
  console.log("\n📝 Next steps:");
  console.log("   1. Fill in decision title");
  console.log("   2. Complete decision section (REQUIRED)");
  console.log("   3. Document consequences");
  console.log("   4. Describe boundary impact (if cross-module)");
  console.log("   5. Link ADR in PR description");
}

main();
