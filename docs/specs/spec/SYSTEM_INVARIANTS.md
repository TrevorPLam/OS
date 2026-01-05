# System Invariants

## Frozen decisions (must not change)
1. **No re-opening frozen decisions**: previously locked seam decisions remain fixed; this document only codifies them.
2. **No new features or architecture changes**: specifications must reflect existing decisions only.
3. **Reports are derived and non-authoritative**: reporting outputs are explicitly non-authoritative and derived from source records.
4. **Billing is append-only history**: financial facts are never overwritten; adjustments are new records only.
5. **DMS bindings reference immutable identifiers**: binding events must reference a `DocumentVersion` ID or `FrozenArtifact` reference.
6. **Client access is portal-only**: clients can access only the curated Client Portal surface.
7. **No cross-module permission leakage**: portal access does not inherit permissions from any other module.
8. **Asset Management is standalone**: Asset Management has no dependency on CRM.

## Non-goals
- Define or redesign product features beyond locked seam decisions.
- Introduce a new system of record or “single source of truth.”
- Change existing billing workflows, only document append-only behavior.
- Expand client access beyond the Client Portal surface.
- Create any dependency between Asset Management and CRM.

## Glossary
- **Quote**: A pre-acceptance commercial offer or proposal to a client.
- **Acceptance**: The formal approval/acceptance of a quote by authorized parties.
- **Invoice**: A billing document issued to a client for approved billable items.
- **Adjustment**: An append-only billing record that modifies financial outcomes without overwriting original invoices/lines.
- **BillableEvent**: A PM-originated, approved trigger that can generate an invoice line.
- **DocumentVersion**: An immutable identifier for a specific version of a document.
- **FrozenArtifact**: An immutable artifact snapshot (e.g., a PDF hash or snapshot ID).
- **PortalArtifact**: A curated artifact exposed in the Client Portal (e.g., invoice, signed proposal).
