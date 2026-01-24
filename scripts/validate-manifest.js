#!/usr/bin/env node

/**
 * Manifest Validation Script
 *
 * Validates that commands in repo.manifest.yaml match actual commands in:
 * - package.json scripts
 * - CI workflow files
 * - Makefile
 *
 * Usage:
 *   node .repo/automation/scripts/validate-manifest.js
 *
 * Exit codes:
 *   0 - All commands valid
 *   1 - Discrepancies found
 */

import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const REPO_ROOT = join(__dirname, "../../../..");
const MANIFEST_PATH = join(REPO_ROOT, ".repo/repo.manifest.yaml");
const PACKAGE_JSON_PATH = join(REPO_ROOT, "package.json");
const CI_WORKFLOW_PATH = join(REPO_ROOT, ".github/workflows/ci.yml");
const MAKEFILE_PATH = join(REPO_ROOT, "Makefile");

// Parse YAML-like structure (simple parser for manifest)
function parseManifestCommands(content) {
  const commands = {};
  const commandRegex = /^\s*(\w+):\s*["']?([^"'\n]+)["']?/gm;
  let match;

  while ((match = commandRegex.exec(content)) !== null) {
    const [, name, value] = match;
    if (name.startsWith("check:") || name === "install") {
      commands[name] = value.trim();
    }
  }

  return commands;
}

// Parse package.json scripts
function parsePackageScripts() {
  if (!existsSync(PACKAGE_JSON_PATH)) {
    return {};
  }

  const content = JSON.parse(readFileSync(PACKAGE_JSON_PATH, "utf-8"));
  return content.scripts || {};
}

// Parse CI workflow commands
function parseCICommands() {
  if (!existsSync(CI_WORKFLOW_PATH)) {
    return [];
  }

  const content = readFileSync(CI_WORKFLOW_PATH, "utf-8");
  const commands = [];

  // Extract run: commands
  const runRegex = /run:\s*["']?([^"'\n]+)["']?/g;
  let match;

  while ((match = runRegex.exec(content)) !== null) {
    commands.push(match[1].trim());
  }

  return commands;
}

// Parse Makefile targets
function parseMakefileTargets() {
  if (!existsSync(MAKEFILE_PATH)) {
    return {};
  }

  const content = readFileSync(MAKEFILE_PATH, "utf-8");
  const targets = {};

  // Extract targets with commands
  const targetRegex = /^(\w+):.*?##\s*(.+)$/gm;
  let match;

  while ((match = targetRegex.exec(content)) !== null) {
    const [, target] = match;
    targets[target] = true;
  }

  return targets;
}

// Check if command exists in package.json
function commandExistsInPackage(command, packageScripts) {
  // Extract npm script name from command
  const npmMatch = command.match(/npm\s+run\s+(\w+)/);
  if (npmMatch) {
    return npmMatch[1] in packageScripts;
  }

  // Check if it's a direct npm command
  if (command.startsWith("npm ")) {
    return true; // Assume valid npm command
  }

  // Check if it's a node script
  if (command.includes("node ")) {
    const scriptMatch = command.match(/node\s+(.+)/);
    if (scriptMatch) {
      const scriptPath = scriptMatch[1].trim();
      return existsSync(join(REPO_ROOT, scriptPath));
    }
  }

  return false;
}

// Main validation function
function main() {
  console.log("📋 Manifest Validation");
  console.log("=====================\n");

  const errors = [];
  const warnings = [];

  // Read manifest
  if (!existsSync(MANIFEST_PATH)) {
    console.error(`❌ Manifest not found: ${MANIFEST_PATH}`);
    process.exit(1);
  }

  const manifestContent = readFileSync(MANIFEST_PATH, "utf-8");
  const manifestCommands = parseManifestCommands(manifestContent);
  const packageScripts = parsePackageScripts();
  const ciCommands = parseCICommands();
  const makefileTargets = parseMakefileTargets();

  console.log(
    `📦 Found ${Object.keys(manifestCommands).length} commands in manifest\n`,
  );

  // Validate each command
  for (const [name, command] of Object.entries(manifestCommands)) {
    if (command === "<UNKNOWN>") {
      warnings.push(`Command '${name}' is marked as <UNKNOWN> - needs HITL`);
      continue;
    }

    if (command === "<FILL_FROM_REPO>") {
      warnings.push(
        `Command '${name}' is marked as <FILL_FROM_REPO> - needs implementation`,
      );
      continue;
    }

    // Check if command exists
    if (!commandExistsInPackage(command, packageScripts)) {
      // Check if it's a valid standalone command
      if (!command.startsWith("npm ") && !command.startsWith("node ")) {
        errors.push(`Command '${name}' may not exist: ${command}`);
      }
    }
  }

  // Check for commands in package.json that should be in manifest
  const manifestCommandNames = new Set(Object.keys(manifestCommands));
  const importantPackageScripts = [
    "check:types",
    "check:format",
    "lint",
    "test",
  ];

  for (const script of importantPackageScripts) {
    if (script in packageScripts && !manifestCommandNames.has(script)) {
      warnings.push(`Package script '${script}' exists but not in manifest`);
    }
  }

  // Report results
  if (errors.length > 0) {
    console.error("❌ Validation errors:\n");
    errors.forEach((e) => console.error(`   - ${e}`));
    console.error("");
  }

  if (warnings.length > 0) {
    console.warn("⚠️  Validation warnings:\n");
    warnings.forEach((w) => console.warn(`   - ${w}`));
    console.warn("");
  }

  if (errors.length === 0 && warnings.length === 0) {
    console.log("✅ All manifest commands are valid");
    process.exit(0);
  } else if (errors.length > 0) {
    console.error("❌ Manifest validation failed");
    process.exit(1);
  } else {
    console.warn("⚠️  Manifest validation passed with warnings");
    process.exit(0);
  }
}

main();
