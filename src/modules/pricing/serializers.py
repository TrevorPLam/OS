"""
Serializers for Pricing module (DOC-09.2).

Implements API serialization for:
- RuleSet: Versioned pricing rule collections
- Quote: Mutable working drafts
- QuoteVersion: Immutable pricing snapshots for audit
- QuoteLineItem: Line items within quote versions

TIER 0: All serializers respect firm tenancy.
DOC-09.2: QuoteVersion is read-only once issued for audit purposes.
"""

from rest_framework import serializers

from modules.pricing.models import Quote, QuoteLineItem, QuoteVersion, RuleSet


class RuleSetSerializer(serializers.ModelSerializer):
    """
    Serializer for RuleSet model.

    DOC-09.1: RuleSets are versioned pricing rule collections.
    Published rulesets are immutable.
    """

    created_by_name = serializers.SerializerMethodField()
    is_published = serializers.SerializerMethodField()

    class Meta:
        model = RuleSet
        fields = [
            "id",
            "firm",
            "name",
            "code",
            "version",
            "schema_version",
            "rules_json",
            "checksum",
            "status",
            "published_at",
            "deprecated_at",
            "default_currency",
            "created_at",
            "created_by",
            "created_by_name",
            "updated_at",
            "is_published",
        ]
        read_only_fields = [
            "firm",
            "checksum",
            "created_at",
            "created_by",
            "updated_at",
            "published_at",
            "deprecated_at",
        ]

    def get_created_by_name(self, obj):
        """Return name of user who created this ruleset."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def get_is_published(self, obj):
        """Return whether this ruleset is published."""
        return obj.status == "published"

    def validate(self, attrs):
        """Validate that published rulesets cannot be modified."""
        if self.instance and self.instance.status == "published":
            raise serializers.ValidationError(
                "Published rulesets cannot be modified. Create a new version instead."
            )
        return attrs


class RuleSetListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for RuleSet list view.

    Excludes heavy rules_json field for performance.
    """

    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = RuleSet
        fields = [
            "id",
            "name",
            "code",
            "version",
            "schema_version",
            "status",
            "published_at",
            "default_currency",
            "created_at",
            "created_by_name",
        ]
        read_only_fields = fields

    def get_created_by_name(self, obj):
        """Return name of user who created this ruleset."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class QuoteLineItemSerializer(serializers.ModelSerializer):
    """
    Serializer for QuoteLineItem model.

    DOC-09.1: Line items map to EngagementLine candidates.
    """

    class Meta:
        model = QuoteLineItem
        fields = [
            "id",
            "line_number",
            "product_code",
            "name",
            "description",
            "quantity",
            "unit_price",
            "amount",
            "billing_model",
            "billing_unit",
            "notes",
            "tax_category",
        ]
        read_only_fields = ["id"]


class QuoteVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for QuoteVersion model.

    DOC-09.2: QuoteVersion is immutable snapshot for audit.
    Once issued, cannot be modified - only retrieved for audit purposes.
    """

    line_item_records = QuoteLineItemSerializer(many=True, read_only=True)
    issued_by_name = serializers.SerializerMethodField()
    accepted_by_name = serializers.SerializerMethodField()
    ruleset_name = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = QuoteVersion
        fields = [
            "id",
            "firm",
            "quote",
            "version_number",
            "ruleset",
            "ruleset_name",
            "ruleset_checksum",
            "context_snapshot",
            "line_items",
            "totals",
            "assumptions",
            "warnings",
            "evaluation_trace",
            "outputs_checksum",
            "currency",
            "status",
            "issued_at",
            "issued_by",
            "issued_by_name",
            "accepted_at",
            "accepted_by",
            "accepted_by_name",
            "created_at",
            "correlation_id",
            "line_item_records",
            "total_amount",
        ]
        read_only_fields = [
            "id",
            "firm",
            "ruleset_checksum",
            "outputs_checksum",
            "created_at",
            "issued_at",
            "issued_by",
            "accepted_at",
            "accepted_by",
        ]

    def get_issued_by_name(self, obj):
        """Return name of user who issued this quote version."""
        if obj.issued_by:
            return obj.issued_by.get_full_name() or obj.issued_by.username
        return None

    def get_accepted_by_name(self, obj):
        """Return name of user who accepted this quote version."""
        if obj.accepted_by:
            return obj.accepted_by.get_full_name() or obj.accepted_by.username
        return None

    def get_ruleset_name(self, obj):
        """Return name of the ruleset used for evaluation."""
        return f"{obj.ruleset.name} v{obj.ruleset.version}"

    def validate(self, attrs):
        """
        Validate that accepted quote versions cannot be modified.

        DOC-09.2: Immutability enforcement for accepted quotes.
        """
        if self.instance and self.instance.status == "accepted":
            # Check if any critical fields are being modified
            critical_fields = [
                "context_snapshot",
                "line_items",
                "totals",
                "evaluation_trace",
            ]
            for field in critical_fields:
                if field in attrs and attrs[field] != getattr(self.instance, field):
                    raise serializers.ValidationError(
                        {field: "Accepted quote versions cannot be modified. Create a new version instead."}
                    )
        return attrs


class QuoteVersionListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for QuoteVersion list view.

    Excludes heavy trace and context fields for performance.
    """

    issued_by_name = serializers.SerializerMethodField()
    accepted_by_name = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = QuoteVersion
        fields = [
            "id",
            "quote",
            "version_number",
            "status",
            "currency",
            "total_amount",
            "issued_at",
            "issued_by_name",
            "accepted_at",
            "accepted_by_name",
            "created_at",
        ]
        read_only_fields = fields

    def get_issued_by_name(self, obj):
        """Return name of user who issued this quote version."""
        if obj.issued_by:
            return obj.issued_by.get_full_name() or obj.issued_by.username
        return None

    def get_accepted_by_name(self, obj):
        """Return name of user who accepted this quote version."""
        if obj.accepted_by:
            return obj.accepted_by.get_full_name() or obj.accepted_by.username
        return None


class QuoteSerializer(serializers.ModelSerializer):
    """
    Serializer for Quote model.

    DOC-09.1: Quote is mutable working draft before snapshotting.
    """

    created_by_name = serializers.SerializerMethodField()
    current_version_details = QuoteVersionListSerializer(
        source="current_version",
        read_only=True,
    )
    client_name = serializers.CharField(source="client.company_name", read_only=True)

    class Meta:
        model = Quote
        fields = [
            "id",
            "firm",
            "quote_number",
            "client",
            "client_name",
            "status",
            "current_version",
            "current_version_details",
            "valid_until",
            "created_at",
            "created_by",
            "created_by_name",
            "updated_at",
        ]
        read_only_fields = [
            "firm",
            "created_at",
            "created_by",
            "updated_at",
        ]

    def get_created_by_name(self, obj):
        """Return name of user who created this quote."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class QuoteListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for Quote list view.
    """

    client_name = serializers.CharField(source="client.company_name", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Quote
        fields = [
            "id",
            "quote_number",
            "client_name",
            "status",
            "valid_until",
            "created_at",
            "created_by_name",
        ]
        read_only_fields = fields

    def get_created_by_name(self, obj):
        """Return name of user who created this quote."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None
