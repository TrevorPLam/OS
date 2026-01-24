#!/usr/bin/env node
// Intelligent Reviewer Assignment
// Usage: node scripts/intelligent/intelligent-reviewer-assignment.mjs [--pr-number N] [--dry-run]

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const PR_NUMBER = process.argv.find((arg) => arg.startsWith("--pr-number="))?.split("=")[1];
const DRY_RUN = process.argv.includes("--dry-run");

function getCodeOwners(filePath) {
  try {
    // Use git blame to find code owners
    const blame = execSync(`git blame --line-porcelain "${filePath}" | grep "^author " | sort | uniq -c | sort -rn`, {
      encoding: "utf8",
      cwd: REPO_ROOT,
      shell: true,
    });

    const owners = [];
    const lines = blame.trim().split("\n").slice(0, 3); // Top 3 contributors
    for (const line of lines) {
      const match = line.match(/\d+\s+author\s+(.+)/);
      if (match) {
        owners.push(match[1].trim());
      }
    }
    return owners;
  } catch (e) {
    return [];
  }
}

function getChangedFiles(baseRef = "main") {
  try {
    const files = execSync(`git diff --name-only ${baseRef}...HEAD`, {
      encoding: "utf8",
      cwd: REPO_ROOT,
    })
      .trim()
      .split("\n")
      .filter(Boolean);
    return files;
  } catch (e) {
    return [];
  }
}

function detectChangeType(changedFiles) {
  const files = changedFiles.join(" ").toLowerCase();
  
  if (files.includes("auth") || files.includes("security")) {
    return "security";
  }
  if (files.includes("api/") || files.includes("routes")) {
    return "api";
  }
  if (files.includes("mobile/") || files.includes("components/")) {
    return "frontend";
  }
  return "general";
}

function assignReviewers(changedFiles, changeType) {
  const reviewers = new Map(); // email -> score

  // Get code owners for each file
  for (const file of changedFiles.slice(0, 20)) {
    // Limit to first 20 files for performance
    const filePath = path.join(REPO_ROOT, file);
    if (fs.existsSync(filePath)) {
      const owners = getCodeOwners(filePath);
      owners.forEach((owner, index) => {
        const score = reviewers.get(owner) || 0;
        reviewers.set(owner, score + (3 - index)); // Higher score for more contributions
      });
    }
  }

  // Sort by score
  const sortedReviewers = Array.from(reviewers.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3) // Top 3 reviewers
    .map(([email]) => email);

  return sortedReviewers;
}

function getGitHubUsername(email) {
  try {
    // Try to get GitHub username from git config or commits
    const config = execSync(`git config user.name`, { encoding: "utf8", cwd: REPO_ROOT }).trim();
    // This is a simplified version - in real implementation, you'd map emails to GitHub usernames
    return email.split("@")[0]; // Fallback
  } catch (e) {
    return null;
  }
}

function main() {
  console.log("👥 Intelligent Reviewer Assignment\n");

  if (!PR_NUMBER) {
    console.error("❌ PR number required. Use --pr-number=N");
    console.log("   Or set GITHUB_EVENT_PATH environment variable");
    process.exit(1);
  }

  console.log(`📋 PR: #${PR_NUMBER}\n`);

  const changedFiles = getChangedFiles();
  console.log(`📁 Changed Files: ${changedFiles.length}\n`);

  if (changedFiles.length === 0) {
    console.log("⚠️  No changed files found");
    return;
  }

  const changeType = detectChangeType(changedFiles);
  console.log(`🔍 Change Type: ${changeType}\n`);

  const reviewers = assignReviewers(changedFiles, changeType);

  console.log(`👥 Suggested Reviewers:\n`);
  reviewers.forEach((email, i) => {
    const username = getGitHubUsername(email);
    console.log(`   ${i + 1}. ${email}${username ? ` (@${username})` : ""}`);
  });

  if (DRY_RUN) {
    console.log(`\n[DRY RUN] Would assign reviewers to PR #${PR_NUMBER}`);
  } else {
    console.log(`\n💡 To assign reviewers, use GitHub API or GitHub CLI:`);
    console.log(`   gh pr edit ${PR_NUMBER} --add-reviewer ${reviewers.map((r) => getGitHubUsername(r) || r).join(" ")}`);
  }
}

main();
