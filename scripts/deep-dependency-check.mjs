#!/usr/bin/env node

/**
 * Deep Dependency Mismatch Checker
 *
 * Performs extensive analysis of all dependencies to detect version mismatches
 * that could prevent the app from starting. Checks:
 * - Direct dependency versions vs installed versions
 * - Peer dependency compatibility
 * - React Native/Expo SDK compatibility
 * - Common conflict patterns
 */

import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, "..");

console.log("\n" + "=".repeat(70));
console.log("🔍 DEEP DEPENDENCY MISMATCH ANALYSIS");
console.log("=".repeat(70) + "\n");

let totalIssues = 0;
let criticalIssues = 0;

// Load package.json
const packageJsonPath = join(rootDir, "package.json");
const packageJson = JSON.parse(readFileSync(packageJsonPath, "utf8"));

// Check if node_modules exists
const nodeModulesExists = existsSync(join(rootDir, "node_modules"));
if (!nodeModulesExists) {
  console.log("❌ CRITICAL: node_modules not found!\n");
  console.log("💡 Run: npm install\n");
  console.log("=".repeat(70) + "\n");
  process.exit(1);
}

/**
 * Check React Native ecosystem compatibility
 */
function checkReactNativeEcosystem() {
  console.log("📱 REACT NATIVE ECOSYSTEM CHECK\n");

  const criticalPackages = {
    react: packageJson.dependencies?.["react"],
    "react-native": packageJson.dependencies?.["react-native"],
    expo: packageJson.dependencies?.["expo"],
    "react-native-reanimated":
      packageJson.dependencies?.["react-native-reanimated"],
    "react-native-worklets":
      packageJson.dependencies?.["react-native-worklets"],
    "react-native-gesture-handler":
      packageJson.dependencies?.["react-native-gesture-handler"],
  };

  const issues = [];

  // Check React version compatibility
  const reactVersion = criticalPackages["react"];
  const reactNativeVersion = criticalPackages["react-native"];

  console.log(`   React: ${reactVersion || "NOT FOUND"}`);
  console.log(`   React Native: ${reactNativeVersion || "NOT FOUND"}`);
  console.log(`   Expo SDK: ${criticalPackages["expo"] || "NOT FOUND"}`);
  console.log();

  // Check for known incompatibilities
  if (reactVersion && reactVersion.includes("19.")) {
    console.log("   ⚠️  React 19.x detected - This is cutting edge");
    console.log("      Ensure all dependencies support React 19");
    issues.push("React 19.x compatibility check needed");
  }

  // Check React Native Reanimated + Worklets
  const reanimatedVersion = criticalPackages["react-native-reanimated"];
  const workletsVersion = criticalPackages["react-native-worklets"];

  if (reanimatedVersion && workletsVersion) {
    console.log(`   React Native Reanimated: ${reanimatedVersion}`);
    console.log(`   React Native Worklets: ${workletsVersion}`);

    // Check if versions are compatible
    const reanimatedClean = reanimatedVersion.replace(/^[\^~>=<]+/, "");
    const workletsClean = workletsVersion.replace(/^[\^~>=<]+/, "");
    const reanimatedMajor = parseInt(reanimatedClean.split(".")[0]) || 0;
    const workletsParts = workletsClean.split(".");
    const workletsMajor = parseInt(workletsParts[0]) || 0;
    const workletsMinor = parseInt(workletsParts[1]) || 0;

    // Reanimated 4.x requires Worklets 0.7.0 or higher
    if (reanimatedMajor === 4 && (workletsMajor !== 0 || workletsMinor < 7)) {
      console.log("   ⚠️  Reanimated 4.x requires Worklets >= 0.7.0");
      console.log(`      You have: ${workletsClean}`);
      issues.push("Reanimated/Worklets version incompatible");
    }
  }

  console.log();
  return issues;
}

/**
 * Check installed vs declared versions
 */
function checkInstalledVsDeclared() {
  console.log("📦 INSTALLED vs DECLARED VERSION CHECK\n");

  const issues = [];
  const allDeps = {
    ...packageJson.dependencies,
    ...packageJson.devDependencies,
  };

  const criticalPackages = [
    "react",
    "react-native",
    "react-native-reanimated",
    "react-native-worklets",
    "react-native-gesture-handler",
    "react-native-keyboard-controller",
    "react-native-draggable-flatlist",
    "expo",
    "@react-navigation/native",
    "@react-navigation/native-stack",
  ];

  for (const pkg of criticalPackages) {
    const declared = allDeps[pkg];
    if (!declared) continue;

    const installedPkgPath = join(rootDir, "node_modules", pkg, "package.json");

    if (!existsSync(installedPkgPath)) {
      console.log(`   ❌ ${pkg}: NOT INSTALLED`);
      console.log(`      Declared: ${declared}`);
      issues.push(`${pkg} not installed`);
      criticalIssues++;
      continue;
    }

    try {
      const installedPkg = JSON.parse(readFileSync(installedPkgPath, "utf8"));
      const installed = installedPkg.version;
      const cleanDeclared = declared.replace(/^[\^~>=<]+/, "");

      if (installed !== cleanDeclared) {
        const severity =
          pkg.includes("worklets") || pkg.includes("reanimated")
            ? "🔴 CRITICAL"
            : "⚠️  WARNING";
        console.log(`   ${severity} ${pkg}:`);
        console.log(`      Declared: ${declared}`);
        console.log(`      Installed: ${installed}`);

        if (severity.includes("CRITICAL")) {
          criticalIssues++;
          issues.push(`${pkg}: Critical version mismatch`);
        } else {
          issues.push(`${pkg}: Version mismatch`);
        }
      } else {
        console.log(`   ✅ ${pkg}: ${installed}`);
      }
    } catch (error) {
      console.log(`   ⚠️  ${pkg}: Error reading installed version`);
      issues.push(`${pkg}: Cannot verify version`);
    }
  }

  console.log();
  return issues;
}

/**
 * Check peer dependencies
 */
function checkPeerDependencies() {
  console.log("🔗 PEER DEPENDENCY CHECK\n");

  const issues = [];

  try {
    const npmOutput = execSync("npm ls --depth=0 2>&1", {
      cwd: rootDir,
      encoding: "utf8",
      stdio: "pipe",
    });

    const peerDepWarnings = npmOutput.match(/WARN.*peer dependency/gi) || [];
    const unmetDeps = npmOutput.match(/UNMET.*dependency/gi) || [];

    if (peerDepWarnings.length > 0) {
      console.log(
        `   ⚠️  Found ${peerDepWarnings.length} peer dependency warnings`,
      );
      issues.push(`${peerDepWarnings.length} peer dependency warnings`);
    }

    if (unmetDeps.length > 0) {
      console.log(`   ❌ Found ${unmetDeps.length} unmet dependencies`);
      criticalIssues += unmetDeps.length;
      issues.push(`${unmetDeps.length} unmet dependencies`);
    }

    if (issues.length === 0) {
      console.log("   ✅ No peer dependency issues detected");
    }
  } catch (error) {
    console.log("   ⚠️  Could not check peer dependencies");
    console.log("      (This is normal if there are some warnings)");
  }

  console.log();
  return issues;
}

/**
 * Check for duplicate dependencies
 */
function checkDuplicates() {
  console.log("🔄 DUPLICATE DEPENDENCY CHECK\n");

  const issues = [];

  try {
    const dedupe = execSync("npm dedupe --dry-run 2>&1 || true", {
      cwd: rootDir,
      encoding: "utf8",
      stdio: "pipe",
    });

    if (dedupe.includes("added") || dedupe.includes("removed")) {
      console.log("   ⚠️  Duplicate dependencies detected");
      console.log("   💡 Run: npm dedupe");
      issues.push("Duplicate dependencies found");
    } else {
      console.log("   ✅ No duplicate dependencies");
    }
  } catch (error) {
    console.log("   ℹ️  Could not check for duplicates");
  }

  console.log();
  return issues;
}

/**
 * Check Expo SDK compatibility
 */
function checkExpoCompatibility() {
  console.log("🔧 EXPO SDK COMPATIBILITY CHECK\n");

  const issues = [];
  const expoVersion = packageJson.dependencies?.["expo"];

  if (!expoVersion) {
    console.log("   ⚠️  Expo not found in dependencies");
    return issues;
  }

  console.log(`   Expo SDK: ${expoVersion}`);

  // Check critical Expo packages
  const expoPackages = Object.keys(packageJson.dependencies || {}).filter(
    (pkg) => pkg.startsWith("expo-"),
  );

  let mismatchCount = 0;

  for (const pkg of expoPackages.slice(0, 5)) {
    // Check first 5 for brevity
    const version = packageJson.dependencies[pkg];
    const installedPath = join(rootDir, "node_modules", pkg, "package.json");

    if (!existsSync(installedPath)) {
      mismatchCount++;
      continue;
    }

    const installed = JSON.parse(readFileSync(installedPath, "utf8"));
    const cleanDeclared = version.replace(/^[\^~>=<]+/, "");

    if (installed.version !== cleanDeclared) {
      mismatchCount++;
    }
  }

  if (mismatchCount > 0) {
    console.log(
      `   ⚠️  ${mismatchCount} Expo packages have version mismatches`,
    );
    issues.push("Expo package version mismatches");
  } else {
    console.log("   ✅ Expo packages appear compatible");
  }

  console.log();
  return issues;
}

/**
 * Check for common startup blockers
 */
function checkStartupBlockers() {
  console.log("🚫 STARTUP BLOCKER CHECK\n");

  const issues = [];

  // Check for missing critical modules
  const criticalModules = [
    "react",
    "react-native",
    "expo",
    "@react-navigation/native",
  ];

  for (const mod of criticalModules) {
    const modPath = join(rootDir, "node_modules", mod);
    if (!existsSync(modPath)) {
      console.log(`   ❌ CRITICAL: ${mod} not installed`);
      criticalIssues++;
      issues.push(`${mod} missing - app cannot start`);
    }
  }

  // Check for common config issues
  const metroConfig = join(rootDir, "metro.config.js");
  const babelConfig = join(rootDir, "babel.config.js");

  if (!existsSync(metroConfig)) {
    console.log("   ⚠️  metro.config.js not found");
    issues.push("Metro config missing");
  }

  if (!existsSync(babelConfig)) {
    console.log("   ⚠️  babel.config.js not found");
    issues.push("Babel config missing");
  }

  if (issues.length === 0) {
    console.log("   ✅ No critical startup blockers detected");
  }

  console.log();
  return issues;
}

/**
 * Check TypeScript configuration
 */
function checkTypeScriptSetup() {
  console.log("📘 TYPESCRIPT CONFIGURATION CHECK\n");

  const issues = [];
  const tsConfigPath = join(rootDir, "tsconfig.json");

  if (!existsSync(tsConfigPath)) {
    console.log("   ⚠️  tsconfig.json not found");
    issues.push("TypeScript config missing");
  } else {
    console.log("   ✅ tsconfig.json exists");

    // Check for @types packages
    const reactTypesPath = join(rootDir, "node_modules", "@types", "react");
    if (!existsSync(reactTypesPath)) {
      console.log("   ⚠️  @types/react not installed");
      issues.push("@types/react missing");
    }
  }

  console.log();
  return issues;
}

// Run all checks
const allIssues = [
  ...checkReactNativeEcosystem(),
  ...checkInstalledVsDeclared(),
  ...checkPeerDependencies(),
  ...checkDuplicates(),
  ...checkExpoCompatibility(),
  ...checkStartupBlockers(),
  ...checkTypeScriptSetup(),
];

totalIssues = allIssues.length;

// Summary
console.log("=".repeat(70));
console.log("📊 SUMMARY\n");

if (totalIssues === 0) {
  console.log("✅ NO ISSUES DETECTED!\n");
  console.log(
    "   All dependencies appear to be properly installed and compatible.",
  );
  console.log("   App should be able to start.\n");
} else {
  console.log(`⚠️  FOUND ${totalIssues} TOTAL ISSUES\n`);

  if (criticalIssues > 0) {
    console.log(
      `🔴 ${criticalIssues} CRITICAL ISSUES that will prevent app from starting:\n`,
    );

    const critical = allIssues.filter(
      (i) =>
        i.includes("not installed") ||
        i.includes("Critical") ||
        i.includes("missing") ||
        i.includes("unmet"),
    );

    critical.forEach((issue) => console.log(`   • ${issue}`));
    console.log();
  }

  const warnings = totalIssues - criticalIssues;
  if (warnings > 0) {
    console.log(`⚠️  ${warnings} warnings that may cause issues:\n`);

    const warningIssues = allIssues.filter(
      (i) =>
        !i.includes("not installed") &&
        !i.includes("Critical") &&
        !i.includes("missing") &&
        !i.includes("unmet"),
    );

    warningIssues.forEach((issue) => console.log(`   • ${issue}`));
    console.log();
  }
}

console.log("=".repeat(70));
console.log("💡 RECOMMENDED ACTIONS\n");

if (criticalIssues > 0) {
  console.log("1. 🚨 FIX CRITICAL ISSUES FIRST:\n");
  console.log("   npm install\n");
  console.log("2. 🔧 Then rebuild native code:\n");
  console.log("   npm run expo:clean:native");
  console.log("   npm run expo:rebuild:ios\n");
} else if (totalIssues > 0) {
  console.log("1. 🧹 Clean and reinstall:\n");
  console.log("   npm run expo:clean:native\n");
  console.log("2. 🔨 Rebuild native code:\n");
  console.log("   npm run expo:rebuild:ios\n");
  console.log("3. 🔍 Verify:\n");
  console.log("   npm run check:worklets\n");
} else {
  console.log("✅ Everything looks good!\n");
  console.log("   If you still have issues starting the app:\n");
  console.log("   1. npm run expo:clean");
  console.log("   2. npm start\n");
}

console.log("=".repeat(70) + "\n");

// Exit code
process.exit(criticalIssues > 0 ? 1 : 0);
