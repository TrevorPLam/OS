"""Knowledge System Serializers (DOC-35.1)."""

from rest_framework import serializers
from .models import KnowledgeItem, KnowledgeVersion, KnowledgeReview, KnowledgeAttachment


class KnowledgeItemSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    
    class Meta:
        model = KnowledgeItem
        fields = [
            "id", "type", "title", "summary", "status", "version_number",
            "owner", "owner_name", "tags", "category", "access_level",
            "published_at", "deprecated_at", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "version_number", "published_at", "deprecated_at", "created_at", "updated_at"]


class KnowledgeItemDetailSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    
    class Meta:
        model = KnowledgeItem
        fields = "__all__"
        read_only_fields = ["id", "firm", "version_number", "published_at", "deprecated_at", 
                            "created_at", "created_by", "updated_at", "updated_by"]


class KnowledgeVersionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    
    class Meta:
        model = KnowledgeVersion
        fields = "__all__"
        read_only_fields = fields


class KnowledgeReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.get_full_name", read_only=True)
    requested_by_name = serializers.CharField(source="requested_by.get_full_name", read_only=True)
    
    class Meta:
        model = KnowledgeReview
        fields = "__all__"
        read_only_fields = ["id", "firm", "requested_at", "requested_by", "reviewed_at"]


class KnowledgeAttachmentSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    
    class Meta:
        model = KnowledgeAttachment
        fields = "__all__"
        read_only_fields = ["id", "firm", "created_at", "created_by"]
