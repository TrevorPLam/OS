#!/usr/bin/env node
// Auto-Generate Test Cases from Code
// Usage: node scripts/intelligent/auto-generate-test-cases.mjs [--file path/to/file.ts] [--output-dir]

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const TARGET_FILE = process.argv.find((arg) => arg.startsWith("--file="))?.split("=")[1];
const OUTPUT_DIR = process.argv.find((arg) => arg.startsWith("--output-dir="))?.split("=")[1];
const DRY_RUN = process.argv.includes("--dry-run");

function parseFunctionSignatures(content) {
  const functions = [];

  // Match function declarations
  const functionPatterns = [
    /(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)/g,
    /(?:export\s+)?const\s+(\w+)\s*[:=]\s*(?:async\s+)?\(([^)]*)\)\s*=>/g,
    /(?:export\s+)?const\s+(\w+)\s*[:=]\s*(?:async\s+)?function\s*\(([^)]*)\)/g,
  ];

  for (const pattern of functionPatterns) {
    let match;
    while ((match = pattern.exec(content)) !== null) {
      const name = match[1];
      const params = match[2]
        .split(",")
        .map((p) => p.trim())
        .filter(Boolean)
        .map((p) => {
          const paramMatch = p.match(/(\w+)(?::\s*(.+))?/);
          return {
            name: paramMatch?.[1] || p,
            type: paramMatch?.[2] || "any",
          };
        });

      functions.push({ name, params, async: content.includes("async") });
    }
  }

  return functions;
}

function parseComponentSignatures(content) {
  const components = [];

  // Match React components
  const componentPatterns = [
    /(?:export\s+)?(?:const|function)\s+(\w+)\s*[:=]\s*(?:\(([^)]*)\)\s*=>|function\s*\(([^)]*)\))/g,
  ];

  for (const pattern of componentPatterns) {
    let match;
    while ((match = pattern.exec(content)) !== null) {
      const name = match[1];
      const props = (match[2] || match[3] || "")
        .split(",")
        .map((p) => p.trim())
        .filter(Boolean)
        .map((p) => {
          const propMatch = p.match(/(\w+)(?::\s*(.+))?/);
          return {
            name: propMatch?.[1] || p,
            type: propMatch?.[2] || "any",
          };
        });

      if (name[0] === name[0].toUpperCase()) {
        // React component (PascalCase)
        components.push({ name, props });
      }
    }
  }

  return components;
}

function generateTestCases(functions, components, filePath) {
  const relativePath = path.relative(REPO_ROOT, filePath);
  const testCases = [];

  // Generate test cases for functions
  for (const func of functions) {
    const testCase = {
      name: `should ${func.name} work correctly`,
      function: func.name,
      type: "function",
      test: generateFunctionTest(func),
    };
    testCases.push(testCase);
  }

  // Generate test cases for components
  for (const component of components) {
    const testCase = {
      name: `should render ${component.name}`,
      component: component.name,
      type: "component",
      test: generateComponentTest(component),
    };
    testCases.push(testCase);
  }

  return testCases;
}

function generateFunctionTest(func) {
  const params = func.params.map((p) => {
    if (p.type.includes("string")) return `"test"`;
    if (p.type.includes("number")) return `1`;
    if (p.type.includes("boolean")) return `true`;
    if (p.type.includes("[]") || p.type.includes("Array")) return `[]`;
    if (p.type.includes("{}") || p.type.includes("object")) return `{}`;
    return `mock${p.name.charAt(0).toUpperCase() + p.name.slice(1)}`;
  });

  return `describe('${func.name}', () => {
  it('should work correctly', ${func.async ? "async " : ""}() => {
    ${func.async ? "const result = await " : "const result = "}${func.name}(${params.join(", ")});
    expect(result).toBeDefined();
  });

  it('should handle edge cases', ${func.async ? "async " : ""}() => {
    // TODO: Add edge case tests
  });

  it('should handle errors', ${func.async ? "async " : ""}() => {
    // TODO: Add error handling tests
  });
});`;
}

function generateComponentTest(component) {
  const props = component.props.map((p) => `${p.name}={mock${p.name.charAt(0).toUpperCase() + p.name.slice(1)}}`).join(" ");

  return `import { render, screen } from '@testing-library/react-native';
import { ${component.name} } from './${path.basename(filePath, path.extname(filePath))}';

describe('${component.name}', () => {
  it('should render correctly', () => {
    render(<${component.name} ${props} />);
    expect(screen.getByTestId('${component.name.toLowerCase()}')).toBeDefined();
  });

  it('should handle props correctly', () => {
    // TODO: Add prop testing
  });

  it('should handle user interactions', () => {
    // TODO: Add interaction tests
  });
});`;
}

function findExistingTestFile(filePath) {
  const dir = path.dirname(filePath);
  const basename = path.basename(filePath, path.extname(filePath));
  const testExtensions = [".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx"];

  for (const ext of testExtensions) {
    const testFile = path.join(dir, `${basename}${ext}`);
    if (fs.existsSync(testFile)) {
      return testFile;
    }
  }

  // Check __tests__ directory
  const testDir = path.join(dir, "__tests__");
  if (fs.existsSync(testDir)) {
    for (const ext of testExtensions) {
      const testFile = path.join(testDir, `${basename}${ext}`);
      if (fs.existsSync(testFile)) {
        return testFile;
      }
    }
  }

  return null;
}

function generateTestFile(filePath, testCases) {
  const dir = path.dirname(filePath);
  const basename = path.basename(filePath, path.extname(filePath));
  const ext = path.extname(filePath);
  const isTSX = ext === ".tsx" || filePath.endsWith(".tsx");

  // Determine test file location
  const testDir = OUTPUT_DIR || (filePath.includes("__tests__") ? dir : path.join(dir, "__tests__"));
  const testExt = isTSX ? ".test.tsx" : ".test.ts";
  const testFilePath = path.join(testDir, `${basename}${testExt}`);

  // Check if test file exists
  const existingTest = findExistingTestFile(filePath);
  if (existingTest && !DRY_RUN) {
    console.log(`⚠️  Test file already exists: ${existingTest}`);
    return { testFilePath: existingTest, created: false };
  }

  // Generate test file content
  const imports = `import { ${testCases.map((tc) => (tc.type === "function" ? tc.function : tc.component)).join(", ")} } from '../${path.relative(testDir, filePath).replace(/\\/g, "/")}';`;

  const testContent = `import { describe, it, expect } from '@jest/globals';
${testCases.some((tc) => tc.type === "component") ? "import { render, screen } from '@testing-library/react-native';" : ""}
${imports}

${testCases.map((tc) => tc.test).join("\n\n")}
`;

  return { testFilePath, testContent, created: true };
}

function main() {
  console.log("🧪 Auto-Generating Test Cases\n");

  if (!TARGET_FILE) {
    console.error("❌ Target file required. Use --file=path/to/file.ts");
    process.exit(1);
  }

  const filePath = path.resolve(REPO_ROOT, TARGET_FILE);
  if (!fs.existsSync(filePath)) {
    console.error(`❌ File not found: ${filePath}`);
    process.exit(1);
  }

  console.log(`📄 Analyzing: ${TARGET_FILE}\n`);

  const content = fs.readFileSync(filePath, "utf8");
  const functions = parseFunctionSignatures(content);
  const components = parseComponentSignatures(content);

  console.log(`   Functions: ${functions.length}`);
  console.log(`   Components: ${components.length}\n`);

  if (functions.length === 0 && components.length === 0) {
    console.log("⚠️  No functions or components found to test");
    return;
  }

  const testCases = generateTestCases(functions, components, filePath);
  const { testFilePath, testContent, created } = generateTestFile(filePath, testCases);

  if (DRY_RUN) {
    console.log("[DRY RUN] Would create test file:");
    console.log(`   ${testFilePath}\n`);
    console.log(testContent);
    return;
  }

  if (!created) {
    return;
  }

  // Ensure test directory exists
  const testDir = path.dirname(testFilePath);
  if (!fs.existsSync(testDir)) {
    fs.mkdirSync(testDir, { recursive: true });
  }

  fs.writeFileSync(testFilePath, testContent);
  console.log(`✅ Test file created: ${testFilePath}`);
  console.log(`   Generated ${testCases.length} test case(s)\n`);
}

main();
