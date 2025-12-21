"""
Serializers for Clients module.
"""
from rest_framework import serializers
from modules.clients.models import Client, ClientPortalUser, ClientNote, ClientEngagement


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model."""

    account_manager_name = serializers.SerializerMethodField()
    assigned_team_names = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            'id',
            'source_prospect',
            'source_proposal',
            'company_name',
            'industry',
            'primary_contact_name',
            'primary_contact_email',
            'primary_contact_phone',
            'street_address',
            'city',
            'state',
            'postal_code',
            'country',
            'website',
            'employee_count',
            'status',
            'account_manager',
            'account_manager_name',
            'assigned_team',
            'assigned_team_names',
            'portal_enabled',
            'total_lifetime_value',
            'active_projects_count',
            'client_since',
            'created_at',
            'updated_at',
            'notes',
        ]
        read_only_fields = [
            'id',
            'source_prospect',
            'source_proposal',
            'total_lifetime_value',
            'active_projects_count',
            'created_at',
            'updated_at',
        ]

    def get_account_manager_name(self, obj):
        """Get account manager's full name."""
        if obj.account_manager:
            return f"{obj.account_manager.first_name} {obj.account_manager.last_name}".strip()
        return None

    def get_assigned_team_names(self, obj):
        """Get names of assigned team members."""
        return [
            {
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}".strip() or user.username
            }
            for user in obj.assigned_team.all()
        ]


class ClientPortalUserSerializer(serializers.ModelSerializer):
    """Serializer for ClientPortalUser model."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    client_name = serializers.CharField(source='client.company_name', read_only=True)

    class Meta:
        model = ClientPortalUser
        fields = [
            'id',
            'client',
            'client_name',
            'user',
            'user_email',
            'user_name',
            'role',
            'can_upload_documents',
            'can_view_billing',
            'can_message_team',
            'can_view_projects',
            'invited_by',
            'invited_at',
            'last_login',
        ]
        read_only_fields = ['id', 'invited_by', 'invited_at']

    def get_user_name(self, obj):
        """Get user's full name."""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


class ClientNoteSerializer(serializers.ModelSerializer):
    """Serializer for ClientNote model."""

    author_name = serializers.SerializerMethodField()
    client_name = serializers.CharField(source='client.company_name', read_only=True)

    class Meta:
        model = ClientNote
        fields = [
            'id',
            'client',
            'client_name',
            'author',
            'author_name',
            'note',
            'is_pinned',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_author_name(self, obj):
        """Get author's full name."""
        if obj.author:
            return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.username
        return None

    def create(self, validated_data):
        """Set author from request user."""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ClientEngagementSerializer(serializers.ModelSerializer):
    """Serializer for ClientEngagement model."""

    client_name = serializers.CharField(source='client.company_name', read_only=True)
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    parent_engagement_version = serializers.IntegerField(source='parent_engagement.version', read_only=True)

    class Meta:
        model = ClientEngagement
        fields = [
            'id',
            'client',
            'client_name',
            'contract',
            'contract_number',
            'status',
            'version',
            'parent_engagement',
            'parent_engagement_version',
            'start_date',
            'end_date',
            'actual_end_date',
            'contracted_value',
            'actual_revenue',
            'created_at',
            'updated_at',
            'notes',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
