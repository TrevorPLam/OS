"""
Governance-Aware Serializers (DOC-07.1)

Provides DRF serializer mixins that integrate with the governance classification registry
to ensure proper data handling based on classification levels.

Usage:
    from modules.core.serializer_mixins import GovernanceAwareSerializerMixin

    class ClientSerializer(GovernanceAwareSerializerMixin, serializers.ModelSerializer):
        class Meta:
            model = Client
            fields = '__all__'
"""

from typing import Any, Optional

from rest_framework import serializers

from modules.core.governance import (
    DataClassification,
    governance_registry,
    redact_for_logging,
)


class GovernanceAwareSerializerMixin:
    """
    Mixin for DRF serializers to support classification-based field handling.

    Features:
    - Automatic redaction of HR fields for portal users
    - Support for 'redact_for_logging' context flag
    - Audit logging hooks for sensitive field access

    Set 'governance_entity' in Meta class to specify the entity name for classification lookup.
    If not set, uses the model class name.
    """

    def get_governance_entity(self) -> str:
        """Get the entity name for governance classification lookup."""
        meta = getattr(self, "Meta", None)
        if meta and hasattr(meta, "governance_entity"):
            return meta.governance_entity
        if meta and hasattr(meta, "model"):
            return meta.model.__name__
        return self.__class__.__name__.replace("Serializer", "")

    def should_redact_field(self, field_name: str) -> bool:
        """
        Determine if a field should be redacted based on context.

        Redaction applies when:
        - The context includes 'redact_for_logging=True'
        - The request user is a portal user and field is HR-classified
        """
        context = getattr(self, "context", {})

        # Explicit redaction for logging
        if context.get("redact_for_logging"):
            entity = self.get_governance_entity()
            classification = governance_registry.get_field_classification(entity, field_name)
            return classification and classification.requires_redaction_in_logs()

        # Portal user restrictions for HR fields
        request = context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            if hasattr(user, "is_portal_user") and user.is_portal_user:
                entity = self.get_governance_entity()
                classification = governance_registry.get_field_classification(entity, field_name)
                return classification == DataClassification.HIGHLY_RESTRICTED

        return False

    def redact_value(self, value: Any, field_name: str) -> Any:
        """Redact a value based on governance rules."""
        entity = self.get_governance_entity()
        classification = governance_registry.get_field_classification(entity, field_name)

        if classification == DataClassification.HIGHLY_RESTRICTED:
            return "[REDACTED]"
        elif classification == DataClassification.RESTRICTED_PII:
            return governance_registry._mask_pii(value)
        return value

    def to_representation(self, instance) -> dict:
        """Override to apply governance-based redaction."""
        data = super().to_representation(instance)

        # Check each field for redaction
        fields_to_redact = [
            field_name
            for field_name in data.keys()
            if self.should_redact_field(field_name)
        ]

        for field_name in fields_to_redact:
            data[field_name] = self.redact_value(data[field_name], field_name)

        return data


class ExportSerializerMixin(GovernanceAwareSerializerMixin):
    """
    Mixin for serializers used in data exports.

    Provides additional filtering to exclude HR fields from exports
    and optionally include/exclude R-PII fields.

    Usage:
        class ClientExportSerializer(ExportSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = Client
                fields = '__all__'
                exclude_pii = True  # Set to False to include R-PII in exports
    """

    def get_fields(self):
        """Filter fields based on export governance rules."""
        fields = super().get_fields()
        entity = self.get_governance_entity()

        # Check if we should exclude PII
        meta = getattr(self, "Meta", None)
        exclude_pii = getattr(meta, "exclude_pii", True)

        # Filter out fields based on classification
        filtered_fields = {}
        for field_name, field in fields.items():
            classification = governance_registry.get_field_classification(entity, field_name)

            # Always exclude HR fields from exports
            if classification == DataClassification.HIGHLY_RESTRICTED:
                continue

            # Optionally exclude R-PII fields
            if exclude_pii and classification == DataClassification.RESTRICTED_PII:
                continue

            filtered_fields[field_name] = field

        return filtered_fields


def serialize_for_logging(serializer_class, instance) -> dict:
    """
    Serialize an instance with redaction for logging.

    This is a convenience function for getting a log-safe representation
    of a model instance.

    Usage:
        from modules.core.serializer_mixins import serialize_for_logging
        from api.clients.serializers import ClientSerializer

        logger.info("Client updated: %s", serialize_for_logging(ClientSerializer, client))
    """
    serializer = serializer_class(instance, context={"redact_for_logging": True})
    return serializer.data
