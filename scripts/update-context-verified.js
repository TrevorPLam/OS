#!/usr/bin/env node
// /.repo/automation/scripts/update-context-verified.js
// Update last_verified date in context files
// Usage: node update-context-verified.js [context-file...] or --all

const fs = require("fs");
const path = require("path");

// Get repo root
const REPO_ROOT = path.resolve(__dirname, "../../..");

function findContextFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);

  files.forEach((file) => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (
      stat.isDirectory() &&
      !file.startsWith(".") &&
      file !== "node_modules"
    ) {
      findContextFiles(filePath, fileList);
    } else if (file === ".agent-context.json") {
      fileList.push(filePath);
    }
  });

  return fileList;
}

function updateContextFile(filePath) {
  try {
    const content = JSON.parse(fs.readFileSync(filePath, "utf8"));
    const today = new Date().toISOString().split("T")[0];

    // Ensure metrics object exists
    if (!content.metrics) {
      content.metrics = {};
    }

    // Update last_verified
    content.metrics.last_verified = today;

    // Write back
    fs.writeFileSync(filePath, JSON.stringify(content, null, 2) + "\n", "utf8");

    const relativePath = path.relative(REPO_ROOT, filePath);
    console.log(`✅ Updated ${relativePath}`);
    return true;
  } catch (err) {
    console.error(`❌ Error updating ${filePath}: ${err.message}`);
    return false;
  }
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);
  const updateAll = args.includes("--all");

  let filesToUpdate = [];

  if (updateAll) {
    filesToUpdate = findContextFiles(REPO_ROOT);
  } else if (args.length > 0) {
    filesToUpdate = args
      .map((file) => {
        if (path.isAbsolute(file)) {
          return file;
        }
        return path.join(REPO_ROOT, file);
      })
      .filter((file) => fs.existsSync(file));
  } else {
    console.error(
      "Usage: node update-context-verified.js [context-file...] or --all",
    );
    process.exit(1);
  }

  if (filesToUpdate.length === 0) {
    console.error("No context files found to update");
    process.exit(1);
  }

  console.log(
    `Updating last_verified date for ${filesToUpdate.length} file(s)...\n`,
  );

  let successCount = 0;
  filesToUpdate.forEach((file) => {
    if (updateContextFile(file)) {
      successCount++;
    }
  });

  console.log(`\n✅ Updated ${successCount}/${filesToUpdate.length} file(s)`);
}

// Export for use as module
module.exports = { updateContextFile };
