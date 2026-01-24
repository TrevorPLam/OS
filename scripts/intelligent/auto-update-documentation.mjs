#!/usr/bin/env node
// Auto-Update Documentation from Code
// Usage: node scripts/intelligent/auto-update-documentation.mjs [--file path/to/file.ts] [--dry-run]

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const TARGET_FILE = process.argv.find((arg) => arg.startsWith("--file="))?.split("=")[1];
const DRY_RUN = process.argv.includes("--dry-run");

function findRelatedDocs(filePath) {
  const relativePath = path.relative(REPO_ROOT, filePath);
  const dir = path.dirname(relativePath);
  const basename = path.basename(filePath, path.extname(filePath));

  const possibleDocs = [
    path.join(dir, "README.md"),
    path.join(dir, `${basename}.md`),
    path.join(REPO_ROOT, "docs", relativePath.replace(/\.(ts|tsx|js|jsx)$/, ".md")),
  ];

  return possibleDocs.filter((doc) => fs.existsSync(doc));
}

function extractFunctionDocs(content) {
  const functions = [];
  const functionPattern = /(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)/g;
  let match;

  while ((match = functionPattern.exec(content)) !== null) {
    const name = match[1];
    const params = match[2]
      .split(",")
      .map((p) => p.trim())
      .filter(Boolean)
      .map((p) => {
        const paramMatch = p.match(/(\w+)(?::\s*(.+))?/);
        return {
          name: paramMatch?.[1] || p,
          type: paramMatch?.[2] || "any",
        };
      });

    // Look for JSDoc comment before function
    const beforeFunction = content.substring(0, match.index);
    const jsdocMatch = beforeFunction.match(/(\/\*\*[\s\S]*?\*\/)\s*$/);
    const description = jsdocMatch
      ? jsdocMatch[1]
          .replace(/\/\*\*|\*\//g, "")
          .replace(/\*\s*/g, "")
          .trim()
      : null;

    functions.push({ name, params, description });
  }

  return functions;
}

function updateDocWithFunctions(docPath, functions, filePath) {
  let docContent = fs.readFileSync(docPath, "utf8");
  let updated = false;

  for (const func of functions) {
    // Check if function is already documented
    const funcDocPattern = new RegExp(`##?\\s+${func.name}|###?\\s+${func.name}|\\*\\*${func.name}\\*\\*`, "i");
    if (funcDocPattern.test(docContent)) {
      continue; // Already documented
    }

    // Add function documentation
    const funcDoc = `## ${func.name}

${func.description || `Function in \`${path.relative(REPO_ROOT, filePath)}\``}

**Parameters:**
${func.params.map((p) => `- \`${p.name}\`: ${p.type}`).join("\n")}

**Example:**
\`\`\`typescript
// TODO: Add example
\`\`\`

`;

    // Insert after existing content or at end
    if (docContent.includes("## Functions") || docContent.includes("### Functions")) {
      docContent = docContent.replace(/(## Functions|### Functions)/, `$1\n\n${funcDoc}`);
      updated = true;
    } else {
      docContent += `\n${funcDoc}`;
      updated = true;
    }
  }

  return { docContent, updated };
}

function detectDocDrift(filePath, docPath) {
  const codeContent = fs.readFileSync(filePath, "utf8");
  const docContent = fs.readFileSync(docPath, "utf8");

  const functions = extractFunctionDocs(codeContent);
  const drift = [];

  for (const func of functions) {
    // Check if function exists in code but not in docs
    if (!docContent.includes(func.name)) {
      drift.push({
        type: "missing_doc",
        function: func.name,
        severity: "medium",
      });
    }

    // Check if function signature changed
    const docFuncMatch = docContent.match(new RegExp(`${func.name}[^\\n]*\\(([^)]+)\\)`, "i"));
    if (docFuncMatch) {
      const docParams = docFuncMatch[1].split(",").length;
      if (docParams !== func.params.length) {
        drift.push({
          type: "signature_mismatch",
          function: func.name,
          severity: "high",
        });
      }
    }
  }

  return drift;
}

function main() {
  console.log("📚 Auto-Updating Documentation\n");

  if (!TARGET_FILE) {
    console.error("❌ Target file required. Use --file=path/to/file.ts");
    process.exit(1);
  }

  const filePath = path.resolve(REPO_ROOT, TARGET_FILE);
  if (!fs.existsSync(filePath)) {
    console.error(`❌ File not found: ${filePath}`);
    process.exit(1);
  }

  console.log(`📄 Analyzing: ${TARGET_FILE}\n`);

  const relatedDocs = findRelatedDocs(filePath);
  if (relatedDocs.length === 0) {
    console.log("⚠️  No related documentation found");
    return;
  }

  console.log(`📚 Found ${relatedDocs.length} related doc(s):`);
  relatedDocs.forEach((doc) => console.log(`   - ${path.relative(REPO_ROOT, doc)}`));
  console.log();

  const content = fs.readFileSync(filePath, "utf8");
  const functions = extractFunctionDocs(content);

  console.log(`   Functions: ${functions.length}\n`);

  if (functions.length === 0) {
    console.log("⚠️  No functions found to document");
    return;
  }

  // Check for drift
  for (const docPath of relatedDocs) {
    const drift = detectDocDrift(filePath, docPath);
    if (drift.length > 0) {
      console.log(`⚠️  Documentation drift detected in ${path.relative(REPO_ROOT, docPath)}:`);
      drift.forEach((d) => {
        console.log(`   - [${d.severity.toUpperCase()}] ${d.type}: ${d.function}`);
      });
      console.log();
    }
  }

  // Update documentation
  for (const docPath of relatedDocs) {
    const { docContent, updated } = updateDocWithFunctions(docPath, functions, filePath);

    if (updated) {
      if (DRY_RUN) {
        console.log(`[DRY RUN] Would update: ${path.relative(REPO_ROOT, docPath)}`);
      } else {
        fs.writeFileSync(docPath, docContent);
        console.log(`✅ Updated: ${path.relative(REPO_ROOT, docPath)}`);
      }
    } else {
      console.log(`ℹ️  No updates needed: ${path.relative(REPO_ROOT, docPath)}`);
    }
  }
}

main();
