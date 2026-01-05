#!/usr/bin/env bash
# scripts/validate-enhancements.sh — Final validation for governance framework

set -euo pipefail

echo "=== Governance Framework Validation ==="
echo

echo "1) Regenerating TODO.md..."
./scripts/sync-todo.sh

echo
echo "2) Running governance audit..."
./scripts/ai-audit.sh

echo
echo "3) Running security scan..."
./scripts/security-scan.sh

echo
echo "4) Bash syntax check on scripts..."
bash -n scripts/*.sh

echo
echo "5) Basic existence checks for new components..."
required=(
  "githubactions/workflows (disabled by default)/governance-ci.yml"
  ".github/copilot-instructions.md"
  ".cursor/rules/00-governance/RULE.md"
  "repo.manifest.yaml"
  "docs/ENVIRONMENT.md"
  "docs/CONTEXT_MAP.md"
  "docs/adr/0001-template.md"
  "docs/OBSERVABILITY.md"
  "docs/DEPLOYMENT.md"
  "docs/AI_COST_POLICY.md"
  "docs/SECURITY_BASELINE.md"
  "SECURITY.md"
  "CHANGELOG.md"
  "VERSION"
  "Makefile"
  "scripts/check.sh"
  "scripts/bootstrap.sh"
  "scripts/new-repo.sh"
  ".gitignore"
  ".editorconfig"
  "CLAUDE.md"
  ".aider.conf.yml"
)
missing=0
for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "MISSING: $f"
    missing=1
  fi
done
if [[ "$missing" -eq 1 ]]; then
  echo
  echo "Validation FAILED: missing files."
  exit 1
fi

echo
echo "6) Done. Framework is consistent."
