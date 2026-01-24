#!/usr/bin/env node
// Generate INDEX.json file for a folder
// Usage: node scripts/generate-index-json.mjs [folder_path]

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const folderPath = process.argv[2] ? path.resolve(process.argv[2]) : process.cwd();

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
  "INDEX.json",
  "INDEX.md",
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
  const relativePath = path.relative(basePath, filePath).replace(/\\/g, "/");
  const ext = path.extname(filePath);
  const name = path.basename(filePath);

  let type = "file";
  if (ext) {
    type = ext.slice(1);
  }

  let keyClasses = [];
  let lineCount = 0;
  let description = "";

  try {
    const content = fs.readFileSync(filePath, "utf8");
    lineCount = content.split("\n").length;

    // Extract key classes/functions based on file type
    if (filePath.endsWith(".py")) {
      const classMatches = content.match(/^class\s+(\w+)/gm);
      if (classMatches) {
        keyClasses = classMatches.map((m) => m.replace(/^class\s+/, "")).slice(0, 10);
      }
    } else if (filePath.endsWith(".ts") || filePath.endsWith(".tsx")) {
      const exportMatches = content.match(/^export\s+(?:const|function|class|interface|type)\s+(\w+)/gm);
      if (exportMatches) {
        keyClasses = exportMatches
          .map((m) => m.replace(/^export\s+(?:const|function|class|interface|type)\s+/, ""))
          .slice(0, 10);
      }
    } else if (filePath.endsWith(".js") || filePath.endsWith(".jsx")) {
      const exportMatches = content.match(/^export\s+(?:const|function|class)\s+(\w+)/gm);
      if (exportMatches) {
        keyClasses = exportMatches
          .map((m) => m.replace(/^export\s+(?:const|function|class)\s+/, ""))
          .slice(0, 10);
      }
    }

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
    type,
    key_classes: keyClasses,
    line_count: lineCount,
    size_bytes: stats.size,
    description: description || undefined,
  };
}

function getSubfolders(dirPath) {
  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isDirectory())
      .filter((entry) => shouldIncludeDir(entry.name))
      .map((entry) => {
        const indexPath = path.join(dirPath, entry.name, "INDEX.json");
        const hasIndex = fs.existsSync(indexPath);
        return {
          path: entry.name,
          purpose: hasIndex ? "See INDEX.json for details" : "Directory",
          indexFile: hasIndex ? `${entry.name}/INDEX.json` : undefined,
        };
      });
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

function getDependencies(folderPath) {
  // Placeholder for dependency analysis
  return {
    imports: [],
    imported_by: [],
  };
}

function generateIndexJson(folderPath) {
  const folderName = path.basename(folderPath);
  const relativePath = path.relative(process.cwd(), folderPath).replace(/\\/g, "/") || ".";

  const subfolders = getSubfolders(folderPath);
  const files = getFiles(folderPath);

  // Determine purpose based on folder
  let purpose = "Directory contents";
  if (folderName === "api") {
    purpose = "API server files and directories";
  } else if (folderName === "mobile") {
    purpose = "Mobile application files and directories";
  } else if (folderName === "web") {
    purpose = "Web application files and directories";
  } else if (folderName === "apps") {
    purpose = "Application shells (mobile, API, web)";
  } else if (folderName === "assets") {
    purpose = "Asset files (images, icons, etc.)";
  } else if (folderName === "attached_assets") {
    purpose = "Attached assets and generated content";
  } else if (folderName === "docs") {
    purpose = "Documentation files and directories";
  } else if (folderName === "frontend") {
    purpose = "Frontend code and components";
  } else if (folderName === "packages") {
    purpose = "Shared packages (features, platform, design-system, contracts)";
  } else if (folderName === "scripts") {
    purpose = "Automation and utility scripts";
  } else if (relativePath === ".") {
    purpose = "Master index of all directories in the repository";
  }

  const index = {
    file: "INDEX.json",
    folder: relativePath,
    purpose,
    generated_at: new Date().toISOString(),
    files: files,
    subfolders: subfolders,
    dependencies: getDependencies(folderPath),
  };

  // Add quick navigation for root
  if (relativePath === ".") {
    index.quickNavigation = {
      applications: [
        {
          name: "Mobile App",
          path: "apps/mobile/",
          description: "React Native/Expo mobile application",
          indexFile: "apps/mobile/INDEX.json",
        },
        {
          name: "API Server",
          path: "apps/api/",
          description: "Node.js/Express backend API",
          indexFile: "apps/api/INDEX.json",
        },
        {
          name: "Web App",
          path: "apps/web/",
          description: "Web application",
          indexFile: "apps/web/INDEX.json",
        },
      ],
      packages: [
        {
          name: "Features",
          path: "packages/features/",
          description: "Feature modules (vertical slices)",
        },
        {
          name: "Platform",
          path: "packages/platform/",
          description: "Platform adapters and primitives",
        },
        {
          name: "Design System",
          path: "packages/design-system/",
          description: "Shared UI components",
        },
        {
          name: "Contracts",
          path: "packages/contracts/",
          description: "Shared types and schemas",
        },
      ],
      supportingDirectories: [
        {
          name: "Documentation",
          path: "docs/",
          description: "Comprehensive documentation",
          indexFile: "docs/INDEX.json",
        },
        {
          name: "Scripts",
          path: "scripts/",
          description: "Automation scripts",
          indexFile: "scripts/INDEX.json",
        },
        {
          name: "Assets",
          path: "assets/",
          description: "Asset files",
          indexFile: "assets/INDEX.json",
        },
      ],
    };
  }

  return index;
}

function generateIndex(folderPath) {
  try {
    if (!fs.existsSync(folderPath)) {
      console.warn(`⚠️  Directory not found: ${folderPath}`);
      return false;
    }

    const indexPath = path.join(folderPath, "INDEX.json");
    const index = generateIndexJson(folderPath);
    fs.writeFileSync(indexPath, JSON.stringify(index, null, 2), "utf8");
    console.log(`✅ Generated INDEX.json for ${folderPath}`);
    return true;
  } catch (error) {
    console.error(`❌ Error generating INDEX.json for ${folderPath}:`, error.message);
    return false;
  }
}

// List of directories that should have INDEX.json files
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
    if (generateIndex(fullPath)) {
      successCount++;
    } else {
      failCount++;
    }
  });

  console.log(`\n📊 Summary: ${successCount} generated, ${failCount} failed`);
  return failCount === 0;
}

// Main execution
const resolvedPath = path.resolve(folderPath);
const repoRoot = process.cwd();
const relativePath = path.relative(repoRoot, resolvedPath).replace(/\\/g, "/");

// If it's a specific directory that's not in our list, generate just that one
if (folderPath && folderPath !== "." && folderPath !== process.cwd() && !INDEX_DIRECTORIES.includes(relativePath)) {
  generateIndex(resolvedPath);
} else {
  // Generate all indexes
  generateAllIndexes();
}
