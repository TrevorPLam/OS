#!/usr/bin/env node
// Auto-Build Code Dependency Graph
// Usage: node scripts/intelligent/auto-build-dependency-graph.mjs [--output-format json|dot|svg]

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const OUTPUT_FORMAT = process.argv.find((arg) => arg.startsWith("--output-format="))?.split("=")[1] || "json";

function findCodeFiles(dir = REPO_ROOT) {
  const files = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!entry.name.startsWith(".") && entry.name !== "node_modules") {
        files.push(...findCodeFiles(fullPath));
      }
    } else if (/\.(ts|tsx|js|jsx)$/.test(entry.name)) {
      files.push(fullPath);
    }
  }

  return files;
}

function parseImports(filePath) {
  try {
    const content = fs.readFileSync(filePath, "utf8");
    const imports = [];

    // Match import statements
    const importRegex = /^import\s+(?:(?:\{[^}]+\}|\*\s+as\s+\w+|\w+)(?:\s*,\s*(?:\{[^}]+\}|\*\s+as\s+\w+|\w+))*)\s+from\s+['"]([^'"]+)['"]/gm;
    let match;

    while ((match = importRegex.exec(content)) !== null) {
      const importPath = match[1];
      // Resolve relative imports
      if (importPath.startsWith(".") || importPath.startsWith("/")) {
        const resolvedPath = path.resolve(path.dirname(filePath), importPath);
        imports.push({
          source: importPath,
          resolved: resolvedPath,
          relative: path.relative(REPO_ROOT, resolvedPath),
        });
      } else {
        // External dependency
        imports.push({
          source: importPath,
          external: true,
        });
      }
    }

    return imports;
  } catch (e) {
    return [];
  }
}

function buildDependencyGraph() {
  const files = findCodeFiles();
  const graph = {
    nodes: [],
    edges: [],
    modules: new Map(),
  };

  console.log(`📁 Analyzing ${files.length} files...\n`);

  for (const file of files) {
    const relativePath = path.relative(REPO_ROOT, file);
    const module = relativePath.match(/packages\/features\/(\w+)\//)?.[1] || relativePath.match(/apps\/(\w+)\//)?.[1] || "root";

    if (!graph.modules.has(module)) {
      graph.modules.set(module, []);
    }
    graph.modules.get(module).push(relativePath);

    const node = {
      id: relativePath,
      file: relativePath,
      module,
      imports: [],
    };

    const imports = parseImports(file);
    for (const imp of imports) {
      if (!imp.external && imp.relative) {
        node.imports.push(imp.relative);
        graph.edges.push({
          from: relativePath,
          to: imp.relative,
          type: "import",
        });
      }
    }

    graph.nodes.push(node);
  }

  return graph;
}

function detectCircularDependencies(graph) {
  const cycles = [];
  const visited = new Set();
  const recStack = new Set();

  function dfs(node) {
    visited.add(node);
    recStack.add(node);

    const outgoing = graph.edges.filter((e) => e.from === node).map((e) => e.to);
    for (const neighbor of outgoing) {
      if (!visited.has(neighbor)) {
        if (dfs(neighbor)) return true;
      } else if (recStack.has(neighbor)) {
        // Found cycle
        cycles.push([...Array.from(recStack), neighbor]);
        return true;
      }
    }

    recStack.delete(node);
    return false;
  }

  for (const node of graph.nodes.map((n) => n.id)) {
    if (!visited.has(node)) {
      dfs(node);
    }
  }

  return cycles;
}

function generateOutput(graph, format) {
  const outputPath = path.join(REPO_ROOT, ".repo/automation/dependency-graph");

  if (format === "json") {
    const json = {
      nodes: graph.nodes,
      edges: graph.edges,
      modules: Object.fromEntries(graph.modules),
      generated_at: new Date().toISOString(),
    };
    fs.writeFileSync(`${outputPath}.json`, JSON.stringify(json, null, 2));
    console.log(`✅ Dependency graph written to: ${outputPath}.json`);
  } else if (format === "dot") {
    let dot = "digraph Dependencies {\n";
    dot += "  rankdir=LR;\n";
    for (const edge of graph.edges.slice(0, 100)) {
      // Limit for readability
      dot += `  "${edge.from}" -> "${edge.to}";\n`;
    }
    dot += "}\n";
    fs.writeFileSync(`${outputPath}.dot`, dot);
    console.log(`✅ DOT graph written to: ${outputPath}.dot`);
  }
}

function main() {
  console.log("🕸️  Building Code Dependency Graph\n");

  const graph = buildDependencyGraph();
  console.log(`   Nodes: ${graph.nodes.length}`);
  console.log(`   Edges: ${graph.edges.length}`);
  console.log(`   Modules: ${graph.modules.size}\n`);

  const cycles = detectCircularDependencies(graph);
  if (cycles.length > 0) {
    console.log(`⚠️  Found ${cycles.length} circular dependencies:`);
    cycles.slice(0, 5).forEach((cycle) => {
      console.log(`   - ${cycle.join(" → ")}`);
    });
  } else {
    console.log("✅ No circular dependencies detected");
  }

  // Ensure output directory exists
  const outputDir = path.dirname(path.join(REPO_ROOT, ".repo/automation/dependency-graph.json"));
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  generateOutput(graph, OUTPUT_FORMAT);
}

main();
