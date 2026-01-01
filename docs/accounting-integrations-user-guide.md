# Accounting Integrations User Guide

## Overview

ConsultantPro integrates with popular accounting platforms to streamline your financial workflows. This guide explains how to connect and use QuickBooks Online or Xero with your ConsultantPro account.

**Supported Accounting Platforms:**
- QuickBooks Online
- Xero

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Connecting QuickBooks Online](#connecting-quickbooks-online)
3. [Connecting Xero](#connecting-xero)
4. [Syncing Invoices](#syncing-invoices)
5. [Syncing Payments](#syncing-payments)
6. [Syncing Customers](#syncing-customers)
7. [Managing Connections](#managing-connections)
8. [Troubleshooting](#troubleshooting)
9. [FAQs](#faqs)

---

## Getting Started

### What Gets Synced?

The accounting integration synchronizes three types of data:

1. **Invoices** (ConsultantPro → Accounting System)
   - Push invoices from ConsultantPro to your accounting platform
   - Keeps your accounting records up-to-date with client billing

2. **Payments** (Accounting System → ConsultantPro)
   - Pull payment records from your accounting platform
   - Automatically updates invoice status when payments are recorded

3. **Customers/Contacts** (Bidirectional)
   - Sync client information between systems
   - Ensures consistent customer records

### Prerequisites

Before connecting an accounting platform:

- ✅ You must be a Firm Admin or Master Admin
- ✅ You need active QuickBooks Online or Xero account
- ✅ You have permission to authorize apps in your accounting platform

---

## Connecting QuickBooks Online

### Step 1: Initiate Connection

1. Navigate to **Settings** → **Integrations** → **Accounting**
2. Click **Connect QuickBooks Online**
3. You'll be redirected to the QuickBooks authorization page

### Step 2: Authorize Access

1. Sign in to your QuickBooks Online account
2. Select the company you want to connect
3. Review the permissions requested:
   - Read and manage customers
   - Read and manage invoices
   - Read payment information
4. Click **Authorize**

### Step 3: Complete Setup

1. You'll be redirected back to ConsultantPro
2. Your connection will be automatically saved
3. You'll see a success message confirming the connection

**Connection Settings:**
- **Company Name:** Displays the connected QuickBooks company
- **Status:** Should show "Active"
- **Last Sync:** Shows when data was last synchronized

---

## Connecting Xero

### Step 1: Initiate Connection

1. Navigate to **Settings** → **Integrations** → **Accounting**
2. Click **Connect Xero**
3. You'll be redirected to the Xero authorization page

### Step 2: Authorize Access

1. Sign in to your Xero account
2. Select the organization you want to connect
3. Review the permissions requested:
   - Access to accounting transactions
   - Access to contacts
   - Access to organization settings
4. Click **Allow access**

### Step 3: Complete Setup

1. You'll be redirected back to ConsultantPro
2. Select the Xero organization (if you have multiple)
3. Your connection will be automatically saved
4. You'll see a success message confirming the connection

**Connection Settings:**
- **Organization Name:** Displays the connected Xero organization
- **Status:** Should show "Active"
- **Last Sync:** Shows when data was last synchronized

---

## Syncing Invoices

### Automatic vs. Manual Sync

**Manual Sync (Recommended):**
- Gives you control over when invoices are sent to accounting
- Allows you to review invoices before syncing
- Prevents accidental duplication

**Future Feature:** Automatic background sync will be available in a future release.

### How to Sync an Invoice

1. Navigate to **Finance** → **Invoices**
2. Find the invoice you want to sync
3. Click **Actions** → **Sync to [Accounting Platform]**
4. Confirm the sync operation
5. Wait for confirmation

**What Happens:**
- Invoice is created in your accounting platform
- Customer is automatically synced if not already present
- Invoice number and ID are stored for tracking
- Invoice status remains synchronized

**Important Notes:**
- ⚠️ Once synced, invoices cannot be edited in ConsultantPro
- ⚠️ Make all changes in your accounting platform
- ⚠️ Invoices are only created once (no updates)

### Viewing Sync Status

In the invoice list, you'll see:
- **✓ Synced** - Invoice successfully synced
- **⏳ Pending** - Sync in progress
- **✗ Error** - Sync failed (click for details)
- **—** - Not yet synced

---

## Syncing Payments

### How It Works

Payment sync pulls payment records from your accounting platform and automatically updates invoice status in ConsultantPro.

### How to Sync Payments

**Option 1: Sync All Payments**
1. Navigate to **Settings** → **Integrations** → **Accounting**
2. Find your connected accounting platform
3. Click **Sync Payments**
4. Wait for sync to complete

**Option 2: Schedule Automatic Sync**
- Future feature: Configure automatic payment sync frequency

### What Happens

For each payment in your accounting system:
1. ConsultantPro finds the matching invoice
2. Updates invoice status to "Paid"
3. Records the payment date
4. Displays payment information

**Payment Statuses:**
- **Paid** - Full payment received
- **Partial** - Partial payment received
- **Sent** - Invoice sent, no payment yet
- **Overdue** - Past due date, no payment

---

## Syncing Customers

### When to Sync Customers

Customers are automatically synced when you:
- Sync an invoice for a new customer
- Manually trigger customer sync

### How to Manually Sync a Customer

1. Navigate to **Clients** → **Client List**
2. Find the client you want to sync
3. Click **Actions** → **Sync to [Accounting Platform]**
4. Confirm the sync operation
5. Wait for confirmation

### What Gets Synced

**Customer Information:**
- Name
- Email address
- Phone number (if available)
- Billing address (if available)

**Note:** Additional custom fields may not sync automatically.

### Bidirectional Sync

Customer sync is bidirectional:
- **Create:** New customers can be created in either system
- **Update:** Changes made in either system can be synced
- **Merge:** Existing customers are updated, not duplicated

---

## Managing Connections

### Viewing Connection Status

1. Navigate to **Settings** → **Integrations** → **Accounting**
2. View your connected accounting platforms

**Status Indicators:**
- 🟢 **Active** - Connection working normally
- 🟡 **Expired** - Token needs refresh (reconnect)
- 🔴 **Error** - Connection issue (see error message)
- ⚫ **Revoked** - Connection removed

### Connection Settings

Click **Settings** on your connection to configure:

- **Enable/Disable Sync**
  - Toggle synchronization on/off
  - Useful for temporary pause

- **Invoice Sync**
  - Enable/disable invoice synchronization
  - Default: Enabled

- **Payment Sync**
  - Enable/disable payment synchronization
  - Default: Enabled

- **Customer Sync**
  - Enable/disable customer synchronization
  - Default: Enabled

### Disconnecting

To disconnect your accounting platform:

1. Navigate to **Settings** → **Integrations** → **Accounting**
2. Find your connected platform
3. Click **Disconnect**
4. Confirm the disconnection

**Warning:** 
- ⚠️ Disconnecting removes the connection permanently
- ⚠️ Existing sync mappings are preserved but no longer updated
- ⚠️ You can reconnect at any time

### Reconnecting

If your connection expires or you disconnect:

1. Follow the connection steps again
2. Authorize the app
3. Your previous sync mappings will be restored
4. Continue syncing from where you left off

---

## Troubleshooting

### Connection Issues

**Problem:** Can't connect to accounting platform

**Solutions:**
- ✓ Check your internet connection
- ✓ Ensure you have an active account with the accounting platform
- ✓ Verify you have admin permissions
- ✓ Try clearing browser cache and reconnecting
- ✓ Contact support if issue persists

---

**Problem:** Connection shows "Expired" status

**Solution:**
- Tokens expire after a period of inactivity
- Simply reconnect to refresh the token
- Your sync mappings will be preserved

---

### Invoice Sync Issues

**Problem:** Invoice sync fails with "Customer not found"

**Solution:**
- The customer must be synced before the invoice
- Sync the customer manually first
- Then retry invoice sync

---

**Problem:** Invoice shows as "Not Synced" but I synced it

**Solution:**
- Check the sync status in the invoice details
- Look for error messages
- Retry the sync operation
- Contact support if issue persists

---

**Problem:** Can't edit invoice after syncing

**Explanation:**
- This is by design (accounting best practice)
- Once synced, invoices are locked in ConsultantPro
- Make all changes in your accounting platform
- Changes won't sync back automatically

---

### Payment Sync Issues

**Problem:** Payment recorded but invoice still shows "Sent"

**Solutions:**
- ✓ Trigger manual payment sync
- ✓ Wait a few minutes and check again
- ✓ Verify payment is linked to correct invoice in accounting platform
- ✓ Check sync error messages

---

**Problem:** Wrong invoice marked as paid

**Solution:**
- This usually indicates incorrect invoice mapping
- Contact support to review and fix mappings
- Don't manually change invoice status

---

### Customer Sync Issues

**Problem:** Customer sync creates duplicate

**Solution:**
- Check if customer already exists in accounting platform
- Use the existing customer ID
- Contact support to merge duplicates

---

**Problem:** Customer information doesn't match

**Solution:**
- Customer sync is one-way on each sync
- Last sync wins
- Update customer in the system you want as "source of truth"
- Then sync again

---

## FAQs

### General Questions

**Q: Can I connect multiple accounting platforms?**

A: Currently, you can connect one QuickBooks OR one Xero account per firm. You cannot connect both simultaneously.

---

**Q: Does this work with QuickBooks Desktop?**

A: No, only QuickBooks Online is supported. QuickBooks Desktop uses a different API.

---

**Q: Is my data secure?**

A: Yes. All OAuth tokens are encrypted at rest. We follow industry-standard security practices. See our [Security Policy](../SECURITY.md) for details.

---

**Q: Can multiple users connect the same accounting platform?**

A: Only one connection per firm per platform is allowed. All users in the firm will use the same connection.

---

### Sync Questions

**Q: How often does data sync?**

A: Currently, all syncs are manual. Automatic background sync will be available in a future release.

---

**Q: Can I sync old invoices?**

A: Yes, you can sync any invoice that hasn't been synced yet. Once synced, it cannot be synced again.

---

**Q: What happens if I delete an invoice in accounting platform?**

A: The invoice in ConsultantPro remains unchanged. We don't sync deletions.

---

**Q: Can I unsync an invoice?**

A: No, once synced, the mapping is permanent. You can delete the invoice in your accounting platform directly if needed.

---

**Q: Do recurring invoices sync automatically?**

A: No, each invoice must be synced individually. Automatic recurring invoice sync will be considered for a future release.

---

### Billing Questions

**Q: Is there an extra charge for this feature?**

A: Check your ConsultantPro plan details. Accounting integrations are included in Professional and Enterprise plans.

---

**Q: Does this count towards my QuickBooks/Xero user limit?**

A: No, API connections don't count as user seats in your accounting platform.

---

### Technical Questions

**Q: What API version is used?**

A: We use:
- QuickBooks Online API v3
- Xero Accounting API 2.0

---

**Q: Are webhooks supported?**

A: Not yet. Webhook support for real-time sync is planned for a future release.

---

**Q: Can I build custom integrations using your API?**

A: Yes, see our [API Documentation](../03-reference/api-usage.md) for details on available endpoints.

---

## Getting Help

### Support Resources

- 📚 **Documentation:** https://yourapp.com/docs
- 💬 **Community Forum:** https://community.yourapp.com
- 📧 **Email Support:** support@yourapp.com
- 🎫 **Submit Ticket:** https://support.yourapp.com

### Reporting Issues

When reporting accounting integration issues, please include:

1. Your firm ID
2. Accounting platform (QuickBooks or Xero)
3. Connection status
4. Specific invoice/customer ID (if applicable)
5. Error message (if any)
6. Steps to reproduce

### Feature Requests

Have ideas for improving accounting integrations?

- Submit feature requests in the community forum
- Vote on existing requests
- Participate in beta testing programs

---

## What's Next?

Check out these related guides:

- [Finance Module Guide](../06-user-guides/finance-guide.md) - Managing invoices and billing
- [Client Management Guide](../06-user-guides/client-guide.md) - Working with clients
- [Project Management Guide](../06-user-guides/project-guide.md) - Tracking project financials

**Coming Soon:**
- Automatic background sync
- Webhook support for real-time updates
- Additional accounting platform integrations (FreshBooks, Wave, Sage)
- Advanced sync options and filters
- Reconciliation reporting

---

*Last Updated: January 1, 2026*
