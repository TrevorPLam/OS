#!/usr/bin/env bash
# scripts/security-scan.sh — Lightweight repo-agnostic security gate
set -euo pipefail

echo "[security-scan] Starting security audit..."

FAIL_ON_WARN="${FAIL_ON_WARN:-false}"
warn() { echo "[security-scan] WARNING: $1"; $FAIL_ON_WARN && exit 1 || true; }
fail() { echo "[security-scan] ERROR: $1"; exit 1; }

exclude_dirs=(node_modules .git .next dist build output .venv venv)

grep_excludes=()
for d in "${exclude_dirs[@]}"; do
  grep_excludes+=(--exclude-dir="$d")
done
grep_excludes+=(--exclude="*.log" --exclude="*.tmp")

echo "[security-scan] Scanning for likely secrets..."
# Simple, safe heuristic (will produce false positives sometimes; tune per repo)
SECRET_RE='(password|secret|token|api[_-]?key|private[_-]?key|credential)[[:space:]]*[:=][[:space:]]*[A-Za-z0-9_./+=-]{12,}'

if grep -RInE "${grep_excludes[@]}" "$SECRET_RE" . ; then
  fail "Potential secrets detected. Remove them and use env vars / secret manager."
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git ls-files | grep -E '(^|/)\.env$' >/dev/null 2>&1; then
    warn ".env is tracked by git. Usually this should be ignored."
  fi
fi

if [[ -f "package-lock.json" || -f "pnpm-lock.yaml" || -f "yarn.lock" ]]; then
  echo "[security-scan] Detected JS deps. Consider running npm/pnpm/yarn audit in CI."
fi
if [[ -f "requirements.txt" || -f "pyproject.toml" ]]; then
  echo "[security-scan] Detected Python deps. Consider pip-audit/safety in CI."
fi

echo "[security-scan] PASS"
