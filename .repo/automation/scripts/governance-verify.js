#!/usr/bin/env node
// /.repo/automation/scripts/governance-verify.js
// Governance verification script - checks compliance with governance framework
// This is a Node.js version that can be used alongside or instead of the bash script

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Load agent logger (graceful fallback if not available)
let logger;
try {
  logger = require('./agent-logger.js');
} catch (err) {
  // Logger not available, continue without logging
  logger = null;
}

// Colors
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const GREEN = '\x1b[32m';
const RESET = '\x1b[0m';

let errors = 0;
let warnings = 0;
const hardFailures = [];

function logError(msg) {
  console.error(`${RED}❌ ERROR: ${msg}${RESET}`);
  errors++;
  hardFailures.push(msg);
}

function logWarning(msg) {
  console.warn(`${YELLOW}⚠️  WARNING: ${msg}${RESET}`);
  warnings++;
}

function logInfo(msg) {
  console.log(`${GREEN}ℹ️  INFO: ${msg}${RESET}`);
}

function logSuccess(msg) {
  console.log(`${GREEN}✅ ${msg}${RESET}`);
}

function fileExists(filepath) {
  try {
    return fs.existsSync(filepath) && fs.statSync(filepath).isFile();
  } catch {
    return false;
  }
}

function dirExists(dirpath) {
  try {
    return fs.existsSync(dirpath) && fs.statSync(dirpath).isDirectory();
  } catch {
    return false;
  }
}

function runCommand(cmd, silent = false) {
  try {
    const result = execSync(cmd, {
      encoding: 'utf8',
      stdio: silent ? 'pipe' : 'inherit',
      cwd: process.cwd()
    });
    return { success: true, output: result };
  } catch (e) {
    return { success: false, error: e.message };
  }
}

// Check 1: Required policy files
function checkPolicyFiles() {
  logInfo('Checking required policy files...');
  const requiredFiles = [
    '.repo/policy/CONSTITUTION.md',
    '.repo/policy/PRINCIPLES.md',
    '.repo/policy/QUALITY_GATES.md',
    '.repo/policy/SECURITY_BASELINE.md',
    '.repo/policy/HITL.md',
    '.repo/policy/BOUNDARIES.md'
  ];

  for (const file of requiredFiles) {
    if (fileExists(file)) {
      logSuccess(`Policy file exists: ${file}`);
    } else {
      logError(`Required policy file missing: ${file}`);
    }
  }
}

// Check 2: Manifest exists and no UNKNOWN
function checkManifest() {
  logInfo('Checking repository manifest...');
  const manifestPath = '.repo/repo.manifest.yaml';

  if (!fileExists(manifestPath)) {
    logError(`Repository manifest missing: ${manifestPath}`);
    return;
  }

  logSuccess(`Manifest exists: ${manifestPath}`);

  const manifestContent = fs.readFileSync(manifestPath, 'utf8');
  if (manifestContent.includes('<UNKNOWN>')) {
    logError('Manifest contains <UNKNOWN> placeholders (must be resolved via HITL)');
  }
}

// Check 3: HITL items status
function checkHITLStatus() {
  logInfo('Checking HITL items status...');
  const hitlPath = '.repo/policy/HITL.md';

  if (!fileExists(hitlPath)) {
    logWarning(`HITL index file not found: ${hitlPath}`);
    return;
  }

  const hitlContent = fs.readFileSync(hitlPath, 'utf8');

  // Check for active non-completed HITL items
  const activePattern = /\|(HITL-\d+)\|.*\|(Pending|In Progress|Blocked)\|/g;
  const blockingItems = [];
  let match;

  while ((match = activePattern.exec(hitlContent)) !== null) {
    blockingItems.push(match[1]);
  }

  if (blockingItems.length > 0) {
    logWarning(`Active HITL items found (not Completed): ${blockingItems.join(', ')}`);
    logWarning('  → Check .repo/policy/HITL.md for details');
    logWarning('  → PR merge may be blocked until HITL items are Completed');
  } else {
    logSuccess('No blocking HITL items found');
  }

  // Check HITL item files
  const hitlDir = '.repo/hitl';
  if (dirExists(hitlDir)) {
    const hitlFiles = fs.readdirSync(hitlDir)
      .filter(f => f.startsWith('HITL-') && f.endsWith('.md'));
    if (hitlFiles.length > 0) {
      logInfo(`Found ${hitlFiles.length} HITL item file(s) in .repo/hitl/`);
    }
  }
}

// Check 4: Repository structure
function checkRepositoryStructure() {
  logInfo('Checking repository structure...');
  const requiredDirs = [
    '.repo',
    '.repo/policy',
    '.repo/hitl'
  ];

  for (const dir of requiredDirs) {
    if (dirExists(dir)) {
      logSuccess(`Directory exists: ${dir}`);
    } else {
      logError(`Required directory missing: ${dir}`);
    }
  }
}

// Check 5: Trace log schema
function checkTraceLogSchema() {
  logInfo('Checking trace log schema...');
  const schemaPath = '.repo/templates/AGENT_TRACE_SCHEMA.json';

  if (!fileExists(schemaPath)) {
    logWarning(`Trace log schema not found: ${schemaPath} (optional, but recommended)`);
    return;
  }

  logSuccess(`Trace log schema exists: ${schemaPath}`);

  try {
    JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
    logSuccess('Trace log schema is valid JSON');
  } catch (e) {
    logError(`Trace log schema is not valid JSON: ${schemaPath}`);
  }
}

// Check 6: Trace logs validation
function checkTraceLogs() {
  logInfo('Checking for trace logs in recent changes...');
  const traceDir = '.repo/traces';

  if (!dirExists(traceDir)) {
    logWarning(`Trace log directory missing: ${traceDir} (create with: mkdir -p ${traceDir})`);
    return;
  }

  logSuccess(`Trace log directory exists: ${traceDir}`);

  // Check for trace log files
  const traceFiles = fs.readdirSync(traceDir)
    .filter(f => f.endsWith('.json'))
    .map(f => path.join(traceDir, f));

  if (traceFiles.length > 0) {
    logInfo(`Found ${traceFiles.length} trace log file(s)`);

    // Validate each trace log
    const validator = path.resolve(__dirname, 'validate-agent-trace.js');
    if (fileExists(validator)) {
      for (const traceFile of traceFiles) {
        const result = runCommand(`node "${validator}" "${traceFile}"`, true);
        if (!result.success) {
          logWarning(`Trace log validation failed: ${traceFile}`);
        }
      }
    } else {
      logWarning('Trace log validator not found, skipping validation');
    }
  }
}

// Check 7: ADR triggers
function checkADRTriggers() {
  logInfo('Checking for ADR triggers...');
  const adrDetector = 'scripts/detect-adr-triggers.sh';

  if (fileExists(adrDetector)) {
    const result = runCommand(`bash "${adrDetector}"`, true);
    if (!result.success) {
      logWarning('ADR may be required (run: scripts/detect-adr-triggers.sh for details)');
    } else {
      logSuccess('No ADR triggers detected');
    }
  }
}

// Check 7b: Boundary violations
function checkBoundaries() {
  logInfo('Checking module boundaries...');
  const boundaryChecker = path.resolve(__dirname, 'check-boundaries.js');
  const lintImportsCmd = 'lint-imports --config .importlinter';

  // Try Node.js script first, fall back to direct command
  if (fileExists(boundaryChecker)) {
    const result = runCommand(`node "${boundaryChecker}" --fail-on-violations`, true);
    if (!result.success) {
      logError('Boundary violations detected (hard gate failure)');
      logError('Fix violations or create waiver per .repo/policy/BOUNDARIES.md');
      logError('Run: lint-imports --config .importlinter for details');
      hardFailures.push('Module boundary violations');
    } else {
      logSuccess('No boundary violations detected');
    }
  } else if (runCommand('which lint-imports 2>/dev/null || where lint-imports 2>/dev/null', true).success) {
    // Try direct command if script not available
    const result = runCommand(lintImportsCmd, true);
    if (!result.success) {
      logError('Boundary violations detected (hard gate failure)');
      logError('Fix violations or create waiver per .repo/policy/BOUNDARIES.md');
      hardFailures.push('Module boundary violations');
    } else {
      logSuccess('No boundary violations detected');
    }
  } else {
    logWarning('Boundary checker not available (lint-imports not installed)');
    logWarning('Install with: pip install import-linter==2.0');
  }
}

// Check 8: Expired waivers
function checkExpiredWaivers() {
  logInfo('Checking for expired waivers...');
  const waiverChecker = 'scripts/check-expired-waivers.sh';

  if (fileExists(waiverChecker)) {
    const result = runCommand(`bash "${waiverChecker}"`, true);
    if (!result.success) {
      logWarning('Expired waivers detected (run: scripts/check-expired-waivers.sh for details)');
    } else {
      logSuccess('No expired waivers found');
    }
  }
}

// Check 9: Task format validation
function checkTaskFormat() {
  logInfo('Checking task format...');
  const taskValidator = 'scripts/validate-task-format.sh';

  if (fileExists(taskValidator)) {
    const taskFiles = ['.repo/tasks/TODO.md', '.repo/tasks/BACKLOG.md'];
    for (const taskFile of taskFiles) {
      if (fileExists(taskFile)) {
        const result = runCommand(`bash "${taskValidator}" "${taskFile}"`, true);
        if (!result.success) {
          logWarning(`Task format issues in: ${taskFile}`);
        } else {
          logSuccess(`Task format valid: ${taskFile}`);
        }
      }
    }
  }
}

// Check 11: Required artifacts by change type
function checkArtifactsByChangeType() {
  logInfo('Checking required artifacts by change type...');
  const artifactChecker = path.resolve(__dirname, 'check-artifacts-by-change-type.js');

  if (!fileExists(artifactChecker)) {
    logWarning('Artifact checker script not found, skipping artifact validation');
    return;
  }

  // Try to get PR description from environment or git
  let prDescription = '';
  const prDescFile = process.env.PR_DESCRIPTION_FILE || '.pr-description.md';

  if (fileExists(prDescFile)) {
    prDescription = fs.readFileSync(prDescFile, 'utf8');
  } else if (process.env.PR_DESCRIPTION) {
    prDescription = process.env.PR_DESCRIPTION;
  } else {
    // Try to get from git commit message or PR
    logInfo('No PR description found, artifact checking will be limited');
    return;
  }

  // Get changed files
  let changedFiles = [];
  if (commandExists('git')) {
    const gitResult = runCommand('git diff --name-only HEAD 2>/dev/null || git diff --name-only HEAD~1 HEAD 2>/dev/null || echo ""', true);
    if (gitResult.success && gitResult.output) {
      changedFiles = gitResult.output.trim().split('\n').filter(f => f);
    }
  }

  // Write PR description to temp file
  const tempPrFile = path.join(process.cwd(), '.pr-description-temp.md');
  fs.writeFileSync(tempPrFile, prDescription);

  try {
    const args = [tempPrFile, ...changedFiles];
    const result = runCommand(`node "${artifactChecker}" ${args.map(a => `"${a}"`).join(' ')}`, false);

    if (!result.success) {
      logError('Required artifacts missing for declared change type');
      logError('This is a HARD GATE failure - PR cannot be merged');
      hardFailures.push('Missing required artifacts for change type');
    } else {
      logSuccess('All required artifacts present for change type');
    }
  } catch (e) {
    logWarning(`Artifact checking failed: ${e.message}`);
  } finally {
    // Clean up temp file
    if (fileExists(tempPrFile)) {
      try {
        fs.unlinkSync(tempPrFile);
      } catch (e) {
        // Ignore cleanup errors
      }
    }
  }
}

// Check 10: Directories auto-creation
function checkDirectories() {
  logInfo('Checking required directories...');
  const requiredDirs = ['.repo/logs', '.repo/traces'];

  for (const dir of requiredDirs) {
    if (!dirExists(dir)) {
      logWarning(`Directory missing: ${dir} (should be auto-created by scripts)`);
      // Try to create it
      try {
        fs.mkdirSync(dir, { recursive: true });
        logSuccess(`Created directory: ${dir}`);
      } catch (e) {
        logWarning(`Could not create directory: ${dir}`);
      }
    } else {
      logSuccess(`Directory exists: ${dir}`);
    }
  }
}

// Check 12: Stale context files
function checkStaleContextFiles() {
  logInfo('Checking for stale context files...');
  const staleChecker = path.resolve(__dirname, 'check-stale-context.js');

  if (fileExists(staleChecker)) {
    const result = runCommand(`node "${staleChecker}" --warn-only`, true);
    if (!result.success && result.output && result.output.includes('Stale context files')) {
      logWarning('Some context files are stale (> 30 days old)');
      logWarning('Update with: node .repo/automation/scripts/update-context-verified.js --all');
    } else {
      logSuccess('Context files are up to date');
    }
  } else {
    logWarning('Stale context checker not found, skipping check');
  }
}

// Main execution
function main() {
  const startTime = Date.now();
  console.log('==========================================');
  console.log('Governance Verification (Node.js)');
  console.log('==========================================\n');

  // Log verification start
  if (logger) {
    logger.logInteraction({
      agent: 'governance-verify',
      action: 'verification_start',
      success: true,
      context: {
        script: 'governance-verify.js',
        timestamp: new Date().toISOString()
      }
    });
  }

  try {
  checkPolicyFiles();
  checkManifest();
  checkHITLStatus();
  checkRepositoryStructure();
  checkTraceLogSchema();
  checkTraceLogs();
  checkADRTriggers();
  checkBoundaries();
  checkExpiredWaivers();
  checkTaskFormat();
  checkDirectories();
  checkStaleContextFiles();
  checkArtifactsByChangeType();
  } catch (err) {
    // Log verification error
    if (logger) {
      logger.logError({
        agent: 'governance-verify',
        action: 'verification_run',
        error: err.message,
        context: {
          stack: err.stack
        }
      });
    }
    throw err;
  }

  const duration_ms = Date.now() - startTime;
  const success = errors === 0;

  // Summary
  console.log('\n==========================================');
  console.log('Governance Verification Summary');
  console.log('==========================================');
  console.log(`Errors (hard failures): ${errors}`);
  console.log(`Warnings (waiverable): ${warnings}\n`);

  // Log verification completion
  if (logger) {
    logger.logInteraction({
      agent: 'governance-verify',
      action: 'verification_complete',
      duration_ms,
      success,
      context: {
        errors,
        warnings,
        hard_failures: hardFailures.length
      }
    });

    // Log failures if any
    if (errors > 0 && logger) {
      hardFailures.forEach(failure => {
        logger.logError({
          agent: 'governance-verify',
          action: 'verification_failure',
          error: failure,
          context: {
            total_errors: errors,
            total_warnings: warnings
          }
        });
      });
    }
  }

  if (errors > 0) {
    console.log('Hard failures (blocks merge):');
    hardFailures.forEach(failure => console.log(`  - ${failure}`));
    console.log('\n❌ Governance verification FAILED (hard gate)');
    process.exit(1);
  } else if (warnings > 0) {
    console.log('⚠️  Governance verification passed with warnings (may require waiver)');
    process.exit(2);
  } else {
    console.log('✅ Governance verification PASSED');
    process.exit(0);
  }
}

if (require.main === module) {
  main();
}

module.exports = { main };
