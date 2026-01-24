#!/usr/bin/env node
// Generate .agent-context.json files for folders that don't have them
// Usage: node scripts/generate-missing-agent-contexts.mjs [--dry-run] [--folder <path>]

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DRY_RUN = process.argv.includes("--dry-run");
const SPECIFIC_FOLDER = process.argv.find((arg) => arg.startsWith("--folder="))?.split("=")[1];

// Directories to ignore
const IGNORE_DIRS = new Set([
  "node_modules",
  ".git",
  ".expo",
  ".metro-cache",
  "__pycache__",
  ".next",
  "dist",
  "build",
  ".cache",
  ".turbo",
  "coverage",
  ".nyc_output",
  ".husky",
  ".vscode",
  ".github",
  ".repo",
]);

// Directories that should have agent context files
const TARGET_DIRS = [
  "apps",
  "apps/api",
  "apps/mobile",
  "apps/web",
  "packages",
  "packages/features",
  "packages/platform",
  "packages/design-system",
  "packages/contracts",
  "frontend",
  "scripts",
];

function shouldGenerateContext(dirPath) {
  const dirName = path.basename(dirPath);
  const relativePath = path.relative(process.cwd(), dirPath);

  // Skip ignored directories
  if (IGNORE_DIRS.has(dirName) || dirName.startsWith(".")) {
    return false;
  }

  // Skip if already has context file
  const contextPath = path.join(dirPath, ".agent-context.json");
  if (fs.existsSync(contextPath)) {
    return false;
  }

  // Only generate for target directories or subdirectories of target dirs
  const isTargetDir = TARGET_DIRS.some((target) => {
    return relativePath === target || relativePath.startsWith(target + path.sep);
  });

  // Also generate for directories that have source files
  const hasSourceFiles = fs.readdirSync(dirPath).some((file) => {
    const filePath = path.join(dirPath, file);
    try {
      const stat = fs.statSync(filePath);
      if (stat.isFile()) {
        const ext = path.extname(file);
        return [".ts", ".tsx", ".js", ".jsx", ".py"].includes(ext);
      }
    } catch (e) {
      // Ignore
    }
    return false;
  });

  return isTargetDir || hasSourceFiles;
}

function generateContextFile(dirPath) {
  const relativePath = path.relative(process.cwd(), dirPath).replace(/\\/g, "/");
  const contextPath = path.join(dirPath, ".agent-context.json");

  const template = {
    $schema: "../../.repo/templates/AGENT_CONTEXT_SCHEMA.json",
    version: "1.0.0",
    type: "folder_context",
    folder: {
      path: relativePath || ".",
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
      guide: `${relativePath || "."}/.AGENT.md`,
      index: `${relativePath || "."}/INDEX.json`,
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

  if (DRY_RUN) {
    console.log(`[DRY RUN] Would create: ${contextPath}`);
  } else {
    fs.writeFileSync(contextPath, JSON.stringify(template, null, 2) + "\n");
    console.log(`✅ Created: ${contextPath}`);
  }
}

function scanDirectory(dirPath, depth = 0) {
  if (depth > 10) return; // Limit recursion

  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.isDirectory() && !IGNORE_DIRS.has(entry.name)) {
        const fullPath = path.join(dirPath, entry.name);

        if (shouldGenerateContext(fullPath)) {
          generateContextFile(fullPath);
        }

        // Recurse into subdirectories
        scanDirectory(fullPath, depth + 1);
      }
    }
  } catch (e) {
    // Ignore errors (permissions, etc.)
  }
}

// Main execution
console.log("🔍 Scanning for folders missing .agent-context.json files...\n");

if (SPECIFIC_FOLDER) {
  const fullPath = path.resolve(process.cwd(), SPECIFIC_FOLDER);
  if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
    if (shouldGenerateContext(fullPath)) {
      generateContextFile(fullPath);
    } else {
      console.log(`ℹ️  ${SPECIFIC_FOLDER} already has .agent-context.json or doesn't need one`);
    }
  } else {
    console.error(`❌ Directory not found: ${SPECIFIC_FOLDER}`);
    process.exit(1);
  }
} else {
  scanDirectory(process.cwd());
}

if (DRY_RUN) {
  console.log("\n[DRY RUN] No files were created. Run without --dry-run to generate files.");
} else {
  console.log("\n✅ Scan complete!");
}
