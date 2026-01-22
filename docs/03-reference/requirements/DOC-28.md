# Contributing (CONTRIBUTING.md)

## Branching
- main: protected
- feature/*: work branches
- fix/*: hotfixes

## Spec change process
1. Update the relevant spec doc(s).
2. Add/update a DECISION_LOG entry if it changes an invariant or major decision.
3. Add/update tests if the change affects correctness-critical behavior.
4. Open PR with:
   - summary
   - risk/impact
   - migration notes (if any)

## Review checklist
- Specs updated and consistent
- Permissions enforced
- Idempotency considered for side effects
- Audit events added where required
- Tests added/updated

---
