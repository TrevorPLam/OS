#!/usr/bin/env node
// Intelligent Bundle Size Optimization
// Usage: node scripts/intelligent/intelligent-bundle-optimizer.mjs [--base-ref main] [--threshold 100]

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const BASE_REF = process.argv.find((arg) => arg.startsWith("--base-ref="))?.split("=")[1] || "main";
const THRESHOLD_KB = parseInt(process.argv.find((arg) => arg.startsWith("--threshold="))?.split("=")[1] || "100");

function getBundleSize() {
  try {
    // Try to get bundle size from build output
    const buildOutput = execSync("npm run expo:static:build 2>&1", { encoding: "utf8", cwd: REPO_ROOT });
    
    // Look for bundle size in output
    const sizeMatch = buildOutput.match(/bundle.*?(\d+\.?\d*)\s*(KB|MB)/i);
    if (sizeMatch) {
      const size = parseFloat(sizeMatch[1]);
      const unit = sizeMatch[2].toUpperCase();
      return unit === "MB" ? size * 1024 : size; // Convert to KB
    }

    // Fallback: check dist/build directory
    const distDir = path.join(REPO_ROOT, "dist");
    if (fs.existsSync(distDir)) {
      const files = fs.readdirSync(distDir, { recursive: true });
      let totalSize = 0;
      for (const file of files) {
        const filePath = path.join(distDir, file);
        try {
          const stats = fs.statSync(filePath);
          if (stats.isFile()) {
            totalSize += stats.size;
          }
        } catch (e) {
          // Ignore
        }
      }
      return totalSize / 1024; // Convert to KB
    }
  } catch (e) {
    // Build failed or no bundle
  }
  return null;
}

function analyzeImports(filePath) {
  try {
    const content = fs.readFileSync(filePath, "utf8");
    const imports = [];

    // Match import statements
    const importRegex = /^import\s+(?:(?:\{[^}]+\}|\*\s+as\s+\w+|\w+)(?:\s*,\s*(?:\{[^}]+\}|\*\s+as\s+\w+|\w+))*)\s+from\s+['"]([^'"]+)['"]/gm;
    let match;

    while ((match = importRegex.exec(content)) !== null) {
      const importPath = match[1];
      if (!importPath.startsWith(".") && !importPath.startsWith("/")) {
        // External dependency
        imports.push(importPath);
      }
    }

    return imports;
  } catch (e) {
    return [];
  }
}

function findLargeDependencies() {
  try {
    const packageJson = JSON.parse(fs.readFileSync(path.join(REPO_ROOT, "package.json"), "utf8"));
    const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };

    // Known large dependencies
    const largeDeps = [
      "react",
      "react-native",
      "expo",
      "@react-navigation",
      "@tanstack/react-query",
    ];

    return Object.keys(deps).filter((dep) => largeDeps.some((large) => dep.includes(large)));
  } catch (e) {
    return [];
  }
}

function suggestCodeSplitting(changedFiles) {
  const suggestions = [];

  for (const file of changedFiles) {
    if (file.includes("Screen") || file.includes("Page")) {
      suggestions.push({
        type: "lazy_loading",
        file,
        suggestion: `Consider lazy loading: \`const ${path.basename(file, path.extname(file))} = React.lazy(() => import('./${file}'));\``,
      });
    }

    if (file.includes("components")) {
      const imports = analyzeImports(path.join(REPO_ROOT, file));
      if (imports.length > 10) {
        suggestions.push({
          type: "too_many_imports",
          file,
          suggestion: `Too many imports (${imports.length}). Consider splitting into smaller components.`,
        });
      }
    }
  }

  return suggestions;
}

function main() {
  console.log("📦 Intelligent Bundle Size Optimization\n");

  console.log(`📊 Analyzing bundle size...\n`);

  const currentSize = getBundleSize();
  if (!currentSize) {
    console.log("⚠️  Could not determine bundle size. Run build first.");
    return;
  }

  console.log(`   Current Bundle Size: ${currentSize.toFixed(2)} KB`);
  console.log(`   Threshold: ${THRESHOLD_KB} KB\n`);

  if (currentSize > THRESHOLD_KB) {
    console.log(`⚠️  Bundle size exceeds threshold by ${(currentSize - THRESHOLD_KB).toFixed(2)} KB\n`);
  } else {
    console.log(`✅ Bundle size within threshold\n`);
  }

  // Analyze dependencies
  const largeDeps = findLargeDependencies();
  if (largeDeps.length > 0) {
    console.log(`📚 Large Dependencies Detected:\n`);
    largeDeps.forEach((dep) => console.log(`   - ${dep}`));
    console.log();
  }

  // Get changed files
  try {
    const changedFiles = execSync(`git diff --name-only ${BASE_REF}...HEAD`, {
      encoding: "utf8",
      cwd: REPO_ROOT,
    })
      .trim()
      .split("\n")
      .filter(Boolean);

    if (changedFiles.length > 0) {
      const suggestions = suggestCodeSplitting(changedFiles);
      if (suggestions.length > 0) {
        console.log(`💡 Optimization Suggestions:\n`);
        suggestions.forEach((s, i) => {
          console.log(`   ${i + 1}. [${s.type}] ${s.file}`);
          console.log(`      ${s.suggestion}\n`);
        });
      }
    }
  } catch (e) {
    // No changes or git error
  }

  // Generate report
  const report = {
    timestamp: new Date().toISOString(),
    bundle_size_kb: currentSize,
    threshold_kb: THRESHOLD_KB,
    exceeds_threshold: currentSize > THRESHOLD_KB,
    large_dependencies: largeDeps,
  };

  const reportPath = path.join(REPO_ROOT, ".repo/automation/bundle-report.json");
  const reportDir = path.dirname(reportPath);
  if (!fs.existsSync(reportDir)) {
    fs.mkdirSync(reportDir, { recursive: true });
  }
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  console.log(`✅ Report saved to: ${reportPath}`);

  if (currentSize > THRESHOLD_KB) {
    process.exit(1);
  }
}

main();
