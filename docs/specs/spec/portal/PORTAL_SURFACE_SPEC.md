# Client Portal Surface Spec

## Allowed artifact types
- Invoices
- Statements
- Signed proposals
- Requests
- Deliverables

## Curation rules
- Only curated artifacts appear in the Client Portal.
- Internal-only artifacts (drafts, internal notes, admin reports) never appear.
- Portal artifacts must be scoped to the portal user’s client.

## Access model
- **Portal is the only client surface**. Clients access data exclusively through the Client Portal.
- **No cross-module permission inheritance**: portal access does not grant access to CRM, PM, Finance, or other module endpoints.
- Portal visibility is controlled through portal-specific permissions only.
