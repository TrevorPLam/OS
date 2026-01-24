#!/usr/bin/env node
// Intelligent Breaking Change Detection
// Usage: node scripts/intelligent/intelligent-breaking-change-detector.mjs [--base-ref main] [--output migration-guide.md]

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const BASE_REF = process.argv.find((arg) => arg.startsWith("--base-ref="))?.split("=")[1] || "main";
const OUTPUT_FILE = process.argv.find((arg) => arg.startsWith("--output="))?.split("=")[1];

function analyzeAPIC changes(baseRef) {
  try {
    const diff = execSync(`git diff ${baseRef}...HEAD -- "apps/api/**/*.ts" "packages/**/*.ts"`, {
      encoding: "utf8",
      cwd: REPO_ROOT,
    });

    const breakingChanges = [];

    // Detect function signature changes
    const functionRemoved = diff.match(/^-\s+(?:export\s+)?(?:async\s+)?function\s+(\w+)/gm);
    if (functionRemoved) {
      functionRemoved.forEach((match) => {
        const funcName = match.match(/function\s+(\w+)/)?.[1];
        if (funcName) {
          breakingChanges.push({
            type: "function_removed",
            name: funcName,
            severity: "high",
            description: `Function ${funcName} was removed`,
          });
        }
      });
    }

    // Detect parameter changes
    const paramChanges = diff.match(/^[+-]\s+function\s+\w+\s*\([^)]+\)/gm);
    if (paramChanges && paramChanges.length >= 2) {
      // Compare before/after
      const before = paramChanges.find((p) => p.startsWith("-"));
      const after = paramChanges.find((p) => p.startsWith("+"));
      if (before && after) {
        const beforeParams = before.match(/\(([^)]+)\)/)?.[1]?.split(",").length || 0;
        const afterParams = after.match(/\(([^)]+)\)/)?.[1]?.split(",").length || 0;
        if (beforeParams !== afterParams) {
          breakingChanges.push({
            type: "parameter_change",
            severity: "high",
            description: `Function parameters changed (${beforeParams} → ${afterParams})`,
          });
        }
      }
    }

    // Detect type/interface changes
    const typeRemoved = diff.match(/^-\s+(?:export\s+)?(?:type|interface)\s+(\w+)/gm);
    if (typeRemoved) {
      typeRemoved.forEach((match) => {
        const typeName = match.match(/(?:type|interface)\s+(\w+)/)?.[1];
        if (typeName) {
          breakingChanges.push({
            type: "type_removed",
            name: typeName,
            severity: "high",
            description: `Type/Interface ${typeName} was removed`,
          });
        }
      });
    }

    // Detect export changes
    const exportRemoved = diff.match(/^-\s+export\s+(?:const|function|class|type|interface)\s+(\w+)/gm);
    if (exportRemoved) {
      exportRemoved.forEach((match) => {
        const exportName = match.match(/(?:const|function|class|type|interface)\s+(\w+)/)?.[1];
        if (exportName) {
          breakingChanges.push({
            type: "export_removed",
            name: exportName,
            severity: "high",
            description: `Export ${exportName} was removed`,
          });
        }
      });
    }

    return breakingChanges;
  } catch (e) {
    return [];
  }
}

function analyzeSchemaChanges(baseRef) {
  try {
    const schemaFiles = execSync(`git diff --name-only ${baseRef}...HEAD -- "**/schema.ts" "**/schema.ts" "**/*.schema.*"`, {
      encoding: "utf8",
      cwd: REPO_ROOT,
    })
      .trim()
      .split("\n")
      .filter(Boolean);

    if (schemaFiles.length === 0) return [];

    const breakingChanges = [];
    for (const file of schemaFiles) {
      const diff = execSync(`git diff ${baseRef}...HEAD -- "${file}"`, { encoding: "utf8", cwd: REPO_ROOT });

      // Detect required field additions
      if (diff.includes(".required()") && diff.match(/^\+.*\.required\(\)/m)) {
        breakingChanges.push({
          type: "schema_required_field",
          file,
          severity: "high",
          description: `Required field added to schema in ${file}`,
        });
      }

      // Detect field removals
      const fieldRemoved = diff.match(/^-\s+(\w+):/m);
      if (fieldRemoved) {
        breakingChanges.push({
          type: "schema_field_removed",
          file,
          field: fieldRemoved[1],
          severity: "high",
          description: `Field ${fieldRemoved[1]} removed from schema in ${file}`,
        });
      }
    }

    return breakingChanges;
  } catch (e) {
    return [];
  }
}

function generateMigrationGuide(breakingChanges, baseRef) {
  const hasBreaking = breakingChanges.length > 0;
  const highSeverity = breakingChanges.filter((c) => c.severity === "high").length;

  let guide = `# Migration Guide

**Base Ref**: \`${baseRef}\`  
**Current**: \`HEAD\`  
**Generated**: ${new Date().toISOString()}

## Summary

${hasBreaking ? `⚠️ **${breakingChanges.length} breaking change(s) detected** (${highSeverity} high severity)` : "✅ No breaking changes detected"}

---

`;

  if (breakingChanges.length === 0) {
    guide += `## No Breaking Changes

This update contains no breaking changes. You can safely update without code changes.

`;
    return guide;
  }

  guide += `## Breaking Changes

### High Severity

${breakingChanges
  .filter((c) => c.severity === "high")
  .map((c, i) => {
    return `#### ${i + 1}. ${c.description}

**Type**: ${c.type}  
**Impact**: High

**Migration Steps:**
1. [Identify affected code]
2. [Update code to use new API]
3. [Test thoroughly]

**Example:**
\`\`\`typescript
// Before
${c.name ? `${c.name}()` : "old code"}

// After
${c.name ? `new${c.name}()` : "new code"}
\`\`\`

`;
  })
  .join("\n")}

### Medium Severity

${breakingChanges
  .filter((c) => c.severity === "medium")
  .map((c, i) => `#### ${i + 1}. ${c.description}\n`)
  .join("\n")}

---

## Migration Checklist

- [ ] Review all breaking changes
- [ ] Update affected code
- [ ] Run tests
- [ ] Update documentation
- [ ] Test in staging environment
- [ ] Deploy to production

---

## Need Help?

If you encounter issues during migration, please:
1. Check this guide
2. Review the changelog
3. Open an issue or contact the team

`;

  return guide;
}

function main() {
  console.log("🔍 Intelligent Breaking Change Detection\n");

  console.log(`📊 Analyzing changes from ${BASE_REF}...\n`);

  const apiChanges = analyzeAPIC changes(BASE_REF);
  const schemaChanges = analyzeSchemaChanges(BASE_REF);
  const allChanges = [...apiChanges, ...schemaChanges];

  console.log(`   API Changes: ${apiChanges.length}`);
  console.log(`   Schema Changes: ${schemaChanges.length}`);
  console.log(`   Total Breaking Changes: ${allChanges.length}\n`);

  if (allChanges.length > 0) {
    console.log("⚠️  Breaking Changes Detected:\n");
    allChanges.forEach((change, i) => {
      console.log(`   ${i + 1}. [${change.severity.toUpperCase()}] ${change.description}`);
    });
  } else {
    console.log("✅ No breaking changes detected");
  }

  const migrationGuide = generateMigrationGuide(allChanges, BASE_REF);

  if (OUTPUT_FILE) {
    fs.writeFileSync(OUTPUT_FILE, migrationGuide);
    console.log(`\n✅ Migration guide written to: ${OUTPUT_FILE}`);
  } else {
    console.log("\n" + migrationGuide);
  }

  // Exit with error if high severity breaking changes found
  const highSeverity = allChanges.filter((c) => c.severity === "high");
  if (highSeverity.length > 0) {
    console.log(`\n⚠️  ${highSeverity.length} high-severity breaking change(s) detected`);
    process.exit(1);
  }
}

main();
