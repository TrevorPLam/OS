#!/usr/bin/env node
// Auto-detect task completion by analyzing PRs, commits, and acceptance criteria
// Usage: node scripts/intelligent/auto-detect-task-completion.mjs [--pr-number N] [--commit SHA] [--task-id TASK-XXX]

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const PR_NUMBER = process.argv.find((arg) => arg.startsWith("--pr-number="))?.split("=")[1];
const COMMIT_SHA = process.argv.find((arg) => arg.startsWith("--commit="))?.split("=")[1];
const TASK_ID = process.argv.find((arg) => arg.startsWith("--task-id="))?.split("=")[1];
const DRY_RUN = process.argv.includes("--dry-run");

function parseTaskFile(filePath) {
  const content = fs.readFileSync(filePath, "utf8");
  const task = {
    id: null,
    title: null,
    priority: null,
    status: null,
    acceptanceCriteria: [],
    dependencies: [],
    notes: [],
  };

  // Extract task ID
  const idMatch = content.match(/### \[(TASK-\d+)\]/);
  if (idMatch) task.id = idMatch[1];

  // Extract title
  const titleMatch = content.match(/### \[TASK-\d+\] (.+)/);
  if (titleMatch) task.title = titleMatch[1].trim();

  // Extract priority
  const priorityMatch = content.match(/- \*\*Priority:\*\* (P[0-3])/);
  if (priorityMatch) task.priority = priorityMatch[1];

  // Extract status
  const statusMatch = content.match(/- \*\*Status:\*\* (.+)/);
  if (statusMatch) task.status = statusMatch[1].trim();

  // Extract acceptance criteria
  const criteriaSection = content.match(/#### Acceptance Criteria\n([\s\S]*?)(?=\n####|$)/);
  if (criteriaSection) {
    const criteriaLines = criteriaSection[1].matchAll(/- \[([ x])\] (.+)/g);
    for (const match of criteriaLines) {
      task.acceptanceCriteria.push({
        completed: match[1].trim() === "x",
        text: match[2].trim(),
      });
    }
  }

  // Extract dependencies
  const depsMatch = content.match(/Dependencies?: (.+)/i);
  if (depsMatch) {
    const deps = depsMatch[1].match(/TASK-\d+/g);
    if (deps) task.dependencies = deps;
  }

  return task;
}

function analyzeCodeChanges(taskId) {
  try {
    // Get changed files
    const changedFiles = execSync("git diff --name-only HEAD~1 HEAD", { encoding: "utf8" })
      .trim()
      .split("\n")
      .filter(Boolean);

    // Get diff stats
    const diffStats = execSync("git diff --stat HEAD~1 HEAD", { encoding: "utf8" });

    // Check for test files
    const hasTests = changedFiles.some((f) => f.includes("__tests__") || f.includes(".test.") || f.includes(".spec."));

    // Check for documentation
    const hasDocs = changedFiles.some((f) => f.endsWith(".md") || f.includes("docs/"));

    return {
      changedFiles,
      diffStats,
      hasTests,
      hasDocs,
      fileCount: changedFiles.length,
    };
  } catch (e) {
    return { changedFiles: [], diffStats: "", hasTests: false, hasDocs: false, fileCount: 0 };
  }
}

function checkTestCoverage(taskId) {
  try {
    // Try to get coverage from test output
    const coverageOutput = execSync("npm test -- --coverage --silent 2>&1", { encoding: "utf8" });
    const coverageMatch = coverageOutput.match(/All files\s+\|\s+(\d+\.\d+)%/);
    if (coverageMatch) {
      return parseFloat(coverageMatch[1]);
    }
  } catch (e) {
    // Coverage check failed
  }
  return null;
}

function evaluateAcceptanceCriteria(task, codeChanges) {
  const results = [];

  for (const criterion of task.acceptanceCriteria) {
    if (criterion.completed) {
      results.push({ criterion: criterion.text, status: "already_complete" });
      continue;
    }

    const text = criterion.text.toLowerCase();
    let status = "pending";
    let confidence = 0;

    // Check for test-related criteria
    if (text.includes("test") || text.includes("coverage")) {
      if (codeChanges.hasTests) {
        confidence += 0.5;
      }
      if (text.includes("coverage") && text.match(/\d+%/)) {
        const targetCoverage = parseInt(text.match(/(\d+)%/)?.[1] || "0");
        const actualCoverage = checkTestCoverage(task.id);
        if (actualCoverage && actualCoverage >= targetCoverage) {
          confidence = 1.0;
          status = "complete";
        }
      } else if (codeChanges.hasTests) {
        confidence = 0.8;
        status = "likely_complete";
      }
    }

    // Check for file-specific criteria
    if (text.includes("file") || text.includes("create") || text.includes("add")) {
      if (codeChanges.fileCount > 0) {
        confidence += 0.3;
      }
    }

    // Check for E2E/integration test criteria
    if (text.includes("e2e") || text.includes("integration") || text.includes("end-to-end")) {
      if (codeChanges.hasTests) {
        confidence += 0.4;
      }
    }

    // Check for documentation criteria
    if (text.includes("document") || text.includes("doc")) {
      if (codeChanges.hasDocs) {
        confidence = 0.9;
        status = "likely_complete";
      }
    }

    // High confidence threshold
    if (confidence >= 0.8) {
      status = "complete";
    } else if (confidence >= 0.5) {
      status = "likely_complete";
    }

    results.push({
      criterion: criterion.text,
      status,
      confidence,
    });
  }

  return results;
}

function findTaskInFiles(taskId) {
  const todoPath = path.join(REPO_ROOT, ".repo/tasks/TODO.md");
  const backlogPath = path.join(REPO_ROOT, ".repo/tasks/BACKLOG.md");

  for (const filePath of [todoPath, backlogPath]) {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, "utf8");
      if (content.includes(`[${taskId}]`)) {
        return { filePath, content };
      }
    }
  }
  return null;
}

function archiveTask(task, archivePath) {
  const archiveContent = fs.readFileSync(archivePath, "utf8");
  const completedDate = new Date().toISOString().split("T")[0];

  // Extract task section
  const taskMatch = task.content.match(/(### \[TASK-\d+\][\s\S]*?)(?=\n---|\n###|$)/);
  if (!taskMatch) return;

  let taskSection = taskMatch[1];

  // Update status to Completed
  taskSection = taskSection.replace(/- \*\*Status:\*\* .+/, `- **Status:** Completed`);

  // Add completed date
  if (!taskSection.includes("**Completed:**")) {
    taskSection = taskSection.replace(/- \*\*Created:\*\* .+/, `$&\n- **Completed:** ${completedDate}`);
  }

  // Mark all criteria as complete
  taskSection = taskSection.replace(/- \[ \]/g, "- [x]");

  // Insert at top of archive (after header)
  const headerEnd = archiveContent.indexOf("---");
  const newArchiveContent =
    archiveContent.slice(0, headerEnd + 4) + "\n\n" + taskSection + "\n\n---\n\n" + archiveContent.slice(headerEnd + 4);

  return newArchiveContent;
}

function main() {
  console.log("🔍 Auto-Detecting Task Completion\n");

  // Find tasks to check
  const tasksToCheck = [];

  if (TASK_ID) {
    const taskFile = findTaskInFiles(TASK_ID);
    if (taskFile) {
      tasksToCheck.push({ id: TASK_ID, filePath: taskFile.filePath, content: taskFile.content });
    }
  } else {
    // Check all tasks in TODO.md
    const todoPath = path.join(REPO_ROOT, ".repo/tasks/TODO.md");
    if (fs.existsSync(todoPath)) {
      const content = fs.readFileSync(todoPath, "utf8");
      const taskMatches = content.matchAll(/### \[(TASK-\d+)\]/g);
      for (const match of taskMatches) {
        const taskFile = findTaskInFiles(match[1]);
        if (taskFile) {
          tasksToCheck.push({ id: match[1], filePath: taskFile.filePath, content: taskFile.content });
        }
      }
    }
  }

  if (tasksToCheck.length === 0) {
    console.log("❌ No tasks found to check");
    process.exit(1);
  }

  const codeChanges = analyzeCodeChanges();
  const completedTasks = [];

  for (const taskInfo of tasksToCheck) {
    const task = parseTaskFile(taskInfo.filePath);
    console.log(`\n📋 Checking ${task.id}: ${task.title}`);

    const criteriaResults = evaluateAcceptanceCriteria(task, codeChanges);
    const allComplete = criteriaResults.every((r) => r.status === "complete" || r.status === "already_complete");
    const mostlyComplete = criteriaResults.filter((r) => r.status === "complete" || r.status === "likely_complete").length / criteriaResults.length >= 0.8;

    console.log(`   Criteria: ${criteriaResults.filter((r) => r.status === "complete").length}/${criteriaResults.length} complete`);

    if (allComplete) {
      console.log(`   ✅ Task appears complete!`);
      completedTasks.push({ task, taskInfo, criteriaResults });
    } else if (mostlyComplete) {
      console.log(`   ⚠️  Task mostly complete (${Math.round(mostlyComplete * 100)}%) - review recommended`);
    } else {
      console.log(`   ⏳ Task still in progress`);
    }
  }

  if (completedTasks.length > 0 && !DRY_RUN) {
    console.log(`\n📦 Archiving ${completedTasks.length} completed task(s)...`);
    const archivePath = path.join(REPO_ROOT, ".repo/tasks/ARCHIVE.md");
    let archiveContent = fs.readFileSync(archivePath, "utf8");

    for (const { task, taskInfo } of completedTasks) {
      const newArchive = archiveTask({ content: taskInfo.content }, archivePath);
      if (newArchive) {
        archiveContent = newArchive;
        // Remove from TODO.md
        const todoContent = fs.readFileSync(taskInfo.filePath, "utf8");
        const updatedTodo = todoContent.replace(/(### \[TASK-\d+\][\s\S]*?)(?=\n---|\n###|$)/, "");
        fs.writeFileSync(taskInfo.filePath, updatedTodo);
        console.log(`   ✅ Archived ${task.id}`);
      }
    }

    fs.writeFileSync(archivePath, archiveContent);
    console.log(`\n✅ Task archiving complete!`);
  } else if (DRY_RUN) {
    console.log(`\n[DRY RUN] Would archive ${completedTasks.length} task(s)`);
  }
}

main();
