#!/usr/bin/env node
/**
 * Shared Infrastructure for Ultra High-Leverage Automations
 * Provides common utilities, AI integration, and learning capabilities
 */

import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

/**
 * AI/LLM Integration
 * Supports multiple LLM providers (OpenAI, Anthropic, etc.)
 */
export class AIEngine {
  constructor(config = {}) {
    this.provider = config.provider || process.env.AI_PROVIDER || "openai";
    this.apiKey = config.apiKey || process.env.OPENAI_API_KEY || process.env.ANTHROPIC_API_KEY;
    this.model = config.model || process.env.AI_MODEL || "gpt-4";
    this.enabled = config.enabled !== false && !!this.apiKey;
  }

  async generate(prompt, options = {}) {
    if (!this.enabled) {
      console.warn("AI engine not enabled. Set AI_PROVIDER and API key to enable.");
      return null;
    }

    // Placeholder for actual LLM integration
    // In production, this would call OpenAI, Anthropic, etc.
    console.log(`[AI] Generating response for: ${prompt.substring(0, 50)}...`);
    
    // For now, return a structured response
    return {
      content: `AI-generated response for: ${prompt.substring(0, 50)}`,
      model: this.model,
      provider: this.provider,
    };
  }

  async analyzeCode(code, context = {}) {
    const prompt = `Analyze this code and provide insights:\n\n${code}\n\nContext: ${JSON.stringify(context)}`;
    return this.generate(prompt);
  }

  async suggestRefactoring(code, goal) {
    const prompt = `Suggest refactoring for this code to achieve: ${goal}\n\nCode:\n${code}`;
    return this.generate(prompt);
  }

  async explainCode(code) {
    const prompt = `Explain what this code does:\n\n${code}`;
    return this.generate(prompt);
  }
}

/**
 * Learning System - Tracks outcomes and improves over time
 */
export class LearningSystem {
  constructor(dataPath = path.join(REPO_ROOT, ".repo/automation/learning")) {
    this.dataPath = dataPath;
    this.ensureDataDir();
  }

  ensureDataDir() {
    if (!fs.existsSync(this.dataPath)) {
      fs.mkdirSync(this.dataPath, { recursive: true });
    }
  }

  recordOutcome(automationId, action, outcome, metadata = {}) {
    const record = {
      timestamp: new Date().toISOString(),
      automationId,
      action,
      outcome, // 'success', 'failure', 'partial'
      metadata,
    };

    const filePath = path.join(this.dataPath, `${automationId}.jsonl`);
    fs.appendFileSync(filePath, JSON.stringify(record) + "\n");
  }

  getOutcomes(automationId, limit = 100) {
    const filePath = path.join(this.dataPath, `${automationId}.jsonl`);
    if (!fs.existsSync(filePath)) return [];

    const lines = fs.readFileSync(filePath, "utf8").trim().split("\n");
    return lines
      .filter((line) => line.trim())
      .map((line) => JSON.parse(line))
      .slice(-limit);
  }

  getSuccessRate(automationId) {
    const outcomes = this.getOutcomes(automationId);
    if (outcomes.length === 0) return 0;

    const successes = outcomes.filter((o) => o.outcome === "success").length;
    return successes / outcomes.length;
  }
}

/**
 * Pattern Learning - Learns from codebase patterns
 */
export class PatternLearner {
  constructor() {
    this.patterns = new Map();
  }

  learnPattern(patternId, example, metadata = {}) {
    if (!this.patterns.has(patternId)) {
      this.patterns.set(patternId, []);
    }
    this.patterns.get(patternId).push({ example, metadata, timestamp: Date.now() });
  }

  getPatterns(patternId) {
    return this.patterns.get(patternId) || [];
  }

  findSimilarPatterns(target, patternId) {
    const patterns = this.getPatterns(patternId);
    // Simple similarity check - in production, use more sophisticated algorithms
    return patterns.filter((p) => 
      JSON.stringify(p.example).includes(JSON.stringify(target).substring(0, 50))
    );
  }
}

/**
 * Code Analysis Utilities
 */
export class CodeAnalyzer {
  static getComplexity(filePath) {
    const content = fs.readFileSync(filePath, "utf8");
    // Simple complexity metrics
    const lines = content.split("\n").length;
    const functions = (content.match(/function\s+\w+|const\s+\w+\s*=\s*\(/g) || []).length;
    const conditionals = (content.match(/if\s*\(|switch\s*\(|case\s+/g) || []).length;
    
    return {
      lines,
      functions,
      conditionals,
      complexity: lines + functions * 2 + conditionals * 3,
    };
  }

  static findCodeSmells(filePath) {
    const content = fs.readFileSync(filePath, "utf8");
    const smells = [];

    // Long function detection
    const functions = content.match(/function\s+\w+[^{]*\{[\s\S]{500,}?\}/g) || [];
    if (functions.length > 0) {
      smells.push({ type: "long_function", count: functions.length });
    }

    // Deep nesting
    const deepNesting = content.match(/\{[^{}]*\{[^{}]*\{[^{}]*\{/g) || [];
    if (deepNesting.length > 0) {
      smells.push({ type: "deep_nesting", count: deepNesting.length });
    }

    // Duplicate code (simple check)
    const duplicateLines = this.findDuplicateLines(content);
    if (duplicateLines.length > 0) {
      smells.push({ type: "duplicate_code", count: duplicateLines.length });
    }

    return smells;
  }

  static findDuplicateLines(content) {
    const lines = content.split("\n").map((l) => l.trim()).filter((l) => l.length > 20);
    const seen = new Map();
    const duplicates = [];

    lines.forEach((line, index) => {
      if (seen.has(line)) {
        duplicates.push({ line, first: seen.get(line), duplicate: index });
      } else {
        seen.set(line, index);
      }
    });

    return duplicates;
  }
}

/**
 * Git Utilities
 */
export class GitUtils {
  static getChangedFiles(commitRange = "HEAD~1..HEAD") {
    try {
      const output = execSync(`git diff --name-only ${commitRange}`, {
        cwd: REPO_ROOT,
        encoding: "utf8",
      });
      return output.trim().split("\n").filter((f) => f);
    } catch (error) {
      return [];
    }
  }

  static getFileHistory(filePath, limit = 10) {
    try {
      const output = execSync(`git log --oneline -${limit} -- ${filePath}`, {
        cwd: REPO_ROOT,
        encoding: "utf8",
      });
      return output.trim().split("\n").filter((l) => l);
    } catch (error) {
      return [];
    }
  }

  static getBugPatterns() {
    // Analyze git history for bug patterns
    try {
      const output = execSync('git log --grep="fix" --grep="bug" --oneline', {
        cwd: REPO_ROOT,
        encoding: "utf8",
      });
      return output.trim().split("\n").filter((l) => l);
    } catch (error) {
      return [];
    }
  }
}

/**
 * Safety System - Prevents dangerous operations
 */
export class SafetySystem {
  static async checkSafety(operation, context = {}) {
    const checks = {
      destructive: operation.includes("delete") || operation.includes("remove"),
      modifiesProduction: context.target?.includes("production"),
      requiresApproval: context.requiresApproval || false,
    };

    return {
      safe: !checks.destructive && !checks.modifiesProduction,
      requiresApproval: checks.requiresApproval || checks.destructive,
      warnings: Object.entries(checks)
        .filter(([_, value]) => value)
        .map(([key]) => key),
    };
  }

  static async requestApproval(operation, context = {}) {
    // In production, this would integrate with approval systems
    console.log(`[SAFETY] Approval required for: ${operation}`);
    console.log(`[SAFETY] Context:`, context);
    return false; // Default to requiring manual approval
  }
}

export default {
  AIEngine,
  LearningSystem,
  PatternLearner,
  CodeAnalyzer,
  GitUtils,
  SafetySystem,
  REPO_ROOT,
};
