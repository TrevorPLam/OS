#!/usr/bin/env node
/**
 * Extract PR Template Data
 * 
 * Parses pull request template data from PR body and extracts structured information
 * for injection into trace logs, agent logs, and interaction logs.
 * 
 * Usage:
 *   node scripts/extract-pr-template-data.mjs --pr-body <pr_body_text> [--output <output_file>]
 *   node scripts/extract-pr-template-data.mjs --pr-file <pr_body_file> [--output <output_file>]
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Extract change types from PR body
 */
function extractChangeTypes(prBody) {
  const changeTypes = [];
  const typeSection = prBody.match(/## Type of Change[\s\S]*?(?=##|$)/i);
  
  if (typeSection) {
    const checkedTypes = typeSection[0].match(/- \[x\]\s+(.+)/gi);
    if (checkedTypes) {
      checkedTypes.forEach(type => {
        const cleanType = type.replace(/- \[x\]\s+/i, '').trim();
        changeTypes.push(cleanType);
      });
    }
  }
  
  return changeTypes;
}

/**
 * Extract related issues from PR body
 */
function extractRelatedIssues(prBody) {
  const issues = {
    closes: [],
    relates: [],
    fixes: []
  };
  
  const issueSection = prBody.match(/## Related Issues[\s\S]*?(?=##|$)/i);
  if (issueSection) {
    const closesMatches = issueSection[0].match(/Closes\s+#(\d+)/gi);
    const relatesMatches = issueSection[0].match(/Relates to\s+#(\d+)/gi);
    const fixesMatches = issueSection[0].match(/Fixes\s+#(\d+)/gi);
    
    if (closesMatches) {
      issues.closes = closesMatches.map(m => m.match(/#(\d+)/i)[1]);
    }
    if (relatesMatches) {
      issues.relates = relatesMatches.map(m => m.match(/#(\d+)/i)[1]);
    }
    if (fixesMatches) {
      issues.fixes = fixesMatches.map(m => m.match(/#(\d+)/i)[1]);
    }
  }
  
  return issues;
}

/**
 * Extract description from PR body
 */
function extractDescription(prBody) {
  const descSection = prBody.match(/## Description[\s\S]*?(?=##|$)/i);
  if (descSection) {
    const content = descSection[0]
      .replace(/## Description/i, '')
      .replace(/<!--[\s\S]*?-->/g, '')
      .trim();
    return content || null;
  }
  return null;
}

/**
 * Extract changes summary from PR body
 */
function extractChangesSummary(prBody) {
  const summary = {
    filesModified: [],
    keyChanges: null
  };
  
  const summarySection = prBody.match(/## Changes Summary[\s\S]*?(?=##|$)/i);
  if (summarySection) {
    const filesSection = summarySection[0].match(/### Files Modified[\s\S]*?(?=###|##|$)/i);
    if (filesSection) {
      const fileMatches = filesSection[0].match(/[-*]\s+(.+)/g);
      if (fileMatches) {
        summary.filesModified = fileMatches.map(m => m.replace(/[-*]\s+]/g, '').trim());
      }
    }
    
    const keyChangesSection = summarySection[0].match(/### Key Changes[\s\S]*?(?=###|##|$)/i);
    if (keyChangesSection) {
      summary.keyChanges = keyChangesSection[0]
        .replace(/### Key Changes/i, '')
        .replace(/<!--[\s\S]*?-->/g, '')
        .trim() || null;
    }
  }
  
  return summary;
}

/**
 * Extract verification data from PR body
 */
function extractVerification(prBody) {
  const verification = {
    testCommands: [],
    testResults: {
      allTestsPass: false,
      newTestsAdded: false,
      coverageMaintained: false,
      manualTestingCompleted: false
    },
    platformTesting: {
      ios: false,
      android: false,
      web: false
    },
    evidence: []
  };
  
  const verificationSection = prBody.match(/## Verification[\s\S]*?(?=##|$)/i);
  if (verificationSection) {
    // Extract test commands
    const commandsSection = verificationSection[0].match(/```bash[\s\S]*?```/i);
    if (commandsSection) {
      const commands = commandsSection[0]
        .replace(/```bash/i, '')
        .replace(/```/g, '')
        .split('\n')
        .map(c => c.trim())
        .filter(c => c && !c.startsWith('#'));
      verification.testCommands = commands;
    }
    
    // Extract test results checkboxes
    const testResultsSection = verificationSection[0].match(/### Testing Performed[\s\S]*?(?=###|##|$)/i);
    if (testResultsSection) {
      verification.testResults.allTestsPass = /- \[x\]\s+All existing tests pass/i.test(testResultsSection[0]);
      verification.testResults.newTestsAdded = /- \[x\]\s+New tests added/i.test(testResultsSection[0]);
      verification.testResults.coverageMaintained = /- \[x\]\s+Test coverage maintained/i.test(testResultsSection[0]);
      verification.testResults.manualTestingCompleted = /- \[x\]\s+Manual testing completed/i.test(testResultsSection[0]);
    }
    
    // Extract platform testing
    const platformSection = verificationSection[0].match(/### Platform Testing[\s\S]*?(?=###|##|$)/i);
    if (platformSection) {
      verification.platformTesting.ios = /- \[x\]\s+iOS/i.test(platformSection[0]);
      verification.platformTesting.android = /- \[x\]\s+Android/i.test(platformSection[0]);
      verification.platformTesting.web = /- \[x\]\s+Web/i.test(platformSection[0]);
    }
    
    // Extract evidence
    const evidenceSection = verificationSection[0].match(/### Verification Evidence[\s\S]*?(?=###|##|$)/i);
    if (evidenceSection) {
      const evidenceItems = evidenceSection[0]
        .replace(/### Verification Evidence/i, '')
        .split(/\d+\./)
        .map(e => e.trim())
        .filter(e => e && !e.startsWith('<!--'));
      verification.evidence = evidenceItems;
    }
  }
  
  return verification;
}

/**
 * Extract checklist data from PR body
 */
function extractChecklist(prBody) {
  const checklist = {
    codeQuality: {},
    documentation: {},
    testing: {},
    security: {},
    database: {},
    governance: {}
  };
  
  const checklistSection = prBody.match(/## Checklist[\s\S]*?(?=##|$)/i);
  if (checklistSection) {
    // Extract code quality items
    const codeQualitySection = checklistSection[0].match(/### Code Quality[\s\S]*?(?=###|##|$)/i);
    if (codeQualitySection) {
      checklist.codeQuality = {
        followsStyleGuidelines: /- \[x\]\s+Code follows/i.test(codeQualitySection[0]),
        selfReviewCompleted: /- \[x\]\s+Self-review/i.test(codeQualitySection[0]),
        codeCommented: /- \[x\]\s+Code is commented/i.test(codeQualitySection[0]),
        noWarnings: /- \[x\]\s+No new warnings/i.test(codeQualitySection[0]),
        debugStatementsRemoved: /- \[x\]\s+Debug statements/i.test(codeQualitySection[0])
      };
    }
    
    // Extract governance compliance
    const governanceSection = checklistSection[0].match(/### Governance Compliance[\s\S]*?(?=###|##|$)/i);
    if (governanceSection) {
      checklist.governance = {
        traceLogCreated: /- \[x\]\s+Trace log created/i.test(governanceSection[0]),
        complianceCheckPassed: /- \[x\]\s+Compliance check passed/i.test(governanceSection[0]),
        governanceVerificationPassed: /- \[x\]\s+Governance verification passed/i.test(governanceSection[0]),
        hitlItemsAddressed: /- \[x\]\s+HITL items addressed/i.test(governanceSection[0]),
        waiversDocumented: /- \[x\]\s+Waivers documented/i.test(governanceSection[0])
      };
    }
  }
  
  return checklist;
}

/**
 * Extract risks and deployment notes
 */
function extractRisksAndDeployment(prBody) {
  const risks = [];
  const deployment = {
    environmentVariables: [],
    databaseChanges: null,
    configurationChanges: null,
    rollbackPlan: null
  };
  
  const risksSection = prBody.match(/## Risks & Considerations[\s\S]*?(?=##|$)/i);
  if (risksSection) {
    const riskItems = risksSection[0]
      .replace(/## Risks & Considerations/i, '')
      .replace(/### Potential Impact Areas/i, '')
      .replace(/<!--[\s\S]*?-->/g, '')
      .split(/[-*]/)
      .map(r => r.trim())
      .filter(r => r && !r.startsWith('#'));
    risks.push(...riskItems);
  }
  
  const deploymentSection = prBody.match(/## Deployment Notes[\s\S]*?(?=##|$)/i);
  if (deploymentSection) {
    const envVarsSection = deploymentSection[0].match(/### Environment Variables[\s\S]*?(?=###|##|$)/i);
    if (envVarsSection) {
      const envVars = envVarsSection[0]
        .split(/[-*]/)
        .map(v => v.trim())
        .filter(v => v && !v.startsWith('#'));
      deployment.environmentVariables = envVars;
    }
    
    const dbSection = deploymentSection[0].match(/### Database Changes[\s\S]*?(?=###|##|$)/i);
    if (dbSection) {
      deployment.databaseChanges = dbSection[0]
        .replace(/### Database Changes/i, '')
        .replace(/<!--[\s\S]*?-->/g, '')
        .trim() || null;
    }
  }
  
  return { risks, deployment };
}

/**
 * Main extraction function
 */
function extractPRTemplateData(prBody) {
  return {
    description: extractDescription(prBody),
    changeTypes: extractChangeTypes(prBody),
    relatedIssues: extractRelatedIssues(prBody),
    changesSummary: extractChangesSummary(prBody),
    verification: extractVerification(prBody),
    checklist: extractChecklist(prBody),
    risksAndDeployment: extractRisksAndDeployment(prBody),
    extractedAt: new Date().toISOString()
  };
}

/**
 * Main execution
 */
function main() {
  const args = process.argv.slice(2);
  let prBody = null;
  let outputPath = null;
  
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
    } else if (args[i] === '--output' && i + 1 < args.length) {
      outputPath = args[i + 1];
      i++;
    }
  }
  
  if (!prBody) {
    console.error('Error: PR body required. Use --pr-body <text> or --pr-file <file>');
    process.exit(1);
  }
  
  const extractedData = extractPRTemplateData(prBody);
  
  if (outputPath) {
    fs.writeFileSync(outputPath, JSON.stringify(extractedData, null, 2), 'utf8');
    console.log(`Extracted PR template data written to: ${outputPath}`);
  } else {
    console.log(JSON.stringify(extractedData, null, 2));
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { extractPRTemplateData };
