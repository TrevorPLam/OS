# DOMAIN_MODEL.md — Core Domain Entities
Document Type: Reference
Version: 1.0.0
Last Updated: 2026-01-05
Owner: Repository Root
Status: Active
Canonical Status: Canonical
Dependencies: ARCHITECTURE.md

## Core Entities

This document outlines the primary domain entities in ConsultantPro.

### Multi-Tenancy Foundation

**Firm**
- The root tenant entity
- All user/client data scoped to firm
- Isolation enforced via RLS

**User**
- Platform users (staff, admins)
- Associated with one or more firms
- Roles and permissions per firm

**Client**
- Portal users (external clients)
- Scoped to single firm
- Limited, client-portal-only access

### CRM Domain

**Lead** → **Prospect** → **Client**
- Lead: Initial contact, not qualified
- Prospect: Qualified, in active sales process
- Client: Converted, active customer

**Proposal**
- Sales proposals with pricing
- Versioned (edits don't break history)
- Can be converted to projects/invoices

**Pipeline**
- Sales pipeline stages
- Deal tracking and forecasting
- Custom fields per firm

### Client Management

**Client Portal**
- Branded portal per firm
- Custom domain support
- Document sharing, messaging

**Contact**
- Individual people at a client
- Location fields for segmentation (country/state/city/postal code, optional lat/lon)

**Project**
- Client engagements
- Tasks, milestones, deliverables
- Time tracking integration

### Finance Domain

**Invoice**
- Generated from projects or ad-hoc
- Line items with pricing
- Payment tracking

**Payment**
- Stripe/Square integration
- Multiple payment methods
- Refund support

**BillingLedger**
- Immutable transaction log
- Reconciliation and auditing

### Calendar Domain

**EventType**
- Booking link templates (like Calendly)
- Duration, availability rules
- Buffer times, limits

**Appointment**
- Scheduled events
- Attendees, location, notes
- Calendar sync (Google, Microsoft)

### Marketing Automation

**Automation**
- Visual workflow builder
- Triggers (form submit, email action, etc.)
- Actions (send email, wait, branch, etc.)

**Campaign**
- Email campaigns
- Segmentation and personalization
- Analytics and tracking

**Tag/Segment**
- Contact organization
- Dynamic segmentation rules

### Communications

**Conversation**
- Multi-party threaded conversations
- Email, SMS, portal messages

**Message**
- Individual messages in conversation
- Attachments, read receipts

### Integrations

**WebhookEndpoint**
- Inbound webhook configuration
- Signature verification
- Event mapping and routing

**IntegrationConnection**
- OAuth connections (QuickBooks, Xero, DocuSign)
- Credentials storage (encrypted)
- Sync status and error tracking

See module-specific documentation for detailed schema and relationships.
