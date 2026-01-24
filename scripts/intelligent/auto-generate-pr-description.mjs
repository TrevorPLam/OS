#!/usr/bin/env node
// Auto-generate PR descriptions from code changes
// Usage: node scripts/intelligent/auto-generate-pr-description.mjs [--base-ref main] [--output-file]

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const BASE_REF = process.argv.find((arg) => arg.startsWith("--base-ref="))?.split("=")[1] || "main";
const OUTPUT_FILE = process.argv.find((arg) => arg.startsWith("--output-file="))?.split("=")[1];

function detectChangeType(changedFiles, diffContent) {
  const files = changedFiles.join(" ").toLowerCase();
  const diff = diffContent.toLowerCase();

  if (files.includes("auth") || files.includes("security") || files.includes("payment") || diff.includes("password") || diff.includes("secret")) {
    return "security";
  }
  if (files.includes("api/") || files.includes("routes") || files.includes("endpoint")) {
    return "api_change";
  }
  if (diff.includes("from 'packages/features/") && diff.match(/from 'packages\/features\/\w+\//g)?.length > 1) {
    return "cross_module";
  }
  if (files.includes("feature") || files.includes("screen") || files.includes("component")) {
    return "feature";
  }
  return "non_doc_change";
}

function analyzeChanges(baseRef) {
  try {
    const changedFiles = execSync(`git diff --name-only ${baseRef}...HEAD`, { encoding: "utf8", cwd: REPO_ROOT })
      .trim()
      .split("\n")
      .filter(Boolean);

    const diffContent = execSync(`git diff ${baseRef}...HEAD`, { encoding: "utf8", cwd: REPO_ROOT });
    const diffStats = execSync(`git diff --stat ${baseRef}...HEAD`, { encoding: "utf8", cwd: REPO_ROOT });

    const changeType = detectChangeType(changedFiles, diffContent);

    // Extract commit messages
    const commits = execSync(`git log --oneline ${baseRef}..HEAD`, { encoding: "utf8", cwd: REPO_ROOT })
      .trim()
      .split("\n")
      .filter(Boolean);

    // Analyze what changed
    const hasTests = changedFiles.some((f) => f.includes("__tests__") || f.includes(".test."));
    const hasDocs = changedFiles.some((f) => f.endsWith(".md"));
    const hasAPI = changedFiles.some((f) => f.includes("api/") || f.includes("routes"));
    const hasComponents = changedFiles.some((f) => f.includes("components/") || f.includes("Screen"));

    return {
      changedFiles,
      changeType,
      diffStats,
      commits,
      hasTests,
      hasDocs,
      hasAPI,
      hasComponents,
    };
  } catch (e) {
    console.error("Error analyzing changes:", e.message);
    return null;
  }
}

function generatePRDescription(analysis) {
  const { changeType, changedFiles, diffStats, commits, hasTests, hasDocs, hasAPI, hasComponents } = analysis;

  // Generate "what" section
  const what = `This PR implements changes detected as **${changeType}**.

**Files Modified:**
${changedFiles.slice(0, 20).map((f) => `- \`${f}\``).join("\n")}${changedFiles.length > 20 ? `\n- ... and ${changedFiles.length - 20} more files` : ""}

**Change Summary:**
\`\`\`
${diffStats}
\`\`\`

**Commits:**
${commits.slice(0, 5).map((c) => `- ${c}`).join("\n")}${commits.length > 5 ? `\n- ... and ${commits.length - 5} more commits` : ""}`;

  // Generate "why" section
  const why = `This change addresses:
- [Please fill in the business/technical reason for this change]
- [What problem does this solve?]
- [What value does this provide?]`;

  // Generate "filepaths" section
  const filepaths = `**Primary Changes:**
${changedFiles.slice(0, 10).map((f) => `- \`${f}\``).join("\n")}

**Change Type:** \`${changeType}\`

**Affected Areas:**
${hasAPI ? "- API layer\n" : ""}${hasComponents ? "- UI components\n" : ""}${hasTests ? "- Tests\n" : ""}${hasDocs ? "- Documentation\n" : ""}`;

  // Generate "verification" section
  const verification = `**Verification Steps:**

- [ ] All tests pass: \`npm test\`
- [ ] Type check passes: \`npm run check:types\`
- [ ] Lint passes: \`npm run lint\`
${hasAPI ? "- [ ] API tests pass: \`npm test -- apps/api\`\n" : ""}${hasComponents ? "- [ ] Component tests pass\n" : ""}
**Test Coverage:**
- [ ] Coverage maintained/improved
- [ ] New code has tests
${hasTests ? "- [x] Tests included in this PR\n" : "- [ ] Tests need to be added\n"}`;

  // Generate "risks" section
  const risks = `**Potential Risks:**

${changeType === "security" ? "- Security implications (requires security review)\n" : ""}${changeType === "api_change" ? "- Breaking API changes (requires migration plan)\n" : ""}${changeType === "cross_module" ? "- Cross-module dependencies (requires ADR)\n" : ""}- [Add specific risks for this change]

**Mitigation:**
- [Describe how risks are mitigated]`;

  // Generate "rollback" section
  const rollback = `**Rollback Plan:**

If issues are detected:
1. Revert this PR: \`git revert <commit-sha>\`
2. [Add specific rollback steps if needed]
3. [Add any data migration rollback if applicable]

**Rollback Risk:** [Low | Medium | High]`;

  // Generate full PR description
  const description = `## What

${what}

## Why

${why}

## Filepaths

${filepaths}

## Verification

${verification}

## Risks

${risks}

## Rollback

${rollback}

---

**Change Type:** \`${changeType}\`
**Auto-generated:** ${new Date().toISOString()}
**Please review and complete all sections marked with [ ]**`;

  return description;
}

function main() {
  console.log("📝 Auto-Generating PR Description\n");

  console.log(`🔍 Analyzing changes from ${BASE_REF}...\n`);

  const analysis = analyzeChanges(BASE_REF);
  if (!analysis) {
    console.error("❌ Failed to analyze changes");
    process.exit(1);
  }

  console.log(`   Change Type: ${analysis.changeType}`);
  console.log(`   Files Changed: ${analysis.changedFiles.length}`);
  console.log(`   Commits: ${analysis.commits.length}\n`);

  const description = generatePRDescription(analysis);

  if (OUTPUT_FILE) {
    fs.writeFileSync(OUTPUT_FILE, description);
    console.log(`✅ PR description written to: ${OUTPUT_FILE}`);
  } else {
    console.log(description);
  }
}

main();
