#!/usr/bin/env node
// Generate .agent-context.json file for a folder
// Usage: node generate-agent-context.js <folder_path>

const fs = require("fs");
const path = require("path");

const folderPath = process.argv[2];

if (!folderPath) {
  console.error("Usage: node generate-agent-context.js <folder_path>");
  process.exit(1);
}

const schemaPath = path.resolve(
  __dirname,
  "../../templates/AGENT_CONTEXT_SCHEMA.json",
);
const template = {
  $schema: "../../.repo/templates/AGENT_CONTEXT_SCHEMA.json",
  version: "1.0.0",
  type: "folder_context",
  folder: {
    path: folderPath,
    purpose: "TODO: Describe folder purpose",
    layer: "domain",
    depends_on: [],
    used_by: [],
  },
  agent_rules: {
    can_do: [],
    cannot_do: [],
    requires_hitl: [],
  },
  patterns: {},
  boundaries: {
    can_import_from: [],
    cannot_import_from: [],
    cross_module_requires_adr: true,
  },
  quick_links: {
    guide: `${folderPath}/.AGENT.md`,
    index: `${folderPath}/INDEX.md`,
    policy: ".repo/policy/BOUNDARIES.md",
    best_practices: ".repo/policy/BESTPR.md",
  },
  common_tasks: [],
  metrics: {
    files_count: 0,
    last_modified: new Date().toISOString().split("T")[0],
    test_coverage: 0,
  },
};

const outputPath = path.join(folderPath, ".agent-context.json");
fs.writeFileSync(outputPath, JSON.stringify(template, null, 2));
console.log(`Created ${outputPath}`);
console.log("Please fill in the template with folder-specific information.");
