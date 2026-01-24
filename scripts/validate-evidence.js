#!/usr/bin/env node

/**
 * Evidence Validation Script
 *
 * Validates evidence against EVIDENCE_SCHEMA.json
 *
 * Usage:
 *   node .repo/automation/scripts/validate-evidence.js <evidence-file>
 *
 * Exit codes:
 *   0 - Valid
 *   1 - Invalid
 */

import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const REPO_ROOT = join(__dirname, "../../../..");
const EVIDENCE_SCHEMA_PATH = join(
  REPO_ROOT,
  ".repo/templates/EVIDENCE_SCHEMA.json",
);

function main() {
  const evidencePath = process.argv[2];

  if (!evidencePath) {
    console.error("Usage: node validate-evidence.js <evidence-file>");
    process.exit(1);
  }

  if (!existsSync(evidencePath)) {
    console.error(`Evidence file not found: ${evidencePath}`);
    process.exit(1);
  }

  if (!existsSync(EVIDENCE_SCHEMA_PATH)) {
    console.error(`Schema not found: ${EVIDENCE_SCHEMA_PATH}`);
    process.exit(1);
  }

  const schema = JSON.parse(readFileSync(EVIDENCE_SCHEMA_PATH, "utf-8"));
  const evidence = JSON.parse(readFileSync(evidencePath, "utf-8"));

  const errors = [];

  // Check required fields
  for (const field of schema.required || []) {
    if (!(field in evidence)) {
      errors.push(`Missing required field: ${field}`);
    }
  }

  // Check field types and enums
  for (const [field, spec] of Object.entries(schema.properties || {})) {
    if (field in evidence) {
      const value = evidence[field];

      if (spec.type === "string" && typeof value !== "string") {
        errors.push(`Field '${field}' must be a string`);
      } else if (spec.type === "array" && !Array.isArray(value)) {
        errors.push(`Field '${field}' must be an array`);
      } else if (
        (spec.type === "object" && typeof value !== "object") ||
        Array.isArray(value)
      ) {
        errors.push(`Field '${field}' must be an object`);
      }

      // Check enum values
      if (spec.enum && !spec.enum.includes(value)) {
        errors.push(`Field '${field}' must be one of: ${spec.enum.join(", ")}`);
      }
    }
  }

  if (errors.length > 0) {
    console.error("❌ Evidence validation failed:");
    errors.forEach((e) => console.error(`   - ${e}`));
    process.exit(1);
  }

  console.log("✅ Evidence is valid");
  process.exit(0);
}

main();
