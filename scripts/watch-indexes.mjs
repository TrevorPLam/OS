#!/usr/bin/env node
// Watchdog script to auto-update INDEX.md files on file changes
// Usage: node scripts/watch-indexes.mjs

import { watch } from "fs";
import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const INDEX_DIRECTORIES = [
  ".",
  "apps",
  "apps/api",
  "apps/mobile",
  "apps/web",
  "assets",
  "attached_assets",
  "docs",
  "frontend",
  "packages",
  "scripts",
];

// Debounce timer to avoid excessive updates
let updateTimer = null;
const DEBOUNCE_MS = 1000; // Wait 1 second after last change before updating

function updateIndexes() {
  console.log(`\n🔄 Updating INDEX.json files...`);
  try {
    execSync(
      `node ${path.join(__dirname, "generate-index-json.mjs")}`,
      { stdio: "inherit", cwd: process.cwd() }
    );
    console.log(`✅ Indexes updated at ${new Date().toLocaleTimeString()}\n`);
  } catch (error) {
    console.error(`❌ Error updating indexes:`, error.message);
  }
}

function scheduleUpdate(changedPath) {
  // Clear existing timer
  if (updateTimer) {
    clearTimeout(updateTimer);
  }

  // Determine which index needs updating
  const relativePath = path.relative(process.cwd(), changedPath);
  const dirs = relativePath.split(path.sep);
  
  // Find the closest directory that should have an index
  let targetDir = null;
  for (let i = dirs.length; i > 0; i--) {
    const candidate = dirs.slice(0, i).join(path.sep) || ".";
    if (INDEX_DIRECTORIES.includes(candidate)) {
      targetDir = candidate;
      break;
    }
  }

  if (targetDir) {
    console.log(`📝 Change detected in ${relativePath} (will update ${targetDir}/INDEX.json)`);
  }

  // Schedule update after debounce period
  updateTimer = setTimeout(() => {
    updateIndexes();
    updateTimer = null;
  }, DEBOUNCE_MS);
}

function watchDirectory(dirPath, depth = 0) {
  if (depth > 5) return; // Limit recursion depth

  try {
    watch(
      dirPath,
      { recursive: false },
      (eventType, filename) => {
        if (!filename) return;
        
        // Ignore INDEX.json changes to avoid infinite loops
        if (filename === "INDEX.json" || filename === "INDEX.md") {
          return;
        }

        const fullPath = path.join(dirPath, filename);
        
        // Check if it's a directory we should watch
        try {
          const stats = fs.statSync(fullPath);
          if (stats.isDirectory()) {
            // Watch new subdirectory
            watchDirectory(fullPath, depth + 1);
          }
        } catch (e) {
          // Ignore stat errors
        }

        scheduleUpdate(fullPath);
      }
    );

    // Also watch subdirectories
    try {
      const entries = fs.readdirSync(dirPath, { withFileTypes: true });
      entries.forEach((entry) => {
        if (entry.isDirectory() && !entry.name.startsWith(".") && entry.name !== "node_modules") {
          watchDirectory(path.join(dirPath, entry.name), depth + 1);
        }
      });
    } catch (e) {
      // Ignore readdir errors
    }
  } catch (error) {
    // Ignore watch errors for directories we can't watch
  }
}

console.log("👀 Starting INDEX.json watchdog...");
console.log("   Watching for file changes in:");
INDEX_DIRECTORIES.forEach((dir) => {
  console.log(`   - ${dir}/`);
});
console.log("\n   Press Ctrl+C to stop\n");

// Watch all index directories
INDEX_DIRECTORIES.forEach((dir) => {
  const fullPath = path.resolve(process.cwd(), dir);
  try {
    if (fs.existsSync(fullPath)) {
      watchDirectory(fullPath);
    }
  } catch (e) {
    console.warn(`⚠️  Could not watch ${dir}:`, e.message);
  }
});

// Initial generation
updateIndexes();

// Keep process alive
process.on("SIGINT", () => {
  console.log("\n\n👋 Stopping watchdog...");
  process.exit(0);
});
