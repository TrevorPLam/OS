#!/usr/bin/env node

/**
 * Exception Expiry Checker
 *
 * Validates docs/governance/exceptions.yml for expired exceptions.
 * Fails (non-zero exit) if any active exception is past its expires_date.
 *
 * Usage:
 *   node scripts/tools/check-exceptions.mjs
 *
 * Exit codes:
 *   0 - All active exceptions are valid (not expired)
 *   1 - One or more active exceptions have expired
 *   2 - Error reading or parsing exceptions file
 */

import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { parse as parseYaml } from "yaml";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const REPO_ROOT = join(__dirname, "../..");
// Note: Exceptions are now handled via HITL system (/.repo/hitl/HITL-XXXX.md)
// This script checks the archived exceptions.yml for historical reference
const EXCEPTIONS_PATH = join(
  REPO_ROOT,
  "docs/archive/governance/exceptions.yml",
);

function checkExceptions() {
  console.log("🔍 Exception Expiry Checker");
  console.log("===========================\n");

  // Check if exceptions file exists
  if (!existsSync(EXCEPTIONS_PATH)) {
    console.log("✅ No exceptions file found - this is fine!");
    console.log(`   Expected at: ${EXCEPTIONS_PATH}`);
    return 0;
  }

  // Read and parse exceptions file
  console.log(`📖 Reading exceptions from: ${EXCEPTIONS_PATH}`);
  let exceptionsData;

  try {
    const content = readFileSync(EXCEPTIONS_PATH, "utf-8");
    exceptionsData = parseYaml(content);
  } catch (error) {
    console.error(`❌ Error parsing exceptions.yml: ${error.message}`);
    return 2;
  }

  if (!exceptionsData || !exceptionsData.exceptions) {
    console.log("✅ No exceptions defined in file");
    return 0;
  }

  const exceptions = exceptionsData.exceptions;
  console.log(`   Found ${exceptions.length} exception(s)\n`);

  const now = new Date();
  const expired = [];
  const active = [];
  const closed = [];

  // Check each exception
  for (const exception of exceptions) {
    const { id, title, status, expires_date, owner, policy_violated } =
      exception;

    if (status === "closed") {
      closed.push(exception);
      continue;
    }

    if (status !== "active") {
      console.warn(`⚠️  Exception ${id} has unknown status: ${status}`);
      continue;
    }

    active.push(exception);

    // Parse expiry date
    const expiryDate = new Date(expires_date);

    if (isNaN(expiryDate.getTime())) {
      console.error(
        `❌ Exception ${id} has invalid expires_date: ${expires_date}`,
      );
      expired.push(exception);
      continue;
    }

    // Check if expired
    if (expiryDate < now) {
      console.error(`❌ EXPIRED: ${id}`);
      console.error(`   Title: ${title}`);
      console.error(`   Expired: ${expires_date}`);
      console.error(`   Owner: ${owner}`);
      console.error(`   Policy: ${policy_violated}`);
      console.error("");
      expired.push(exception);
    } else {
      const daysRemaining = Math.ceil(
        (expiryDate - now) / (1000 * 60 * 60 * 24),
      );
      console.log(`✅ Active: ${id}`);
      console.log(`   Title: ${title}`);
      console.log(
        `   Expires: ${expires_date} (${daysRemaining} days remaining)`,
      );
      console.log(`   Owner: ${owner}`);
      console.log("");
    }
  }

  // Summary
  console.log("📊 Summary:");
  console.log(`   Total exceptions: ${exceptions.length}`);
  console.log(`   Active: ${active.length}`);
  console.log(`   Closed: ${closed.length}`);
  console.log(`   Expired: ${expired.length}`);

  if (expired.length > 0) {
    console.error("\n❌ FAILED: One or more exceptions have expired!");
    console.error("\n📝 Action required:");
    console.error("   1. Review expired exceptions");
    console.error("   2. Either:");
    console.error(
      "      a) Fix the underlying issue and close the exception (set status: closed)",
    );
    console.error(
      "      b) Create a new exception with justification (max 90 days)",
    );
    console.error(
      "      c) Update the policy if exception should be permanent",
    );
    console.error("   3. Update docs/governance/exceptions.yml");
    console.error("   4. Commit and push changes");
    return 1;
  }

  console.log("\n✅ All active exceptions are valid (not expired)");
  return 0;
}

// Run checker
const exitCode = checkExceptions();
process.exit(exitCode);
