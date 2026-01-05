#!/usr/bin/env bash
# scripts/new-repo.sh — Stamp this governance framework into a target repo (template)
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/new-repo.sh /path/to/target-repo"
  exit 1
fi

TARGET="$1"
if [[ ! -d "$TARGET" ]]; then
  echo "Target directory does not exist: $TARGET"
  exit 1
fi

echo "[new-repo] Copying governance files into: $TARGET"

copy() {
  local src="$1"
  local dst="$2"
  mkdir -p "$(dirname "$TARGET/$dst")"
  cp "$src" "$TARGET/$dst"
}

# Root governance
copy README.md README.md
copy READMEAI.md READMEAI.md
copy CODEBASECONSTITUTION.md CODEBASECONSTITUTION.md
copy BOOTSTRAP_GUIDE.md BOOTSTRAP_GUIDE.md
copy PROJECT_STATUS.md PROJECT_STATUS.md
copy TODO.md TODO.md
copy repo.manifest.yaml repo.manifest.yaml
copy SECURITY.md SECURITY.md
copy CHANGELOG.md CHANGELOG.md
copy VERSION VERSION
copy Makefile Makefile
copy .editorconfig .editorconfig
copy .gitignore .gitignore
copy .aider.conf.yml .aider.conf.yml
copy CLAUDE.md CLAUDE.md

# Folders
mkdir -p "$TARGET/specs" "$TARGET/docs" "$TARGET/scripts" "$TARGET/.ai/prompts" "$TARGET/.githooks" "$TARGET/githubactions/workflows (disabled by default)" "$TARGET/docs/adr" "$TARGET/.devcontainer" "$TARGET/.cursor/rules/00-governance"

# Copy structured content
for f in specs/project-spec.md specs/technical-plan.md specs/project-tasks.md (non-binding notes) (optional, non-binding); do
  copy "$f" "$f"
done

for f in docs/*.md; do
  copy "$f" "$f"
done

for f in docs/adr/*.md; do
  copy "$f" "$f"
done

for f in scripts/*.sh; do
  copy "$f" "$f"
done

copy .githooks/pre-commit .githooks/pre-commit
copy githubactions/workflows (disabled by default)/governance-ci.yml githubactions/workflows (disabled by default)/governance-ci.yml
copy .github/copilot-instructions.md .github/copilot-instructions.md
copy .cursor/rules/00-governance/RULE.md .cursor/rules/00-governance/RULE.md
copy .devcontainer/devcontainer.json .devcontainer/devcontainer.json
copy .devcontainer/Dockerfile .devcontainer/Dockerfile
copy mise.toml mise.toml
copy .tool-versions .tool-versions

echo "[new-repo] Done. Next: edit repo.manifest.yaml and PROJECT_STATUS.md for the new repo."
