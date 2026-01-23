#!/usr/bin/env node
/**
 * check-artifacts-by-change-type.js
 * Checks required artifacts based on change type declared in PR
 *
 * Usage: node check-artifacts-by-change-type.js [pr-description-file] [changed-files...]
 */

const fs = require('fs');
const path = require('path');

// Required artifacts by change type (from rules.json)
const ARTIFACT_REQUIREMENTS = {
  feature: ['task_packet', 'trace_log', 'tests'],
  api_change: ['task_packet', 'adr', 'trace_log', 'openapi_update'],
  security: ['hitl', 'trace_log', 'security_tests'],
  cross_module: ['adr', 'task_packet', 'trace_log'],
  non_doc_change: ['agent_log', 'trace_log', 'reasoning_summary']
};

function parseChangeType(prDescription) {
  // Try to find change_type in PR description
  // Look for JSON format: "change_type": "..."
  // Or markdown format: ## Change Type: ... or **Change Type:** ...

  if (!prDescription) return null;

  // JSON format
  const jsonMatch = prDescription.match(/"change_type"\s*:\s*"([^"]+)"/);
  if (jsonMatch) return jsonMatch[1];

  // Markdown format
  const mdMatch = prDescription.match(/(?:change[_\s]?type|Change Type)[:：]\s*(\w+)/i);
  if (mdMatch) return mdMatch[1].toLowerCase().replace(/_/g, '_');

  // Try to infer from content
  const lower = prDescription.toLowerCase();
  if (lower.includes('security') || lower.includes('auth') || lower.includes('payment')) {
    return 'security';
  }
  if (lower.includes('api') || lower.includes('endpoint') || lower.includes('openapi')) {
    return 'api_change';
  }
  if (lower.includes('cross-module') || lower.includes('cross module') || lower.includes('boundary')) {
    return 'cross_module';
  }
  if (lower.includes('feature') || lower.includes('new functionality')) {
    return 'feature';
  }

  return null;
}

function checkArtifact(artifactType, changedFiles, repoRoot) {
  switch (artifactType) {
    case 'task_packet':
      // Check if task packet exists in TODO.md or separate file
      const todoFile = path.join(repoRoot, '.repo/tasks/TODO.md');
      if (fs.existsSync(todoFile)) {
        const content = fs.readFileSync(todoFile, 'utf8');
        if (content.includes('task_packet') || content.includes('Task Packet') || content.includes('goal')) {
          return { found: true, location: todoFile };
        }
      }
      // Check for task packet files in .repo/tasks/packets/
      const packetsDir = path.join(repoRoot, '.repo/tasks/packets');
      if (fs.existsSync(packetsDir)) {
        const packetFiles = fs.readdirSync(packetsDir).filter(f => f.endsWith('.json') && f.includes('packet'));
        if (packetFiles.length > 0) {
          // Check if packet file is recent (within last day)
          const latestPacket = packetFiles
            .map(f => ({ file: f, mtime: fs.statSync(path.join(packetsDir, f)).mtime }))
            .sort((a, b) => b.mtime - a.mtime)[0];
          const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
          if (latestPacket.mtime.getTime() > oneDayAgo) {
            return { found: true, location: path.join(packetsDir, latestPacket.file) };
          }
        }
      }
      return { found: false, location: 'TODO.md or .repo/tasks/packets/TASK-XXX-packet.json' };

    case 'trace_log':
      const tracesDir = path.join(repoRoot, '.repo/traces');
      if (fs.existsSync(tracesDir)) {
        const traceFiles = fs.readdirSync(tracesDir).filter(f => f.endsWith('.json'));
        if (traceFiles.length > 0) {
          // Check if trace log is recent (within last day)
          const latestTrace = traceFiles
            .map(f => ({ file: f, mtime: fs.statSync(path.join(tracesDir, f)).mtime }))
            .sort((a, b) => b.mtime - a.mtime)[0];
          const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
          if (latestTrace.mtime.getTime() > oneDayAgo) {
            return { found: true, location: path.join(tracesDir, latestTrace.file) };
          }
        }
      }
      return { found: false, location: '.repo/traces/' };

    case 'agent_log':
      const logsDir = path.join(repoRoot, '.repo/logs');
      if (fs.existsSync(logsDir)) {
        const logFiles = fs.readdirSync(logsDir).filter(f => f.endsWith('.json'));
        if (logFiles.length > 0) {
          const latestLog = logFiles
            .map(f => ({ file: f, mtime: fs.statSync(path.join(logsDir, f)).mtime }))
            .sort((a, b) => b.mtime - a.mtime)[0];
          const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
          if (latestLog.mtime.getTime() > oneDayAgo) {
            return { found: true, location: path.join(logsDir, latestLog.file) };
          }
        }
      }
      return { found: false, location: '.repo/logs/' };

    case 'adr':
      const adrDir = path.join(repoRoot, 'docs/adr');
      if (fs.existsSync(adrDir)) {
        const adrFiles = fs.readdirSync(adrDir).filter(f => f.match(/^ADR-\d+\.md$/));
        if (adrFiles.length > 0) {
          const latestAdr = adrFiles
            .map(f => ({ file: f, mtime: fs.statSync(path.join(adrDir, f)).mtime }))
            .sort((a, b) => b.mtime - a.mtime)[0];
          const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
          if (latestAdr.mtime.getTime() > oneDayAgo) {
            return { found: true, location: path.join(adrDir, latestAdr.file) };
          }
        }
      }
      return { found: false, location: 'docs/adr/' };

    case 'hitl':
      const hitlDir = path.join(repoRoot, '.repo/hitl');
      if (fs.existsSync(hitlDir)) {
        const hitlFiles = fs.readdirSync(hitlDir).filter(f => f.match(/^HITL-\d+\.md$/));
        if (hitlFiles.length > 0) {
          const latestHitl = hitlFiles
            .map(f => ({ file: f, mtime: fs.statSync(path.join(hitlDir, f)).mtime }))
            .sort((a, b) => b.mtime - a.mtime)[0];
          const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
          if (latestHitl.mtime.getTime() > oneDayAgo) {
            return { found: true, location: path.join(hitlDir, latestHitl.file) };
          }
        }
      }
      return { found: false, location: '.repo/hitl/' };

    case 'openapi_update':
      // Check if openapi.yaml was modified
      const openapiFile = path.join(repoRoot, 'backend/openapi.yaml');
      if (changedFiles.some(f => f.includes('openapi.yaml'))) {
        return { found: true, location: openapiFile };
      }
      return { found: false, location: 'backend/openapi.yaml (should be updated)' };

    case 'tests':
      // Check if test files were added/modified
      const hasTests = changedFiles.some(f =>
        f.includes('test') || f.includes('spec') || f.endsWith('.test.ts') || f.endsWith('_test.py')
      );
      return { found: hasTests, location: 'test files' };

    case 'security_tests':
      // Check if security test files were added/modified
      const hasSecurityTests = changedFiles.some(f =>
        (f.includes('test') || f.includes('spec')) &&
        (f.includes('security') || f.includes('auth') || f.includes('payment'))
      );
      return { found: hasSecurityTests, location: 'security test files' };

    case 'reasoning_summary':
      // Check if agent log has reasoning_summary field
      const logsDir2 = path.join(repoRoot, '.repo/logs');
      if (fs.existsSync(logsDir2)) {
        const logFiles = fs.readdirSync(logsDir2).filter(f => f.endsWith('.json'));
        for (const logFile of logFiles.slice(-5)) { // Check last 5 logs
          try {
            const logContent = JSON.parse(fs.readFileSync(path.join(logsDir2, logFile), 'utf8'));
            if (logContent.reasoning_summary && logContent.reasoning_summary.trim()) {
              return { found: true, location: path.join(logsDir2, logFile) };
            }
          } catch (e) {
            // Skip invalid JSON
          }
        }
      }
      return { found: false, location: '.repo/logs/ (agent log with reasoning_summary)' };

    default:
      return { found: false, location: `Unknown artifact type: ${artifactType}` };
  }
}

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error('Usage: node check-artifacts-by-change-type.js [pr-description-file] [changed-files...]');
    process.exit(1);
  }

  const prDescriptionFile = args[0];
  const changedFiles = args.slice(1);
  const repoRoot = process.cwd();

  let prDescription = '';
  if (fs.existsSync(prDescriptionFile)) {
    prDescription = fs.readFileSync(prDescriptionFile, 'utf8');
  }

  const changeType = parseChangeType(prDescription);

  if (!changeType) {
    console.log('⚠️  Could not determine change type from PR description');
    console.log('   Add "change_type" field to PR description');
    process.exit(2);
  }

  if (!ARTIFACT_REQUIREMENTS[changeType]) {
    console.log(`⚠️  Unknown change type: ${changeType}`);
    console.log(`   Valid types: ${Object.keys(ARTIFACT_REQUIREMENTS).join(', ')}`);
    process.exit(2);
  }

  console.log(`\n📋 Checking artifacts for change type: ${changeType}`);
  console.log(`   Required: ${ARTIFACT_REQUIREMENTS[changeType].join(', ')}\n`);

  const requiredArtifacts = ARTIFACT_REQUIREMENTS[changeType];
  const missing = [];
  const found = [];

  for (const artifact of requiredArtifacts) {
    const result = checkArtifact(artifact, changedFiles, repoRoot);
    if (result.found) {
      console.log(`✅ ${artifact}: Found at ${result.location}`);
      found.push(artifact);
    } else {
      console.log(`❌ ${artifact}: Missing (expected at ${result.location})`);
      missing.push(artifact);
    }
  }

  console.log('');

  if (missing.length > 0) {
    console.log(`❌ Missing required artifacts: ${missing.join(', ')}`);
    console.log('   This is a HARD GATE failure - PR cannot be merged');
    process.exit(1);
  } else {
    console.log('✅ All required artifacts present');
    process.exit(0);
  }
}

if (require.main === module) {
  main();
}

module.exports = { parseChangeType, checkArtifact, ARTIFACT_REQUIREMENTS };
