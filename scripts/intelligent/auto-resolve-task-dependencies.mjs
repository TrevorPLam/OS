#!/usr/bin/env node
// Intelligent Task Dependency Resolution - auto-promote tasks when dependencies are met
// Usage: node scripts/intelligent/auto-resolve-task-dependencies.mjs [--dry-run]

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const DRY_RUN = process.argv.includes("--dry-run");

function parseTask(taskContent, taskId) {
  const task = {
    id: taskId,
    priority: null,
    status: null,
    dependencies: [],
    module: null,
    changeType: null,
  };

  // Extract priority
  const priorityMatch = taskContent.match(/- \*\*Priority:\*\* (P[0-3])/);
  if (priorityMatch) task.priority = priorityMatch[1];

  // Extract status
  const statusMatch = taskContent.match(/- \*\*Status:\*\* (.+)/);
  if (statusMatch) task.status = statusMatch[1].trim();

  // Extract dependencies
  const depsMatch = taskContent.match(/Dependencies?: (.+)/i);
  if (depsMatch) {
    const deps = depsMatch[1].match(/TASK-\d+/g);
    if (deps) task.dependencies = deps;
  }

    // Extract module/feature area from context or notes
    const moduleMatch = taskContent.match(/(?:Module|Feature)[:\s]+(\w+)/i);
    if (moduleMatch) task.module = moduleMatch[1].toLowerCase();
  }

  return task;
}

function getCompletedTasks() {
  const archivePath = path.join(REPO_ROOT, ".repo/tasks/ARCHIVE.md");
  if (!fs.existsSync(archivePath)) return new Set();

  const content = fs.readFileSync(archivePath, "utf8");
  const completedTasks = new Set();
  const taskMatches = content.matchAll(/### \[(TASK-\d+)\]/g);
  for (const match of taskMatches) {
    completedTasks.add(match[1]);
  }
  return completedTasks;
}

function getCurrentTasks() {
  const todoPath = path.join(REPO_ROOT, ".repo/tasks/TODO.md");
  if (!fs.existsSync(todoPath)) return new Set();

  const content = fs.readFileSync(todoPath, "utf8");
  const currentTasks = new Set();
  const taskMatches = content.matchAll(/### \[(TASK-\d+)\]/g);
  for (const match of taskMatches) {
    currentTasks.add(match[1]);
  }
  return currentTasks;
}

function getTasksByPriority(backlogPath) {
  const content = fs.readFileSync(backlogPath, "utf8");
  const tasks = [];

  // Split by priority sections
  const prioritySections = content.split(/### (P[0-3])/);
  for (let i = 1; i < prioritySections.length; i += 2) {
    const priority = prioritySections[i];
    const sectionContent = prioritySections[i + 1];

    const taskMatches = sectionContent.matchAll(/(#### \[(TASK-\d+)\][\s\S]*?)(?=\n####|$)/g);
    for (const match of taskMatches) {
      const taskId = match[2];
      const taskContent = match[1];
      const task = parseTask(taskContent, taskId);
      task.priority = priority;
      tasks.push({ task, content: taskContent });
    }
  }

  return tasks;
}

function areDependenciesMet(task, completedTasks) {
  if (!task.dependencies || task.dependencies.length === 0) return true;
  return task.dependencies.every((dep) => completedTasks.has(dep));
}

function groupTasksBySimilarity(tasks) {
  const groups = {
    byModule: {},
    byChangeType: {},
    byPriority: {},
  };

  for (const { task } of tasks) {
    if (task.module) {
      if (!groups.byModule[task.module]) groups.byModule[task.module] = [];
      groups.byModule[task.module].push(task);
    }
    if (task.changeType) {
      if (!groups.byChangeType[task.changeType]) groups.byChangeType[task.changeType] = [];
      groups.byChangeType[task.changeType].push(task);
    }
    if (task.priority) {
      if (!groups.byPriority[task.priority]) groups.byPriority[task.priority] = [];
      groups.byPriority[task.priority].push(task);
    }
  }

  return groups;
}

function shouldPromoteTask(task, currentTasks, completedTasks) {
  // Check if already in TODO
  if (currentTasks.has(task.id)) return false;

  // Check if dependencies are met
  if (!areDependenciesMet(task, completedTasks)) return false;

  // Check if not blocked
  if (task.status === "Blocked") {
    // Re-check if still blocked
    if (areDependenciesMet(task, completedTasks)) {
      return true; // Dependencies now met, can unblock
    }
    return false;
  }

  return true;
}

function maintainTaskGrouping(tasksToPromote, currentTasksContent) {
  // Count current tasks
  const currentTaskMatches = currentTasksContent.matchAll(/### \[TASK-\d+\]/g);
  const currentTaskCount = Array.from(currentTaskMatches).length;

  // If we have 3-5 tasks, try to maintain similar grouping
  if (currentTaskCount >= 3 && currentTaskCount <= 5) {
    // Group by similarity
    const groups = groupTasksBySimilarity(tasksToPromote);
    // Prefer promoting tasks that match current group
    // For now, just promote highest priority
    return tasksToPromote.sort((a, b) => {
      const priorityOrder = { P0: 0, P1: 1, P2: 2, P3: 3 };
      return priorityOrder[a.task.priority] - priorityOrder[b.task.priority];
    });
  }

  // If fewer than 3 tasks, promote to reach 3-5
  const needed = Math.max(0, 3 - currentTaskCount);
  return tasksToPromote.slice(0, needed);
}

function main() {
  console.log("🔄 Auto-Resolving Task Dependencies\n");

  const completedTasks = getCompletedTasks();
  const currentTasks = getCurrentTasks();
  const backlogPath = path.join(REPO_ROOT, ".repo/tasks/BACKLOG.md");
  const todoPath = path.join(REPO_ROOT, ".repo/tasks/TODO.md");

  if (!fs.existsSync(backlogPath)) {
    console.log("❌ BACKLOG.md not found");
    process.exit(1);
  }

  const backlogTasks = getTasksByPriority(backlogPath);
  const tasksToPromote = [];

  console.log(`📊 Analyzing ${backlogTasks.length} backlog tasks...`);
  console.log(`   Completed: ${completedTasks.size}`);
  console.log(`   Current: ${currentTasks.size}\n`);

  for (const { task, content } of backlogTasks) {
    if (shouldPromoteTask(task, currentTasks, completedTasks)) {
      tasksToPromote.push({ task, content });
      console.log(`   ✅ ${task.id} ready to promote (dependencies met)`);
    } else if (task.dependencies && task.dependencies.length > 0) {
      const unmetDeps = task.dependencies.filter((d) => !completedTasks.has(d));
      if (unmetDeps.length > 0) {
        console.log(`   ⏳ ${task.id} waiting for: ${unmetDeps.join(", ")}`);
      }
    }
  }

  if (tasksToPromote.length === 0) {
    console.log("\n✅ No tasks ready to promote");
    return;
  }

  // Maintain task grouping (3-5 similar tasks)
  const currentTodoContent = fs.existsSync(todoPath) ? fs.readFileSync(todoPath, "utf8") : "";
  const tasksToActuallyPromote = maintainTaskGrouping(tasksToPromote, currentTodoContent);

  console.log(`\n📦 Promoting ${tasksToActuallyPromote.length} task(s) to TODO.md...`);

  if (DRY_RUN) {
    for (const { task } of tasksToActuallyPromote) {
      console.log(`   [DRY RUN] Would promote ${task.id}: ${task.priority}`);
    }
    return;
  }

  // Read current TODO
  let todoContent = fs.existsSync(todoPath) ? fs.readFileSync(todoPath, "utf8") : "# 🤖 Current Active Tasks\n\n---\n\n## Active Tasks\n\n";

  // Add promoted tasks
  for (const { content: taskContent } of tasksToActuallyPromote) {
    // Convert #### to ### for TODO format
    const formattedTask = taskContent.replace(/^#### /gm, "### ");
    todoContent += formattedTask + "\n\n---\n\n";
  }

  // Remove from backlog
  let backlogContent = fs.readFileSync(backlogPath, "utf8");
  for (const { task } of tasksToActuallyPromote) {
    const taskPattern = new RegExp(`(#### \\[${task.id}\\][\\s\\S]*?)(?=\\n####|$)`, "g");
    backlogContent = backlogContent.replace(taskPattern, "");
  }

  // Clean up extra newlines
  backlogContent = backlogContent.replace(/\n{3,}/g, "\n\n");

  fs.writeFileSync(todoPath, todoContent);
  fs.writeFileSync(backlogPath, backlogContent);

  console.log(`\n✅ Promoted ${tasksToActuallyPromote.length} task(s) to TODO.md`);
}

main();
