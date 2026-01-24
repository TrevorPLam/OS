#!/usr/bin/env node
// Intelligent TODO → Task Conversion
// Usage: node scripts/intelligent/auto-convert-todos-to-tasks.mjs [--scan-all] [--dry-run]

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const SCAN_ALL = process.argv.includes("--scan-all");
const DRY_RUN = process.argv.includes("--dry-run");

function findTODOs() {
  const todos = [];
  const command = SCAN_ALL
    ? 'rg -n "TODO|FIXME|XXX|HACK" --type-add "code:*.{ts,tsx,js,jsx,py}" -t code -g "!node_modules/**" -g "!.git/**"'
    : 'git diff --cached --name-only | xargs rg -n "TODO|FIXME|XXX|HACK" 2>/dev/null || true';

  try {
    const output = execSync(command, { encoding: "utf8", cwd: REPO_ROOT, shell: true });
    const lines = output.trim().split("\n").filter(Boolean);

    for (const line of lines) {
      const match = line.match(/^(.+?):(\d+):(.+)$/);
      if (match) {
        const [, file, lineNum, content] = match;
        const todoMatch = content.match(/(TODO|FIXME|XXX|HACK)[:\s]*(.+)/i);
        if (todoMatch) {
          todos.push({
            file: file.trim(),
            line: parseInt(lineNum),
            type: todoMatch[1].toUpperCase(),
            text: todoMatch[2].trim(),
            fullLine: content.trim(),
          });
        }
      }
    }
  } catch (e) {
    // No TODOs found or command failed
  }

  return todos;
}

function determinePriority(todo) {
  const text = todo.text.toLowerCase();
  if (text.includes("critical") || text.includes("security") || text.includes("bug") || text.includes("broken")) {
    return "P0";
  }
  if (text.includes("important") || text.includes("feature") || text.includes("enhancement")) {
    return "P1";
  }
  if (text.includes("nice") || text.includes("polish") || text.includes("refactor")) {
    return "P3";
  }
  return "P2";
}

function getNextTaskNumber() {
  const backlogPath = path.join(REPO_ROOT, ".repo/tasks/BACKLOG.md");
  const archivePath = path.join(REPO_ROOT, ".repo/tasks/ARCHIVE.md");
  const todoPath = path.join(REPO_ROOT, ".repo/tasks/TODO.md");

  let maxNum = 0;
  for (const filePath of [backlogPath, archivePath, todoPath]) {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, "utf8");
      const matches = content.matchAll(/TASK-(\d+)/g);
      for (const match of matches) {
        const num = parseInt(match[1]);
        if (num > maxNum) maxNum = num;
      }
    }
  }
  return maxNum + 1;
}

function createTaskFromTODO(todo, taskNumber) {
  const priority = determinePriority(todo);
  const module = todo.file.match(/packages\/features\/(\w+)\//)?.[1] || todo.file.match(/apps\/(\w+)\//)?.[1] || "general";

  const task = `#### [TASK-${taskNumber.toString().padStart(3, "0")}] ${todo.type}: ${todo.text.substring(0, 60)}
- **Priority:** ${priority}
- **Status:** Pending
- **Created:** ${new Date().toISOString().split("T")[0]}
- **Context:** Auto-generated from ${todo.type} comment in \`${todo.file}:${todo.line}\`

#### Acceptance Criteria
- [ ] Address TODO: ${todo.text}
- [ ] Update code at \`${todo.file}:${todo.line}\`
- [ ] Add tests if applicable
- [ ] Update documentation if needed

#### Notes
- Source: \`${todo.file}:${todo.line}\`
- Original comment: \`${todo.fullLine}\`
- File: \`${todo.file}\`

#### Logs
- Trace: \`.repo/traces/TASK-${taskNumber.toString().padStart(3, "0")}-trace-*.json\`
- Agent: \`.repo/logs/TASK-${taskNumber.toString().padStart(3, "0")}-log-*.json\`

`;

  return { task, taskNumber, priority };
}

function addTaskToBacklog(task, priority) {
  const backlogPath = path.join(REPO_ROOT, ".repo/tasks/BACKLOG.md");
  let content = fs.readFileSync(backlogPath, "utf8");

  // Find priority section
  const prioritySection = content.match(new RegExp(`(### ${priority}[\\s\\S]*?)(?=### |$)`));
  if (prioritySection) {
    // Insert at end of priority section
    const sectionEnd = content.indexOf(prioritySection[0]) + prioritySection[0].length;
    content = content.slice(0, sectionEnd) + "\n" + task + "\n" + content.slice(sectionEnd);
  } else {
    // Create priority section
    content += `\n### ${priority} - ${priority === "P0" ? "Critical" : priority === "P1" ? "High" : priority === "P2" ? "Medium" : "Low"} Priority\n\n${task}\n`;
  }

  return content;
}

function main() {
  console.log("📋 Auto-Converting TODOs to Tasks\n");

  const todos = findTODOs();
  console.log(`🔍 Found ${todos.length} TODO/FIXME/XXX/HACK comments\n`);

  if (todos.length === 0) {
    console.log("✅ No TODOs found to convert");
    return;
  }

  let nextTaskNum = getNextTaskNumber();
  const tasksToAdd = [];

  for (const todo of todos) {
    const { task, taskNumber, priority } = createTaskFromTODO(todo, nextTaskNum);
    tasksToAdd.push({ task, priority, todo });
    console.log(`   📝 ${todo.type} in ${todo.file}:${todo.line} → TASK-${taskNumber.toString().padStart(3, "0")} (${priority})`);
    nextTaskNum++;
  }

  if (DRY_RUN) {
    console.log(`\n[DRY RUN] Would add ${tasksToAdd.length} tasks to backlog`);
    return;
  }

  // Group by priority and add to backlog
  const backlogPath = path.join(REPO_ROOT, ".repo/tasks/BACKLOG.md");
  let backlogContent = fs.readFileSync(backlogPath, "utf8");

  // Group tasks by priority
  const tasksByPriority = {};
  for (const { task, priority } of tasksToAdd) {
    if (!tasksByPriority[priority]) tasksByPriority[priority] = [];
    tasksByPriority[priority].push(task);
  }

  // Add tasks to appropriate priority sections
  for (const [priority, tasks] of Object.entries(tasksByPriority)) {
    const prioritySection = backlogContent.match(new RegExp(`(### ${priority}[\\s\\S]*?)(?=### |$)`));
    if (prioritySection) {
      const sectionEnd = backlogContent.indexOf(prioritySection[0]) + prioritySection[0].length;
      backlogContent = backlogContent.slice(0, sectionEnd) + "\n" + tasks.join("\n") + "\n" + backlogContent.slice(sectionEnd);
    } else {
      backlogContent += `\n### ${priority} - ${priority === "P0" ? "Critical" : priority === "P1" ? "High" : priority === "P2" ? "Medium" : "Low"} Priority\n\n${tasks.join("\n")}\n`;
    }
  }

  fs.writeFileSync(backlogPath, backlogContent);
  console.log(`\n✅ Added ${tasksToAdd.length} tasks to backlog`);
}

main();
