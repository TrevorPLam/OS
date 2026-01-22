"""
Data Governance Classifications and Registry

Implements the data classification system defined in docs/03-reference/requirements/DOC-07.md (DATA_GOVERNANCE).
This module provides:
- Classification level enums
- Field-level classification registry
- Utility functions for redaction and masking

Usage:
    from src.modules.core.governance import DataClassification, governance_registry

    # Check field classification
    classification = governance_registry.get_field_classification('Contact', 'email')

    # Redact sensitive data for logging
    safe_data = governance_registry.redact_for_logging(data_dict)
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass


class DataClassification(str, Enum):
    """
    Data classification levels as defined in docs/03-reference/requirements/DOC-07.md section 2.1.

    These levels determine how data is handled across APIs, UIs,
    background workers, integrations, and storage.
    """

    # Public - safe to display publicly, no PII
    PUBLIC = "PUB"

    # Internal - internal platform operational info
    INTERNAL = "INT"

    # Confidential - business-sensitive client data
    CONFIDENTIAL = "CONF"

    # Restricted PII - personal identifying data
    RESTRICTED_PII = "R-PII"

    # Highly Restricted - credentials, secrets, regulated identifiers
    HIGHLY_RESTRICTED = "HR"

    def requires_redaction_in_logs(self) -> bool:
        """Returns True if this classification level requires redaction in logs."""
        return self in (
            DataClassification.HIGHLY_RESTRICTED,
            DataClassification.RESTRICTED_PII,
        )

    def requires_masking_in_ui(self) -> bool:
        """Returns True if this classification level requires masking in UI by default."""
        return self == DataClassification.HIGHLY_RESTRICTED

    def requires_access_logging(self) -> bool:
        """Returns True if access to this data must be logged."""
        return self in (
            DataClassification.HIGHLY_RESTRICTED,
            DataClassification.RESTRICTED_PII,
            DataClassification.CONFIDENTIAL,
        )


@dataclass
class FieldClassification:
    """
    Represents the classification of a specific field.
    """

    entity: str
    field: str
    classification: DataClassification
    notes: Optional[str] = None


@dataclass
class EntityClassification:
    """
    Represents the default classification for an entity and field-level overrides.
    """

    entity: str
    default_classification: DataClassification
    field_overrides: Dict[str, DataClassification]
    notes: Optional[str] = None


class GovernanceRegistry:
    """
    Registry for data classification mappings.

    Implements the field-level classification registry as specified in docs/03-reference/requirements/DOC-07.md section 2.3.
    This registry is used by:
    - Serialization layers (API responses)
    - Logging redaction
    - Export tooling
    """

    def __init__(self):
        self._entity_classifications: Dict[str, EntityClassification] = {}
        self._initialize_baseline_classifications()

    def _initialize_baseline_classifications(self):
        """
        Initialize baseline classifications per docs/03-reference/requirements/DOC-07.md section 2.2.
        """

        # Account (docs/03-reference/requirements/DOC-07.md section 2.2)
        self.register_entity(
            EntityClassification(
                entity="Account",
                default_classification=DataClassification.CONFIDENTIAL,
                field_overrides={
                    "name": DataClassification.RESTRICTED_PII,  # Individual/household
                    "business_metadata": DataClassification.CONFIDENTIAL,
                },
                notes="Account name is R-PII for individuals, CONF for businesses",
            )
        )

        # Contact (docs/03-reference/requirements/DOC-07.md section 2.2)
        self.register_entity(
            EntityClassification(
                entity="Contact",
                default_classification=DataClassification.RESTRICTED_PII,
                field_overrides={
                    "name": DataClassification.RESTRICTED_PII,
                    "email": DataClassification.RESTRICTED_PII,
                    "phone": DataClassification.RESTRICTED_PII,
                    "role": DataClassification.INTERNAL,
                },
                notes="Contact information is personal identifying data",
            )
        )

        # Engagement / EngagementLine / WorkItem (docs/03-reference/requirements/DOC-07.md section 2.2)
        for entity in ["Engagement", "EngagementLine", "WorkItem"]:
            self.register_entity(
                EntityClassification(
                    entity=entity,
                    default_classification=DataClassification.CONFIDENTIAL,
                    field_overrides={
                        "title": DataClassification.CONFIDENTIAL,
                        "description": DataClassification.CONFIDENTIAL,
                        "notes": DataClassification.CONFIDENTIAL,
                    },
                    notes="May embed PII; treat as CONF by default",
                )
            )

        # Documents (docs/03-reference/requirements/DOC-07.md section 2.2)
        self.register_entity(
            EntityClassification(
                entity="Document",
                default_classification=DataClassification.CONFIDENTIAL,
                field_overrides={
                    "classification_label": DataClassification.INTERNAL,
                    "content": DataClassification.CONFIDENTIAL,  # May be R-PII or HR
                },
                notes="Classification label must be stored; may be R-PII or HR depending on content",
            )
        )

        # Communications (docs/03-reference/requirements/DOC-07.md section 2.2)
        self.register_entity(
            EntityClassification(
                entity="Communication",
                default_classification=DataClassification.CONFIDENTIAL,
                field_overrides={
                    "email_header": DataClassification.RESTRICTED_PII,
                    "from_address": DataClassification.RESTRICTED_PII,
                    "to_address": DataClassification.RESTRICTED_PII,
                    "subject": DataClassification.CONFIDENTIAL,
                    "body": DataClassification.CONFIDENTIAL,
                },
                notes="Email headers and addresses are R-PII",
            )
        )

        # Billing (docs/03-reference/requirements/DOC-07.md section 2.2)
        self.register_entity(
            EntityClassification(
                entity="Invoice",
                default_classification=DataClassification.CONFIDENTIAL,
                field_overrides={
                    "amount": DataClassification.CONFIDENTIAL,
                    "line_items": DataClassification.CONFIDENTIAL,
                    "payment_instrument": DataClassification.HIGHLY_RESTRICTED,
                },
                notes="Payment instrument references are HR if stored (prefer tokenization)",
            )
        )

        # Ledger (docs/03-reference/requirements/DOC-07.md section 2.2)
        self.register_entity(
            EntityClassification(
                entity="LedgerEntry",
                default_classification=DataClassification.CONFIDENTIAL,
                field_overrides={
                    "amount": DataClassification.CONFIDENTIAL,
                    "description": DataClassification.CONFIDENTIAL,
                },
                notes="Billing amounts and services are CONF",
            )
        )

        # Audit logs (docs/03-reference/requirements/DOC-07.md section 2.2)
        self.register_entity(
            EntityClassification(
                entity="AuditEvent",
                default_classification=DataClassification.INTERNAL,
                field_overrides={
                    "metadata": DataClassification.INTERNAL,
                    "payload": DataClassification.CONFIDENTIAL,  # Must avoid HR data
                },
                notes="MUST avoid payloads containing HR data",
            )
        )

    def register_entity(self, entity_classification: EntityClassification):
        """Register an entity with its default and field-level classifications."""
        self._entity_classifications[entity_classification.entity] = entity_classification

    def get_entity_classification(self, entity: str) -> Optional[EntityClassification]:
        """Get the classification configuration for an entity."""
        return self._entity_classifications.get(entity)

    def get_field_classification(
        self, entity: str, field: str
    ) -> Optional[DataClassification]:
        """
        Get the classification level for a specific entity field.

        Returns the field-specific override if it exists, otherwise the entity default.
        """
        entity_config = self._entity_classifications.get(entity)
        if not entity_config:
            return None

        # Check for field-level override
        if field in entity_config.field_overrides:
            return entity_config.field_overrides[field]

        # Return entity default
        return entity_config.default_classification

    def get_sensitive_fields(
        self, entity: str, min_classification: DataClassification = DataClassification.RESTRICTED_PII
    ) -> Set[str]:
        """
        Get all fields for an entity that are at or above the specified classification level.

        Useful for identifying fields that need redaction or special handling.
        """
        entity_config = self._entity_classifications.get(entity)
        if not entity_config:
            return set()

        sensitive_fields = set()

        # Check each field override
        for field, classification in entity_config.field_overrides.items():
            if self._is_at_least_as_sensitive(classification, min_classification):
                sensitive_fields.add(field)

        # If default classification is sensitive, all non-override fields are sensitive
        if self._is_at_least_as_sensitive(entity_config.default_classification, min_classification):
            # Return empty set to indicate "all fields not explicitly less sensitive"
            # This is conservative - caller should know entity schema
            pass

        return sensitive_fields

    def _is_at_least_as_sensitive(
        self, classification: DataClassification, minimum: DataClassification
    ) -> bool:
        """
        Check if a classification is at least as sensitive as the minimum.

        Sensitivity hierarchy (least to most):
        PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED_PII < HIGHLY_RESTRICTED
        """
        sensitivity_order = [
            DataClassification.PUBLIC,
            DataClassification.INTERNAL,
            DataClassification.CONFIDENTIAL,
            DataClassification.RESTRICTED_PII,
            DataClassification.HIGHLY_RESTRICTED,
        ]

        try:
            classification_level = sensitivity_order.index(classification)
            minimum_level = sensitivity_order.index(minimum)
            return classification_level >= minimum_level
        except ValueError:
            # Unknown classification, treat as sensitive
            return True

    def redact_for_logging(
        self, entity: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Redact sensitive fields from a data dictionary for safe logging.

        Per docs/03-reference/requirements/DOC-07.md section 3.3:
        - HR values always redacted
        - R-PII values masked unless required (partial masking)
        """
        redacted_data = data.copy()

        for field, value in data.items():
            classification = self.get_field_classification(entity, field)

            if classification == DataClassification.HIGHLY_RESTRICTED:
                # HR: Always redact completely
                redacted_data[field] = "***REDACTED***"
            elif classification == DataClassification.RESTRICTED_PII:
                # R-PII: Partial masking
                redacted_data[field] = self._mask_pii(value)

        return redacted_data

    def _mask_pii(self, value: Any) -> str:
        """
        Apply partial masking to PII values.

        Examples:
        - Email: j***@example.com
        - Phone: ***-***-1234
        - Name: J*** D***
        """
        if not isinstance(value, str):
            return "***MASKED***"

        if "@" in value:
            # Email: show first char and domain
            parts = value.split("@")
            if len(parts) == 2:
                return f"{parts[0][0]}***@{parts[1]}"

        if len(value) > 4:
            # Last 4 characters visible
            return f"***{value[-4:]}"

        # Too short to mask safely
        return "***MASKED***"

    def should_log_access(self, entity: str, field: Optional[str] = None) -> bool:
        """
        Determine if access to this entity/field should be logged.

        Per docs/03-reference/requirements/DOC-07.md section 3.4, access to governed artifacts must be logged.
        """
        if field:
            classification = self.get_field_classification(entity, field)
        else:
            entity_config = self.get_entity_classification(entity)
            classification = entity_config.default_classification if entity_config else None

        if classification:
            return classification.requires_access_logging()

        # Default to logging access for unknown classifications (conservative)
        return True


# Global registry instance
governance_registry = GovernanceRegistry()


# Utility functions for common redaction scenarios

def redact_for_logging(entity: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to redact data for logging.

    Usage:
        from src.modules.core.governance import redact_for_logging
        logger.info("Contact data: %s", redact_for_logging("Contact", contact_dict))
    """
    return governance_registry.redact_for_logging(entity, data)


def get_sensitive_fields(entity: str) -> Set[str]:
    """
    Convenience function to get sensitive fields for an entity.

    Usage:
        from src.modules.core.governance import get_sensitive_fields
        sensitive = get_sensitive_fields("Contact")
    """
    return governance_registry.get_sensitive_fields(entity)


def requires_access_logging(entity: str, field: Optional[str] = None) -> bool:
    """
    Convenience function to check if access logging is required.

    Usage:
        from src.modules.core.governance import requires_access_logging
        if requires_access_logging("Document"):
            log_access_event(user, document)
    """
    return governance_registry.should_log_access(entity, field)
