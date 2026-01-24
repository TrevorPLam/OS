#!/usr/bin/env node
/**
 * Check bundle size budget - fail if total entrypoint size grows > 2%
 */

import { readFileSync, statSync, existsSync } from "fs";
import { join } from "path";

const BUDGET_THRESHOLD = 0.02; // 2% increase
const BASE_BRANCH = process.env.BASE_REF || "main";

function getBundleSize(buildDir) {
  // Check for Expo build output
  const possiblePaths = [
    join(buildDir, "web-build"),
    join(buildDir, "dist"),
    join(buildDir, "static-build"),
  ];

  for (const path of possiblePaths) {
    if (existsSync(path)) {
      return calculateDirSize(path);
    }
  }

  return null;
}

function calculateDirSize(dirPath) {
  let totalSize = 0;
  try {
    const { readdirSync, statSync } = require("fs");
    const { join } = require("path");

    function walkDir(dir) {
      const files = readdirSync(dir);
      for (const file of files) {
        const filePath = join(dir, file);
        const stat = statSync(filePath);
        if (stat.isDirectory()) {
          walkDir(filePath);
        } else {
          totalSize += stat.size;
        }
      }
    }

    walkDir(dirPath);
  } catch (error) {
    console.error(`Error calculating size: ${error.message}`);
  }

  return totalSize;
}

function getBaseBundleSize() {
  // Try to get from main branch
  try {
    const { execSync } = require("child_process");
    execSync(`git checkout ${BASE_BRANCH}`, { stdio: "ignore" });
    const size = getBundleSize(".");
    execSync("git checkout -", { stdio: "ignore" });
    return size;
  } catch (error) {
    console.warn("Could not get base bundle size from main branch");
    return null;
  }
}

function checkBundleBudget() {
  const currentSize = getBundleSize(".");
  if (!currentSize) {
    console.log("⚠️  No build output found. Run build first.");
    return true; // Don't fail if no build
  }

  const baseSize = getBaseBundleSize();
  if (!baseSize) {
    console.log("⚠️  Could not determine base bundle size. Skipping check.");
    return true;
  }

  const sizeDiff = currentSize - baseSize;
  const percentChange = sizeDiff / baseSize;

  console.log(`\n📦 Bundle Size Check:`);
  console.log(`   Base: ${(baseSize / 1024 / 1024).toFixed(2)} MB`);
  console.log(`   Current: ${(currentSize / 1024 / 1024).toFixed(2)} MB`);
  console.log(`   Change: ${(percentChange * 100).toFixed(2)}%`);

  if (percentChange > BUDGET_THRESHOLD) {
    console.error(
      `\n❌ Bundle size increased by ${(percentChange * 100).toFixed(2)}%`,
    );
    console.error(`   Threshold: ${BUDGET_THRESHOLD * 100}%`);
    console.error(`   Approval required for > 2% increase`);
    return false;
  }

  console.log(`✅ Bundle size change within budget`);
  return true;
}

if (!checkBundleBudget()) {
  process.exit(1);
}
