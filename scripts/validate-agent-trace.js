#!/usr/bin/env node
// /.repo/automation/scripts/validate-agent-trace.js
// Validate trace logs against AGENT_TRACE_SCHEMA.json using JSON schema validation

const fs = require("fs");
const path = require("path");

// Colors for output
const RED = "\x1b[31m";
const GREEN = "\x1b[32m";
const YELLOW = "\x1b[33m";
const RESET = "\x1b[0m";

function logError(msg) {
  console.error(`${RED}✗ ${msg}${RESET}`);
}

function logSuccess(msg) {
  console.log(`${GREEN}✓ ${msg}${RESET}`);
}

function logWarning(msg) {
  console.warn(`${YELLOW}⚠ ${msg}${RESET}`);
}

function validateTraceLog(traceFile, schemaFile) {
  // Read files
  let traceData, schemaData;

  try {
    traceData = JSON.parse(fs.readFileSync(traceFile, "utf8"));
  } catch (e) {
    logError(`Invalid JSON in trace log: ${traceFile}`);
    console.error(e.message);
    return false;
  }

  try {
    schemaData = JSON.parse(fs.readFileSync(schemaFile, "utf8"));
  } catch (e) {
    logError(`Invalid JSON in schema: ${schemaFile}`);
    console.error(e.message);
    return false;
  }

  // Check required fields from schema
  const required = schemaData.required || [];
  const missing = required.filter((field) => !(field in traceData));

  if (missing.length > 0) {
    logError(`Missing required fields: ${missing.join(", ")}`);
    return false;
  }

  // Validate field types
  const properties = schemaData.properties || {};
  let valid = true;

  for (const [field, spec] of Object.entries(properties)) {
    if (!(field in traceData)) continue; // Optional fields

    const value = traceData[field];
    const expectedType = spec.type;

    if (expectedType === "array" && !Array.isArray(value)) {
      logError(`Field '${field}' must be an array`);
      valid = false;
    } else if (expectedType === "string" && typeof value !== "string") {
      logError(`Field '${field}' must be a string`);
      valid = false;
    } else if (
      expectedType === "object" &&
      (typeof value !== "object" || Array.isArray(value))
    ) {
      logError(`Field '${field}' must be an object`);
      valid = false;
    }
  }

  if (valid) {
    logSuccess(`Trace log validation passed: ${traceFile}`);
    return true;
  }

  return false;
}

// Main
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.error(
      "Usage: validate-agent-trace.js <trace-log-file> [schema-file]",
    );
    process.exit(1);
  }

  const traceFile = path.resolve(args[0]);
  const schemaFile =
    args[1] ||
    path.resolve(__dirname, "../../templates/AGENT_TRACE_SCHEMA.json");

  if (!fs.existsSync(traceFile)) {
    logError(`Trace log file not found: ${traceFile}`);
    process.exit(1);
  }

  if (!fs.existsSync(schemaFile)) {
    logError(`Schema file not found: ${schemaFile}`);
    process.exit(1);
  }

  const valid = validateTraceLog(traceFile, schemaFile);
  process.exit(valid ? 0 : 1);
}

module.exports = { validateTraceLog };
