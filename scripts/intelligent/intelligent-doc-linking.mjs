#!/usr/bin/env node
// Intelligent Documentation Linking
// Usage: node scripts/intelligent/intelligent-doc-linking.mjs [--scan-all] [--dry-run]

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const SCAN_ALL = process.argv.includes("--scan-all");
const DRY_RUN = process.argv.includes("--dry-run");

function findMarkdownFiles(dir = path.join(REPO_ROOT, "docs")) {
  const files = [];
  if (!fs.existsSync(dir)) return files;

  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory() && !entry.name.startsWith(".")) {
      files.push(...findMarkdownFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith(".md")) {
      files.push(fullPath);
    }
  }
  return files;
}

function extractTopics(content) {
  const topics = [];

  // Extract headings
  const headings = content.matchAll(/^#{1,3}\s+(.+)$/gm);
  for (const match of headings) {
    topics.push(match[1].trim().toLowerCase());
  }

  // Extract keywords (common technical terms)
  const keywords = [
    "api",
    "authentication",
    "authorization",
    "database",
    "schema",
    "migration",
    "testing",
    "deployment",
    "ci/cd",
    "security",
    "performance",
    "optimization",
  ];

  const lowerContent = content.toLowerCase();
  for (const keyword of keywords) {
    if (lowerContent.includes(keyword)) {
      topics.push(keyword);
    }
  }

  return [...new Set(topics)];
}

function findRelatedDocs(docPath, allDocs, topicMap) {
  const content = fs.readFileSync(docPath, "utf8");
  const topics = extractTopics(content);
  const related = [];

  for (const [otherPath, otherTopics] of topicMap.entries()) {
    if (otherPath === docPath) continue;

    // Calculate topic overlap
    const overlap = topics.filter((t) => otherTopics.includes(t));
    if (overlap.length >= 2) {
      // At least 2 topics in common
      related.push({
        path: otherPath,
        topics: overlap,
        score: overlap.length,
      });
    }
  }

  return related.sort((a, b) => b.score - a.score).slice(0, 5); // Top 5 related docs
}

function addLinksToDoc(docPath, relatedDocs) {
  let content = fs.readFileSync(docPath, "utf8");
  const relativePath = path.relative(REPO_ROOT, docPath);

  // Check if "Related Documentation" section exists
  if (content.includes("## Related") || content.includes("### Related")) {
    // Update existing section
    const relatedSection = content.match(/(## Related[\s\S]*?)(?=\n##|$)/);
    if (relatedSection) {
      const newLinks = relatedDocs
        .map((r) => {
          const relPath = path.relative(path.dirname(docPath), r.path).replace(/\\/g, "/");
          return `- [${path.basename(r.path, ".md")}](${relPath}) - ${r.topics.join(", ")}`;
        })
        .join("\n");

      content = content.replace(relatedSection[0], `## Related Documentation\n\n${newLinks}\n`);
      return { content, updated: true };
    }
  }

  // Add new section at end
  const links = relatedDocs
    .map((r) => {
      const relPath = path.relative(path.dirname(docPath), r.path).replace(/\\/g, "/");
      return `- [${path.basename(r.path, ".md")}](${relPath})`;
    })
    .join("\n");

  content += `\n\n## Related Documentation\n\n${links}\n`;
  return { content, updated: true };
}

function checkBrokenLinks(docPath) {
  const content = fs.readFileSync(docPath, "utf8");
  const broken = [];

  // Find markdown links
  const linkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
  let match;

  while ((match = linkPattern.exec(content)) !== null) {
    const linkText = match[1];
    const linkPath = match[2];

    // Skip external links
    if (linkPath.startsWith("http") || linkPath.startsWith("mailto:")) continue;

    // Resolve relative path
    const docDir = path.dirname(docPath);
    const resolvedPath = path.resolve(docDir, linkPath);

    if (!fs.existsSync(resolvedPath)) {
      broken.push({ link: linkText, path: linkPath, doc: docPath });
    }
  }

  return broken;
}

function main() {
  console.log("🔗 Intelligent Documentation Linking\n");

  const docs = findMarkdownFiles();
  console.log(`📚 Found ${docs.length} documentation files\n`);

  if (docs.length === 0) {
    console.log("⚠️  No documentation files found");
    return;
  }

  // Build topic map
  console.log("🔍 Analyzing topics...");
  const topicMap = new Map();
  for (const doc of docs) {
    const topics = extractTopics(fs.readFileSync(doc, "utf8"));
    topicMap.set(doc, topics);
  }
  console.log(`   Analyzed ${topicMap.size} files\n`);

  // Find related docs and add links
  let updatedCount = 0;
  const brokenLinks = [];

  for (const doc of docs) {
    const related = findRelatedDocs(doc, docs, topicMap);
    if (related.length > 0) {
      const broken = checkBrokenLinks(doc);
      brokenLinks.push(...broken);

      if (DRY_RUN) {
        console.log(`[DRY RUN] Would update: ${path.relative(REPO_ROOT, doc)}`);
        console.log(`   Related: ${related.length} docs`);
      } else {
        const { content, updated } = addLinksToDoc(doc, related);
        if (updated) {
          fs.writeFileSync(doc, content);
          updatedCount++;
          console.log(`✅ Updated: ${path.relative(REPO_ROOT, doc)} (${related.length} links)`);
        }
      }
    }
  }

  // Report broken links
  if (brokenLinks.length > 0) {
    console.log(`\n⚠️  Found ${brokenLinks.length} broken link(s):\n`);
    brokenLinks.slice(0, 10).forEach((link) => {
      console.log(`   - ${path.relative(REPO_ROOT, link.doc)}: [${link.link}](${link.path})`);
    });
    if (brokenLinks.length > 10) {
      console.log(`   ... and ${brokenLinks.length - 10} more`);
    }
  }

  if (!DRY_RUN) {
    console.log(`\n✅ Updated ${updatedCount} documentation files with cross-references`);
  }
}

main();
