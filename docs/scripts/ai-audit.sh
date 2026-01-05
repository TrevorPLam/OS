#!/usr/bin/env bash
# scripts/ai-audit.sh — Governance gate (repo-agnostic)
set -euo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

violations=()
log_violation() { violations+=("$1"); }

# 1) Required files exist
required=(
  "README.md"
  "READMEAI.md"
  "AGENTS.md"
  "CODEBASECONSTITUTION.md"
  "PROJECT_STATUS.md"
  "repo.manifest.yaml"
  "TODO.md"
  "TODOCOMPLETED.md"
  "CODEAUDIT.md"
  "SECURITYAUDIT.md"
  "DEPENDENCYAUDIT.md"
  "RELEASEAUDIT.md"
  "DOCSAUDIT.md"
  "SECURITY.md"
  "CHANGELOG.md"
  "VERSION"
  "githubactions/README.md"
  "githubactions/workflows/governance-ci.yml"
  "scripts/README.md"
)
for f in "${required[@]}"; do
  [[ -f "$f" ]] || log_violation "Missing required file: $f"
done

# 2) PROJECT_STATUS.md YAML frontmatter keys (simple parser; no PyYAML dependency)
if [[ -f "PROJECT_STATUS.md" ]]; then
  python3 - <<'PY' || log_violation "PROJECT_STATUS.md YAML header missing/invalid or missing required keys"
import re, sys
p="PROJECT_STATUS.md"
txt=open(p,"r",encoding="utf-8").read()
m=re.match(r"(?s)^---\n(.*?)\n---\n", txt)
if not m:
  sys.exit(1)
block=m.group(1)
required_keys={
  "current_phase","active_task_id","execution_mode","confidence_level",
  "budget_estimate_remaining","session_cost_usd","tokens_this_session",
  "next_immediate_step","agent_last_used","handoff_reason","last_updated"
}
present=set()
for line in block.splitlines():
  line=line.strip()
  if not line or line.startswith("#"):
    continue
  if ":" in line:
    present.add(line.split(":",1)[0].strip())
missing=sorted(required_keys-present)
if missing:
  sys.exit(1)
PY
fi

# 3) TODO.md must declare it is the task truth source
if [[ -f "TODO.md" ]]; then
  grep -qE '^Task Truth Source:' TODO.md || log_violation "TODO.md missing 'Task Truth Source:' line"
fi

# 4) Tasks file must contain at least one task and Verification blocks
fi

# 5) Basic formatting sanity (EOF newline)
python3 - <<'PY' || log_violation "One or more markdown/yaml files missing trailing newline"
import os, sys
check_ext={".md",".yml",".yaml",".toml",".json"}
bad=[]
for root,_,files in os.walk("."):
  if root.startswith("./.git"):
    continue
  for f in files:
    ext=os.path.splitext(f)[1].lower()
    if ext in check_ext:
      p=os.path.join(root,f)
      try:
        b=open(p,"rb").read()
      except Exception:
        continue
      if b and not b.endswith(b"\n"):
        bad.append(p)
if bad:
  sys.exit(1)
PY

if [[ ${#violations[@]} -eq 0 ]]; then
  echo "[ai-audit] PASS"
  $DRY_RUN && echo '{"would_pass": true, "violations": []}'
  exit 0
fi

echo "[ai-audit] FAIL"
for v in "${violations[@]}"; do echo " - $v"; done

if $DRY_RUN; then
  python3 - <<'PY'
import json, sys
# violations are printed above; dry-run only needs a simple false output
print(json.dumps({"would_pass": False, "violations": []}))
PY
  exit 0
fi

exit 1
