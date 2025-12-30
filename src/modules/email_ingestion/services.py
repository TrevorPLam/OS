"""
Email Ingestion Services.

Provides mapping suggestion logic and ingestion workflows.
Implements docs/15 section 3 (mapping suggestions) and section 4 (staleness heuristics).
Enhanced with DOC-15.2: staleness detection and retry-safety.
"""

import uuid
from decimal import Decimal
from typing import Dict, Optional, Tuple, List
from django.db import transaction
from django.utils import timezone

from modules.crm.models import Account, Engagement, Contact
from modules.projects.models import WorkItem
from .models import EmailArtifact, EmailConnection, IngestionAttempt
from .staleness_service import StalenessDetector, StalenessConfig


class EmailMappingService:
    """
    Service for suggesting mappings from emails to domain objects.

    Implements docs/15 section 3: mapping suggestions with confidence scoring.
    Enhanced with DOC-15.2: staleness detection per docs/15 section 4.
    """

    # Thresholds per docs/15 section 3
    AUTO_MAP_THRESHOLD = Decimal("0.85")  # Auto-map only if confidence >= 0.85
    TRIAGE_THRESHOLD = Decimal("0.50")  # Below this, always send to triage

    def __init__(self, staleness_detector: StalenessDetector = None):
        self.staleness_detector = staleness_detector or StalenessDetector()

    def suggest_mapping(
        self, email: EmailArtifact
    ) -> Tuple[Optional[Account], Optional[Engagement], Optional[WorkItem], Decimal, str, bool]:
        """
        Suggest mapping for an email artifact.

        Returns:
            (account, engagement, work_item, adjusted_confidence, reasons, requires_triage)

        Per docs/15 section 3: uses sender/recipient domain, subject keywords,
        prior thread mappings, and contact matching.

        Enhanced with DOC-15.2: staleness detection per docs/15 section 4.
        """
        reasons = []
        confidence = Decimal("0.0")
        account = None
        engagement = None
        work_item = None

        # Signal 1: Match sender email to known contacts
        from_domain = self._extract_domain(email.from_address)
        contacts = Contact.objects.filter(
            firm=email.firm, email__iexact=email.from_address
        ).select_related("account")

        if contacts.exists():
            contact = contacts.first()
            account = contact.account
            confidence += Decimal("0.40")
            reasons.append(f"Sender email matches contact: {contact.name}")

            # Try to find active engagement for this account
            active_engagements = Engagement.objects.filter(
                firm=email.firm, account=account, status__in=["lead", "opportunity", "active"]
            ).order_by("-created_at")

            if active_engagements.exists():
                engagement = active_engagements.first()
                confidence += Decimal("0.20")
                reasons.append(f"Active engagement found: {engagement.title}")

        # Signal 2: Match domain to known accounts
        elif from_domain:
            domain_contacts = Contact.objects.filter(
                firm=email.firm, email__icontains=f"@{from_domain}"
            ).select_related("account")

            if domain_contacts.exists():
                account = domain_contacts.first().account
                confidence += Decimal("0.25")
                reasons.append(f"Domain {from_domain} matches account contacts")

        # Signal 3: Look for engagement codes in subject (e.g., "ENG-12345")
        if email.subject:
            # Simple pattern: look for "ENG-" followed by digits
            import re

            engagement_pattern = r"ENG-(\d+)"
            match = re.search(engagement_pattern, email.subject, re.IGNORECASE)
            if match:
                engagement_id = match.group(1)
                try:
                    possible_engagement = Engagement.objects.get(
                        firm=email.firm, pk=int(engagement_id)
                    )
                    engagement = possible_engagement
                    account = engagement.account
                    confidence += Decimal("0.35")
                    reasons.append(f"Subject contains engagement code: ENG-{engagement_id}")
                except (Engagement.DoesNotExist, ValueError):
                    pass

        # Signal 4: Check prior thread mappings
        if email.thread_id:
            prior_in_thread = (
                EmailArtifact.objects.filter(
                    firm=email.firm,
                    thread_id=email.thread_id,
                    status="mapped",
                )
                .exclude(pk=email.pk)
                .order_by("-sent_at")
            )

            if prior_in_thread.exists():
                prior = prior_in_thread.first()
                if prior.confirmed_account:
                    account = prior.confirmed_account
                    confidence += Decimal("0.30")
                    reasons.append("Prior email in thread mapped to this account")

                if prior.confirmed_engagement:
                    engagement = prior.confirmed_engagement
                    confidence += Decimal("0.20")
                    reasons.append("Prior email in thread mapped to this engagement")

        # Clamp confidence to [0, 1]
        confidence = min(confidence, Decimal("1.0"))

        # Apply staleness detection (DOC-15.2)
        adjusted_confidence, staleness_reasons, staleness_triage = self.staleness_detector.detect_staleness(
            email, confidence
        )

        # Combine reasons
        all_reasons = reasons + staleness_reasons
        reason_str = "; ".join(all_reasons) if all_reasons else "No strong signals found"

        # Determine if should force triage
        requires_triage = self.staleness_detector.should_force_triage(
            email, adjusted_confidence, staleness_reasons
        )

        return account, engagement, work_item, adjusted_confidence, reason_str, requires_triage

    def should_auto_map(self, confidence: Decimal) -> bool:
        """Return True if confidence is high enough for auto-mapping."""
        return confidence >= self.AUTO_MAP_THRESHOLD

    def should_triage(self, confidence: Decimal) -> bool:
        """Return True if confidence is too low and needs manual review."""
        return confidence < self.TRIAGE_THRESHOLD

    def _extract_domain(self, email_address: str) -> Optional[str]:
        """Extract domain from email address."""
        if "@" in email_address:
            return email_address.split("@")[1].lower()
        return None


class EmailIngestionService:
    """
    Service for ingesting emails from providers.

    Implements docs/15 section 2.3: IngestionAttempt logging for retry-safety.
    """

    def __init__(self):
        self.mapping_service = EmailMappingService()

    @transaction.atomic
    def ingest_email(
        self,
        connection: EmailConnection,
        external_message_id: str,
        thread_id: Optional[str],
        from_address: str,
        to_addresses: str,
        cc_addresses: str,
        subject: str,
        sent_at,
        received_at,
        body_preview: str,
        correlation_id: Optional[uuid.UUID] = None,
    ) -> EmailArtifact:
        """
        Ingest an email and create an EmailArtifact.

        Implements docs/15 section 2: idempotent ingestion.
        Returns existing artifact if (connection, external_message_id) already exists.
        """
        correlation_id = correlation_id or uuid.uuid4()
        start_time = timezone.now()

        # Check if already ingested (idempotency per docs/15 section 2)
        existing = EmailArtifact.objects.filter(
            connection=connection, external_message_id=external_message_id
        ).first()

        if existing:
            # Log successful idempotent fetch
            duration_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            IngestionAttempt.objects.create(
                firm=connection.firm,
                connection=connection,
                email_artifact=existing,
                operation="fetch",
                status="success",
                correlation_id=correlation_id,
                duration_ms=duration_ms,
            )
            return existing

        # Create new artifact
        try:
            email = EmailArtifact.objects.create(
                firm=connection.firm,
                connection=connection,
                provider=connection.provider,
                external_message_id=external_message_id,
                thread_id=thread_id,
                from_address=from_address,
                to_addresses=to_addresses,
                cc_addresses=cc_addresses,
                subject=subject,
                sent_at=sent_at,
                received_at=received_at,
                body_preview=body_preview[:500],  # Bounded per docs/15 section 2.1
                status="ingested",
            )

            # Log successful fetch
            fetch_duration_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            IngestionAttempt.objects.create(
                firm=connection.firm,
                connection=connection,
                email_artifact=email,
                operation="fetch",
                status="success",
                correlation_id=correlation_id,
                duration_ms=fetch_duration_ms,
            )

            # Attempt mapping
            map_start_time = timezone.now()
            try:
                account, engagement, work_item, confidence, reasons, requires_triage = self.mapping_service.suggest_mapping(
                    email
                )

                email.suggested_account = account
                email.suggested_engagement = engagement
                email.suggested_work_item = work_item
                email.mapping_confidence = confidence
                email.mapping_reasons = reasons

                # Determine status based on confidence and staleness (DOC-15.2)
                if requires_triage:
                    # Staleness heuristics force triage
                    email.status = "triage"
                elif self.mapping_service.should_auto_map(confidence):
                    # Auto-map: copy suggestions to confirmed fields
                    email.confirmed_account = account
                    email.confirmed_engagement = engagement
                    email.confirmed_work_item = work_item
                    email.status = "mapped"
                elif self.mapping_service.should_triage(confidence):
                    email.status = "triage"
                else:
                    # Medium confidence: keep as ingested, wait for review
                    email.status = "ingested"

                email.save()

                # Log successful mapping
                map_duration_ms = int((timezone.now() - map_start_time).total_seconds() * 1000)
                IngestionAttempt.objects.create(
                    firm=connection.firm,
                    connection=connection,
                    email_artifact=email,
                    operation="map",
                    status="success",
                    correlation_id=correlation_id,
                    duration_ms=map_duration_ms,
                )

            except Exception as map_error:
                # Log mapping failure (non-fatal)
                map_duration_ms = int((timezone.now() - map_start_time).total_seconds() * 1000)
                IngestionAttempt.objects.create(
                    firm=connection.firm,
                    connection=connection,
                    email_artifact=email,
                    operation="map",
                    status="fail",
                    error_summary=f"Mapping failed: {type(map_error).__name__}",
                    correlation_id=correlation_id,
                    duration_ms=map_duration_ms,
                )
                # Email still created, just without mapping

            return email

        except Exception as e:
            # Log fetch failure
            duration_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            IngestionAttempt.objects.create(
                firm=connection.firm,
                connection=connection,
                email_artifact=None,
                operation="fetch",
                status="fail",
                error_summary=f"Ingestion failed: {type(e).__name__}",
                correlation_id=correlation_id,
                duration_ms=duration_ms,
            )
            raise
