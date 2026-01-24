#!/usr/bin/env node
// Intelligent Code Smell Detection & Auto-Fix
// Usage: node scripts/intelligent/intelligent-code-cleanup.mjs [--fix] [--check-only]

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const FIX = process.argv.includes("--fix");
const CHECK_ONLY = process.argv.includes("--check-only");

function findCodeFiles() {
  try {
    const files = execSync('find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "*/node_modules/*" -not -path "*/.git/*"', {
      encoding: "utf8",
      cwd: REPO_ROOT,
      shell: true,
    })
      .trim()
      .split("\n")
      .filter(Boolean);
    return files;
  } catch (e) {
    return [];
  }
}

function detectUnusedImports(filePath) {
  try {
    const content = fs.readFileSync(filePath, "utf8");
    const lines = content.split("\n");
    const issues = [];

    // Simple heuristic: check for imports that might be unused
    const importMatches = content.matchAll(/^import\s+(?:(?:\{[^}]+\}|\*\s+as\s+\w+|\w+)(?:\s*,\s*(?:\{[^}]+\}|\*\s+as\s+\w+|\w+))*)\s+from\s+['"]([^'"]+)['"]/gm);

    for (const match of importMatches) {
      const importLine = match[0];
      const importPath = match[match.length - 1];
      const importedItems = importLine.match(/\{([^}]+)\}/)?.[1]?.split(",").map((i) => i.trim()) || [];

      // Check if imported items are used (simple check)
      for (const item of importedItems) {
        const itemName = item.split(" as ")[0].trim();
        const usageRegex = new RegExp(`\\b${itemName}\\b`, "g");
        const matches = content.match(usageRegex);
        if (matches && matches.length <= 1) {
          // Only found in import line
          issues.push({
            type: "unused_import",
            file: filePath,
            line: importLine,
            item: itemName,
            severity: "low",
          });
        }
      }
    }

    return issues;
  } catch (e) {
    return [];
  }
}

function detectLongFunctions(filePath) {
  try {
    const content = fs.readFileSync(filePath, "utf8");
    const lines = content.split("\n");
    const issues = [];

    let inFunction = false;
    let functionStart = 0;
    let functionName = "";
    let braceCount = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Detect function start
      if (line.match(/(?:function|const|let|var)\s+(\w+)\s*[=(]/)) {
        inFunction = true;
        functionStart = i;
        functionName = line.match(/(?:function|const|let|var)\s+(\w+)/)?.[1] || "anonymous";
        braceCount = 0;
      }

      if (inFunction) {
        braceCount += (line.match(/\{/g) || []).length;
        braceCount -= (line.match(/\}/g) || []).length;

        if (braceCount === 0 && line.includes("}")) {
          // Function ended
          const functionLength = i - functionStart;
          if (functionLength > 50) {
            issues.push({
              type: "long_function",
              file: filePath,
              function: functionName,
              lines: functionLength,
              severity: functionLength > 100 ? "high" : "medium",
            });
          }
          inFunction = false;
        }
      }
    }

    return issues;
  } catch (e) {
    return [];
  }
}

function detectComplexConditionals(filePath) {
  try {
    const content = fs.readFileSync(filePath, "utf8");
    const lines = content.split("\n");
    const issues = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      // Count && and || operators
      const andCount = (line.match(/&&/g) || []).length;
      const orCount = (line.match(/\|\|/g) || []).length;
      const totalComplexity = andCount + orCount;

      if (totalComplexity > 3) {
        issues.push({
          type: "complex_conditional",
          file: filePath,
          line: i + 1,
          complexity: totalComplexity,
          severity: totalComplexity > 5 ? "high" : "medium",
        });
      }
    }

    return issues;
  } catch (e) {
    return [];
  }
}

function autoFixUnusedImports(filePath, issues) {
  try {
    let content = fs.readFileSync(filePath, "utf8");
    let modified = false;

    for (const issue of issues) {
      if (issue.type === "unused_import") {
        // Remove unused import item
        const importLine = issue.line;
        const itemName = issue.item;
        const newImportLine = importLine.replace(new RegExp(`\\s*${itemName}\\s*,?`), "").replace(/,\s*,/g, ",").replace(/,\s*}/, "}");

        if (newImportLine !== importLine) {
          content = content.replace(importLine, newImportLine);
          modified = true;
        }
      }
    }

    if (modified) {
      fs.writeFileSync(filePath, content);
      return true;
    }
    return false;
  } catch (e) {
    return false;
  }
}

function main() {
  console.log("🔍 Intelligent Code Smell Detection\n");

  const files = findCodeFiles();
  console.log(`📁 Scanning ${files.length} files...\n`);

  const allIssues = {
    unused_imports: [],
    long_functions: [],
    complex_conditionals: [],
  };

  for (const file of files.slice(0, 100)) {
    // Limit to first 100 files for performance
    const filePath = path.join(REPO_ROOT, file);

    allIssues.unused_imports.push(...detectUnusedImports(filePath));
    allIssues.long_functions.push(...detectLongFunctions(filePath));
    allIssues.complex_conditionals.push(...detectComplexConditionals(filePath));
  }

  // Report issues
  console.log("📊 Issues Found:\n");
  console.log(`   Unused Imports: ${allIssues.unused_imports.length}`);
  console.log(`   Long Functions: ${allIssues.long_functions.length}`);
  console.log(`   Complex Conditionals: ${allIssues.complex_conditionals.length}\n`);

  if (allIssues.unused_imports.length > 0) {
    console.log("🔧 Unused Imports:");
    allIssues.unused_imports.slice(0, 10).forEach((issue) => {
      console.log(`   - ${issue.file}: ${issue.item}`);
    });
    if (allIssues.unused_imports.length > 10) {
      console.log(`   ... and ${allIssues.unused_imports.length - 10} more`);
    }
    console.log();
  }

  if (FIX && !CHECK_ONLY) {
    console.log("🔧 Auto-fixing unused imports...");
    let fixedCount = 0;
    const filesToFix = new Set(allIssues.unused_imports.map((i) => i.file));
    for (const file of filesToFix) {
      const fileIssues = allIssues.unused_imports.filter((i) => i.file === file);
      if (autoFixUnusedImports(file, fileIssues)) {
        fixedCount++;
      }
    }
    console.log(`✅ Fixed ${fixedCount} files\n`);
  } else if (!CHECK_ONLY) {
    console.log("💡 Run with --fix to auto-fix unused imports");
  }

  // Exit with error if high severity issues found
  const highSeverityIssues = [
    ...allIssues.long_functions.filter((i) => i.severity === "high"),
    ...allIssues.complex_conditionals.filter((i) => i.severity === "high"),
  ];

  if (highSeverityIssues.length > 0) {
    console.log(`⚠️  Found ${highSeverityIssues.length} high-severity issues`);
    process.exit(1);
  }
}

main();
