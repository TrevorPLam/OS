#!/usr/bin/env node
// Generate INDEX.md file for a folder
// Usage: node scripts/generate-index-md.mjs <folder_path> [--watch]

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const folderPath = process.argv[2] || process.cwd();
const watchMode = process.argv.includes("--watch");

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
]);

// Files to ignore
const IGNORE_FILES = new Set([
  "INDEX.md",
  "INDEX.json",
  ".DS_Store",
  "Thumbs.db",
  ".gitkeep",
]);

// File extensions to include
const INCLUDE_EXTENSIONS = new Set([
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".py",
  ".md",
  ".json",
  ".yaml",
  ".yml",
  ".sh",
  ".mjs",
  ".css",
  ".html",
  ".sql",
]);

function shouldIncludeFile(fileName) {
  if (IGNORE_FILES.has(fileName)) return false;
  const ext = path.extname(fileName);
  return ext === "" || INCLUDE_EXTENSIONS.has(ext);
}

function shouldIncludeDir(dirName) {
  return !dirName.startsWith(".") && !IGNORE_DIRS.has(dirName);
}

function getFileInfo(filePath, basePath) {
  const stats = fs.statSync(filePath);
  let relativePath = path.relative(basePath, filePath);
  // Normalize path separators to forward slashes for consistency
  relativePath = relativePath.replace(/\\/g, "/");
  const ext = path.extname(filePath);
  const name = path.basename(filePath);

  let type = "file";
  if (ext) {
    type = ext.slice(1);
  }

  let description = "";
  try {
    const content = fs.readFileSync(filePath, "utf8");
    // Try to extract description from comments or first line
    if (content.length > 0) {
      const firstLine = content.split("\n")[0];
      if (firstLine.includes("//") || firstLine.includes("#")) {
        description = firstLine
          .replace(/^[#/]*\s*/, "")
          .replace(/^\*\s*/, "")
          .trim()
          .slice(0, 100);
      }
    }
  } catch (e) {
    // Ignore read errors
  }

  return {
    path: relativePath,
    name,
    type,
    size: stats.size,
    description,
  };
}

function getSubfolders(dirPath) {
  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isDirectory())
      .filter((entry) => shouldIncludeDir(entry.name))
      .map((entry) => ({
        name: entry.name,
        path: entry.name,
      }));
  } catch (e) {
    return [];
  }
}

function getFiles(dirPath) {
  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isFile())
      .filter((entry) => shouldIncludeFile(entry.name))
      .map((entry) => getFileInfo(path.join(dirPath, entry.name), dirPath));
  } catch (e) {
    return [];
  }
}

function generateIndexMarkdown(folderPath) {
  const folderName = path.basename(folderPath);
  let relativePath = path.relative(process.cwd(), folderPath) || ".";
  // Normalize path separators to forward slashes for consistency
  relativePath = relativePath.replace(/\\/g, "/");
  const isRoot = relativePath === ".";

  const subfolders = getSubfolders(folderPath);
  const files = getFiles(folderPath);

  // Determine title based on folder
  let title = folderName.charAt(0).toUpperCase() + folderName.slice(1);
  if (isRoot) {
    title = "Repository Index";
  } else if (folderName === "api") {
    title = "API Server Index";
  } else if (folderName === "mobile") {
    title = "Mobile Application Index";
  } else if (folderName === "web") {
    title = "Web Application Index";
  }

  // Build markdown content
  let md = `# ${title}\n\n`;
  md += `**File**: \`${relativePath}/INDEX.md\`\n\n`;

  // Add description based on folder type
  if (isRoot) {
    md += `This is the master index for the AIOS repository. `;
    md += `It provides navigation to all major directories and their indexes.\n\n`;
  } else if (folderName === "api") {
    md += `This index provides navigation to all files and directories in the API server.\n\n`;
  } else if (folderName === "mobile") {
    md += `This index provides navigation to all files and directories in the mobile application.\n\n`;
  } else if (folderName === "web") {
    md += `This index provides navigation to all files and directories in the web application.\n\n`;
  } else if (folderName === "assets") {
    md += `This index catalogs all asset files (images, icons, etc.) in the repository.\n\n`;
  } else if (folderName === "attached_assets") {
    md += `This index catalogs attached assets and generated content.\n\n`;
  } else if (folderName === "docs") {
    md += `This index provides navigation to all documentation in the repository.\n\n`;
  } else if (folderName === "frontend") {
    md += `This index provides navigation to all frontend code and components.\n\n`;
  } else {
    md += `This index provides navigation to all files and directories in this folder.\n\n`;
  }

  // Add structure section
  if (subfolders.length > 0 || files.length > 0) {
    md += `## Directory Structure\n\n`;
    md += `\`\`\`\n`;
    md += `${folderName}/\n`;

    // Add subfolders
    subfolders.forEach((subfolder) => {
      md += `├── ${subfolder.name}/\n`;
    });

    // Add files (limit to 10 for readability)
    const filesToShow = files.slice(0, 10);
    filesToShow.forEach((file, index) => {
      const prefix = index === filesToShow.length - 1 ? "└──" : "├──";
      md += `${prefix} ${file.name}\n`;
    });

    if (files.length > 10) {
      md += `└── ... (${files.length - 10} more files)\n`;
    }

    md += `\`\`\`\n\n`;
  }

  // Add subfolders section
  if (subfolders.length > 0) {
    md += `## Subdirectories\n\n`;
    subfolders.forEach((subfolder) => {
      const indexPath = path.join(folderPath, subfolder.name, "INDEX.md");
      const hasIndex = fs.existsSync(indexPath);
      if (hasIndex) {
        md += `- [\`${subfolder.name}/\`](./${subfolder.name}/INDEX.md) - See index for details\n`;
      } else {
        md += `- [\`${subfolder.name}/\`](./${subfolder.name}/) - Directory\n`;
      }
    });
    md += `\n`;
  }

  // Add files section
  if (files.length > 0) {
    md += `## Files\n\n`;

    // Group files by type
    const filesByType = {};
    files.forEach((file) => {
      if (!filesByType[file.type]) {
        filesByType[file.type] = [];
      }
      filesByType[file.type].push(file);
    });

    Object.keys(filesByType)
      .sort()
      .forEach((type) => {
        const typeFiles = filesByType[type];
        md += `### ${type.toUpperCase()} Files\n\n`;
        typeFiles.forEach((file) => {
          md += `- [\`${file.name}\`](./${file.path})`;
          if (file.description) {
            md += ` - ${file.description}`;
          }
          md += `\n`;
        });
        md += `\n`;
      });
  }

  // Add navigation section
  md += `## Navigation\n\n`;
  if (!isRoot) {
    md += `- [Repository Root Index](../INDEX.md) - Master repository index\n`;
  }
  if (folderName === "apps") {
    md += `- [\`packages/INDEX.md\`](../packages/INDEX.md) - Packages index\n`;
    md += `- [\`scripts/INDEX.md\`](../scripts/INDEX.md) - Scripts index\n`;
  } else if (folderName === "api" || folderName === "mobile" || folderName === "web") {
    md += `- [\`apps/INDEX.md\`](../INDEX.md) - Applications index\n`;
    md += `- [\`packages/INDEX.md\`](../../packages/INDEX.md) - Packages index\n`;
  } else if (folderName === "packages") {
    md += `- [\`apps/INDEX.md\`](../apps/INDEX.md) - Applications index\n`;
    md += `- [\`scripts/INDEX.md\`](../scripts/INDEX.md) - Scripts index\n`;
  } else if (folderName === "scripts") {
    md += `- [\`apps/INDEX.md\`](../apps/INDEX.md) - Applications index\n`;
    md += `- [\`packages/INDEX.md\`](../packages/INDEX.md) - Packages index\n`;
  }

  md += `\n---\n\n`;
  md += `## Governance & Best Practices\n\n`;
  md += `**Constitution (Article 8): HITL for External Systems**\n`;
  md += `- Changes to external integrations, credentials, or production systems require human approval\n\n`;
  md += `**Principles:**\n`;
  md += `- **Read Repo First (P8)**: Check existing docs and code before making assumptions\n`;
  md += `- **Evidence Over Vibes (P6)**: Cite specific filepaths and show verification\n`;
  md += `- **Respect Boundaries by Default (P13)**: Follow architectural boundaries defined in \`.repo/policy/BOUNDARIES.md\`\n\n`;
  md += `**Best Practices:**\n`;
  md += `- Follow existing patterns in similar modules\n`;
  md += `- Update this index when adding new files\n`;
  md += `- Keep navigation clear and logical\n`;
  md += `- Link to related documentation\n\n`;
  md += `**See Also:**\n`;
  md += `- [\`.repo/policy/constitution.json\`](../../.repo/policy/constitution.json) - Full governance rules\n`;
  md += `- [\`.repo/policy/BOUNDARIES.md\`](../../.repo/policy/BOUNDARIES.md) - Architectural boundaries\n`;
  md += `- [\`docs/decisions/\`](../../docs/decisions/) - Architecture Decision Records\n\n`;
  md += `*Last updated: ${new Date().toISOString()}*\n`;

  return md;
}

function generateIndex(folderPath) {
  try {
    const indexPath = path.join(folderPath, "INDEX.md");
    const content = generateIndexMarkdown(folderPath);
    fs.writeFileSync(indexPath, content, "utf8");
    console.log(`✅ Generated INDEX.md for ${folderPath}`);
    return true;
  } catch (error) {
    console.error(`❌ Error generating INDEX.md for ${folderPath}:`, error.message);
    return false;
  }
}

// List of directories that should have INDEX.md files
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

function generateAllIndexes() {
  const repoRoot = process.cwd();
  let successCount = 0;
  let failCount = 0;

  INDEX_DIRECTORIES.forEach((dir) => {
    const fullPath = path.join(repoRoot, dir);
    if (fs.existsSync(fullPath)) {
      if (generateIndex(fullPath)) {
        successCount++;
      } else {
        failCount++;
      }
    } else {
      console.warn(`⚠️  Directory not found: ${fullPath}`);
    }
  });

  console.log(`\n📊 Summary: ${successCount} generated, ${failCount} failed`);
  return failCount === 0;
}

// Main execution
if (watchMode) {
  console.log("👀 Watch mode not yet implemented. Use --watch flag in future version.");
  generateAllIndexes();
} else {
  // Check if a specific folder path was provided
  const resolvedPath = path.resolve(folderPath);
  const repoRoot = process.cwd();
  const relativePath = path.relative(repoRoot, resolvedPath);
  
  // If it's a specific directory that's not in our list, generate just that one
  if (folderPath && folderPath !== "." && folderPath !== process.cwd() && !INDEX_DIRECTORIES.includes(relativePath)) {
    // Generate for specific folder
    generateIndex(resolvedPath);
  } else {
    // Generate all indexes
    generateAllIndexes();
  }
}
