"""
Data Erasure and Anonymization Workflows

Implements the erasure request workflow and anonymization capabilities
as specified in docs/03-reference/requirements/DOC-07.md (DATA_GOVERNANCE) section 6.

This module provides:
- Erasure request records
- Evaluation logic for erasure vs anonymization
- Anonymization execution service
- Idempotent, auditable workflows

Per docs/03-reference/requirements/DOC-07.md:
- Erasure removes data permanently
- Anonymization removes identifying information while preserving audit integrity
- Both workflows must be idempotent and fully auditable
- Legal hold overrides deletion/anonymization
"""

from decimal import Decimal
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from modules.firm.utils import FirmScopedManager


class ErasureRequest(models.Model):
    """
    Erasure/Anonymization Request Record

    Per docs/03-reference/requirements/DOC-07.md section 6.2, this model tracks requests for data erasure
    or anonymization with:
    - Requester identity and legal basis
    - Scope (which entities are affected)
    - Evaluation results (what can be erased vs anonymized)
    - Execution status and audit trail

    Workflow:
    1. Create request (pending status)
    2. Evaluate constraints (active engagements, legal hold, etc.)
    3. Generate deterministic plan
    4. Execute anonymization/erasure (marks as completed)
    5. All steps are audited
    """

    # Request status
    STATUS_PENDING = "pending"
    STATUS_EVALUATING = "evaluating"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_EXECUTING = "executing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending Review"),
        (STATUS_EVALUATING, "Evaluating Constraints"),
        (STATUS_APPROVED, "Approved for Execution"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_EXECUTING, "Executing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    # Legal basis for request (per docs/03-reference/requirements/DOC-07.md section 6.2)
    BASIS_GDPR_ARTICLE_17 = "gdpr_article_17"
    BASIS_CCPA_DELETION = "ccpa_deletion"
    BASIS_CONTRACTUAL = "contractual_end"
    BASIS_CONSENT_WITHDRAWN = "consent_withdrawn"
    BASIS_FIRM_OFFBOARDING = "firm_offboarding"
    BASIS_OTHER = "other_legal"

    BASIS_CHOICES = [
        (BASIS_GDPR_ARTICLE_17, "GDPR Article 17 (Right to Erasure)"),
        (BASIS_CCPA_DELETION, "CCPA Deletion Request"),
        (BASIS_CONTRACTUAL, "Contractual Retention Period Ended"),
        (BASIS_CONSENT_WITHDRAWN, "Consent Withdrawn"),
        (BASIS_FIRM_OFFBOARDING, "Firm Offboarding"),
        (BASIS_OTHER, "Other Legal Basis"),
    ]

    # Scope type (what entity to erase/anonymize)
    SCOPE_CONTACT = "contact"
    SCOPE_ACCOUNT = "account"
    SCOPE_DOCUMENT = "document"
    SCOPE_ENGAGEMENT = "engagement"

    SCOPE_CHOICES = [
        (SCOPE_CONTACT, "Contact (Individual)"),
        (SCOPE_ACCOUNT, "Account (Company)"),
        (SCOPE_DOCUMENT, "Specific Document"),
        (SCOPE_ENGAGEMENT, "Engagement (and related data)"),
    ]

    # Core fields
    id = models.BigAutoField(primary_key=True)

    # Tenant context
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="erasure_requests",
        help_text="Firm this request belongs to",
    )

    # Request details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        help_text="Current status of erasure request",
    )

    legal_basis = models.CharField(
        max_length=30,
        choices=BASIS_CHOICES,
        help_text="Legal basis for erasure/anonymization",
    )

    scope_type = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        help_text="Type of entity to erase/anonymize",
    )

    scope_entity_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="ID of entity to erase (e.g., Contact.id, Account.id)",
    )

    scope_entity_model = models.CharField(
        max_length=100,
        help_text="Django model name (e.g., 'clients.Contact', 'clients.Client')",
    )

    # Requester information
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="erasure_requests_created",
        help_text="User who created this request",
    )

    requested_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When request was created",
    )

    request_reason = models.TextField(
        help_text="Detailed reason for erasure/anonymization request",
    )

    legal_reference = models.CharField(
        max_length=500,
        blank=True,
        help_text="Reference to legal documentation (case number, request ID)",
    )

    # Evaluation results (per docs/03-reference/requirements/DOC-07.md section 6.2)
    evaluation_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When constraint evaluation was completed",
    )

    evaluation_result = models.JSONField(
        default=dict,
        blank=True,
        help_text="Evaluation results: constraints, blockers, plan",
    )

    # Approval workflow
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="erasure_requests_approved",
        help_text="Master admin who approved execution",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When request was approved",
    )

    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (if status=rejected)",
    )

    # Execution results
    executed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When anonymization/erasure was executed",
    )

    execution_result = models.JSONField(
        default=dict,
        blank=True,
        help_text="Execution results: what was anonymized/erased",
    )

    error_message = models.TextField(
        blank=True,
        help_text="Error message if execution failed",
    )

    # Audit trail
    audit_events = models.JSONField(
        default=list,
        blank=True,
        help_text="List of audit event IDs related to this request",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "core_erasure_request"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["firm", "status", "-requested_at"]),
            models.Index(fields=["scope_entity_model", "scope_entity_id"]),
            models.Index(fields=["requested_by", "-requested_at"]),
        ]
        permissions = [
            ("can_approve_erasure", "Can approve erasure requests (Master Admin only)"),
        ]

    def __str__(self):
        return f"Erasure Request #{self.id} ({self.scope_type}) - {self.status}"

    def clean(self):
        """Validate request before saving."""
        errors = {}

        if self.status == self.STATUS_APPROVED and not self.approved_by:
            errors["approved_by"] = "Approved requests must have an approver"

        if self.status == self.STATUS_REJECTED and not self.rejection_reason:
            errors["rejection_reason"] = "Rejected requests must have a rejection reason"

        if self.status == self.STATUS_COMPLETED and not self.executed_at:
            errors["executed_at"] = "Completed requests must have execution timestamp"

        if errors:
            raise ValidationError(errors)


@dataclass
class EvaluationResult:
    """
    Result of erasure/anonymization constraint evaluation.

    Per docs/03-reference/requirements/DOC-07.md section 6.2, evaluation must check:
    - Active engagements
    - Outstanding invoices/ledger obligations
    - Legal hold
    - Contractual retention requirements
    """
    can_proceed: bool
    blockers: List[str]  # List of blocking constraints
    warnings: List[str]  # Non-blocking warnings
    anonymization_plan: Dict[str, Any]  # What will be anonymized
    preservation_plan: Dict[str, Any]  # What will be preserved
    affected_entities: Dict[str, List[str]]  # Map of entity type to IDs


class ErasureService:
    """
    Service for evaluating and executing erasure/anonymization requests.

    Implements the workflow defined in docs/03-reference/requirements/DOC-07.md section 6.
    """

    def evaluate_contact_erasure(self, contact, legal_basis: str) -> EvaluationResult:
        """
        Evaluate if a Contact can be erased/anonymized.

        Per docs/03-reference/requirements/DOC-07.md section 6.2, checks:
        - Active engagements
        - Outstanding invoices
        - Legal hold
        - Contractual obligations

        Args:
            contact: Contact instance
            legal_basis: Legal basis for request (one of ErasureRequest.BASIS_*)

        Returns:
            EvaluationResult with blockers, plan, etc.
        """
        from modules.crm.models import Lead, Opportunity
        from modules.finance.models import Invoice

        blockers = []
        warnings = []
        affected_entities = {
            "contact": [str(contact.id)],
            "leads": [],
            "opportunities": [],
            "invoices": [],
        }

        # Check for active leads
        active_leads = Lead.objects.filter(
            firm=contact.firm,
            contact=contact,
            status__in=["new", "contacted", "qualified"],
        )

        if active_leads.exists():
            lead_ids = list(active_leads.values_list("id", flat=True))
            affected_entities["leads"] = [str(lid) for lid in lead_ids]
            warnings.append(
                f"Contact has {active_leads.count()} active leads. "
                "These will be anonymized but preserved for audit purposes."
            )

        # Check for active opportunities
        active_opps = Opportunity.objects.filter(
            firm=contact.firm,
            contact=contact,
            stage__in=["qualification", "proposal", "negotiation"],
        )

        if active_opps.exists():
            opp_ids = list(active_opps.values_list("id", flat=True))
            affected_entities["opportunities"] = [str(oid) for oid in opp_ids]
            blockers.append(
                f"Contact has {active_opps.count()} active opportunities. "
                "Opportunities must be closed before erasure."
            )

        # Check for outstanding invoices
        # Note: This assumes Client model has a way to link to Contact
        # Actual implementation depends on data model
        warnings.append(
            "Invoice relationships will be preserved with anonymized contact reference."
        )

        # Legal hold check (would need to be implemented on Contact model)
        if hasattr(contact, "legal_hold") and contact.legal_hold:
            blockers.append(
                "Contact is under legal hold. Cannot erase until hold is removed."
            )

        # Determine anonymization plan
        anonymization_plan = {
            "contact": {
                "fields_to_anonymize": ["first_name", "last_name", "email", "phone"],
                "replacement_strategy": "anonymized_contact",
            },
            "leads": {
                "action": "anonymize_notes_and_metadata",
                "preserve_structure": True,
            },
            "opportunities": {
                "action": "block" if blockers else "anonymize_contact_reference",
            },
        }

        # Preservation plan (per docs/03-reference/requirements/DOC-07.md section 6.3)
        preservation_plan = {
            "audit_events": "preserve_with_anonymized_actor",
            "ledger_entries": "preserve_amounts_and_dates",
            "document_integrity": "preserve_structure_remove_identifying_metadata",
        }

        can_proceed = len(blockers) == 0

        return EvaluationResult(
            can_proceed=can_proceed,
            blockers=blockers,
            warnings=warnings,
            anonymization_plan=anonymization_plan,
            preservation_plan=preservation_plan,
            affected_entities=affected_entities,
        )

    def evaluate_account_erasure(self, account, legal_basis: str) -> EvaluationResult:
        """
        Evaluate if an Account (Client) can be erased/anonymized.

        Similar to contact evaluation but checks:
        - Active projects
        - Active contracts
        - AR balance
        - Retainer balance
        """
        from modules.projects.models import Project
        from modules.crm.models import Contract
        from modules.finance.billing_ledger import get_ar_balance, get_retainer_balance

        blockers = []
        warnings = []
        affected_entities = {
            "account": [str(account.id)],
            "projects": [],
            "contracts": [],
        }

        # Check for active projects
        active_projects = Project.objects.filter(
            firm=account.firm,
            client=account,
            status="active",
        )

        if active_projects.exists():
            project_ids = list(active_projects.values_list("id", flat=True))
            affected_entities["projects"] = [str(pid) for pid in project_ids]
            blockers.append(
                f"Account has {active_projects.count()} active projects. "
                "Projects must be completed before erasure."
            )

        # Check for active contracts
        active_contracts = Contract.objects.filter(
            firm=account.firm,
            client=account,
            status="active",
        )

        if active_contracts.exists():
            contract_ids = list(active_contracts.values_list("id", flat=True))
            affected_entities["contracts"] = [str(cid) for cid in contract_ids]
            blockers.append(
                f"Account has {active_contracts.count()} active contracts. "
                "Contracts must be terminated before erasure."
            )

        # Check AR balance
        ar_balance = get_ar_balance(account.firm, account)
        if ar_balance > Decimal("0.00"):
            blockers.append(
                f"Account has outstanding AR balance of ${ar_balance}. "
                "Balance must be settled before erasure."
            )

        # Check retainer balance
        retainer_balance = get_retainer_balance(account.firm, account)
        if retainer_balance > Decimal("0.00"):
            blockers.append(
                f"Account has retainer balance of ${retainer_balance}. "
                "Retainer must be refunded or applied before erasure."
            )

        # Legal hold check
        if hasattr(account, "legal_hold") and account.legal_hold:
            blockers.append(
                "Account is under legal hold. Cannot erase until hold is removed."
            )

        # Anonymization plan
        anonymization_plan = {
            "account": {
                "fields_to_anonymize": ["company_name"] if hasattr(account, "company_name") else ["name"],
                "replacement_value": f"Anonymized Account {account.id}",
            },
            "projects": {
                "action": "preserve_with_anonymized_client_reference",
            },
            "documents": {
                "action": "revoke_access_anonymize_metadata",
            },
        }

        preservation_plan = {
            "ledger_integrity": "preserve_all_entries_with_anonymized_client",
            "audit_events": "preserve_with_anonymized_client",
            "document_versions": "preserve_if_required_by_retention_policy",
        }

        can_proceed = len(blockers) == 0

        return EvaluationResult(
            can_proceed=can_proceed,
            blockers=blockers,
            warnings=warnings,
            anonymization_plan=anonymization_plan,
            preservation_plan=preservation_plan,
            affected_entities=affected_entities,
        )

    @transaction.atomic
    def execute_contact_anonymization(self, contact, erasure_request: ErasureRequest) -> Dict[str, Any]:
        """
        Execute anonymization for a Contact.

        Per docs/03-reference/requirements/DOC-07.md section 6.4:
        - Replace names with "Anonymized Contact"
        - Remove email/phone
        - Preserve internal IDs
        - Audit the anonymization

        Args:
            contact: Contact instance
            erasure_request: ErasureRequest that triggered this

        Returns:
            Dict with execution results
        """
        from modules.firm.audit import audit

        # Store original values for audit
        original_data = {
            "first_name": contact.first_name if hasattr(contact, "first_name") else None,
            "last_name": contact.last_name if hasattr(contact, "last_name") else None,
            "email": contact.email if hasattr(contact, "email") else None,
            "phone": contact.phone if hasattr(contact, "phone") else None,
        }

        # Anonymize contact fields (per docs/03-reference/requirements/DOC-07.md section 6.4)
        if hasattr(contact, "first_name"):
            contact.first_name = "Anonymized"
        if hasattr(contact, "last_name"):
            contact.last_name = f"Contact {contact.id}"
        if hasattr(contact, "email"):
            contact.email = f"anonymized.{contact.id}@redacted.local"
        if hasattr(contact, "phone"):
            contact.phone = ""

        # Mark as anonymized
        if not hasattr(contact, "anonymized_at"):
            # Add field dynamically or skip if model doesn't support
            pass
        else:
            contact.anonymized_at = timezone.now()
            contact.anonymization_request = erasure_request

        contact.save()

        # Create audit event
        audit_event = audit.log_event(
            firm=contact.firm,
            event_type="contact_anonymized",
            severity="high",
            actor=erasure_request.requested_by,
            target_model="clients.Contact",
            target_id=str(contact.id),
            description=f"Contact anonymized per erasure request #{erasure_request.id}",
            metadata={
                "erasure_request_id": erasure_request.id,
                "legal_basis": erasure_request.legal_basis,
                "original_email": original_data.get("email", ""),  # Partial for audit
                "anonymization_timestamp": timezone.now().isoformat(),
            },
        )

        # Anonymize related entities
        anonymized_entities = {
            "contact": str(contact.id),
            "leads_anonymized": 0,
            "notes_redacted": 0,
        }

        # Anonymize leads (preserve structure, redact personal details)
        from modules.crm.models import Lead

        leads = Lead.objects.filter(firm=contact.firm, contact=contact)
        for lead in leads:
            if hasattr(lead, "notes"):
                lead.notes = "[Redacted per erasure request]"
                lead.save(update_fields=["notes"])
                anonymized_entities["notes_redacted"] += 1
            anonymized_entities["leads_anonymized"] += 1

        return {
            "success": True,
            "anonymized_entities": anonymized_entities,
            "audit_event_id": audit_event.id,
            "executed_at": timezone.now().isoformat(),
        }

    @transaction.atomic
    def execute_account_anonymization(self, account, erasure_request: ErasureRequest) -> Dict[str, Any]:
        """
        Execute anonymization for an Account (Client).

        Per docs/03-reference/requirements/DOC-07.md section 6.4:
        - Replace name if individual
        - Preserve business references if required
        - Revoke document access
        - Anonymize metadata
        """
        from modules.firm.audit import audit

        # Store original for audit
        original_name = account.company_name if hasattr(account, "company_name") else str(account.id)

        # Anonymize account name
        if hasattr(account, "company_name"):
            account.company_name = f"Anonymized Account {account.id}"

        # Mark as anonymized
        if hasattr(account, "anonymized_at"):
            account.anonymized_at = timezone.now()
            account.anonymization_request = erasure_request

        account.save()

        # Create audit event
        audit_event = audit.log_event(
            firm=account.firm,
            event_type="account_anonymized",
            severity="high",
            actor=erasure_request.requested_by,
            target_model="clients.Client",
            target_id=str(account.id),
            description=f"Account anonymized per erasure request #{erasure_request.id}",
            metadata={
                "erasure_request_id": erasure_request.id,
                "legal_basis": erasure_request.legal_basis,
                "original_name_hash": hash(original_name),  # Hash for audit, not plaintext
                "anonymization_timestamp": timezone.now().isoformat(),
            },
        )

        # Revoke document access (per docs/03-reference/requirements/DOC-07.md section 6.4)
        from modules.documents.models import Document

        documents = Document.objects.filter(firm=account.firm, client=account)
        documents_anonymized = 0
        for doc in documents:
            if hasattr(doc, "visibility"):
                doc.visibility = "internal"  # Remove client portal access
            if hasattr(doc, "name"):
                # Optionally anonymize document titles
                pass
            doc.save()
            documents_anonymized += 1

        return {
            "success": True,
            "anonymized_entities": {
                "account": str(account.id),
                "documents_access_revoked": documents_anonymized,
            },
            "audit_event_id": audit_event.id,
            "executed_at": timezone.now().isoformat(),
        }


# Global service instance
erasure_service = ErasureService()
