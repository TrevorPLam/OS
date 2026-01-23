# Agent Rules (Compact)

**Token-optimized essential rules. Full context: `.repo/agents/QUICK_REFERENCE.md`**

## Required Files (Start)
1. `.repo/tasks/TODO.md`
2. `.repo/repo.manifest.yaml`
3. `.repo/agents/QUICK_REFERENCE.md`

## Constitution (8 Articles)
- **A1:** Solo founder = final authority
- **A2:** Verification evidence required (proof > persuasion)
- **A3:** Unknown → Mark `<UNKNOWN>` → HITL → Stop
- **A4:** Small, shippable increments (no mega-PRs)
- **A5:** Link to task, archive completed
- **A6:** Risky → STOP → HITL → VERIFY → PROCEED
- **A7:** Workflow varies per repo (manifest)
- **A8:** External systems = always HITL

## Principles (Critical)
- **Global:** Filepaths everywhere
- **P3:** One change type per PR
- **P6:** Evidence over vibes
- **P7:** UNKNOWN is first-class
- **P10:** Risk → STOP → HITL
- **P13:** Respect boundaries
- **P17:** PR: what/why/filepaths/verification/risks/rollback
- **P23:** Cross-boundaries → ADR required

## Workflow: Three-Pass
1. **Plan:** Actions, risks, files, UNKNOWNs → Approval
2. **Change:** Edits, patterns, filepaths
3. **Verify:** Tests, evidence, logs, quality gates, PR docs

## HITL Decision Tree
```
Risky? (security/money/prod/external) → YES → HITL → Stop
Unknown? (not in docs/manifest/code) → YES → <UNKNOWN> → HITL → Stop
Cross-boundaries? → YES → ADR required
```

## Security Triggers (A8)
1. Auth/login change
2. Money/payment flow
3. External service
4. Sensitive data
5. Production config/keys
6. Cryptography/security
7. Dependency vulns

## Always
- Filepaths in all changes
- Link to `.repo/tasks/TODO.md` (A5)
- UNKNOWN → HITL (A3)
- Three-pass workflow
- `make lint` before PR
- Archive completed (A5)
- Verification evidence (A2, P6)
- PR: what/why/filepaths/verification/risks/rollback (P17)
- Update docs/examples when code changes (P19, P20)
- Declare assumptions (P9)
- Rollback thinking for risky (P12)

## Never
- Guess commands (A3) → Use manifest/HITL
- Skip filepaths (global)
- Modify policies without approval
- Commit secrets/.env (prohibited)
- Cross boundaries without ADR (P23)
- Proceed with UNKNOWN (A3)
- Risky changes without HITL (A6, A8)
- Mega-PRs (A4)
- Skip verification (A2)
- Silent scope creep (P18)
- Undeclared assumptions (P9)

## Artifacts by Change Type
- **Feature:** Task packet, trace log, tests
- **API:** Task packet, ADR, trace log, OpenAPI update
- **Security:** HITL, trace log, security tests
- **Cross-module:** ADR, task packet, trace log
- **Non-doc:** Agent log, trace log, reasoning summary (P24)

## Commands (Source: `.repo/repo.manifest.yaml`)
```bash
make setup          # Install
make lint           # Lint
make test           # Test
make verify         # CI (light)
make verify SKIP_HEAVY=0  # CI (full)
make -C backend migrate/openapi
make -C frontend test/e2e
```

## Tech Stack
- **Backend:** Django 4.2 + Python 3.11 + PostgreSQL 15
- **Frontend:** React 18.3 + TypeScript 5.9 + Vite 5.4
- **Data:** TanStack React Query, React Hook Form

## Code Patterns
- **Backend:** `class ViewSet(FirmScopedMixin, viewsets.ModelViewSet)`
- **Frontend:** `export const Component: React.FC = () => { useQuery(...) }`

## Conditional Reading
- **Security work:** `.repo/policy/SECURITY_BASELINE.md` + `.repo/policy/HITL.md`
- **Cross-boundaries:** `.repo/policy/BOUNDARIES.md`
- **Creating PR:** `.repo/policy/QUALITY_GATES.md` + `.repo/templates/PR_TEMPLATE.md`
- **Unknown:** `.repo/policy/HITL.md`

**Full rules:** `.repo/agents/QUICK_REFERENCE.md` | **Machine-readable:** `.repo/agents/rules.json`
