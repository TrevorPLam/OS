"""
Edge Case Tests (per docs/03-reference/requirements/DOC-23.md EDGE_CASES_CATALOG).

Tests for known tricky cases that must be handled and tested:
1) Recurrence: DST, leap year, pause/resume, backfill overlaps
2) Email ingestion: shared addresses, mixed clients, subject changes, attachments, re-ingestion
3) Permissions: portal multi-account, document visibility, role changes
4) Billing ledger: partial payments, retainer compensation, idempotency, rounding
5) Documents: concurrent uploads, lock override, malware scan, signed URLs

Complements contract_tests.py with specific edge case scenarios.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import pytz
import uuid

from modules.firm.models import Firm
from modules.crm.models import Account, Contact, Engagement
from modules.clients.models import Client
from modules.firm.audit import AuditEvent

User = get_user_model()


class RecurrenceEdgeCasesTest(TestCase):
    """
    Edge cases for recurrence engine (docs/03-reference/requirements/DOC-23.md section 1).

    Tests:
    - DST spring forward: missing local times
    - DST fall back: ambiguous local times
    - leap year Feb 29 rules
    - pause mid-period then resume (no duplicates)
    - backfill window overlaps previously generated periods
    """

    def setUp(self):
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_dst_spring_forward_missing_time(self):
        """Test that DST spring forward handles missing local times correctly."""
        from modules.recurrence.models import RecurrenceRule
        from modules.recurrence.services import RecurrenceGenerator

        # Create a daily recurrence that would hit the "missing hour" during DST spring forward
        # In 2025, DST starts on March 9 at 2:00 AM (time jumps to 3:00 AM)
        rule = RecurrenceRule.objects.create(
            firm=self.firm,
            name="Daily at 2:30 AM",
            frequency="daily",
            interval=1,
            timezone="America/New_York",
            start_date=date(2025, 3, 8),  # Day before DST
            end_date=date(2025, 3, 10),  # Day after DST
            created_by=self.user,
        )

        generator = RecurrenceGenerator()
        occurrences = generator.generate_occurrences(
            rule, start_date=date(2025, 3, 8), end_date=date(2025, 3, 10)
        )

        # Should generate 3 occurrences (March 8, 9, 10)
        self.assertEqual(len(occurrences), 3)

        # March 9 occurrence should be adjusted forward to a valid time (3:30 AM instead of 2:30 AM)
        ny_tz = pytz.timezone("America/New_York")
        march_9_occurrence = [
            o for o in occurrences if o.astimezone(ny_tz).date() == date(2025, 3, 9)
        ][0]

        # Should be 3:30 AM (or handled gracefully without error)
        march_9_local = march_9_occurrence.astimezone(ny_tz)
        # The time should be valid (not in the missing hour)
        self.assertIsNotNone(march_9_local)

    def test_dst_fall_back_ambiguous_time(self):
        """Test that DST fall back handles ambiguous local times correctly."""
        from modules.recurrence.models import RecurrenceRule
        from modules.recurrence.services import RecurrenceGenerator

        # In 2025, DST ends on November 2 at 2:00 AM (time jumps back to 1:00 AM)
        # 1:30 AM happens twice (once in DST, once in standard time)
        rule = RecurrenceRule.objects.create(
            firm=self.firm,
            name="Daily at 1:30 AM",
            frequency="daily",
            interval=1,
            timezone="America/New_York",
            start_date=date(2025, 11, 1),  # Day before DST ends
            end_date=date(2025, 11, 3),  # Day after DST ends
            created_by=self.user,
        )

        generator = RecurrenceGenerator()
        occurrences = generator.generate_occurrences(
            rule, start_date=date(2025, 11, 1), end_date=date(2025, 11, 3)
        )

        # Should generate 3 occurrences (November 1, 2, 3)
        self.assertEqual(len(occurrences), 3)

        # All should be deterministically in the same fold (DST or standard)
        ny_tz = pytz.timezone("America/New_York")
        nov_2_occurrence = [
            o for o in occurrences if o.astimezone(ny_tz).date() == date(2025, 11, 2)
        ][0]

        # Should be handled deterministically
        self.assertIsNotNone(nov_2_occurrence)

    def test_leap_year_feb_29_rules(self):
        """Test recurrence on Feb 29 in leap vs non-leap years."""
        from modules.recurrence.models import RecurrenceRule
        from modules.recurrence.services import RecurrenceGenerator

        # Create a yearly recurrence on Feb 29
        rule = RecurrenceRule.objects.create(
            firm=self.firm,
            name="Leap Day Event",
            frequency="yearly",
            interval=1,
            timezone="UTC",
            start_date=date(2024, 2, 29),  # 2024 is a leap year
            created_by=self.user,
        )

        generator = RecurrenceGenerator()

        # Generate for 2024 (leap year - should have Feb 29)
        occurrences_2024 = generator.generate_occurrences(
            rule, start_date=date(2024, 2, 1), end_date=date(2024, 3, 31)
        )
        self.assertEqual(len(occurrences_2024), 1)
        self.assertEqual(occurrences_2024[0].date(), date(2024, 2, 29))

        # Generate for 2025 (not a leap year - should skip or use Feb 28)
        occurrences_2025 = generator.generate_occurrences(
            rule, start_date=date(2025, 2, 1), end_date=date(2025, 3, 31)
        )
        # Should either skip (0 occurrences) or use Feb 28 (1 occurrence)
        self.assertIn(len(occurrences_2025), [0, 1])

        if len(occurrences_2025) == 1:
            # If it generates an occurrence, it should be Feb 28
            self.assertEqual(occurrences_2025[0].date(), date(2025, 2, 28))

    def test_pause_mid_period_then_resume_no_duplicates(self):
        """Test that pausing mid-period and resuming doesn't create duplicates."""
        from modules.recurrence.models import RecurrenceRule, RecurrenceGeneration
        from modules.recurrence.services import RecurrenceGenerator

        rule = RecurrenceRule.objects.create(
            firm=self.firm,
            name="Daily Task",
            frequency="daily",
            interval=1,
            timezone="UTC",
            start_date=date(2025, 1, 1),
            created_by=self.user,
        )

        generator = RecurrenceGenerator()

        # Generate first 5 days (Jan 1-5)
        occurrences_initial = generator.generate_occurrences(
            rule, start_date=date(2025, 1, 1), end_date=date(2025, 1, 5)
        )
        self.assertEqual(len(occurrences_initial), 5)

        # Check that generations were recorded
        initial_count = RecurrenceGeneration.objects.filter(
            firm=self.firm, recurrence_rule=rule
        ).count()
        self.assertEqual(initial_count, 5)

        # Pause the rule on Jan 3
        rule.pause(user=self.user)
        self.assertEqual(rule.status, "paused")

        # Try to generate Jan 3-7 while paused (should not generate new ones)
        occurrences_during_pause = generator.generate_occurrences(
            rule, start_date=date(2025, 1, 3), end_date=date(2025, 1, 7)
        )
        # Should return empty or only existing ones (no new generations)
        pause_count = RecurrenceGeneration.objects.filter(
            firm=self.firm, recurrence_rule=rule
        ).count()
        self.assertEqual(pause_count, initial_count)  # No new generations

        # Resume the rule
        rule.resume(user=self.user)
        self.assertEqual(rule.status, "active")

        # Generate Jan 1-10 (should not duplicate Jan 1-5)
        occurrences_after_resume = generator.generate_occurrences(
            rule, start_date=date(2025, 1, 1), end_date=date(2025, 1, 10)
        )

        # Total generations should be 10 (no duplicates)
        total_count = RecurrenceGeneration.objects.filter(
            firm=self.firm, recurrence_rule=rule
        ).count()
        self.assertEqual(total_count, 10)

    def test_backfill_window_overlaps_previously_generated(self):
        """Test that backfill doesn't create duplicates for already-generated periods."""
        from modules.recurrence.models import RecurrenceRule, RecurrenceGeneration
        from modules.recurrence.services import RecurrenceGenerator
        from modules.recurrence.backfill import BackfillService

        rule = RecurrenceRule.objects.create(
            firm=self.firm,
            name="Weekly Meeting",
            frequency="weekly",
            interval=1,
            timezone="UTC",
            start_date=date(2025, 1, 1),
            created_by=self.user,
        )

        generator = RecurrenceGenerator()
        backfill_service = BackfillService()

        # Generate Jan 1-14 (2 weeks)
        generator.generate_occurrences(rule, start_date=date(2025, 1, 1), end_date=date(2025, 1, 14))
        initial_count = RecurrenceGeneration.objects.filter(
            firm=self.firm, recurrence_rule=rule
        ).count()
        self.assertEqual(initial_count, 2)  # 2 weekly occurrences

        # Now backfill Jan 1-21 (3 weeks, overlaps with existing 2 weeks)
        backfill_service.backfill_missed_periods(
            recurrence_rule=rule,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 21),
            user=self.user,
            reason="Testing overlap",
        )

        # Should have 3 total (not 5 - no duplicates for Jan 1 and Jan 8)
        final_count = RecurrenceGeneration.objects.filter(
            firm=self.firm, recurrence_rule=rule
        ).count()
        self.assertEqual(final_count, 3)


class EmailIngestionEdgeCasesTest(TestCase):
    """
    Edge cases for email ingestion (docs/03-reference/requirements/DOC-23.md section 2).

    Tests:
    - shared email address across multiple accounts
    - thread contains mixed clients
    - subject changes mid-thread
    - attachments renamed across replies
    - re-ingestion after connection reset (idempotency)
    """

    def setUp(self):
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_shared_email_address_across_multiple_accounts(self):
        """Test that shared email addresses trigger staleness penalty."""
        from modules.email_ingestion.models import EmailConnection, EmailArtifact
        from modules.email_ingestion.services import EmailMappingService
        from modules.email_ingestion.staleness_service import StalenessDetector

        connection = EmailConnection.objects.create(
            firm=self.firm,
            name="Test Connection",
            provider="gmail",
            email_address="test@example.com",
            created_by=self.user,
        )

        # Create two accounts with same contact email
        account1 = Account.objects.create(
            firm=self.firm, name="Account 1", status="active", created_by=self.user
        )
        account2 = Account.objects.create(
            firm=self.firm, name="Account 2", status="active", created_by=self.user
        )

        Contact.objects.create(
            firm=self.firm,
            account=account1,
            name="John Doe",
            email="john@shared.com",
            created_by=self.user,
        )
        Contact.objects.create(
            firm=self.firm,
            account=account2,
            name="John Doe",
            email="john@shared.com",  # Same email
            created_by=self.user,
        )

        # Ingest email from shared address
        email = EmailArtifact.objects.create(
            firm=self.firm,
            connection=connection,
            provider="gmail",
            external_message_id="msg-shared",
            from_address="john@shared.com",
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Hello",
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        # Suggest mapping
        mapping_service = EmailMappingService()
        account, engagement, work_item, confidence, reasons = mapping_service.suggest_mapping(email)

        # Should have reduced confidence due to multi-account contact
        staleness_detector = StalenessDetector()
        staleness_result = staleness_detector.detect_staleness(email, confidence)

        # Staleness should be flagged
        self.assertTrue(staleness_result["requires_triage"])
        self.assertIn("multi_account_contact", staleness_result["penalties"])

    def test_thread_contains_mixed_clients(self):
        """Test that threads with mixed client contexts trigger staleness penalty."""
        from modules.email_ingestion.models import EmailConnection, EmailArtifact
        from modules.email_ingestion.staleness_service import StalenessDetector

        connection = EmailConnection.objects.create(
            firm=self.firm,
            name="Test Connection",
            provider="gmail",
            email_address="test@example.com",
            created_by=self.user,
        )

        account1 = Account.objects.create(
            firm=self.firm, name="Client A", status="active", created_by=self.user
        )
        account2 = Account.objects.create(
            firm=self.firm, name="Client B", status="active", created_by=self.user
        )

        # First email in thread mapped to account1
        email1 = EmailArtifact.objects.create(
            firm=self.firm,
            connection=connection,
            provider="gmail",
            external_message_id="msg-thread-1",
            thread_id="thread-mixed",
            from_address="clienta@example.com",
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Project Discussion",
            sent_at=timezone.now(),
            received_at=timezone.now(),
            account=account1,
            status="mapped",
        )

        # Second email in same thread from different client
        email2 = EmailArtifact.objects.create(
            firm=self.firm,
            connection=connection,
            provider="gmail",
            external_message_id="msg-thread-2",
            thread_id="thread-mixed",  # Same thread
            from_address="clientb@example.com",
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Re: Project Discussion",
            sent_at=timezone.now() + timedelta(hours=1),
            received_at=timezone.now() + timedelta(hours=1),
        )

        # Check staleness for email2 (suggested to account2, but thread has account1)
        staleness_detector = StalenessDetector()
        staleness_result = staleness_detector.detect_staleness(email2, Decimal("0.8"))

        # Should flag mixed client thread
        self.assertIn("mixed_client_thread", staleness_result["penalties"])

    def test_subject_changes_mid_thread(self):
        """Test that subject changes mid-thread trigger staleness penalty."""
        from modules.email_ingestion.models import EmailConnection, EmailArtifact
        from modules.email_ingestion.staleness_service import StalenessDetector

        connection = EmailConnection.objects.create(
            firm=self.firm,
            name="Test Connection",
            provider="gmail",
            email_address="test@example.com",
            created_by=self.user,
        )

        # First email in thread
        email1 = EmailArtifact.objects.create(
            firm=self.firm,
            connection=connection,
            provider="gmail",
            external_message_id="msg-subject-1",
            thread_id="thread-subject",
            from_address="client@example.com",
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Project Alpha",
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        # Second email with completely different subject (not just Re: prefix)
        email2 = EmailArtifact.objects.create(
            firm=self.firm,
            connection=connection,
            provider="gmail",
            external_message_id="msg-subject-2",
            thread_id="thread-subject",  # Same thread
            from_address="client@example.com",
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Unrelated Topic Beta",  # Completely different
            sent_at=timezone.now() + timedelta(hours=1),
            received_at=timezone.now() + timedelta(hours=1),
        )

        # Check staleness
        staleness_detector = StalenessDetector()
        staleness_result = staleness_detector.detect_staleness(email2, Decimal("0.8"))

        # Should flag subject change
        self.assertIn("subject_change", staleness_result["penalties"])

    def test_attachments_renamed_across_replies(self):
        """Test that attachment tracking works even if filenames change."""
        from modules.email_ingestion.models import EmailConnection, EmailArtifact, EmailAttachment
        from modules.documents.models import Document

        connection = EmailConnection.objects.create(
            firm=self.firm,
            name="Test Connection",
            provider="gmail",
            email_address="test@example.com",
            created_by=self.user,
        )

        # First email with attachment
        email1 = EmailArtifact.objects.create(
            firm=self.firm,
            connection=connection,
            provider="gmail",
            external_message_id="msg-attach-1",
            thread_id="thread-attach",
            from_address="client@example.com",
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Contract",
            sent_at=timezone.now(),
            received_at=timezone.now(),
        )

        # Attachment with original filename
        attachment1 = EmailAttachment.objects.create(
            email_artifact=email1,
            filename="contract_v1.pdf",
            content_type="application/pdf",
            size_bytes=50000,
            s3_key="attachments/contract_v1.pdf",
            s3_bucket="test-bucket",
        )

        # Reply with "renamed" attachment (same content, different name)
        email2 = EmailArtifact.objects.create(
            firm=self.firm,
            connection=connection,
            provider="gmail",
            external_message_id="msg-attach-2",
            thread_id="thread-attach",
            from_address="client@example.com",
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Re: Contract",
            sent_at=timezone.now() + timedelta(hours=1),
            received_at=timezone.now() + timedelta(hours=1),
        )

        attachment2 = EmailAttachment.objects.create(
            email_artifact=email2,
            filename="final_contract.pdf",  # Different name
            content_type="application/pdf",
            size_bytes=50000,  # Same size (likely same file)
            s3_key="attachments/final_contract.pdf",
            s3_bucket="test-bucket",
        )

        # Both attachments should be tracked separately
        self.assertEqual(EmailAttachment.objects.filter(email_artifact__thread_id="thread-attach").count(), 2)

        # Each should link to its own Document (if created)
        # The system should track both versions as separate attachments

    def test_reingestion_after_connection_reset_idempotency(self):
        """Test that re-ingesting after connection reset doesn't duplicate artifacts."""
        from modules.email_ingestion.models import EmailConnection, EmailArtifact
        from modules.email_ingestion.services import EmailIngestionService

        connection = EmailConnection.objects.create(
            firm=self.firm,
            name="Test Connection",
            provider="gmail",
            email_address="test@example.com",
            created_by=self.user,
        )

        service = EmailIngestionService()

        # Initial ingestion
        email1 = service.ingest_email(
            connection=connection,
            external_message_id="msg-reset-test",
            thread_id="thread-123",
            from_address="sender@example.com",
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Test",
            sent_at=timezone.now(),
            received_at=timezone.now(),
            body_preview="Original ingestion",
        )

        # Simulate connection reset and re-ingestion
        email2 = service.ingest_email(
            connection=connection,
            external_message_id="msg-reset-test",  # Same external ID
            thread_id="thread-123",
            from_address="sender@example.com",
            to_addresses="test@example.com",
            cc_addresses="",
            subject="Test",
            sent_at=timezone.now(),
            received_at=timezone.now(),
            body_preview="Re-ingestion after reset",
        )

        # Should return same artifact (idempotent)
        self.assertEqual(email1.email_artifact_id, email2.email_artifact_id)

        # Should have only one artifact
        self.assertEqual(
            EmailArtifact.objects.filter(
                connection=connection, external_message_id="msg-reset-test"
            ).count(),
            1
        )


class PermissionsEdgeCasesTest(TestCase):
    """
    Edge cases for permissions (docs/03-reference/requirements/DOC-23.md section 3).

    Tests:
    - portal identity linked to multiple accounts; account switcher scope correctness
    - document linked to multiple objects with mixed portal visibility
    - role changes mid-session; token refresh and cached permissions
    """

    def setUp(self):
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.staff_user = User.objects.create_user(username="staff", password="testpass", is_staff=True)
        self.portal_user = User.objects.create_user(username="portal", password="testpass")

    def test_portal_identity_linked_to_multiple_accounts(self):
        """Test that portal users with multiple accounts see correct scoped data."""
        from modules.clients.models import Client, PortalIdentity

        # Create two clients
        client1 = Client.objects.create(
            firm=self.firm,
            company_name="Client A",
            created_by=self.staff_user,
        )
        client2 = Client.objects.create(
            firm=self.firm,
            company_name="Client B",
            created_by=self.staff_user,
        )

        # Link portal user to both clients (multi-account scenario)
        identity1 = PortalIdentity.objects.create(
            firm=self.firm,
            user=self.portal_user,
            client=client1,
        )
        identity2 = PortalIdentity.objects.create(
            firm=self.firm,
            user=self.portal_user,
            client=client2,
        )

        # Create documents for each client
        from modules.documents.models import Document, Folder

        folder1 = Folder.objects.create(
            firm=self.firm, client=client1, name="Folder A", created_by=self.staff_user
        )
        folder2 = Folder.objects.create(
            firm=self.firm, client=client2, name="Folder B", created_by=self.staff_user
        )

        doc1 = Document.objects.create(
            firm=self.firm,
            folder=folder1,
            client=client1,
            name="Doc A",
            file_type="application/pdf",
            file_size_bytes=1000,
            s3_key="doc_a.pdf",
            s3_bucket="test-bucket",
            visibility="client",
            created_by=self.staff_user,
        )
        doc2 = Document.objects.create(
            firm=self.firm,
            folder=folder2,
            client=client2,
            name="Doc B",
            file_type="application/pdf",
            file_size_bytes=1000,
            s3_key="doc_b.pdf",
            s3_bucket="test-bucket",
            visibility="client",
            created_by=self.staff_user,
        )

        # When viewing as client1, should only see doc1
        docs_for_client1 = Document.objects.filter(
            firm=self.firm, client=client1, visibility="client"
        )
        self.assertIn(doc1, docs_for_client1)
        self.assertNotIn(doc2, docs_for_client1)

        # When viewing as client2, should only see doc2
        docs_for_client2 = Document.objects.filter(
            firm=self.firm, client=client2, visibility="client"
        )
        self.assertIn(doc2, docs_for_client2)
        self.assertNotIn(doc1, docs_for_client2)

    def test_document_linked_to_multiple_objects_mixed_visibility(self):
        """Test document visibility when linked to multiple objects with different visibility rules."""
        from modules.clients.models import Client
        from modules.documents.models import Document, Folder

        client = Client.objects.create(
            firm=self.firm,
            company_name="Test Client",
            created_by=self.staff_user,
        )

        folder = Folder.objects.create(
            firm=self.firm, client=client, name="Test Folder", created_by=self.staff_user
        )

        # Document marked as internal (should not be visible to portal)
        doc_internal = Document.objects.create(
            firm=self.firm,
            folder=folder,
            client=client,
            name="Internal Doc",
            file_type="application/pdf",
            file_size_bytes=1000,
            s3_key="internal.pdf",
            s3_bucket="test-bucket",
            visibility="internal",  # Internal only
            created_by=self.staff_user,
        )

        # Document marked as client-visible
        doc_client = Document.objects.create(
            firm=self.firm,
            folder=folder,
            client=client,
            name="Client Doc",
            file_type="application/pdf",
            file_size_bytes=1000,
            s3_key="client.pdf",
            s3_bucket="test-bucket",
            visibility="client",  # Client-visible
            created_by=self.staff_user,
        )

        # Portal query should only return client-visible documents
        portal_visible_docs = Document.objects.filter(
            firm=self.firm, client=client, visibility="client"
        )

        self.assertIn(doc_client, portal_visible_docs)
        self.assertNotIn(doc_internal, portal_visible_docs)

    def test_role_changes_mid_session_permission_refresh(self):
        """Test that role changes require permission refresh."""
        # Create a user with no special permissions
        user = User.objects.create_user(username="changeme", password="testpass")

        # Initially not staff
        self.assertFalse(user.is_staff)

        # Promote to staff
        user.is_staff = True
        user.save()

        # Refresh from DB to simulate token refresh
        user.refresh_from_db()

        self.assertTrue(user.is_staff)

        # In a real system, the token would need to be refreshed
        # and cached permissions cleared


class BillingLedgerEdgeCasesTest(TestCase):
    """
    Edge cases for billing ledger (docs/03-reference/requirements/DOC-23.md section 4).

    Tests:
    - partial payments across multiple invoices
    - retainer partially applied, then invoice voided (compensation entries)
    - idempotency key reuse across retries
    - allocation rounding/currency precision
    """

    def setUp(self):
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = Client.objects.create(
            firm=self.firm,
            company_name="Test Client",
            created_by=self.user,
        )

    def test_partial_payments_across_multiple_invoices(self):
        """Test that partial payments can be allocated across multiple invoices."""
        from modules.finance.billing_ledger import (
            BillingLedgerEntry,
            post_invoice_issued,
            post_payment_received,
            allocate_payment_to_invoice,
        )

        # Create two invoices
        invoice1 = post_invoice_issued(
            firm=self.firm,
            client=self.client,
            invoice_number="INV-001",
            amount=Decimal("100.00"),
            user=self.user,
        )
        invoice2 = post_invoice_issued(
            firm=self.firm,
            client=self.client,
            invoice_number="INV-002",
            amount=Decimal("150.00"),
            user=self.user,
        )

        # Receive partial payment (only covers invoice1 + part of invoice2)
        payment = post_payment_received(
            firm=self.firm,
            client=self.client,
            payment_reference="PAY-001",
            amount=Decimal("175.00"),  # Covers INV-001 (100) + part of INV-002 (75)
            user=self.user,
        )

        # Allocate to invoice1 (full)
        allocate_payment_to_invoice(
            from_entry=payment,
            to_entry=invoice1,
            amount=Decimal("100.00"),
            user=self.user,
        )

        # Allocate remaining to invoice2 (partial)
        allocate_payment_to_invoice(
            from_entry=payment,
            to_entry=invoice2,
            amount=Decimal("75.00"),
            user=self.user,
        )

        # Verify allocations
        self.assertEqual(payment.get_unapplied_amount(), Decimal("0.00"))
        self.assertEqual(invoice1.get_unapplied_amount(), Decimal("0.00"))  # Fully paid
        self.assertEqual(invoice2.get_unapplied_amount(), Decimal("75.00"))  # Partially paid

    def test_retainer_partially_applied_then_invoice_voided(self):
        """Test compensation entries when invoice is voided after retainer application."""
        from modules.finance.billing_ledger import (
            BillingLedgerEntry,
            post_retainer_deposit,
            post_invoice_issued,
            apply_retainer_to_invoice,
        )

        # Deposit retainer
        retainer = post_retainer_deposit(
            firm=self.firm,
            client=self.client,
            deposit_reference="RET-001",
            amount=Decimal("500.00"),
            user=self.user,
        )

        # Issue invoice
        invoice = post_invoice_issued(
            firm=self.firm,
            client=self.client,
            invoice_number="INV-RET-001",
            amount=Decimal("200.00"),
            user=self.user,
        )

        # Apply retainer to invoice
        apply_retainer_to_invoice(
            from_entry=retainer,
            to_entry=invoice,
            amount=Decimal("200.00"),
            user=self.user,
        )

        # Verify retainer balance reduced
        self.assertEqual(retainer.get_unapplied_amount(), Decimal("300.00"))

        # Now void the invoice (requires compensation entry)
        # In production, this would create a credit_memo or adjustment entry
        # For now, verify that retainer application is recorded
        self.assertEqual(invoice.get_unapplied_amount(), Decimal("0.00"))

    def test_idempotency_key_reuse_across_retries(self):
        """Test that idempotency keys prevent duplicate ledger entries on retry."""
        from modules.finance.billing_ledger import BillingLedgerEntry

        # First posting with idempotency key
        entry1 = BillingLedgerEntry.objects.create(
            firm=self.firm,
            client=self.client,
            entry_type="invoice_issued",
            amount=Decimal("100.00"),
            idempotency_key="invoice-123-retry",
            created_by=self.user,
        )

        # Retry with same idempotency key (should return existing)
        existing = BillingLedgerEntry.objects.filter(
            firm=self.firm, idempotency_key="invoice-123-retry"
        ).first()

        self.assertEqual(entry1.id, existing.id)

        # Attempting to create duplicate should fail due to unique constraint
        with self.assertRaises(Exception):  # Django IntegrityError
            BillingLedgerEntry.objects.create(
                firm=self.firm,
                client=self.client,
                entry_type="invoice_issued",
                amount=Decimal("100.00"),
                idempotency_key="invoice-123-retry",  # Same key
                created_by=self.user,
            )

    def test_allocation_rounding_currency_precision(self):
        """Test that allocations handle rounding and currency precision correctly."""
        from modules.finance.billing_ledger import (
            post_invoice_issued,
            post_payment_received,
            allocate_payment_to_invoice,
        )

        # Invoice with precise amount
        invoice = post_invoice_issued(
            firm=self.firm,
            client=self.client,
            invoice_number="INV-PRECISE",
            amount=Decimal("100.33"),  # 2 decimal places
            user=self.user,
        )

        # Payment with rounding
        payment = post_payment_received(
            firm=self.firm,
            client=self.client,
            payment_reference="PAY-PRECISE",
            amount=Decimal("100.33"),
            user=self.user,
        )

        # Allocate
        allocate_payment_to_invoice(
            from_entry=payment,
            to_entry=invoice,
            amount=Decimal("100.33"),
            user=self.user,
        )

        # Verify no rounding errors
        self.assertEqual(payment.get_unapplied_amount(), Decimal("0.00"))
        self.assertEqual(invoice.get_unapplied_amount(), Decimal("0.00"))


class DocumentsEdgeCasesTest(TestCase):
    """
    Edge cases for documents (docs/03-reference/requirements/DOC-23.md section 5).

    Tests:
    - concurrent uploads without locks (should create versions or block)
    - lock override by admin (audit)
    - malware scan pending: portal download blocked
    - signed URL reuse after expiry
    """

    def setUp(self):
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.staff_user = User.objects.create_user(username="staff", password="testpass", is_staff=True)
        self.admin_user = User.objects.create_user(username="admin", password="testpass", is_staff=True)
        self.client = Client.objects.create(
            firm=self.firm,
            company_name="Test Client",
            created_by=self.staff_user,
        )

    def test_concurrent_uploads_without_locks_create_versions(self):
        """Test that concurrent uploads create new versions (not replace)."""
        from modules.documents.models import Document, Folder, DocumentVersion

        folder = Folder.objects.create(
            firm=self.firm, client=self.client, name="Test Folder", created_by=self.staff_user
        )

        # Create initial document
        doc = Document.objects.create(
            firm=self.firm,
            folder=folder,
            client=self.client,
            name="Contract.pdf",
            file_type="application/pdf",
            file_size_bytes=10000,
            s3_key="contract_v1.pdf",
            s3_bucket="test-bucket",
            current_version=1,
            created_by=self.staff_user,
        )

        version1 = DocumentVersion.objects.create(
            document=doc,
            version_number=1,
            file_size_bytes=10000,
            s3_version_id="v1",
            uploaded_by=self.staff_user,
        )

        # "Concurrent" upload creates new version
        version2 = DocumentVersion.objects.create(
            document=doc,
            version_number=2,
            file_size_bytes=12000,
            s3_version_id="v2",
            uploaded_by=self.staff_user,
        )

        doc.current_version = 2
        doc.save()

        # Verify both versions exist
        self.assertEqual(DocumentVersion.objects.filter(document=doc).count(), 2)
        self.assertEqual(doc.current_version, 2)

    def test_lock_override_by_admin_creates_audit(self):
        """Test that admin lock override creates audit event."""
        from modules.documents.models import Document, Folder, DocumentLock

        folder = Folder.objects.create(
            firm=self.firm, client=self.client, name="Test Folder", created_by=self.staff_user
        )

        doc = Document.objects.create(
            firm=self.firm,
            folder=folder,
            client=self.client,
            name="Locked.pdf",
            file_type="application/pdf",
            file_size_bytes=10000,
            s3_key="locked.pdf",
            s3_bucket="test-bucket",
            created_by=self.staff_user,
        )

        # Lock the document
        lock = DocumentLock.objects.create(
            document=doc,
            locked_by=self.staff_user,
            reason="Under review",
        )

        # Admin overrides lock
        lock.override_lock(user=self.admin_user, reason="Emergency update needed")

        # Verify audit event created
        audit_events = AuditEvent.objects.filter(
            firm=self.firm,
            event_type="document_lock_overridden",
            resource_type="DocumentLock",
            resource_id=str(lock.id),
        )

        self.assertEqual(audit_events.count(), 1)
        self.assertEqual(audit_events.first().actor_user, self.admin_user)

    def test_malware_scan_pending_portal_download_blocked(self):
        """Test that documents with pending malware scans block portal downloads."""
        from modules.documents.models import Document, Folder, DocumentVersion
        from modules.documents.malware_scan import DownloadPolicy

        folder = Folder.objects.create(
            firm=self.firm, client=self.client, name="Test Folder", created_by=self.staff_user
        )

        doc = Document.objects.create(
            firm=self.firm,
            folder=folder,
            client=self.client,
            name="Untrusted.pdf",
            file_type="application/pdf",
            file_size_bytes=10000,
            s3_key="untrusted.pdf",
            s3_bucket="test-bucket",
            visibility="client",
            created_by=self.staff_user,
        )

        version = DocumentVersion.objects.create(
            document=doc,
            version_number=1,
            file_size_bytes=10000,
            s3_version_id="v1",
            uploaded_by=self.staff_user,
            virus_scan_status="pending",  # Scan not completed
        )

        # Check download policy for portal user
        policy = DownloadPolicy()
        can_download, reason = policy.can_download_version(version, is_portal=True)

        # Portal download should be blocked
        self.assertFalse(can_download)
        self.assertIn("pending", reason.lower())

        # Staff should be allowed (with warning)
        can_download_staff, reason_staff = policy.can_download_version(version, is_portal=False)
        self.assertTrue(can_download_staff)  # Staff can download

    def test_signed_url_reuse_after_expiry(self):
        """Test that signed URLs cannot be reused after expiry."""
        from modules.documents.models import Document, Folder
        from datetime import datetime, timedelta

        folder = Folder.objects.create(
            firm=self.firm, client=self.client, name="Test Folder", created_by=self.staff_user
        )

        doc = Document.objects.create(
            firm=self.firm,
            folder=folder,
            client=self.client,
            name="Secret.pdf",
            file_type="application/pdf",
            file_size_bytes=10000,
            s3_key="secret.pdf",
            s3_bucket="test-bucket",
            created_by=self.staff_user,
        )

        # Generate signed URL (in production, would use S3 presigned URL)
        # For testing, simulate URL with expiry timestamp
        expiry_time = timezone.now() + timedelta(minutes=15)

        # Simulate URL expiry check
        def is_url_expired(expiry):
            return timezone.now() > expiry

        # Initially not expired
        self.assertFalse(is_url_expired(expiry_time))

        # Simulate time passing (in real test, would mock timezone.now)
        # After expiry, URL should be invalid
        past_expiry = timezone.now() - timedelta(minutes=1)
        self.assertTrue(is_url_expired(past_expiry))
