#!/usr/bin/env node
// Watchdog script to auto-update copilot instructions and AGENTS.md files
// when .repo/policy/constitution.json changes
// Usage: node scripts/watch-constitution.mjs

import { watch } from "fs";
import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CONSTITUTION_PATH = path.resolve(process.cwd(), ".repo/policy/constitution.json");

// Debounce timer to avoid excessive updates
let updateTimer = null;
const DEBOUNCE_MS = 500; // Wait 500ms after last change before updating

function updateConstitution() {
  console.log("\nUpdating copilot instructions and AGENTS.md files...");
  try {
    execSync(
      `npm run compile:constitution`,
      { stdio: "inherit", cwd: process.cwd() }
    );
    console.log(`Constitution compiled at ${new Date().toLocaleTimeString()}\n`);
  } catch (error) {
    console.error(`Error compiling constitution:`, error.message);
  }
}

function scheduleUpdate() {
  // Clear existing timer
  if (updateTimer) {
    clearTimeout(updateTimer);
  }

  console.log(`Change detected in ${CONSTITUTION_PATH}`);

  // Schedule update after debounce period
  updateTimer = setTimeout(() => {
    updateConstitution();
    updateTimer = null;
  }, DEBOUNCE_MS);
}

console.log("Starting constitution watchdog...");
console.log(`   Watching: ${CONSTITUTION_PATH}`);
console.log("\n   Press Ctrl+C to stop\n");

// Check if constitution file exists
if (!fs.existsSync(CONSTITUTION_PATH)) {
  console.error(`Error: Constitution file not found at ${CONSTITUTION_PATH}`);
  process.exit(1);
}

// Watch the constitution file
try {
  watch(
    CONSTITUTION_PATH,
    { recursive: false },
    (eventType, filename) => {
      if (!filename) return;
      
      // Only react to changes (not deletions)
      if (eventType === 'change') {
        scheduleUpdate();
      }
    }
  );

  // Initial compilation
  updateConstitution();

  // Keep process alive
  process.on("SIGINT", () => {
    console.log("\n\nStopping watchdog...");
    process.exit(0);
  });
} catch (error) {
  console.error(`Error setting up file watcher:`, error.message);
  process.exit(1);
}
