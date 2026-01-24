#!/usr/bin/env node
/**
 * Test Coverage Analyzer for OS Frontend
 */

import { readFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const args = process.argv.slice(2);
const jsonOutput = args.includes('--json');
const targetArg = args.find(arg => arg.startsWith('--target='));
const targetCoverage = targetArg ? parseInt(targetArg.split('=')[1]) : 80;

function readCoverageReport() {
  const coveragePaths = [
    'coverage/coverage-final.json',
    'coverage/lcov.info',
    'coverage/coverage.json'
  ];

  for (const path of coveragePaths) {
    if (existsSync(path)) {
      try {
        const content = readFileSync(path, 'utf-8');
        if (path.endsWith('.json')) {
          return JSON.parse(content);
        }
        return null;
      } catch (error) {
        console.warn(`Could not read ${path}:`, error.message);
      }
    }
  }

  return null;
}

function analyzeCoverage(coverageData) {
  if (!coverageData) {
    return {
      error: 'No coverage data found. Run tests with coverage first.',
      suggestion: 'Run: npm run test:coverage'
    };
  }

  const files = Object.keys(coverageData);
  const stats = {
    total: { statements: 0, branches: 0, functions: 0, lines: 0 },
    covered: { statements: 0, branches: 0, functions: 0, lines: 0 },
    files: []
  };

  for (const file of files) {
    const fileData = coverageData[file];
    const fileStats = {
      path: file,
      statements: { total: 0, covered: 0 },
      branches: { total: 0, covered: 0 },
      functions: { total: 0, covered: 0 },
      lines: { total: 0, covered: 0 }
    };

    if (fileData.s) {
      for (const statementId in fileData.s) {
        fileStats.statements.total++;
        stats.total.statements++;
        if (fileData.s[statementId] > 0) {
          fileStats.statements.covered++;
          stats.covered.statements++;
        }
      }
    }

    if (fileData.b) {
      for (const branchId in fileData.b) {
        const branch = fileData.b[branchId];
        fileStats.branches.total += branch.length;
        stats.total.branches += branch.length;
        const covered = branch.filter(b => b > 0).length;
        fileStats.branches.covered += covered;
        stats.covered.branches += covered;
      }
    }

    if (fileData.f) {
      for (const functionId in fileData.f) {
        fileStats.functions.total++;
        stats.total.functions++;
        if (fileData.f[functionId] > 0) {
          fileStats.functions.covered++;
          stats.covered.functions++;
        }
      }
    }

    fileStats.percentages = {
      statements: fileStats.statements.total > 0
        ? (fileStats.statements.covered / fileStats.statements.total * 100).toFixed(2)
        : 100,
      branches: fileStats.branches.total > 0
        ? (fileStats.branches.covered / fileStats.branches.total * 100).toFixed(2)
        : 100,
      functions: fileStats.functions.total > 0
        ? (fileStats.functions.covered / fileStats.functions.total * 100).toFixed(2)
        : 100,
      lines: fileStats.lines.total > 0
        ? (fileStats.lines.covered / fileStats.lines.total * 100).toFixed(2)
        : 100
    };

    stats.files.push(fileStats);
  }

  stats.overall = {
    statements: stats.total.statements > 0
      ? (stats.covered.statements / stats.total.statements * 100).toFixed(2)
      : 100,
    branches: stats.total.branches > 0
      ? (stats.covered.branches / stats.total.branches * 100).toFixed(2)
      : 100,
    functions: stats.total.functions > 0
      ? (stats.covered.functions / stats.total.functions * 100).toFixed(2)
      : 100,
    lines: stats.total.lines > 0
      ? (stats.covered.lines / stats.total.lines * 100).toFixed(2)
      : 100
  };

  return stats;
}

function getFilesNeedingTests(stats) {
  return stats.files
    .filter(file => {
      const avgCoverage = (
        parseFloat(file.percentages.statements) +
        parseFloat(file.percentages.branches) +
        parseFloat(file.percentages.functions) +
        parseFloat(file.percentages.lines)
      ) / 4;
      return avgCoverage < targetCoverage;
    })
    .sort((a, b) => {
      const avgA = (
        parseFloat(a.percentages.statements) +
        parseFloat(a.percentages.branches) +
        parseFloat(a.percentages.functions) +
        parseFloat(a.percentages.lines)
      ) / 4;
      const avgB = (
        parseFloat(b.percentages.statements) +
        parseFloat(b.percentages.branches) +
        parseFloat(b.percentages.functions) +
        parseFloat(b.percentages.lines)
      ) / 4;
      return avgA - avgB;
    });
}

function main() {
  console.log('📊 Analyzing test coverage...\n');

  const coverageData = readCoverageReport();
  const stats = analyzeCoverage(coverageData);

  if (stats.error) {
    console.error(`❌ ${stats.error}`);
    console.log(`💡 ${stats.suggestion}`);
    process.exit(1);
  }

  if (jsonOutput) {
    console.log(JSON.stringify(stats, null, 2));
    return;
  }

  console.log('📈 Overall Coverage:\n');
  console.log(`Statements: ${stats.overall.statements}% (${stats.covered.statements}/${stats.total.statements})`);
  console.log(`Branches:   ${stats.overall.branches}% (${stats.covered.branches}/${stats.total.branches})`);
  console.log(`Functions:  ${stats.overall.functions}% (${stats.covered.functions}/${stats.total.functions})`);
  console.log(`Lines:      ${stats.overall.lines}% (${stats.covered.lines}/${stats.total.lines})`);
  console.log(`\nTarget: ${targetCoverage}%\n`);

  const overallAvg = (
    parseFloat(stats.overall.statements) +
    parseFloat(stats.overall.branches) +
    parseFloat(stats.overall.functions) +
    parseFloat(stats.overall.lines)
  ) / 4;

  if (overallAvg >= targetCoverage) {
    console.log(`✅ Coverage target (${targetCoverage}%) met!`);
  } else {
    console.log(`⚠️  Coverage (${overallAvg.toFixed(2)}%) below target (${targetCoverage}%)`);

    const filesNeedingTests = getFilesNeedingTests(stats);
    if (filesNeedingTests.length > 0) {
      console.log(`\n📝 Files needing tests (top 10):\n`);
      filesNeedingTests.slice(0, 10).forEach((file, index) => {
        const avg = (
          parseFloat(file.percentages.statements) +
          parseFloat(file.percentages.branches) +
          parseFloat(file.percentages.functions) +
          parseFloat(file.percentages.lines)
        ) / 4;
        console.log(`${index + 1}. ${file.path}`);
        console.log(`   Coverage: ${avg.toFixed(2)}%`);
        console.log(`   Statements: ${file.percentages.statements}%, Branches: ${file.percentages.branches}%, Functions: ${file.percentages.functions}%, Lines: ${file.percentages.lines}%\n`);
      });
    }

    process.exit(1);
  }
}

main();
