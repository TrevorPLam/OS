# E-Signature Integration User Guide

## Overview

ConsultantPro integrates with DocuSign to provide electronic signature capabilities for proposals and contracts. This guide explains how to set up and use the e-signature integration.

**Key Benefits:**
- ✅ Legally binding electronic signatures
- ✅ Faster proposal acceptance process
- ✅ Automatic status tracking
- ✅ Complete audit trail
- ✅ Mobile-friendly signing experience
- ✅ Email notifications to signers

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [For Firm Administrators](#for-firm-administrators)
3. [For Firm Users](#for-firm-users)
4. [For Clients](#for-clients)
5. [FAQ](#faq)
6. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

To use the e-signature integration, you need:

1. **DocuSign Account** - Sign up at [docusign.com](https://www.docusign.com/)
2. **Firm Administrator Access** - Only firm administrators can connect DocuSign
3. **Active Proposals** - Have proposals ready to send for signature

### Quick Start

1. Administrator connects DocuSign account (one-time setup)
2. Create and send proposals as usual
3. Client accepts proposal → DocuSign envelope created automatically
4. Client receives email from DocuSign to sign
5. Client signs electronically
6. Proposal status updates to "Accepted" automatically

---

## For Firm Administrators

### Connecting DocuSign

**Step 1: Access Integration Settings**
1. Log in to ConsultantPro
2. Navigate to **Settings** → **Integrations** → **E-Signature**
3. Click **"Connect DocuSign"**

**Step 2: Authorize DocuSign**
1. You'll be redirected to DocuSign's authorization page
2. Log in with your DocuSign credentials
3. Review the requested permissions:
   - Send envelopes
   - View envelope status
   - Access your account information
4. Click **"Allow Access"**

**Step 3: Confirmation**
1. You'll be redirected back to ConsultantPro
2. See confirmation message: "DocuSign connection created successfully"
3. Connection is now active for your entire firm

**Important Notes:**
- Only one DocuSign account can be connected per firm
- All firm users will use this connection
- The connection uses your DocuSign account for sending limits and branding

### Monitoring the Integration

**View Connection Status**
1. Go to **Admin** → **E-Signature** → **DocuSign Connections**
2. View connection details:
   - Account name and ID
   - Connection status (Active/Inactive)
   - Last sync time
   - Any error messages

**View Envelope History**
1. Go to **Admin** → **E-Signature** → **Envelopes**
2. See all envelopes sent:
   - Envelope ID
   - Linked proposal/contract
   - Current status
   - Recipient information
   - Sent/signed/completed timestamps

**View Webhook Events (Advanced)**
1. Go to **Admin** → **E-Signature** → **Webhook Events**
2. See all status updates received from DocuSign
3. Useful for debugging if status updates aren't working

### Disconnecting DocuSign

**When to Disconnect:**
- Switching to a different DocuSign account
- DocuSign credentials compromised
- No longer need e-signature functionality

**How to Disconnect:**
1. Go to **Admin** → **E-Signature** → **DocuSign Connections**
2. Click on your connection
3. Click **"Disconnect"**
4. Connection will be marked inactive (historical data preserved)

**Reconnecting:**
- Follow the "Connecting DocuSign" steps above
- Old envelopes remain linked to old connection
- New envelopes use new connection

### Configuration Options

**Environment Variables (Developer/DevOps)**

For production deployment, configure:

```bash
DOCUSIGN_CLIENT_ID=your_client_id_here
DOCUSIGN_CLIENT_SECRET=your_client_secret_here
DOCUSIGN_REDIRECT_URI=https://yourapp.com/api/v1/esignature/docusign/callback/
DOCUSIGN_WEBHOOK_SECRET=your_webhook_secret_here
DOCUSIGN_ENVIRONMENT=production  # or "sandbox" for testing
```

**DocuSign Developer Settings**

1. Create integration key in [DocuSign Admin](https://admindemo.docusign.com/)
2. Set redirect URI to match your application
3. Configure webhook URL: `https://yourapp.com/webhooks/docusign/webhook/`
4. Enable events: sent, delivered, signed, completed, declined, voided

---

## For Firm Users

### Sending Proposals for Signature

**The Process:**
1. Create proposal as usual in ConsultantPro
2. Mark proposal as **"Sent"** to client
3. Client receives proposal via email/portal
4. When ready, client clicks **"Accept Proposal"**
5. System automatically:
   - Creates DocuSign envelope
   - Sends email to client with signing link
   - Updates proposal status to "Pending Signature"

**What Happens Next:**
- Client receives email from DocuSign (noreply@docusign.net)
- Client clicks "Review Document" in email
- Client signs electronically
- Proposal status updates to "Accepted" automatically
- You receive notification of acceptance

### Tracking Signature Status

**View Proposal Status:**
1. Go to **Proposals** in navigation
2. Find your proposal
3. Status shows:
   - **Sent** - Waiting for client to accept
   - **Pending Signature** - DocuSign envelope sent
   - **Accepted** - Client signed successfully
   - **Declined** - Client declined to sign
   - **Voided** - Envelope was cancelled

**View Envelope Details:**
1. Go to proposal detail page
2. See "E-Signature" section with:
   - Envelope ID
   - Current status
   - Sent date
   - Signed date (if completed)
   - Link to view in DocuSign (admin only)

### Handling Issues

**Client Didn't Receive Email:**
1. Check spam/junk folder
2. Verify client email address is correct
3. Resend from DocuSign admin console
4. Alternative: Use embedded signing (coming soon)

**Need to Cancel Envelope:**
1. Go to **Admin** → **E-Signature** → **Envelopes**
2. Find the envelope
3. Click **"Void"**
4. Enter reason for voiding
5. Envelope will be cancelled in DocuSign

**Client Needs to Sign Again:**
1. Void the existing envelope
2. Have client click "Accept Proposal" again
3. New envelope will be created

---

## For Clients

### Receiving a Proposal for Signature

**Email from DocuSign:**
You'll receive an email with subject: "Please sign proposal [NUMBER]"

**Email Contents:**
- Sender: noreply@docusign.net (or your firm's custom domain)
- Subject: Please sign proposal [proposal number]
- Message: From your consulting firm
- Button: "Review Document"

**Important:**
- This is a legitimate email from DocuSign
- Email may go to spam - check your junk folder
- Link expires after 120 days (default)

### Signing the Document

**Step 1: Open Document**
1. Click **"Review Document"** in email
2. DocuSign opens in your browser
3. Document loads (may take a few seconds)

**Step 2: Review Proposal**
1. Read through the entire proposal
2. Scroll to see all pages
3. Look for yellow "Sign Here" tags

**Step 3: Sign**
1. Click on each "Sign Here" tag
2. Choose signature style:
   - Type your name
   - Draw with mouse/finger
   - Upload signature image
3. Click **"Adopt and Sign"**
4. Initial if required
5. Fill any other required fields

**Step 4: Finish**
1. Click **"Finish"** button
2. Confirmation page appears
3. You'll receive email confirmation
4. Proposal status updates in ConsultantPro automatically

### Mobile Signing

**On Phone/Tablet:**
- Click email link on mobile device
- DocuSign opens in mobile browser
- Interface optimized for touch
- Can draw signature with finger
- Same steps as desktop

**DocuSign Mobile App:**
- Download DocuSign app (iOS/Android)
- Sign in with your email
- Envelopes appear in app
- Better mobile experience

### After Signing

**What You'll Receive:**
1. Email confirmation from DocuSign
2. PDF copy of signed document (attached to email)
3. Certificate of completion

**In ConsultantPro:**
1. Proposal status changes to "Accepted"
2. Project setup begins
3. Contract may be sent for signature next

### Need Help?

**Common Questions:**

**Q: I can't find the email**
- Check spam/junk folder
- Search for "docusign.net"
- Contact your consultant for resend

**Q: Link says expired**
- Contact your consultant
- They can resend the proposal
- New signing link will be sent

**Q: I made a mistake**
- Contact your consultant immediately
- They can void the envelope
- You can sign a new one

**Q: Can I sign later?**
- Yes, link stays active for 120 days
- You can close browser and return
- Just click the email link again

---

## FAQ

### General Questions

**Q: Is DocuSign legally binding?**
A: Yes, DocuSign complies with the ESIGN Act and eIDAS regulation, making electronic signatures legally binding in most jurisdictions.

**Q: How secure is DocuSign?**
A: DocuSign uses bank-level security with 256-bit SSL encryption. All signatures are authenticated and audited.

**Q: Can I use my own DocuSign account?**
A: Administrators connect one DocuSign account for the entire firm. Personal accounts cannot be used.

**Q: Does this cost extra?**
A: Depends on your DocuSign plan. Most plans include envelopes, but check your DocuSign account for limits.

### For Administrators

**Q: Can I use DocuSign sandbox for testing?**
A: Yes, set `DOCUSIGN_ENVIRONMENT=sandbox` environment variable and use sandbox credentials.

**Q: What happens if we disconnect DocuSign?**
A: New envelopes cannot be sent, but historical data and old envelopes remain accessible.

**Q: Can we use multiple DocuSign accounts?**
A: No, only one connection per firm. Disconnect old account first, then connect new one.

**Q: How are envelopes counted?**
A: Each "Accept Proposal" action creates one envelope, counted against your DocuSign plan limit.

### For Users

**Q: Can I track who signed?**
A: Yes, envelope details show recipient information and signing timestamps.

**Q: Can I resend a signing request?**
A: Void the envelope and have the client accept the proposal again to create a new envelope.

**Q: What if client doesn't have DocuSign account?**
A: No account needed! Signers can sign via email link without creating a DocuSign account.

### For Clients

**Q: Do I need a DocuSign account?**
A: No, you can sign via email link without creating an account.

**Q: Is my signature secure?**
A: Yes, DocuSign uses multiple verification methods and provides a complete audit trail.

**Q: Can I download the signed document?**
A: Yes, you receive a PDF copy by email after signing.

**Q: Can multiple people sign?**
A: Depends on how the proposal is configured. Contact your consultant for details.

---

## Troubleshooting

### Administrator Issues

**Issue: OAuth connection fails**
- **Check:** Client ID and secret are correct
- **Check:** Redirect URI matches exactly (trailing slash matters)
- **Try:** Use sandbox environment first to test
- **Solution:** Verify credentials in DocuSign admin console

**Issue: "No active connection" error**
- **Check:** Connection status in admin (should be "Active")
- **Solution:** Reconnect DocuSign if connection inactive

**Issue: Webhook events not processed**
- **Check:** Webhook URL configured in DocuSign
- **Check:** `DOCUSIGN_WEBHOOK_SECRET` matches DocuSign config
- **Check:** HTTPS enabled on webhook endpoint
- **Solution:** Reconfigure webhook in DocuSign admin

**Issue: Token expired errors**
- **Check:** Last sync time (should refresh automatically)
- **Try:** Make any API call to trigger refresh
- **Solution:** Disconnect and reconnect if persistent

### User Issues

**Issue: Envelope creation fails**
- **Check:** DocuSign connection is active
- **Check:** Proposal is in "sent" or "under_review" status
- **Check:** DocuSign account has available envelopes
- **Solution:** Contact administrator if problem persists

**Issue: Client reports not receiving email**
- **Check:** Client email address is correct
- **Check:** Client's spam/junk folder
- **Try:** View envelope in DocuSign admin and resend
- **Alternative:** Use embedded signing (when available)

**Issue: Status not updating**
- **Check:** Webhook events in admin (should show recent events)
- **Wait:** Updates may take 1-2 minutes
- **Solution:** Check webhook configuration if persistent

### Client Issues

**Issue: "Document not found" error**
- **Cause:** Envelope was voided or expired
- **Solution:** Contact consultant to resend

**Issue: Can't click signature field**
- **Try:** Different browser (Chrome/Safari recommended)
- **Try:** Clear browser cache
- **Try:** Mobile device instead
- **Solution:** Contact consultant if blocked

**Issue: Signature won't save**
- **Try:** Use "Draw" instead of "Type"
- **Try:** Refresh page and try again
- **Check:** JavaScript enabled in browser
- **Solution:** Try DocuSign mobile app

---

## Support

### Getting Help

**For Administrators:**
- Check Admin → E-Signature sections for status
- Review webhook events for errors
- Contact platform support with envelope IDs

**For Users:**
- Contact firm administrator
- Provide proposal number and error message
- Administrator can check envelope details

**For Clients:**
- Contact your consulting firm
- Provide proposal number
- Your consultant can resend if needed

### Contact

- **Platform Support:** support@consultantpro.com
- **DocuSign Support:** [docusign.com/support](https://www.docusign.com/support)
- **Documentation:** This guide and Sprint 4 Implementation Summary

---

## Additional Resources

- [DocuSign Help Center](https://support.docusign.com/)
- [DocuSign Video Tutorials](https://www.docusign.com/trust/compliance/global-e-signature-legality)
- [E-Signature Legality Guide](https://www.docusign.com/trust/compliance/global-e-signature-legality)
- [Sprint 4 Implementation Summary](SPRINT_4_IMPLEMENTATION_SUMMARY.md) (Technical details)
- [ADR-004: Provider Selection](05-decisions/ADR-004-esignature-provider-selection.md)

---

**Last Updated:** January 1, 2026  
**Version:** 1.0  
**Sprint:** 4 - E-Signature Integration
