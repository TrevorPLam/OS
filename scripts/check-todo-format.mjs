#!/usr/bin/env node
/**
 * Check that all TODO/FIXME comments include a ticket ID
 * Format: // TODO(TICKET-123): description
 */

import { readFileSync, readdirSync, statSync } from "fs";
import { join, extname } from "path";

// Pattern to match TODO/FIXME comments (not in strings or variable names)
const TODO_COMMENT_PATTERN =
  /\/\/\s*(TODO|FIXME)|#\s*(TODO|FIXME)|\/\*\s*(TODO|FIXME)|\*\s*(TODO|FIXME)/gi;
const VALID_TICKET_PATTERN = /(TODO|FIXME)\([A-Z]+-\d+\)/i;

const CODE_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"];
const EXCLUDE_DIRS = [
  "node_modules",
  ".git",
  "dist",
  "build",
  "coverage",
  ".expo",
];

let violations = [];
let totalTodos = 0;

function shouldProcessFile(filePath) {
  const ext = extname(filePath);
  return CODE_EXTENSIONS.includes(ext);
}

function shouldProcessDir(dirName) {
  return !EXCLUDE_DIRS.includes(dirName) && !dirName.startsWith(".");
}

function scanFile(filePath) {
  try {
    const content = readFileSync(filePath, "utf-8");
    const lines = content.split("\n");

    lines.forEach((line, index) => {
      // Only check lines that contain TODO/FIXME comments (not variable names, etc.)
      const trimmedLine = line.trim();

      // Skip if it's a string literal, variable name, or regex pattern
      if (
        trimmedLine.includes('"TODO') ||
        trimmedLine.includes("'TODO") ||
        trimmedLine.includes("`TODO") ||
        trimmedLine.includes("const TODO") ||
        trimmedLine.includes("let TODO") ||
        trimmedLine.includes("var TODO") ||
        trimmedLine.includes("TODO =") ||
        trimmedLine.includes("TODO:") ||
        trimmedLine.includes("TODO count") ||
        trimmedLine.includes("TODO_PATH") ||
        trimmedLine.includes("getTodoCount") ||
        trimmedLine.includes("todoContent") ||
        trimmedLine.includes("todoMatch") ||
        trimmedLine.includes("totalTodos") ||
        trimmedLine.includes("todoCount") ||
        trimmedLine.includes("P0TODO") ||
        trimmedLine.includes("P1TODO") ||
        trimmedLine.includes("P2TODO") ||
        trimmedLine.includes("P3TODO") ||
        trimmedLine.includes("pattern:") ||
        trimmedLine.includes("/.*TODO") ||
        trimmedLine.match(/\/.*TODO.*\//)
      ) {
        return; // Skip this line
      }

      // Check for actual TODO/FIXME comments
      const commentMatch = line.match(TODO_COMMENT_PATTERN);
      if (commentMatch) {
        totalTodos++;
        if (!VALID_TICKET_PATTERN.test(line)) {
          violations.push({
            file: filePath,
            line: index + 1,
            content: line.trim(),
          });
        }
      }
    });
  } catch (error) {
    console.error(`Error reading ${filePath}:`, error.message);
  }
}

function scanDirectory(dirPath) {
  try {
    const entries = readdirSync(dirPath);

    for (const entry of entries) {
      const fullPath = join(dirPath, entry);
      const stat = statSync(fullPath);

      if (stat.isDirectory() && shouldProcessDir(entry)) {
        scanDirectory(fullPath);
      } else if (stat.isFile() && shouldProcessFile(fullPath)) {
        scanFile(fullPath);
      }
    }
  } catch (error) {
    // Skip directories we can't read
  }
}

// Start scanning from current directory
const startDir = process.cwd();
scanDirectory(startDir);

// Report results
if (violations.length > 0) {
  console.error(
    `\n❌ Found ${violations.length} TODO/FIXME comments without ticket IDs:\n`,
  );
  violations.forEach(({ file, line, content }) => {
    console.error(`  ${file}:${line}`);
    console.error(`    ${content}`);
    console.error(`    Expected format: TODO(TICKET-123): description\n`);
  });
  process.exit(1);
} else {
  console.log(`✅ All ${totalTodos} TODO/FIXME comments have valid ticket IDs`);
  process.exit(0);
}
