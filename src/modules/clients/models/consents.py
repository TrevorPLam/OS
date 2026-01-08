import hashlib
import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


class ConsentRecord(models.Model):
    """
    Immutable consent ledger for tracking all consent grants and revocations (CRM-INT-4).
    
    This model implements a blockchain-style append-only ledger for GDPR/CCPA compliance.
    Records cannot be modified or deleted once created - only new records can be added.
    Each record is cryptographically linked to the previous record via hash chaining.
    
    TIER 0: Belongs to exactly one Firm (via contact relationship).
    """
    
    # Consent types
    CONSENT_TYPE_MARKETING = "marketing"
    CONSENT_TYPE_EMAIL = "email"
    CONSENT_TYPE_SMS = "sms"
    CONSENT_TYPE_PHONE = "phone"
    CONSENT_TYPE_DATA_PROCESSING = "data_processing"
    CONSENT_TYPE_DATA_SHARING = "data_sharing"
    CONSENT_TYPE_ANALYTICS = "analytics"
    CONSENT_TYPE_PROFILING = "profiling"
    CONSENT_TYPE_TOS = "terms_of_service"
    CONSENT_TYPE_PRIVACY_POLICY = "privacy_policy"
    
    CONSENT_TYPE_CHOICES = [
        (CONSENT_TYPE_MARKETING, "Marketing Communications"),
        (CONSENT_TYPE_EMAIL, "Email Communications"),
        (CONSENT_TYPE_SMS, "SMS Communications"),
        (CONSENT_TYPE_PHONE, "Phone Communications"),
        (CONSENT_TYPE_DATA_PROCESSING, "Data Processing"),
        (CONSENT_TYPE_DATA_SHARING, "Data Sharing with Third Parties"),
        (CONSENT_TYPE_ANALYTICS, "Analytics & Tracking"),
        (CONSENT_TYPE_PROFILING, "Profiling & Automated Decision Making"),
        (CONSENT_TYPE_TOS, "Terms of Service"),
        (CONSENT_TYPE_PRIVACY_POLICY, "Privacy Policy"),
    ]
    
    # Consent actions
    ACTION_GRANTED = "granted"
    ACTION_REVOKED = "revoked"
    ACTION_UPDATED = "updated"
    
    ACTION_CHOICES = [
        (ACTION_GRANTED, "Consent Granted"),
        (ACTION_REVOKED, "Consent Revoked"),
        (ACTION_UPDATED, "Consent Updated"),
    ]

    # Consent methods (CAN-SPAM consent classification)
    CONSENT_METHOD_EXPRESS = "express"
    CONSENT_METHOD_IMPLIED = "implied"

    CONSENT_METHOD_CHOICES = [
        (CONSENT_METHOD_EXPRESS, "Express Consent"),
        (CONSENT_METHOD_IMPLIED, "Implied Consent"),
    ]
    
    # Legal basis for processing (GDPR Article 6)
    LEGAL_BASIS_CONSENT = "consent"
    LEGAL_BASIS_CONTRACT = "contract"
    LEGAL_BASIS_LEGAL_OBLIGATION = "legal_obligation"
    LEGAL_BASIS_VITAL_INTERESTS = "vital_interests"
    LEGAL_BASIS_PUBLIC_TASK = "public_task"
    LEGAL_BASIS_LEGITIMATE_INTERESTS = "legitimate_interests"
    
    LEGAL_BASIS_CHOICES = [
        (LEGAL_BASIS_CONSENT, "Consent (GDPR Art. 6.1.a)"),
        (LEGAL_BASIS_CONTRACT, "Contract Performance (GDPR Art. 6.1.b)"),
        (LEGAL_BASIS_LEGAL_OBLIGATION, "Legal Obligation (GDPR Art. 6.1.c)"),
        (LEGAL_BASIS_VITAL_INTERESTS, "Vital Interests (GDPR Art. 6.1.d)"),
        (LEGAL_BASIS_PUBLIC_TASK, "Public Task (GDPR Art. 6.1.e)"),
        (LEGAL_BASIS_LEGITIMATE_INTERESTS, "Legitimate Interests (GDPR Art. 6.1.f)"),
    ]
    
    # Data categories being consented to
    DATA_CATEGORY_PERSONAL = "personal"
    DATA_CATEGORY_CONTACT = "contact"
    DATA_CATEGORY_FINANCIAL = "financial"
    DATA_CATEGORY_BEHAVIORAL = "behavioral"
    DATA_CATEGORY_LOCATION = "location"
    DATA_CATEGORY_DEVICE = "device"
    
    DATA_CATEGORY_CHOICES = [
        (DATA_CATEGORY_PERSONAL, "Personal Identifiable Information"),
        (DATA_CATEGORY_CONTACT, "Contact Information"),
        (DATA_CATEGORY_FINANCIAL, "Financial Information"),
        (DATA_CATEGORY_BEHAVIORAL, "Behavioral Data"),
        (DATA_CATEGORY_LOCATION, "Location Data"),
        (DATA_CATEGORY_DEVICE, "Device Information"),
    ]
    
    # TIER 0: Firm tenancy (via contact)
    contact = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,  # PROTECT: never delete consent records
        related_name="consent_records",
        help_text="Contact this consent record belongs to"
    )
    
    # Consent details
    consent_type = models.CharField(
        max_length=50,
        choices=CONSENT_TYPE_CHOICES,
        help_text="Type of consent being tracked"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Action taken (granted/revoked/updated)"
    )
    
    # GDPR/CCPA compliance fields
    legal_basis = models.CharField(
        max_length=50,
        choices=LEGAL_BASIS_CHOICES,
        default=LEGAL_BASIS_CONSENT,
        help_text="Legal basis for processing (GDPR Article 6)"
    )
    data_categories = models.JSONField(
        default=list,
        help_text="List of data categories this consent applies to"
    )
    
    # Consent text and version tracking
    consent_text = models.TextField(
        blank=True,
        help_text="The exact consent text shown to the user"
    )
    consent_version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Version of the consent text (e.g., 'v1.2', '2024-01-01')"
    )
    consent_method = models.CharField(
        max_length=20,
        choices=CONSENT_METHOD_CHOICES,
        null=True,
        blank=True,
        help_text="Whether consent was express or implied"
    )
    
    # Source and context
    source = models.CharField(
        max_length=100,
        help_text="Source of consent (e.g., 'signup_form', 'email_campaign', 'portal_settings')"
    )
    source_url = models.URLField(
        blank=True,
        validators=[validate_safe_url],
        help_text="URL where consent was captured (if applicable)"
    )
    
    # Audit trail
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this consent action occurred (immutable)"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address from which consent was given/revoked"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string from the browser/client"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consent_records_created",
        help_text="User who created this record (if action was performed by staff)"
    )
    
    # Blockchain-style chain verification
    previous_record_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 hash of the previous consent record for this contact+type (chain verification)"
    )
    record_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of this record for chain verification (computed on save)"
    )
    
    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (e.g., campaign_id, form_id, referrer)"
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about this consent record"
    )
    
    class Meta:
        db_table = "clients_consent_record"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["contact", "consent_type", "-timestamp"], name="consent_contact_type_idx"),
            models.Index(fields=["contact", "-timestamp"], name="consent_contact_time_idx"),
            models.Index(fields=["consent_type", "-timestamp"], name="consent_type_time_idx"),
            models.Index(fields=["action", "-timestamp"], name="consent_action_time_idx"),
            models.Index(fields=["record_hash"], name="consent_hash_idx"),
        ]
        # Prevent modifications by using database-level constraints (if supported)
        permissions = [
            ("view_consent_chain", "Can view consent chain verification"),
            ("export_consent_proof", "Can export consent proof"),
        ]
    
    def __str__(self):
        return f"{self.contact.full_name} - {self.get_consent_type_display()} - {self.get_action_display()} ({self.timestamp})"
    
    def save(self, *args, **kwargs):
        """
        Override save to compute record hash and prevent modifications.
        
        Raises:
            ValueError: If attempting to modify an existing record
        """
        # Prevent modifications to existing records (immutability)
        if self.pk is not None:
            raise ValueError(
                "ConsentRecord is immutable. Cannot modify existing consent records. "
                "Create a new record instead."
            )
        
        # Get the previous record hash for chain verification
        if not self.previous_record_hash:
            previous_record = ConsentRecord.objects.filter(
                contact=self.contact,
                consent_type=self.consent_type
            ).order_by("-timestamp").first()
            
            if previous_record:
                self.previous_record_hash = previous_record.record_hash
            else:
                # First record in the chain for this contact+type
                self.previous_record_hash = "0" * 64  # Genesis block
        
        # Compute the record hash
        if not self.record_hash:
            # Ensure timestamp is set (should be auto-set by auto_now_add)
            if not self.timestamp:
                raise ValueError("Timestamp must be set before computing hash")
            
            hash_data = {
                "contact_id": self.contact_id,
                "consent_type": self.consent_type,
                "action": self.action,
                "timestamp": self.timestamp.isoformat(),
                "previous_hash": self.previous_record_hash,
                "legal_basis": self.legal_basis,
                "data_categories": sorted(self.data_categories) if self.data_categories else [],
                "source": self.source,
            }
            hash_string = json.dumps(hash_data, sort_keys=True)
            self.record_hash = hashlib.sha256(hash_string.encode()).hexdigest()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Prevent deletion of consent records (immutability).
        
        Raises:
            ValueError: Always - consent records cannot be deleted
        """
        raise ValueError(
            "ConsentRecord is immutable. Cannot delete consent records. "
            "They must be retained for compliance purposes."
        )
    
    @classmethod
    def verify_chain(cls, contact, consent_type=None):
        """
        Verify the integrity of the consent chain for a contact.
        
        Args:
            contact: Contact instance to verify chain for
            consent_type: Optional consent type to verify (if None, verifies all types)
        
        Returns:
            dict: Verification result with status and details
                {
                    'valid': bool,
                    'records_verified': int,
                    'errors': list of error messages (if any)
                }
        """
        filters = {"contact": contact}
        if consent_type:
            filters["consent_type"] = consent_type
        
        records = cls.objects.filter(**filters).order_by("timestamp")
        
        errors = []
        verified_count = 0
        expected_previous_hash = "0" * 64  # Genesis
        
        for record in records:
            # Verify the previous hash matches
            if record.previous_record_hash != expected_previous_hash:
                errors.append(
                    f"Record {record.id} has invalid previous_hash. "
                    f"Expected: {expected_previous_hash}, Got: {record.previous_record_hash}"
                )
            
            # Verify the record hash is correct (imports at top of file)
            hash_data = {
                "contact_id": record.contact_id,
                "consent_type": record.consent_type,
                "action": record.action,
                "timestamp": record.timestamp.isoformat(),
                "previous_hash": record.previous_record_hash,
                "legal_basis": record.legal_basis,
                "data_categories": sorted(record.data_categories) if record.data_categories else [],
                "source": record.source,
            }
            hash_string = json.dumps(hash_data, sort_keys=True)
            computed_hash = hashlib.sha256(hash_string.encode()).hexdigest()
            
            if record.record_hash != computed_hash:
                errors.append(
                    f"Record {record.id} has invalid record_hash. "
                    f"Expected: {computed_hash}, Got: {record.record_hash}"
                )
            
            verified_count += 1
            expected_previous_hash = record.record_hash
        
        return {
            "valid": len(errors) == 0,
            "records_verified": verified_count,
            "errors": errors
        }
    
    @classmethod
    def get_current_consent(cls, contact, consent_type):
        """
        Get the current consent status for a contact and consent type.
        
        Args:
            contact: Contact instance
            consent_type: Consent type to check
        
        Returns:
            dict: Current consent status
                {
                    'has_consent': bool,
                    'latest_action': str (granted/revoked/updated),
                    'timestamp': datetime,
                    'record': ConsentRecord instance
                }
        """
        latest_record = cls.objects.filter(
            contact=contact,
            consent_type=consent_type
        ).order_by("-timestamp").first()
        
        if not latest_record:
            return {
                "has_consent": False,
                "latest_action": None,
                "timestamp": None,
                "record": None
            }
        
        return {
            "has_consent": latest_record.action == cls.ACTION_GRANTED,
            "latest_action": latest_record.action,
            "timestamp": latest_record.timestamp,
            "record": latest_record
        }
    
    @classmethod
    def export_consent_proof(cls, contact, consent_type=None):
        """
        Export consent proof for a contact (GDPR right to access).
        
        Args:
            contact: Contact instance
            consent_type: Optional consent type to export (if None, exports all)
        
        Returns:
            dict: Complete consent history and verification
        """
        filters = {"contact": contact}
        if consent_type:
            filters["consent_type"] = consent_type
        
        records = cls.objects.filter(**filters).order_by("timestamp")
        
        # Verify chain integrity
        verification = cls.verify_chain(contact, consent_type)
        
        # Build export data
        export_data = {
            "contact": {
                "id": contact.id,
                "name": contact.full_name,
                "email": contact.email,
            },
            "export_timestamp": timezone.now().isoformat(),
            "chain_verification": verification,
            "consent_records": []
        }
        
        for record in records:
            export_data["consent_records"].append({
                "id": record.id,
                "consent_type": record.consent_type,
                "consent_type_display": record.get_consent_type_display(),
                "action": record.action,
                "action_display": record.get_action_display(),
                "legal_basis": record.legal_basis,
                "legal_basis_display": record.get_legal_basis_display(),
                "data_categories": record.data_categories,
                "consent_text": record.consent_text,
                "consent_version": record.consent_version,
                "consent_method": record.consent_method,
                "consent_method_display": record.get_consent_method_display()
                if record.consent_method
                else None,
                "source": record.source,
                "source_url": record.source_url,
                "timestamp": record.timestamp.isoformat(),
                "ip_address": record.ip_address,
                "user_agent": record.user_agent,
                "actor": record.actor.email if record.actor else None,
                "previous_record_hash": record.previous_record_hash,
                "record_hash": record.record_hash,
                "metadata": record.metadata,
                "notes": record.notes,
            })
        
        return export_data
