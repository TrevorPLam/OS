#!/usr/bin/env bash
# scripts/bootstrap.sh — Minimal bootstrap (template)
set -euo pipefail

echo "[bootstrap] Starting bootstrap..."

# Ensure scripts are executable (best-effort)
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x .githooks/pre-commit 2>/dev/null || true

# Install git hooks (opt-in)
if [[ -d ".git" && "${ENABLE_GITHOOKS:-0}" == "1" ]]; then
  mkdir -p .git/hooks
  cp .githooks/pre-commit .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit
  echo "[bootstrap] Installed pre-commit hook (ENABLE_GITHOOKS=1)."
else
  echo "[bootstrap] Skipped git hook install. Set ENABLE_GITHOOKS=1 to enable."
fi
else
  echo "[bootstrap] No .git directory found (skipping hook install)."
fi

# Generate TODO.md from tasks
if [[ -x "scripts/sync-todo.sh" ]]; then
  scripts/sync-todo.sh || true
fi

echo "[bootstrap] Complete."
