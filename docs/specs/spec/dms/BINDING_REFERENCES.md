# DMS Binding References

## Definitions
- **DocumentVersion**: Immutable identifier for a specific version of a document.
- **FrozenArtifact**: Immutable artifact snapshot (e.g., PDF hash, snapshot ID).

## Binding event requirements
- Binding events must reference **immutable identifiers** only:
  - `document_version_id` (DocumentVersion), or
  - `frozen_artifact_id` / `frozen_artifact_hash` (FrozenArtifact).
- The binding event must store enough information to reproduce the historical reference:
  - Immutable identifier
  - Artifact type (DocumentVersion or FrozenArtifact)
  - Timestamp and actor

## Non-mutation rule
- Later edits **never** mutate historical binding references.
- Any correction or change is recorded as a new binding event with a new immutable reference.
