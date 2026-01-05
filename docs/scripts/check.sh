#!/usr/bin/env bash
# scripts/check.sh — Best-effort verification entrypoint (stack-aware)
set -euo pipefail

echo "[check] Starting checks..."

# Always run governance-related checks
if [[ -x "scripts/ai-audit.sh" ]]; then
  scripts/ai-audit.sh --dry-run >/dev/null || true
fi

# Detect project type and run checks if commands exist.
# This template avoids guessing package managers. Prefer repo.manifest.yaml to define canonical commands.

run_if_exists() {
  local cmd="$1"
  if command -v ${cmd%% *} >/dev/null 2>&1; then
    echo "[check] Running: $cmd"
    eval "$cmd"
  else
    echo "[check] Skipping (missing command): $cmd"
  fi
}

# Node projects
if [[ -f "package.json" ]]; then
  if [[ -f "pnpm-lock.yaml" ]]; then
    run_if_exists "pnpm -s test"
  elif [[ -f "yarn.lock" ]]; then
    run_if_exists "yarn -s test"
  elif [[ -f "package-lock.json" ]]; then
    run_if_exists "npm test --silent"
  else
    echo "[check] package.json found but no lockfile; define checks in repo.manifest.yaml."
  fi
fi

# Python projects
if [[ -f "pyproject.toml" || -f "requirements.txt" ]]; then
  run_if_exists "python3 -m pytest"
fi

# Go projects
if [[ -f "go.mod" ]]; then
  run_if_exists "go test ./..."
fi

echo "[check] Done."
