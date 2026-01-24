#!/usr/bin/env node
/**
 * Bundle Size Analyzer for OS Frontend
 */

import { readFileSync, existsSync, statSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const args = process.argv.slice(2);
const jsonOutput = args.includes('--json');
const limitArg = args.find(arg => arg.startsWith('--limit='));
const sizeLimit = limitArg ? parseInt(limitArg.split('=')[1]) : null;

function getBundleSizes() {
  const sizes = {};

  // Check for Vite build output
  if (existsSync('dist')) {
    sizes.dist = calculateDirectorySize('dist');
    sizes.total = sizes.dist;
  }

  return sizes;
}

function calculateDirectorySize(dirPath) {
  let totalSize = 0;
  try {
    const { readdirSync, statSync } = require('fs');
    const { join } = require('path');

    const items = readdirSync(dirPath);
    for (const item of items) {
      const itemPath = join(dirPath, item);
      const stats = statSync(itemPath);
      if (stats.isDirectory()) {
        totalSize += calculateDirectorySize(itemPath);
      } else {
        totalSize += stats.size;
      }
    }
  } catch (error) {
    // Ignore errors
  }
  return totalSize;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function getRecommendations(sizes) {
  const recommendations = [];

  if (sizes.total > 500000) {
    recommendations.push({
      severity: 'high',
      message: 'Bundle size exceeds 500KB. Consider code splitting.',
      action: 'Implement route-based code splitting and lazy loading'
    });
  }

  if (sizes.total > 1000000) {
    recommendations.push({
      severity: 'critical',
      message: 'Bundle size exceeds 1MB. This will significantly impact performance.',
      action: 'Review dependencies and remove unused code. Consider tree-shaking.'
    });
  }

  return recommendations;
}

function main() {
  console.log('📦 Analyzing bundle sizes...\n');

  const sizes = getBundleSizes();

  if (Object.keys(sizes).length === 0) {
    console.log('⚠️  No build output found. Run "npm run build" first.');
    process.exit(1);
  }

  if (jsonOutput) {
    console.log(JSON.stringify({ sizes, recommendations: getRecommendations(sizes) }, null, 2));
    return;
  }

  console.log('📊 Bundle Size Report\n');
  console.log('Asset                        Size');
  console.log('─'.repeat(50));

  for (const [key, size] of Object.entries(sizes)) {
    const formattedSize = formatBytes(size);
    const padding = ' '.repeat(30 - key.length);
    console.log(`${key}${padding}${formattedSize}`);
  }

  console.log('\n');

  const recommendations = getRecommendations(sizes);
  if (recommendations.length > 0) {
    console.log('💡 Optimization Recommendations:\n');
    recommendations.forEach((rec) => {
      const icon = rec.severity === 'critical' ? '🔴' : rec.severity === 'high' ? '🟠' : '🟡';
      console.log(`${icon} ${rec.message}`);
      console.log(`   Action: ${rec.action}\n`);
    });
  } else {
    console.log('✅ Bundle sizes are within acceptable limits!\n');
  }

  if (sizeLimit && sizes.total > sizeLimit) {
    console.error(`❌ Bundle size (${formatBytes(sizes.total)}) exceeds limit (${formatBytes(sizeLimit)})`);
    process.exit(1);
  }

  console.log(`\nTotal bundle size: ${formatBytes(sizes.total)}`);
}

main();
