# Client Portal Information Architecture (CLIENT_PORTAL_INFORMATION_ARCHITECTURE)

Defines permission-gated navigation and common client flows.

Primary nav (left; gated by scopes)
1. Home
2. Messages
3. Documents
4. Appointments
5. Billing
6. Engagements (optional; if exposing limited status)
7. Profile

Account switcher
- shown only if portal identity has multiple account grants
- switching must re-scope all lists and permissions

Common flows
- Message: open thread → send message → attach document (upload or select allowed)
- Upload: view upload request → upload → confirm → appears in Documents and notifies staff
- Book: choose meeting type → choose staff availability → confirm → calendar sync
- Pay: view invoice → pay (provider) → receipt → status updates

---
