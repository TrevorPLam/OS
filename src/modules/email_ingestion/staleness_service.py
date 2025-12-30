"""
Email Ingestion Staleness Detection Service.

Implements DOC-15.2: staleness heuristics per docs/15 section 4.

Staleness detection identifies emails that should go to triage due to:
- Contact email matches multiple accounts
- Thread contains mixed clients
- Subject changes across threads
- Last confident mapping is older than threshold
"""

from datetime import timedelta
from decimal import Decimal
from typing import Tuple, List
from django.utils import timezone
from django.db.models import Count, Q

from modules.crm.models import Contact
from .models import EmailArtifact


class StalenessConfig:
    """
    Configuration for staleness heuristics.

    Thresholds are configurable per firm (future enhancement).
    """

    # Staleness threshold: if last confident mapping is older than this, flag as stale
    MAPPING_STALENESS_DAYS = 90  # 3 months

    # Confidence penalty for stale mappings
    STALENESS_CONFIDENCE_PENALTY = Decimal("0.30")

    # Multi-account contact penalty
    MULTI_ACCOUNT_PENALTY = Decimal("0.25")

    # Mixed client thread penalty
    MIXED_CLIENT_PENALTY = Decimal("0.35")

    # Subject change penalty
    SUBJECT_CHANGE_PENALTY = Decimal("0.15")


class StalenessDetector:
    """
    Detects staleness conditions for email mapping suggestions.

    Implements docs/15 section 4: staleness heuristics and triage rules.
    """

    def __init__(self, config: StalenessConfig = None):
        self.config = config or StalenessConfig()

    def detect_staleness(
        self, email: EmailArtifact, suggested_confidence: Decimal
    ) -> Tuple[Decimal, List[str], bool]:
        """
        Detect staleness conditions and adjust confidence.

        Args:
            email: EmailArtifact to check
            suggested_confidence: Initial confidence from mapping service

        Returns:
            (adjusted_confidence, staleness_reasons, requires_triage)
        """
        adjusted_confidence = suggested_confidence
        staleness_reasons = []
        requires_triage = False

        # Check 1: Contact email matches multiple accounts
        multi_account_penalty = self._check_multi_account_contact(email)
        if multi_account_penalty > 0:
            adjusted_confidence -= multi_account_penalty
            staleness_reasons.append(
                f"Contact email associated with multiple accounts (penalty: {multi_account_penalty})"
            )
            requires_triage = True

        # Check 2: Thread contains mixed clients
        mixed_client_penalty = self._check_mixed_client_thread(email)
        if mixed_client_penalty > 0:
            adjusted_confidence -= mixed_client_penalty
            staleness_reasons.append(
                f"Thread contains emails from multiple accounts (penalty: {mixed_client_penalty})"
            )
            requires_triage = True

        # Check 3: Subject changes across thread
        subject_change_penalty = self._check_subject_change_in_thread(email)
        if subject_change_penalty > 0:
            adjusted_confidence -= subject_change_penalty
            staleness_reasons.append(
                f"Subject line changed within thread (penalty: {subject_change_penalty})"
            )

        # Check 4: Last confident mapping is stale
        stale_mapping_penalty = self._check_stale_prior_mapping(email)
        if stale_mapping_penalty > 0:
            adjusted_confidence -= stale_mapping_penalty
            staleness_reasons.append(
                f"Last confident mapping is older than {self.config.MAPPING_STALENESS_DAYS} days (penalty: {stale_mapping_penalty})"
            )
            requires_triage = True

        # Clamp confidence to [0, 1]
        adjusted_confidence = max(Decimal("0.0"), min(adjusted_confidence, Decimal("1.0")))

        return adjusted_confidence, staleness_reasons, requires_triage

    def _check_multi_account_contact(self, email: EmailArtifact) -> Decimal:
        """
        Check if sender email is associated with multiple accounts.

        Returns:
            Penalty amount (0 if no penalty)
        """
        # Count distinct accounts for this email address
        contact_count = (
            Contact.objects.filter(firm=email.firm, email__iexact=email.from_address)
            .values("account")
            .distinct()
            .count()
        )

        if contact_count > 1:
            return self.config.MULTI_ACCOUNT_PENALTY

        return Decimal("0.0")

    def _check_mixed_client_thread(self, email: EmailArtifact) -> Decimal:
        """
        Check if thread contains emails mapped to different accounts.

        Returns:
            Penalty amount (0 if no penalty)
        """
        if not email.thread_id:
            return Decimal("0.0")

        # Get all mapped emails in this thread
        thread_emails = EmailArtifact.objects.filter(
            firm=email.firm, thread_id=email.thread_id, status="mapped"
        ).exclude(pk=email.pk)

        if not thread_emails.exists():
            return Decimal("0.0")

        # Count distinct accounts in thread
        distinct_accounts = (
            thread_emails.filter(confirmed_account__isnull=False)
            .values("confirmed_account")
            .distinct()
            .count()
        )

        if distinct_accounts > 1:
            return self.config.MIXED_CLIENT_PENALTY

        return Decimal("0.0")

    def _check_subject_change_in_thread(self, email: EmailArtifact) -> Decimal:
        """
        Check if subject changed within the thread.

        Returns:
            Penalty amount (0 if no penalty)
        """
        if not email.thread_id:
            return Decimal("0.0")

        # Get subjects from prior emails in thread
        prior_emails = (
            EmailArtifact.objects.filter(firm=email.firm, thread_id=email.thread_id)
            .exclude(pk=email.pk)
            .order_by("-sent_at")
        )

        if not prior_emails.exists():
            return Decimal("0.0")

        # Simple heuristic: check if current subject differs from most recent prior email
        # (More sophisticated: check for "Re:" prefix stripping, etc.)
        most_recent_prior = prior_emails.first()

        # Normalize subjects: remove "Re:", "Fwd:", etc.
        current_subject_normalized = self._normalize_subject(email.subject)
        prior_subject_normalized = self._normalize_subject(most_recent_prior.subject)

        if current_subject_normalized != prior_subject_normalized:
            return self.config.SUBJECT_CHANGE_PENALTY

        return Decimal("0.0")

    def _check_stale_prior_mapping(self, email: EmailArtifact) -> Decimal:
        """
        Check if last confident mapping in thread is stale.

        Returns:
            Penalty amount (0 if no penalty)
        """
        if not email.thread_id:
            return Decimal("0.0")

        staleness_threshold = timezone.now() - timedelta(days=self.config.MAPPING_STALENESS_DAYS)

        # Find most recent confident mapping in thread
        recent_confident = (
            EmailArtifact.objects.filter(
                firm=email.firm,
                thread_id=email.thread_id,
                status="mapped",
                mapping_confidence__gte=Decimal("0.85"),  # High confidence threshold
            )
            .exclude(pk=email.pk)
            .order_by("-sent_at")
            .first()
        )

        if recent_confident and recent_confident.sent_at < staleness_threshold:
            return self.config.STALENESS_CONFIDENCE_PENALTY

        return Decimal("0.0")

    def _normalize_subject(self, subject: str) -> str:
        """
        Normalize subject line for comparison.

        Removes common prefixes like "Re:", "Fwd:", etc.
        """
        if not subject:
            return ""

        normalized = subject.strip()

        # Remove common prefixes (case-insensitive)
        prefixes = ["re:", "fwd:", "fw:", "forward:", "reply:"]
        for prefix in prefixes:
            while normalized.lower().startswith(prefix):
                normalized = normalized[len(prefix) :].strip()

        return normalized.lower()

    def should_force_triage(
        self, email: EmailArtifact, adjusted_confidence: Decimal, staleness_reasons: List[str]
    ) -> bool:
        """
        Determine if email should be forced to triage regardless of confidence.

        Per docs/15 section 4: if confidence is low or ambiguity exists, place in Triage.

        Returns:
            True if should go to triage
        """
        # Rule 1: Low confidence always goes to triage
        if adjusted_confidence < Decimal("0.50"):
            return True

        # Rule 2: Multiple staleness signals = triage
        if len(staleness_reasons) >= 2:
            return True

        # Rule 3: Critical staleness signals (multi-account or mixed client)
        critical_keywords = ["multiple accounts", "multiple accounts"]
        for reason in staleness_reasons:
            if any(keyword in reason.lower() for keyword in critical_keywords):
                return True

        return False
