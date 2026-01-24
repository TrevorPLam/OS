#!/usr/bin/env node
// Intelligent Code Similarity Detection
// Usage: node scripts/intelligent/intelligent-code-similarity-detector.mjs [--threshold 0.7] [--suggest-fixes]

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const THRESHOLD = parseFloat(process.argv.find((arg) => arg.startsWith("--threshold="))?.split("=")[1] || "0.7");
const SUGGEST_FIXES = process.argv.includes("--suggest-fixes");

function findCodeFiles(dir = REPO_ROOT, depth = 0) {
  if (depth > 5) return []; // Limit depth

  const files = [];
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (!entry.name.startsWith(".") && entry.name !== "node_modules") {
          files.push(...findCodeFiles(fullPath, depth + 1));
        }
      } else if (/\.(ts|tsx|js|jsx)$/.test(entry.name)) {
        files.push(fullPath);
      }
    }
  } catch (e) {
    // Skip directory
  }
  return files;
}

function normalizeCode(content) {
  // Remove comments
  content = content.replace(/\/\*[\s\S]*?\*\//g, "");
  content = content.replace(/\/\/.*$/gm, "");

  // Normalize whitespace
  content = content.replace(/\s+/g, " ");

  // Remove string literals (simplified)
  content = content.replace(/['"`][^'"`]*['"`]/g, '""');

  // Remove numbers
  content = content.replace(/\b\d+\b/g, "0");

  return content.trim();
}

function calculateSimilarity(content1, content2) {
  const norm1 = normalizeCode(content1);
  const norm2 = normalizeCode(content2);

  // Simple similarity using longest common subsequence
  const lcs = longestCommonSubsequence(norm1, norm2);
  const similarity = (2 * lcs) / (norm1.length + norm2.length);

  return similarity;
}

function longestCommonSubsequence(str1, str2) {
  const m = str1.length;
  const n = str2.length;
  const dp = Array(m + 1)
    .fill(null)
    .map(() => Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (str1[i - 1] === str2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  return dp[m][n];
}

function extractFunctionBodies(content) {
  const functions = [];
  const functionPattern = /(?:function\s+\w+|const\s+\w+\s*[:=]\s*(?:async\s+)?\([^)]*\)\s*=>)\s*\{([^}]+)\}/g;
  let match;

  while ((match = functionPattern.exec(content)) !== null) {
    functions.push(match[1]);
  }

  return functions;
}

function findSimilarCode() {
  const files = findCodeFiles().slice(0, 100); // Limit for performance
  const similarities = [];

  console.log(`📁 Analyzing ${files.length} files...\n`);

  for (let i = 0; i < files.length; i++) {
    for (let j = i + 1; j < files.length; j++) {
      try {
        const content1 = fs.readFileSync(files[i], "utf8");
        const content2 = fs.readFileSync(files[j], "utf8");

        const similarity = calculateSimilarity(content1, content2);

        if (similarity >= THRESHOLD) {
          similarities.push({
            file1: path.relative(REPO_ROOT, files[i]),
            file2: path.relative(REPO_ROOT, files[j]),
            similarity,
          });
        }
      } catch (e) {
        // Skip file
      }
    }
  }

  return similarities.sort((a, b) => b.similarity - a.similarity);
}

function suggestConsolidation(similarity) {
  const { file1, file2, similarity: sim } = similarity;

  // Extract function names or component names
  const name1 = path.basename(file1, path.extname(file1));
  const name2 = path.basename(file2, path.extname(file2));

  // Determine common directory
  const dir1 = path.dirname(file1);
  const dir2 = path.dirname(file2);
  const commonDir = dir1 === dir2 ? dir1 : path.dirname(REPO_ROOT);

  return {
    suggestion: `Consider consolidating ${name1} and ${name2} into a shared utility`,
    location: path.join(commonDir, "utils", "shared.ts"),
    similarity: sim,
  };
}

function main() {
  console.log("🔍 Intelligent Code Similarity Detection\n");
  console.log(`📊 Threshold: ${(THRESHOLD * 100).toFixed(0)}%\n`);

  const similarities = findSimilarCode();

  if (similarities.length === 0) {
    console.log("✅ No similar code patterns detected");
    return;
  }

  console.log(`⚠️  Found ${similarities.length} similar code pattern(s):\n`);

  const topSimilarities = similarities.slice(0, 10);
  for (const sim of topSimilarities) {
    console.log(`   ${(sim.similarity * 100).toFixed(1)}% similar:`);
    console.log(`      - ${sim.file1}`);
    console.log(`      - ${sim.file2}`);
    if (SUGGEST_FIXES) {
      const suggestion = suggestConsolidation(sim);
      console.log(`      💡 ${suggestion.suggestion}`);
    }
    console.log();
  }

  if (similarities.length > 10) {
    console.log(`   ... and ${similarities.length - 10} more\n`);
  }

  // Generate report
  const report = {
    timestamp: new Date().toISOString(),
    threshold: THRESHOLD,
    similarities_found: similarities.length,
    top_similarities: topSimilarities.map((s) => ({
      file1: s.file1,
      file2: s.file2,
      similarity: s.similarity,
    })),
  };

  const reportPath = path.join(REPO_ROOT, ".repo/automation/similarity-report.json");
  const reportDir = path.dirname(reportPath);
  if (!fs.existsSync(reportDir)) {
    fs.mkdirSync(reportDir, { recursive: true });
  }
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  console.log(`✅ Report saved to: ${reportPath}`);
}

main();
