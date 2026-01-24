#!/usr/bin/env node
/**
 * Inject PR Template Data into Logs
 * 
 * Extracts PR template data and injects it into trace logs, agent logs, and interaction logs.
 * 
 * Usage:
 *   node scripts/inject-pr-data-to-logs.mjs --pr-body <pr_body> --trace-log <trace_log_path> [--agent-log <agent_log_path>]
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { extractPRTemplateData } from "./extract-pr-template-data.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REPO_ROOT = path.resolve(__dirname, "..");
const TRACES_DIR = path.join(REPO_ROOT, ".repo/traces");
const LOGS_DIR = path.join(REPO_ROOT, ".repo/logs");
const AGENT_LOGS_DIR = path.join(REPO_ROOT, ".agent-logs/interactions");

/**
 * Inject PR data into trace log
 */
function injectIntoTraceLog(traceLogPath, prData) {
  if (!fs.existsSync(traceLogPath)) {
    console.warn(`Warning: Trace log not found: ${traceLogPath}`);
    return false;
  }
  
  const traceLog = JSON.parse(fs.readFileSync(traceLogPath, 'utf8'));
  
  // Add PR template data as metadata
  traceLog.pr_template_data = {
    description: prData.description,
    changeTypes: prData.changeTypes,
    relatedIssues: prData.relatedIssues,
    changesSummary: prData.changesSummary,
    verification: prData.verification,
    checklist: prData.checklist,
    risksAndDeployment: prData.risksAndDeployment,
    injectedAt: new Date().toISOString()
  };
  
  // Enhance existing fields with PR data if available
  if (prData.changesSummary.filesModified.length > 0) {
    // Merge with existing files, avoiding duplicates
    const existingFiles = new Set(traceLog.files || []);
    prData.changesSummary.filesModified.forEach(file => {
      if (!existingFiles.has(file)) {
        traceLog.files.push(file);
      }
    });
  }
  
  if (prData.verification.testCommands.length > 0) {
    const existingCommands = new Set(traceLog.commands || []);
    prData.verification.testCommands.forEach(cmd => {
      if (!existingCommands.has(cmd)) {
        traceLog.commands.push(cmd);
      }
    });
  }
  
  if (prData.verification.evidence.length > 0) {
    const existingEvidence = new Set(traceLog.evidence || []);
    prData.verification.evidence.forEach(ev => {
      if (!existingEvidence.has(ev)) {
        traceLog.evidence.push(ev);
      }
    });
  }
  
  fs.writeFileSync(traceLogPath, JSON.stringify(traceLog, null, 2), 'utf8');
  console.log(`Injected PR data into trace log: ${traceLogPath}`);
  return true;
}

/**
 * Inject PR data into agent log
 */
function injectIntoAgentLog(agentLogPath, prData) {
  if (!fs.existsSync(agentLogPath)) {
    console.warn(`Warning: Agent log not found: ${agentLogPath}`);
    return false;
  }
  
  const agentLog = JSON.parse(fs.readFileSync(agentLogPath, 'utf8'));
  
  // Add PR template data
  agentLog.pr_template_data = {
    description: prData.description,
    changeTypes: prData.changeTypes,
    relatedIssues: prData.relatedIssues,
    changesSummary: prData.changesSummary,
    verification: prData.verification,
    checklist: prData.checklist,
    risksAndDeployment: prData.risksAndDeployment,
    injectedAt: new Date().toISOString()
  };
  
  // Add verification evidence to agent log
  if (prData.verification.evidence.length > 0) {
    prData.verification.evidence.forEach(ev => {
      agentLog.evidence.push({
        type: "pr_verification",
        description: ev,
        timestamp: new Date().toISOString(),
        source: "pr_template"
      });
    });
  }
  
  // Add risks to agent log
  if (prData.risksAndDeployment.risks.length > 0) {
    prData.risksAndDeployment.risks.forEach(risk => {
      agentLog.risks.push({
        description: risk,
        source: "pr_template",
        timestamp: new Date().toISOString()
      });
    });
  }
  
  agentLog.metadata.updated = new Date().toISOString();
  
  fs.writeFileSync(agentLogPath, JSON.stringify(agentLog, null, 2), 'utf8');
  console.log(`Injected PR data into agent log: ${agentLogPath}`);
  return true;
}

/**
 * Log PR data to interaction log
 */
function logToInteractionLog(prData, context = {}) {
  const today = new Date().toISOString().split('T')[0];
  const logFile = path.join(AGENT_LOGS_DIR, `${today}.jsonl`);
  
  // Ensure directory exists
  if (!fs.existsSync(AGENT_LOGS_DIR)) {
    fs.mkdirSync(AGENT_LOGS_DIR, { recursive: true });
  }
  
  const logEntry = {
    timestamp: new Date().toISOString(),
    agent: context.agent || "Auto",
    action: "pr_template_injected",
    success: true,
    context: {
      ...context,
      pr_template_data: {
        changeTypes: prData.changeTypes,
        relatedIssues: prData.relatedIssues,
        hasVerification: prData.verification.testCommands.length > 0,
        hasRisks: prData.risksAndDeployment.risks.length > 0
      }
    }
  };
  
  try {
    fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n', 'utf8');
    console.log(`Logged PR data to interaction log: ${logFile}`);
    return true;
  } catch (error) {
    console.error(`Error writing to interaction log: ${error.message}`);
    return false;
  }
}

/**
 * Find latest trace log
 */
function findLatestTraceLog() {
  if (!fs.existsSync(TRACES_DIR)) {
    return null;
  }
  
  const files = fs.readdirSync(TRACES_DIR)
    .filter(f => f.startsWith('trace-') && f.endsWith('.json'))
    .map(f => ({
      name: f,
      path: path.join(TRACES_DIR, f),
      mtime: fs.statSync(path.join(TRACES_DIR, f)).mtime
    }))
    .sort((a, b) => b.mtime - a.mtime);
  
  return files.length > 0 ? files[0].path : null;
}

/**
 * Find latest agent log
 */
function findLatestAgentLog() {
  if (!fs.existsSync(LOGS_DIR)) {
    return null;
  }
  
  const files = fs.readdirSync(LOGS_DIR)
    .filter(f => f.startsWith('log-') && f.endsWith('.json'))
    .map(f => ({
      name: f,
      path: path.join(LOGS_DIR, f),
      mtime: fs.statSync(path.join(LOGS_DIR, f)).mtime
    }))
    .sort((a, b) => b.mtime - a.mtime);
  
  return files.length > 0 ? files[0].path : null;
}

/**
 * Main execution
 */
function main() {
  const args = process.argv.slice(2);
  let prBody = null;
  let traceLogPath = null;
  let agentLogPath = null;
  let autoFind = false;
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--pr-body' && i + 1 < args.length) {
      prBody = args[i + 1];
      i++;
    } else if (args[i] === '--pr-file' && i + 1 < args.length) {
      const filePath = path.resolve(args[i + 1]);
      if (!fs.existsSync(filePath)) {
        console.error(`Error: PR body file not found: ${filePath}`);
        process.exit(1);
      }
      prBody = fs.readFileSync(filePath, 'utf8');
      i++;
    } else if (args[i] === '--trace-log' && i + 1 < args.length) {
      traceLogPath = path.resolve(args[i + 1]);
      i++;
    } else if (args[i] === '--agent-log' && i + 1 < args.length) {
      agentLogPath = path.resolve(args[i + 1]);
      i++;
    } else if (args[i] === '--auto-find') {
      autoFind = true;
    }
  }
  
  if (!prBody) {
    console.error('Error: PR body required. Use --pr-body <text> or --pr-file <file>');
    process.exit(1);
  }
  
  // Extract PR template data
  const prData = extractPRTemplateData(prBody);
  
  // Auto-find logs if requested
  if (autoFind) {
    if (!traceLogPath) {
      traceLogPath = findLatestTraceLog();
    }
    if (!agentLogPath) {
      agentLogPath = findLatestAgentLog();
    }
  }
  
  // Inject into trace log
  if (traceLogPath) {
    injectIntoTraceLog(traceLogPath, prData);
  } else {
    console.warn('Warning: No trace log specified. Use --trace-log <path> or --auto-find');
  }
  
  // Inject into agent log
  if (agentLogPath) {
    injectIntoAgentLog(agentLogPath, prData);
  } else {
    console.warn('Warning: No agent log specified. Use --agent-log <path> or --auto-find');
  }
  
  // Always log to interaction log
  logToInteractionLog(prData, {
    traceLog: traceLogPath,
    agentLog: agentLogPath
  });
  
  console.log('\nPR template data injection complete.');
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { injectIntoTraceLog, injectIntoAgentLog, logToInteractionLog };
