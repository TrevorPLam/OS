# Firm Administrator Guide

**Audience:** Firm Master Admins and Firm Admins  
**Purpose:** Complete guide to managing your consulting firm in ConsultantPro

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Managing Users & Permissions](#managing-users--permissions)
4. [CRM: Leads & Prospects](#crm-leads--prospects)
5. [Client Management](#client-management)
6. [Project Management](#project-management)
7. [Time Tracking](#time-tracking)
8. [Invoicing & Billing](#invoicing--billing)
9. [Document Management](#document-management)
10. [Reports & Analytics](#reports--analytics)
11. [Settings & Configuration](#settings--configuration)

---

## Getting Started

### First Login

1. Navigate to your firm's ConsultantPro URL (e.g., `https://yourfirm.consultantpro.com`)
2. Log in with your credentials
3. You'll see the main dashboard

### Your Role

As a **Firm Administrator**, you have access to:
- ✅ All firm data and settings
- ✅ User management
- ✅ Client and project management
- ✅ Financial data and reporting
- ✅ System configuration

**Note:** Master Admins have additional override capabilities.

---

## Dashboard Overview

The dashboard provides a quick overview of your firm's performance:

### Key Metrics
- **Active Projects** - Number of ongoing projects
- **Pending Invoices** - Outstanding invoices awaiting payment
- **Monthly Revenue** - Revenue for current month
- **Team Utilization** - Percentage of billable time

### Quick Actions
- Create new lead
- Add new client
- Start new project
- Create invoice

### Recent Activity
- Latest client interactions
- Recent time entries
- Payment notifications
- System alerts

---

## Managing Users & Permissions

### Adding a New User

1. Go to **Settings** → **Team Members**
2. Click **Add Team Member**
3. Fill in user details:
   - **Name:** Full name
   - **Email:** Work email address
   - **Role:** Select role (see below)
4. Click **Send Invitation**
5. User will receive email with setup instructions

### User Roles

#### Master Admin (Owner)
- Full access to all features
- Can override system settings
- Access to break-glass features
- Can delete/deactivate firm

**Best Practice:** Limit to 1-2 people.

#### Firm Admin
- Manage users and permissions
- Access all clients and projects
- View all financial data
- Configure firm settings

**Best Practice:** Senior partners and operations managers.

#### Staff
- Access assigned clients and projects only
- Submit time entries
- View assigned documents
- Limited financial visibility

**Best Practice:** Consultants, analysts, and support staff.

### Managing Permissions

1. Go to **Settings** → **Team Members**
2. Click on user name
3. Toggle permissions:
   - **Can manage clients**
   - **Can manage projects**
   - **Can view finances**
   - **Can manage documents**
4. Click **Save**

### Deactivating Users

When someone leaves:

1. Go to **Settings** → **Team Members**
2. Click on user
3. Click **Deactivate**
4. Select reason:
   - Left company
   - End of contract
   - Other
5. Confirm deactivation

**Important:** Deactivation preserves all their historical data and audit logs.

---

## CRM: Leads & Prospects

### Managing Leads

#### Creating a Lead

1. Go to **CRM** → **Leads**
2. Click **New Lead**
3. Fill in details:
   - **Contact Name**
   - **Company**
   - **Email** and **Phone**
   - **Source** (Website, Referral, Event, etc.)
   - **Notes**
4. Click **Create**

#### Lead Scoring

ConsultantPro automatically scores leads based on:
- Company size
- Industry fit
- Engagement level
- Budget indicators

Higher scores = Higher priority to follow up.

#### Converting to Prospect

When a lead is qualified:

1. Open lead record
2. Click **Convert to Prospect**
3. Select **Pipeline Stage** (see below)
4. Click **Convert**

### Managing Prospects

#### Pipeline Stages

1. **Discovery** - Initial conversations
2. **Needs Analysis** - Understanding requirements
3. **Proposal** - Preparing proposal
4. **Negotiation** - Discussing terms
5. **Won** - Deal closed, convert to client
6. **Lost** - Deal didn't close

#### Creating Proposals

1. Open prospect record
2. Click **Create Proposal**
3. Fill in:
   - **Services Description**
   - **Pricing** (fixed, hourly, or mixed)
   - **Timeline**
   - **Terms**
4. Click **Generate Proposal**
5. Send to prospect for review

#### Moving Through Pipeline

1. Open prospect record
2. Update **Pipeline Stage** dropdown
3. Add notes about the stage change
4. Click **Save**

#### Winning a Deal

When prospect accepts:

1. Open prospect record
2. Change status to **Won**
3. Click **Create Client**
4. System creates:
   - Client record
   - Initial engagement
   - Optional: Project skeleton

---

## Client Management

### Client Records

Each client has:
- **Contact Information** - Primary contacts
- **Engagements** - Active and past projects
- **Invoices** - Billing history
- **Documents** - Shared files
- **Notes** - Internal notes and history

### Creating a Client

1. Go to **Clients** → **All Clients**
2. Click **New Client**
3. Fill in:
   - **Client Name**
   - **Primary Contact**
   - **Billing Address**
   - **Payment Terms**
   - **Pricing Model** (package, hourly, mixed)
4. Click **Create**

### Client Engagements

An engagement represents a specific service contract:

#### Creating an Engagement

1. Open client record
2. Go to **Engagements** tab
3. Click **New Engagement**
4. Fill in:
   - **Name** (e.g., "2025 Strategy Consulting")
   - **Start Date** and **End Date**
   - **Pricing Model**:
     - **Package Fee**: Fixed monthly/quarterly/annual fee
     - **Hourly**: Time & materials with rate
     - **Mixed**: Combination of package + hourly
   - **Package Fee** (if applicable)
   - **Hourly Rate** (if applicable)
5. Click **Create**

#### Engagement Status

- **Active** - Currently ongoing
- **Completed** - Finished successfully
- **On Hold** - Temporarily paused
- **Cancelled** - Terminated early

### Client Portal Access

Give clients access to their own portal:

1. Open client record
2. Go to **Portal Users** tab
3. Click **Add Portal User**
4. Fill in:
   - **Name**
   - **Email**
   - **Access Level** (typically "Client User")
5. Click **Send Invitation**

Clients can view:
- Their projects and tasks
- Invoices and payment history
- Shared documents
- Communication history

**Security:** Portal users CANNOT see other clients or firm-internal data.

---

## Project Management

### Creating a Project

1. Go to **Projects** → **All Projects**
2. Click **New Project**
3. Fill in:
   - **Project Name**
   - **Client** (select from dropdown)
   - **Engagement** (select from client's engagements)
   - **Start Date** and **Target End Date**
   - **Project Manager** (assign team member)
   - **Status** (Draft, Active, On Hold, Completed)
4. Add **Description** and **Goals**
5. Click **Create**

### Project Structure

Each project has:
- **Tasks** - Specific work items
- **Milestones** - Key deliverables
- **Time Entries** - Hours worked
- **Expenses** - Project costs
- **Documents** - Project files
- **Team** - Assigned staff

### Managing Tasks

#### Creating a Task

1. Open project
2. Go to **Tasks** tab
3. Click **New Task**
4. Fill in:
   - **Task Name**
   - **Description**
   - **Assigned To** (team member)
   - **Due Date**
   - **Estimated Hours**
   - **Priority** (Low, Medium, High, Critical)
5. Click **Create**

#### Task Dependencies

For tasks that must be completed in order:

1. Open task
2. Go to **Dependencies** section
3. Select **Depends On** tasks
4. Click **Save**

System will warn if trying to complete a task before its dependencies.

#### Task Status

- **To Do** - Not started
- **In Progress** - Currently working
- **Blocked** - Waiting on something
- **Review** - Ready for review
- **Done** - Completed

### Milestones

Track major deliverables:

1. Open project
2. Go to **Milestones** section
3. Click **Add Milestone**
4. Fill in:
   - **Name** (e.g., "Phase 1 Complete")
   - **Due Date**
   - **Description**
   - **Deliverables**
5. Click **Save**

Mark complete when delivered:
1. Open milestone
2. Click **Mark Complete**
3. System records completion date

---

## Time Tracking

### Recording Time

#### Quick Time Entry

1. Go to **Time** → **New Entry**
2. Select:
   - **Date**
   - **Client**
   - **Project**
   - **Task** (optional)
   - **Hours** (e.g., 2.5)
3. Add **Description** of work
4. Mark **Billable** (if client should be charged)
5. Click **Submit**

#### Time Entry from Project

1. Go to project
2. Go to **Time** tab
3. Click **Log Time**
4. Fill in details (client/project pre-filled)
5. Click **Submit**

### Time Entry Approval

**For Firm Admins:**

Time entries must be approved before billing:

1. Go to **Time** → **Pending Approval**
2. Review entries:
   - Check hours are reasonable
   - Verify work was authorized
   - Confirm billable flag is correct
3. Select entries to approve
4. Click **Approve Selected**

**Important:** Once approved and invoiced, time entries cannot be modified.

### Time Reports

View team utilization:

1. Go to **Reports** → **Time & Utilization**
2. Select:
   - **Date Range**
   - **Team Member** (or All)
   - **Client** (or All)
3. View metrics:
   - Total hours
   - Billable vs. non-billable
   - Hours by project
   - Utilization rate

---

## Invoicing & Billing

### Understanding Billing Models

#### Package Fee Billing
- Fixed amount charged per period
- Regardless of hours worked
- Predictable for client
- Example: $5,000/month retainer

#### Hourly Billing
- Charge based on time worked
- Hourly rate × approved hours
- Common for time & materials work
- Example: 20 hours × $200/hr = $4,000

#### Mixed Billing
- Combination of package + hourly
- Base retainer + hourly for additional work
- Example: $3,000/month + $200/hr over 15 hours

### Package Invoice Auto-Generation

For package fee clients, ConsultantPro automatically generates invoices:

- **Monthly**: 1st of each month
- **Quarterly**: 1st of each quarter
- **Annual**: Anniversary of engagement start

**How it works:**
1. System runs nightly at 2 AM
2. Checks all active engagements
3. Generates invoices for periods due
4. Prevents duplicates (one invoice per period)
5. Invoices are created in "draft" status

### Creating a Manual Invoice

For hourly or one-time charges:

1. Go to **Finance** → **Invoices**
2. Click **New Invoice**
3. Select:
   - **Client**
   - **Engagement**
4. Add line items:
   - **Description** (e.g., "Consulting Services - January 2025")
   - **Quantity** (e.g., 20 hours)
   - **Rate** (e.g., $200/hour)
   - **Amount** (auto-calculated: 20 × $200 = $4,000)
5. Review **Subtotal**, **Tax** (if applicable), **Total**
6. Add **Payment Terms** (e.g., "Net 30")
7. Click **Create Draft**

### Invoice Status Workflow

1. **Draft** - Being prepared, not sent yet
2. **Sent** - Delivered to client, awaiting payment
3. **Partial** - Partially paid
4. **Paid** - Fully paid
5. **Overdue** - Past due date, not paid
6. **Cancelled** - Voided/cancelled

### Sending an Invoice

1. Open invoice (in draft status)
2. Review all details carefully
3. Click **Send Invoice**
4. Choose delivery method:
   - **Email** - Send to client email
   - **Portal** - Make available in client portal
   - **Both** (recommended)
5. Click **Confirm Send**

Client receives:
- Email with invoice PDF
- Link to pay online (if Stripe configured)
- Portal access to view/download

### Recording Payments

#### Automatic (via Stripe/Autopay)

If client pays online or has autopay:
- Payment recorded automatically
- Invoice status updated
- Client notified

#### Manual Payment Entry

For checks or bank transfers:

1. Open invoice
2. Click **Record Payment**
3. Fill in:
   - **Amount**
   - **Payment Date**
   - **Payment Method** (Check, Wire, ACH, etc.)
   - **Reference** (check #, transaction ID)
4. Click **Record**

### Autopay (Recurring Billing)

Allow clients to pay automatically:

#### Enabling Autopay for Client

1. Open client record
2. Go to **Billing** tab
3. Click **Enable Autopay**
4. Client must:
   - Add payment method (credit card or bank account)
   - Authorize recurring charges
5. System charges invoices automatically on due date

#### How Autopay Works

1. Invoice becomes due
2. System attempts charge via Stripe
3. If successful:
   - Invoice marked as paid
   - Payment recorded
   - Client notified
4. If failed:
   - Retry in 3 days
   - Retry in 7 days (if still failing)
   - Retry in 14 days (if still failing)
   - After 3 failures: Manual intervention required

### Handling Payment Failures

View failed payments:

1. Go to **Finance** → **Payment Failures**
2. Review failures:
   - **Reason** (declined, expired card, insufficient funds)
   - **Retry Schedule**
   - **Contact Status**
3. Actions:
   - **Contact Client** - Request payment method update
   - **Retry Now** - Attempt charge again
   - **Cancel Autopay** - Require manual payment

### Credits & Adjustments

#### Applying a Credit

For overpayments, refunds, or goodwill:

1. Open client record
2. Go to **Credits** tab
3. Click **Add Credit**
4. Fill in:
   - **Amount**
   - **Reason** (Overpayment, Refund, Goodwill, Promo, Correction)
   - **Approval** (Master Admin approval required for Goodwill/Correction)
   - **Notes**
5. Click **Create Credit**

#### Using Credits

Credits automatically apply to next invoice or can be applied manually:

1. Open invoice
2. Click **Apply Credit**
3. Select credit amount to apply
4. Click **Apply**

**Important:** Credit ledger is immutable - entries cannot be edited or deleted.

---

## Document Management

### Folder Structure

Organize documents in folders:

1. Go to **Documents**
2. Click **New Folder**
3. Name folder (e.g., "Client Contracts", "2025 Q1 Reports")
4. Set permissions:
   - **Firm Only** - Internal documents
   - **Client Visible** - Shared with client portal
5. Click **Create**

### Uploading Documents

1. Navigate to folder
2. Click **Upload Document**
3. Select file(s) from computer
4. Fill in:
   - **Document Name** (auto-filled from filename)
   - **Description**
   - **Tags** (optional, for searching)
   - **Client** (if client-specific)
   - **Retention Policy** (see below)
5. Click **Upload**

**File size limit:** 100 MB per file

### Retention Policies

Automatic document retention:

- **Legal** - 7 years (contracts, legal docs)
- **Financial** - 7 years (invoices, financial records)
- **Standard** - 3 years (general business docs)
- **Short-term** - 1 year (temporary files)

System automatically flags documents for review/deletion when retention period expires.

### Legal Holds

Prevent deletion during litigation or investigation:

1. Open document
2. Click **Actions** → **Place Legal Hold**
3. Fill in:
   - **Reason** (Matter name, case number)
   - **Applied By** (your name)
4. Click **Confirm**

**Important:** Documents with legal hold CANNOT be deleted, even after retention period.

### Version Control

System automatically tracks document versions:

1. Open document
2. Click **Upload New Version**
3. Select updated file
4. Add **Version Notes** (what changed)
5. Click **Upload**

Previous versions remain accessible:
- Click **Versions** tab
- Download or view any previous version
- See who uploaded and when

### Sharing with Clients

1. Upload/select document
2. Check **Visible in Portal**
3. Select **Client** (if specific client)
4. Click **Save**

Document appears in client's portal under **Documents** section.

---

## Reports & Analytics

### Dashboard Reports

Quick reports on dashboard:

- **Revenue by Client** - Top revenue clients
- **Project Pipeline** - Projects by status
- **Team Utilization** - Billable hours percentage
- **Outstanding AR** - Unpaid invoices

### Time & Utilization Reports

1. Go to **Reports** → **Time & Utilization**
2. Configure:
   - **Date Range**
   - **Group By** (Team Member, Client, Project)
   - **Include Non-Billable** (yes/no)
3. Click **Generate**

Shows:
- Total hours worked
- Billable vs. non-billable breakdown
- Utilization rate per person
- Revenue per consultant

### Financial Reports

#### Revenue Report

1. Go to **Reports** → **Revenue**
2. Select:
   - **Date Range**
   - **Group By** (Month, Client, Engagement)
3. Click **Generate**

Shows:
- Total revenue
- Package vs. hourly breakdown
- Revenue by client
- Monthly trends

#### Accounts Receivable (AR) Aging

1. Go to **Reports** → **AR Aging**
2. Click **Generate**

Shows invoices by age:
- **Current** (not yet due)
- **1-30 days** overdue
- **31-60 days** overdue
- **61-90 days** overdue
- **90+ days** overdue

Use this to identify collection issues.

### Exporting Reports

All reports can be exported:

1. Generate report
2. Click **Export**
3. Choose format:
   - **PDF** - For printing/sharing
   - **CSV** - For Excel analysis
   - **Excel** - Native spreadsheet format
4. Click **Download**

---

## Settings & Configuration

### Firm Profile

Update firm information:

1. Go to **Settings** → **Firm Profile**
2. Update:
   - **Firm Name**
   - **Address**
   - **Phone** and **Email**
   - **Logo** (upload image)
   - **Website**
3. Click **Save**

### Billing Settings

Configure billing defaults:

1. Go to **Settings** → **Billing**
2. Set:
   - **Default Payment Terms** (Net 30, Net 15, etc.)
   - **Default Currency** (USD, EUR, GBP, etc.)
   - **Tax Rate** (if applicable)
   - **Invoice Numbering** (prefix, starting number)
   - **Invoice Footer** (payment instructions, notes)
3. Click **Save**

### Stripe Integration

Connect Stripe for online payments:

1. Go to **Settings** → **Integrations** → **Stripe**
2. Click **Connect Stripe Account**
3. Sign in to Stripe (or create account)
4. Authorize connection
5. Test mode:
   - Use for testing without real charges
   - Switch to live mode when ready for production
6. Click **Save**

### Email Notifications

Configure email preferences:

1. Go to **Settings** → **Notifications**
2. Set preferences for:
   - **Invoice Sent** - Notify client when invoice sent
   - **Payment Received** - Notify firm when payment received
   - **Project Updates** - Notify team of project changes
   - **Overdue Invoices** - Remind clients of overdue payments
3. Customize email templates (optional)
4. Click **Save**

### Audit Log Access

View all firm activity:

1. Go to **Settings** → **Audit Log**
2. Filter by:
   - **Date Range**
   - **Event Type** (Login, Create, Update, Delete, etc.)
   - **User**
   - **Resource** (Client, Project, Invoice, etc.)
3. Click **Search**

Useful for:
- Security audits
- Compliance requirements
- Troubleshooting issues
- Understanding who changed what

---

## Common Workflows

### Lead to Cash Flow

Complete workflow from first contact to payment:

1. **Lead created** (inbound inquiry or outbound prospecting)
2. **Qualify lead** → Convert to Prospect
3. **Move through pipeline** (Discovery → Proposal → Negotiation)
4. **Create proposal** and send to prospect
5. **Win deal** → Convert to Client
6. **Create engagement** with pricing terms
7. **Start project** with tasks and milestones
8. **Team logs time** on project tasks
9. **Approve time entries** (Firm Admin)
10. **Generate invoice** (automatic for package, manual for hourly)
11. **Send invoice** to client
12. **Receive payment** (autopay or manual)
13. **Close project** when complete

### Monthly Billing Routine

Recommended monthly process:

1. **Week 1: Review time entries**
   - Approve all pending time entries
   - Resolve any questions with team

2. **Week 2: Generate invoices**
   - Review auto-generated package invoices
   - Create manual hourly invoices
   - Add any expenses or adjustments

3. **Week 3: Send invoices**
   - Review all draft invoices
   - Send to clients (email + portal)
   - Follow up on previous month's overdue invoices

4. **Week 4: Process payments**
   - Record manual payments
   - Review autopay results
   - Follow up on failed payments
   - Generate AR aging report

---

## Getting Help

### Support Resources

- **Documentation:** [docs.consultantpro.com](https://docs.consultantpro.com)
- **Knowledge Base:** Searchable articles and FAQs
- **Video Tutorials:** Step-by-step video guides
- **Email Support:** support@consultantpro.com
- **Priority Support:** Available for enterprise plans

### Common Issues

**"I can't see a client"**
- Check your permissions (Settings → Team Members)
- Ensure you're assigned to that client
- Contact your Firm Admin

**"Invoice won't send"**
- Verify client email address is correct
- Check invoice is in draft status
- Ensure all required fields are filled

**"Autopay failed"**
- Client's payment method may be expired
- Contact client to update payment method
- Check Finance → Payment Failures for details

**"Can't upload document"**
- File may be too large (100 MB limit)
- Check file format is supported
- Ensure you have document upload permissions

---

## Security Best Practices

1. **Use strong passwords** (12+ characters, mix of types)
2. **Never share your login** with others
3. **Log out when done**, especially on shared computers
4. **Report suspicious activity** to your Firm Admin immediately
5. **Review audit logs** periodically
6. **Keep client data confidential** - don't share outside platform
7. **Use secure Wi-Fi** when accessing ConsultantPro remotely

---

**Need help?** Contact your firm's ConsultantPro administrator or reach out to support@consultantpro.com.

**Last Updated:** December 26, 2025
