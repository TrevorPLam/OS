#!/usr/bin/env bash
# docs/scripts/pre_launch_gate.sh — Pre-launch checklist gate
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CHECKLIST_PATH="${SCRIPT_DIR}/../PRE_LAUNCH_CHECKLIST.md"
TODO_PATH="${SCRIPT_DIR}/../../TODO.md"

failures=()

if [[ ! -f "${CHECKLIST_PATH}" ]]; then
  failures+=("Missing checklist: ${CHECKLIST_PATH}")
fi

if [[ ! -f "${TODO_PATH}" ]]; then
  failures+=("Missing task source: ${TODO_PATH}")
fi

if [[ -f "${TODO_PATH}" ]]; then
  TODO_PATH="${TODO_PATH}" python3 - <<'PY' || failures+=("TODO.md contains invalid Status values")
import os
import re
allowed = {"READY", "BLOCKED", "IN-PROGRESS", "IN-REVIEW"}
todo_path = os.environ["TODO_PATH"]
with open(todo_path, "r", encoding="utf-8") as handle:
    for line in handle:
        if line.startswith("Status:"):
            status = line.split(":", 1)[1].strip()
            if status not in allowed:
                raise SystemExit(1)
PY
fi

if [[ -f "${CHECKLIST_PATH}" ]]; then
  CHECKLIST_PATH="${CHECKLIST_PATH}" python3 - <<'PY' || failures+=("Pre-launch checklist has unchecked items")
import os
import re

unchecked = 0
in_code_block = False
checklist_path = os.environ["CHECKLIST_PATH"]
with open(checklist_path, "r", encoding="utf-8") as handle:
    for line in handle:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if re.match(r"^\s*-\s\[\s\]\s", line):
            unchecked += 1

if unchecked:
    raise SystemExit(1)
PY
fi

if (( ${#failures[@]} )); then
  echo "[pre-launch-gate] FAIL"
  for failure in "${failures[@]}"; do
    echo " - ${failure}"
  done
  exit 1
fi

echo "[pre-launch-gate] PASS"
