#!/usr/bin/env node
// Generate INDEX.json file for a folder
// Usage: node generate-index-json.js <folder_path>

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const folderPath = process.argv[2] || process.cwd();

if (!fs.existsSync(folderPath)) {
  console.error(`Folder not found: ${folderPath}`);
  process.exit(1);
}

function getFileInfo(filePath) {
  const stats = fs.statSync(filePath);
  const content = fs.readFileSync(filePath, "utf8");

  // Try to detect file type and key classes
  let type = "unknown";
  let keyClasses = [];

  if (filePath.endsWith(".py")) {
    type = "python";
    // Extract class definitions
    const classMatches = content.match(/^class\s+(\w+)/gm);
    if (classMatches) {
      keyClasses = classMatches.map((m) => m.replace(/^class\s+/, ""));
    }
  } else if (filePath.endsWith(".ts") || filePath.endsWith(".tsx")) {
    type = "typescript";
    // Extract class/function exports
    const exportMatches = content.match(
      /^export\s+(?:const|function|class)\s+(\w+)/gm,
    );
    if (exportMatches) {
      keyClasses = exportMatches.map((m) =>
        m.replace(/^export\s+(?:const|function|class)\s+/, ""),
      );
    }
  } else if (filePath.endsWith(".md")) {
    type = "markdown";
  } else if (filePath.endsWith(".json")) {
    type = "json";
  }

  return {
    path: path.relative(folderPath, filePath),
    type,
    key_classes: keyClasses.slice(0, 10), // Limit to 10
    line_count: content.split("\n").length,
    size_bytes: stats.size,
  };
}

function getSubfolders(dirPath) {
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isDirectory())
    .filter(
      (entry) =>
        !entry.name.startsWith(".") &&
        entry.name !== "__pycache__" &&
        entry.name !== "node_modules",
    )
    .map((entry) => ({
      path: entry.name,
      purpose: "TODO: Describe subfolder purpose",
    }));
}

function getDependencies(folderPath) {
  // Try to detect imports/dependencies
  const dependencies = {
    imports: [],
    imported_by: [],
  };

  // This is a placeholder - could be enhanced with actual import analysis
  return dependencies;
}

function main() {
  const index = {
    folder: folderPath,
    generated_at: new Date().toISOString(),
    files: [],
    subfolders: [],
    dependencies: getDependencies(folderPath),
  };

  // Get all files
  function walkDir(dir, baseDir = dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      const relativePath = path.relative(baseDir, fullPath);

      if (entry.isDirectory()) {
        if (
          !entry.name.startsWith(".") &&
          entry.name !== "__pycache__" &&
          entry.name !== "node_modules"
        ) {
          walkDir(fullPath, baseDir);
        }
      } else if (entry.isFile()) {
        // Skip hidden files and common non-code files
        if (
          !entry.name.startsWith(".") &&
          !entry.name.endsWith(".pyc") &&
          !entry.name.endsWith(".log")
        ) {
          try {
            index.files.push(getFileInfo(fullPath));
          } catch (e) {
            // Skip files that can't be read
          }
        }
      }
    }
  }

  walkDir(folderPath);

  // Get subfolders
  index.subfolders = getSubfolders(folderPath);

  // Write index
  const outputPath = path.join(folderPath, "INDEX.json");
  fs.writeFileSync(outputPath, JSON.stringify(index, null, 2));

  console.log(`✅ Generated INDEX.json for ${folderPath}`);
  console.log(`   Files: ${index.files.length}`);
  console.log(`   Subfolders: ${index.subfolders.length}`);
}

main();
