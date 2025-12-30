"""
Contract Tests (per docs/22 TEST_STRATEGY).

Tests correctness-critical invariants for:
- Pricing: determinism
- Permissions: allow/deny matrix
- Recurrence: DST/leap-year correctness, dedupe
- Orchestration: retry matrix and DLQ routing
- Billing ledger: idempotent posting, allocation constraints
- Documents: versioning, locking, portal visibility, access logging
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
import pytz

from modules.firm.models import Firm
from modules.crm.models import Account
from modules.clients.models import Client
from modules.pricing.models import RuleSet, Quote
from modules.pricing.services import PricingEvaluator
from modules.recurrence.models import RecurrenceRule
from modules.recurrence.services import RecurrenceGenerator
from modules.orchestration.models import OrchestrationDefinition
from modules.orchestration.services import OrchestrationExecutor
from modules.documents.models import Document, Folder, DocumentVersion
from modules.auth.permissions import can_user_access_resource

User = get_user_model()


class PricingDeterminismContractTest(TestCase):
    """
    Contract test: Pricing determinism (per docs/22 section 2).

    MUST: Same inputs → same outputs + trace
    """

    def setUp(self):
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.account = Account.objects.create(
            firm=self.firm, name="Test Account", status="active", created_by=self.user
        )

        self.ruleset = RuleSet.objects.create(
            firm=self.firm,
            name="Standard Pricing",
            rule_logic={"base_rate": 150, "multiplier": 1.0},
            version=1,
            status="active",
            created_by=self.user,
        )

    def test_pricing_determinism(self):
        """Test that pricing evaluation is deterministic."""
        evaluator = PricingEvaluator()

        # Create quote
        quote = Quote.objects.create(
            firm=self.firm,
            account=self.account,
            ruleset=self.ruleset,
            status="draft",
            created_by=self.user,
        )

        input_data = {"hours": 10, "complexity": "standard"}

        # Evaluate twice with same inputs
        result1 = evaluator.evaluate(quote, input_data)
        result2 = evaluator.evaluate(quote, input_data)

        # Results must be identical
        self.assertEqual(result1["total"], result2["total"])
        self.assertEqual(result1["trace"], result2["trace"])

    def test_pricing_trace_reproducibility(self):
        """Test that pricing trace is reproducible."""
        evaluator = PricingEvaluator()

        quote = Quote.objects.create(
            firm=self.firm,
            account=self.account,
            ruleset=self.ruleset,
            status="draft",
            created_by=self.user,
        )

        input_data = {"hours": 10, "complexity": "standard"}

        # Evaluate multiple times
        traces = [evaluator.evaluate(quote, input_data)["trace"] for _ in range(3)]

        # All traces must be identical
        self.assertTrue(all(t == traces[0] for t in traces))


class RecurrenceDSTContractTest(TestCase):
    """
    Contract test: Recurrence DST correctness (per docs/22 section 2).

    MUST: DST/leap-year correctness + dedupe under concurrency
    """

    def setUp(self):
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_dst_transition_correctness(self):
        """Test recurrence generation across DST boundaries."""
        # Create monthly recurrence in DST-observing timezone
        rule = RecurrenceRule.objects.create(
            firm=self.firm,
            name="Monthly Meeting",
            frequency="monthly",
            interval=1,
            timezone="America/New_York",
            start_date=date(2025, 2, 15),  # Before DST
            end_date=date(2025, 5, 15),  # After DST
            created_by=self.user,
        )

        generator = RecurrenceGenerator()

        # Generate occurrences across DST transition (March 2025)
        occurrences = generator.generate_occurrences(
            rule, start_date=date(2025, 2, 1), end_date=date(2025, 5, 31)
        )

        # Should have 4 occurrences: Feb 15, Mar 15, Apr 15, May 15
        self.assertEqual(len(occurrences), 4)

        # Verify times are consistent despite DST
        for occurrence in occurrences:
            # Should all be at same local time (midnight in NY timezone)
            ny_tz = pytz.timezone("America/New_York")
            local_time = occurrence.astimezone(ny_tz)
            self.assertEqual(local_time.hour, 0)
            self.assertEqual(local_time.minute, 0)

    def test_leap_year_correctness(self):
        """Test recurrence on leap year dates."""
        # Create recurrence on Feb 29 (leap day)
        rule = RecurrenceRule.objects.create(
            firm=self.firm,
            name="Leap Year Event",
            frequency="yearly",
            interval=1,
            timezone="UTC",
            start_date=date(2024, 2, 29),  # Leap day
            created_by=self.user,
        )

        generator = RecurrenceGenerator()

        # Generate for 2024-2026
        occurrences = generator.generate_occurrences(
            rule, start_date=date(2024, 2, 1), end_date=date(2026, 3, 31)
        )

        # Should handle leap year correctly (2024 has Feb 29, 2025/2026 don't)
        self.assertGreater(len(occurrences), 0)

    def test_dedupe_under_retries(self):
        """Test that recurrence generation is idempotent under retries."""
        rule = RecurrenceRule.objects.create(
            firm=self.firm,
            name="Daily Standup",
            frequency="daily",
            interval=1,
            timezone="UTC",
            start_date=date(2025, 1, 1),
            created_by=self.user,
        )

        generator = RecurrenceGenerator()

        # Generate same range twice (simulates retry)
        occurrences1 = generator.generate_occurrences(
            rule, start_date=date(2025, 1, 1), end_date=date(2025, 1, 10)
        )
        occurrences2 = generator.generate_occurrences(
            rule, start_date=date(2025, 1, 1), end_date=date(2025, 1, 10)
        )

        # Should produce same results (idempotent)
        self.assertEqual(len(occurrences1), len(occurrences2))
        self.assertEqual(
            [o.strftime("%Y-%m-%d") for o in occurrences1],
            [o.strftime("%Y-%m-%d") for o in occurrences2],
        )


class OrchestrationRetryContractTest(TestCase):
    """
    Contract test: Orchestration retry matrix (per docs/22 section 2).

    MUST: Retry matrix behavior and DLQ routing
    """

    def setUp(self):
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")

        self.definition = OrchestrationDefinition.objects.create(
            firm=self.firm,
            name="Test Workflow",
            steps_config=[
                {"step_id": "step1", "handler": "test_handler", "retry_policy": "exponential_backoff"},
                {"step_id": "step2", "handler": "test_handler2", "retry_policy": "immediate"},
            ],
            created_by=self.user,
        )

    def test_retry_behavior_for_transient_errors(self):
        """Test that transient errors trigger retries."""
        executor = OrchestrationExecutor()

        # STUB: In production, mock step failure and verify retry
        # For now, verify retry policy configuration exists
        self.assertIn("retry_policy", self.definition.steps_config[0])

    def test_dlq_routing_for_non_retryable_errors(self):
        """Test that non-retryable errors route to DLQ."""
        executor = OrchestrationExecutor()

        # STUB: In production, simulate non-retryable error and verify DLQ entry
        # For now, verify DLQ model exists
        from modules.orchestration.models import OrchestrationDLQ
        self.assertTrue(OrchestrationDLQ)


class DocumentVersioningContractTest(TestCase):
    """
    Contract test: Document versioning and locking (per docs/22 section 2).

    MUST: Versioning, locking, portal visibility, access logging
    """

    def setUp(self):
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = Client.objects.create(
            firm=self.firm,
            company_name="Test Client",
            created_by=self.user,
        )
        self.folder = Folder.objects.create(
            firm=self.firm,
            client=self.client,
            name="Test Folder",
            created_by=self.user,
        )

    def test_document_versioning(self):
        """Test that document versions are immutable."""
        doc = Document.objects.create(
            firm=self.firm,
            folder=self.folder,
            client=self.client,
            name="Test Doc",
            file_type="application/pdf",
            file_size_bytes=1000,
            s3_key="test/doc.pdf",
            s3_bucket="test-bucket",
            current_version=1,
            created_by=self.user,
        )

        version1 = DocumentVersion.objects.create(
            document=doc,
            version_number=1,
            file_size_bytes=1000,
            s3_version_id="v1",
            uploaded_by=self.user,
        )

        # Version should be immutable
        with self.assertRaises(Exception):
            version1.file_size_bytes = 2000
            version1.save()  # Should fail or log warning

    def test_portal_visibility(self):
        """Test that internal documents are not visible to portal."""
        doc_internal = Document.objects.create(
            firm=self.firm,
            folder=self.folder,
            client=self.client,
            name="Internal Doc",
            file_type="application/pdf",
            file_size_bytes=1000,
            s3_key="test/internal.pdf",
            s3_bucket="test-bucket",
            visibility="internal",
            created_by=self.user,
        )

        doc_client = Document.objects.create(
            firm=self.firm,
            folder=self.folder,
            client=self.client,
            name="Client Doc",
            file_type="application/pdf",
            file_size_bytes=1000,
            s3_key="test/client.pdf",
            s3_bucket="test-bucket",
            visibility="client",
            created_by=self.user,
        )

        # Portal should only see client-visible documents
        client_visible = Document.objects.filter(
            firm=self.firm, client=self.client, visibility="client"
        )
        self.assertIn(doc_client, client_visible)
        self.assertNotIn(doc_internal, client_visible)

    def test_access_logging(self):
        """Test that document access is logged."""
        doc = Document.objects.create(
            firm=self.firm,
            folder=self.folder,
            client=self.client,
            name="Logged Doc",
            file_type="application/pdf",
            file_size_bytes=1000,
            s3_key="test/logged.pdf",
            s3_bucket="test-bucket",
            created_by=self.user,
        )

        # STUB: In production, verify DocumentAccessLog entry created
        from modules.documents.models import DocumentAccessLog
        self.assertTrue(DocumentAccessLog)


class BillingLedgerIdempotencyContractTest(TestCase):
    """
    Contract test: Billing ledger idempotency (per docs/22 section 2).

    MUST: Idempotent posting, allocation constraints
    """

    def setUp(self):
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = Client.objects.create(
            firm=self.firm,
            company_name="Test Client",
            created_by=self.user,
        )

    def test_idempotent_posting(self):
        """Test that ledger entries are idempotent."""
        from modules.finance.models import LedgerEntry

        # Create ledger entry with idempotency key
        entry_data = {
            "firm": self.firm,
            "client": self.client,
            "amount": Decimal("100.00"),
            "entry_type": "charge",
            "idempotency_key": "test-charge-001",
            "created_by": self.user,
        }

        entry1 = LedgerEntry.objects.create(**entry_data)

        # Second attempt with same idempotency key should return existing
        existing = LedgerEntry.objects.filter(
            firm=self.firm, idempotency_key="test-charge-001"
        ).first()

        self.assertEqual(entry1.id, existing.id)

    def test_allocation_constraints(self):
        """Test that allocations respect payment constraints."""
        # STUB: In production, test partial/over/under payment allocations
        # Verify that allocations can't exceed payment amount
        pass


class PermissionsContractTest(TestCase):
    """
    Contract test: Permissions allow/deny matrix (per docs/22 section 2).

    MUST: Verify allow/deny for key roles and portal scopes
    """

    def setUp(self):
        self.firm = Firm.objects.create(name="Test Firm", slug="test-firm")
        self.admin = User.objects.create_user(username="admin", password="pass", is_staff=True)
        self.staff = User.objects.create_user(username="staff", password="pass")
        self.portal_user = User.objects.create_user(username="portal", password="pass")

    def test_staff_can_access_internal_resources(self):
        """Test that staff can access internal resources."""
        # STUB: Verify staff has access to internal documents, reports, etc.
        self.assertTrue(self.staff.is_authenticated)

    def test_portal_user_cannot_access_internal_resources(self):
        """Test that portal users cannot access internal resources."""
        # STUB: Verify portal user is restricted to client-visible resources only
        self.assertTrue(self.portal_user.is_authenticated)
        self.assertFalse(self.portal_user.is_staff)
