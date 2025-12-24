"""
Serializers for Clients module.
"""
from rest_framework import serializers
from modules.clients.models import (
    Client,
    ClientPortalUser,
    ClientNote,
    ClientEngagement,
    ClientComment,
    ClientChatThread,
    ClientMessage,
    ClientMessageContent,
    ClientNoteContent,
    ClientCommentContent,
)


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
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)

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
        note_body = validated_data.pop('note', '') or ''
        validated_data['author'] = self.context['request'].user
        note = super().create(validated_data)
        ClientNoteContent.objects.create(note=note, body=note_body)
        return note

    def update(self, instance, validated_data):
        note_body = validated_data.pop('note', None)
        instance = super().update(instance, validated_data)
        if note_body is not None:
            content_record, _created = ClientNoteContent.objects.get_or_create(
                note=instance,
                defaults={'body': note_body or ''},
            )
            if not _created:
                content_record.body = note_body or ''
                content_record.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and getattr(request, 'platform_role', None) == 'operator':
            data.pop('note', None)
            return data

        try:
            content = instance.content
        except ClientNoteContent.DoesNotExist:
            content = None

        data['note'] = content.body if content else ''
        return data

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and getattr(request, 'platform_role', None) == 'operator':
            fields.pop('note', None)
        return fields


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


class ClientCommentSerializer(serializers.ModelSerializer):
    """Serializer for ClientComment model."""

    author_name = serializers.SerializerMethodField()
    author_email = serializers.EmailField(source='user.email', read_only=True)
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_project = serializers.SerializerMethodField()
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = ClientComment
        fields = [
            'id',
            'client',
            'client_name',
            'task',
            'task_title',
            'task_project',
            'author',
            'author_name',
            'author_email',
            'comment',
            'has_attachment',
            'is_read_by_firm',
            'read_by',
            'read_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'author',
            'is_read_by_firm',
            'read_by',
            'read_at',
            'created_at',
            'updated_at',
        ]

    def get_author_name(self, obj):
        """Get author's full name."""
        if obj.author:
            return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.username
        return None

    def get_task_project(self, obj):
        """Get task's project info."""
        if obj.task and obj.task.project:
            return {
                'id': obj.task.project.id,
                'name': obj.task.project.name,
                'project_code': obj.task.project.project_code if hasattr(obj.task.project, 'project_code') else None,
            }
        return None

    def create(self, validated_data):
        """Set author and client from request context."""
        request = self.context.get('request')
        comment_body = validated_data.pop('comment', '') or ''
        validated_data['author'] = request.user

        # Get client from portal user
        from modules.clients.models import ClientPortalUser
        try:
            portal_user = ClientPortalUser.objects.get(user=request.user)
            validated_data['client'] = portal_user.client
        except ClientPortalUser.DoesNotExist:
            raise serializers.ValidationError("User is not a client portal user")

        comment = super().create(validated_data)
        ClientCommentContent.objects.create(comment=comment, body=comment_body)
        return comment

    def update(self, instance, validated_data):
        comment_body = validated_data.pop('comment', None)
        instance = super().update(instance, validated_data)
        if comment_body is not None:
            content_record, _created = ClientCommentContent.objects.get_or_create(
                comment=instance,
                defaults={'body': comment_body or ''},
            )
            if not _created:
                content_record.body = comment_body or ''
                content_record.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and getattr(request, 'platform_role', None) == 'operator':
            data.pop('comment', None)
            return data

        try:
            content = instance.content
        except ClientCommentContent.DoesNotExist:
            content = None

        data['comment'] = content.body if content else ''
        return data

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and getattr(request, 'platform_role', None) == 'operator':
            fields.pop('comment', None)
        return fields


class ClientTaskSerializer(serializers.ModelSerializer):
    """
    Client-facing Task serializer (read-only).

    Shows task details without exposing sensitive firm information.
    """
    assigned_to_name = serializers.SerializerMethodField()
    hours_logged = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        from modules.projects.models import Task
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'priority',
            'position',
            'estimated_hours',
            'due_date',
            'completed_at',
            'created_at',
            'updated_at',
            'assigned_to_name',
            'hours_logged',
            'comments',
            'progress_percentage',
        ]
        read_only_fields = fields  # All fields are read-only for clients

    def get_assigned_to_name(self, obj):
        """Get assigned team member's name (hide sensitive info)."""
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip() or "Team Member"
        return None

    def get_hours_logged(self, obj):
        """Calculate total hours logged for this task."""
        from django.db.models import Sum
        total = obj.time_entries.aggregate(total=Sum('hours'))['total']
        return float(total) if total else 0.0

    def get_comments(self, obj):
        """Get client comments for this task."""
        from modules.clients.models import ClientComment
        comments = ClientComment.objects.filter(task=obj).select_related('content').order_by('-created_at')[:10]
        return [{
            'id': comment.id,
            'author_name': comment.author.get_full_name() or comment.author.username,
            'comment': comment.content.body if hasattr(comment, 'content') else '',
            'created_at': comment.created_at,
        } for comment in comments]

    def get_progress_percentage(self, obj):
        """Calculate progress percentage based on status."""
        status_progress = {
            'todo': 0,
            'in_progress': 50,
            'review': 75,
            'done': 100,
        }
        return status_progress.get(obj.status, 0)


class ClientProjectSerializer(serializers.ModelSerializer):
    """
    Client-facing Project serializer (read-only).

    Shows project details with tasks, suitable for client portal.
    Hides sensitive firm information like hourly rates and internal notes.
    """
    project_manager_name = serializers.SerializerMethodField()
    tasks = ClientTaskSerializer(many=True, read_only=True, source='tasks_set')
    total_hours_logged = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    tasks_summary = serializers.SerializerMethodField()

    class Meta:
        from modules.projects.models import Project
        model = Project
        fields = [
            'id',
            'project_code',
            'name',
            'description',
            'status',
            'budget',  # Show budget but hide hourly_rate
            'start_date',
            'end_date',
            'actual_completion_date',
            'created_at',
            'updated_at',
            'project_manager_name',
            'tasks',
            'total_hours_logged',
            'progress_percentage',
            'tasks_summary',
        ]
        read_only_fields = fields  # All fields are read-only for clients

    def get_project_manager_name(self, obj):
        """Get project manager's name."""
        if obj.project_manager:
            return f"{obj.project_manager.first_name} {obj.project_manager.last_name}".strip() or "Project Manager"
        return None

    def get_total_hours_logged(self, obj):
        """Calculate total hours logged for this project."""
        from django.db.models import Sum
        total = obj.time_entries.aggregate(total=Sum('hours'))['total']
        return float(total) if total else 0.0

    def get_progress_percentage(self, obj):
        """Calculate overall project progress based on completed tasks."""
        from modules.projects.models import Task
        total_tasks = Task.objects.filter(project=obj).count()
        if total_tasks == 0:
            return 0

        completed_tasks = Task.objects.filter(project=obj, status='done').count()
        return int((completed_tasks / total_tasks) * 100)

    def get_tasks_summary(self, obj):
        """Get task counts by status."""
        from modules.projects.models import Task
        from django.db.models import Count

        summary = Task.objects.filter(project=obj).values('status').annotate(
            count=Count('id')
        )

        result = {
            'todo': 0,
            'in_progress': 0,
            'review': 0,
            'done': 0,
            'total': 0,
        }

        for item in summary:
            status = item['status']
            count = item['count']
            if status in result:
                result[status] = count
            result['total'] += count

        return result


class ClientInvoiceSerializer(serializers.ModelSerializer):
    """
    Client-facing Invoice serializer (read-only).

    Shows invoice details suitable for client portal.
    Hides sensitive firm information like internal notes and markup details.
    """
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_code = serializers.SerializerMethodField()
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_due = serializers.SerializerMethodField()
    can_pay_online = serializers.SerializerMethodField()

    class Meta:
        from modules.finance.models import Invoice
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'client_name',
            'project',
            'project_name',
            'project_code',
            'status',
            'subtotal',
            'tax_amount',
            'total_amount',
            'amount_paid',
            'balance_due',
            'issue_date',
            'due_date',
            'paid_date',
            'line_items',
            'is_overdue',
            'days_until_due',
            'can_pay_online',
            'created_at',
        ]
        read_only_fields = fields  # All fields are read-only for clients

    def get_project_code(self, obj):
        """Get project code if available."""
        if obj.project and hasattr(obj.project, 'project_code'):
            return obj.project.project_code
        return None

    def get_days_until_due(self, obj):
        """Calculate days until due date."""
        from django.utils import timezone
        if obj.due_date:
            today = timezone.now().date()
            delta = (obj.due_date - today).days
            return delta
        return None

    def get_can_pay_online(self, obj):
        """Check if invoice can be paid online."""
        # Can pay if status is sent, partial, or overdue and has balance due
        payable_statuses = ['sent', 'partial', 'overdue']
        return obj.status in payable_statuses and obj.balance_due > 0


class ClientMessageSerializer(serializers.ModelSerializer):
    """Serializer for ClientMessage model."""

    sender_name = serializers.SerializerMethodField()
    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    attachment_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    attachment_filename = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    attachment_size_bytes = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = ClientMessage
        fields = [
            'id',
            'thread',
            'sender',
            'sender_name',
            'sender_email',
            'is_from_client',
            'message_type',
            'content',
            'attachment_url',
            'attachment_filename',
            'attachment_size_bytes',
            'is_read',
            'read_at',
            'read_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'sender',
            'is_from_client',
            'is_read',
            'read_at',
            'read_by',
            'created_at',
            'updated_at',
        ]

    def get_sender_name(self, obj):
        """Get sender's full name."""
        if obj.sender:
            return f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.username
        return None

    def create(self, validated_data):
        """Set sender and is_from_client from request context."""
        request = self.context.get('request')
        content_data = {
            'content': validated_data.pop('content', '') or '',
            'attachment_url': validated_data.pop('attachment_url', '') or '',
            'attachment_filename': validated_data.pop('attachment_filename', '') or '',
            'attachment_size_bytes': validated_data.pop('attachment_size_bytes', None),
        }
        validated_data['sender'] = request.user

        # Check if sender is a client portal user
        from modules.clients.models import ClientPortalUser
        try:
            ClientPortalUser.objects.get(user=request.user)
            validated_data['is_from_client'] = True
        except ClientPortalUser.DoesNotExist:
            validated_data['is_from_client'] = False

        message = super().create(validated_data)
        ClientMessageContent.objects.create(message=message, **content_data)
        return message

    def update(self, instance, validated_data):
        content_data = {
            'content': validated_data.pop('content', None),
            'attachment_url': validated_data.pop('attachment_url', None),
            'attachment_filename': validated_data.pop('attachment_filename', None),
            'attachment_size_bytes': validated_data.pop('attachment_size_bytes', None),
        }
        instance = super().update(instance, validated_data)
        if any(value is not None for value in content_data.values()):
            content_record, _created = ClientMessageContent.objects.get_or_create(
                message=instance,
                defaults={
                    'content': content_data['content'] or '',
                    'attachment_url': content_data['attachment_url'] or '',
                    'attachment_filename': content_data['attachment_filename'] or '',
                    'attachment_size_bytes': content_data['attachment_size_bytes'],
                },
            )
            if not _created:
                if content_data['content'] is not None:
                    content_record.content = content_data['content']
                if content_data['attachment_url'] is not None:
                    content_record.attachment_url = content_data['attachment_url'] or ''
                if content_data['attachment_filename'] is not None:
                    content_record.attachment_filename = content_data['attachment_filename'] or ''
                if content_data['attachment_size_bytes'] is not None:
                    content_record.attachment_size_bytes = content_data['attachment_size_bytes']
                content_record.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and getattr(request, 'platform_role', None) == 'operator':
            data.pop('content', None)
            data.pop('attachment_url', None)
            data.pop('attachment_filename', None)
            data.pop('attachment_size_bytes', None)
            return data

        try:
            content = instance.content
        except ClientMessageContent.DoesNotExist:
            content = None

        data['content'] = content.content if content else ''
        data['attachment_url'] = content.attachment_url if content else ''
        data['attachment_filename'] = content.attachment_filename if content else ''
        data['attachment_size_bytes'] = content.attachment_size_bytes if content else None
        return data

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and getattr(request, 'platform_role', None) == 'operator':
            fields.pop('content', None)
            fields.pop('attachment_url', None)
            fields.pop('attachment_filename', None)
            fields.pop('attachment_size_bytes', None)
        return fields


class ClientChatThreadSerializer(serializers.ModelSerializer):
    """Serializer for ClientChatThread model."""

    client_name = serializers.CharField(source='client.company_name', read_only=True)
    last_message_by_name = serializers.SerializerMethodField()
    messages = ClientMessageSerializer(many=True, read_only=True)
    recent_messages = serializers.SerializerMethodField()

    class Meta:
        model = ClientChatThread
        fields = [
            'id',
            'client',
            'client_name',
            'date',
            'is_active',
            'archived_at',
            'message_count',
            'last_message_at',
            'last_message_by',
            'last_message_by_name',
            'created_at',
            'updated_at',
            'messages',
            'recent_messages',
        ]
        read_only_fields = [
            'id',
            'message_count',
            'last_message_at',
            'last_message_by',
            'archived_at',
            'created_at',
            'updated_at',
        ]

    def get_last_message_by_name(self, obj):
        """Get last message sender's name."""
        if obj.last_message_by:
            return f"{obj.last_message_by.first_name} {obj.last_message_by.last_name}".strip() or obj.last_message_by.username
        return None

    def get_recent_messages(self, obj):
        """Get recent messages (last 50) for efficiency."""
        messages = obj.messages.all().order_by('-created_at')[:50]
        return ClientMessageSerializer(messages, many=True).data


class ClientProposalSerializer(serializers.ModelSerializer):
    """
    Client-facing Proposal serializer (read-only).

    Shows proposal details suitable for client portal.
    Hides internal firm information and decision-making details.
    """
    client_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_proposal_type_display', read_only=True)
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()

    class Meta:
        from modules.crm.models import Proposal
        model = Proposal
        fields = [
            'id',
            'proposal_number',
            'proposal_type',
            'type_display',
            'title',
            'description',
            'status',
            'status_display',
            'total_value',
            'currency',
            'valid_until',
            'estimated_start_date',
            'estimated_end_date',
            'sent_at',
            'accepted_at',
            'is_expired',
            'days_until_expiry',
            'client_name',
            'created_at',
        ]
        read_only_fields = fields  # All fields are read-only for clients

    def get_client_name(self, obj):
        """Get client or prospect company name."""
        if obj.client:
            return obj.client.company_name
        elif obj.prospect:
            return obj.prospect.company_name
        return None

    def get_is_expired(self, obj):
        """Check if proposal has expired."""
        from django.utils import timezone
        if obj.valid_until:
            return obj.valid_until < timezone.now().date()
        return False

    def get_days_until_expiry(self, obj):
        """Calculate days until expiry."""
        from django.utils import timezone
        if obj.valid_until:
            today = timezone.now().date()
            delta = (obj.valid_until - today).days
            return delta
        return None


class ClientContractSerializer(serializers.ModelSerializer):
    """
    Client-facing Contract serializer (read-only).

    Shows contract details suitable for client portal.
    Hides internal firm notes and sensitive information.
    """
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_terms_display = serializers.CharField(source='get_payment_terms_display', read_only=True)
    proposal_number = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        from modules.crm.models import Contract
        model = Contract
        fields = [
            'id',
            'contract_number',
            'title',
            'description',
            'status',
            'status_display',
            'total_value',
            'currency',
            'payment_terms',
            'payment_terms_display',
            'start_date',
            'end_date',
            'signed_date',
            'contract_file_url',
            'proposal_number',
            'is_active',
            'days_remaining',
            'client_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields  # All fields are read-only for clients

    def get_proposal_number(self, obj):
        """Get related proposal number if exists."""
        if obj.proposal:
            return obj.proposal.proposal_number
        return None

    def get_is_active(self, obj):
        """Check if contract is currently active."""
        return obj.status == 'active'

    def get_days_remaining(self, obj):
        """Calculate days remaining in contract."""
        from django.utils import timezone
        if obj.end_date:
            today = timezone.now().date()
            delta = (obj.end_date - today).days
            return delta
        return None


class ClientEngagementDetailSerializer(serializers.ModelSerializer):
    """
    Client-facing ClientEngagement serializer with nested contract.

    Shows engagement history with version tracking.
    """
    contract = ClientContractSerializer(read_only=True)
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    has_parent = serializers.SerializerMethodField()
    has_renewals = serializers.SerializerMethodField()

    class Meta:
        from modules.clients.models import ClientEngagement
        model = ClientEngagement
        fields = [
            'id',
            'client_name',
            'contract',
            'status',
            'status_display',
            'version',
            'start_date',
            'end_date',
            'actual_end_date',
            'has_parent',
            'has_renewals',
        ]
        read_only_fields = fields  # All fields are read-only for clients

    def get_has_parent(self, obj):
        """Check if this engagement is a renewal."""
        return obj.parent_engagement is not None

    def get_has_renewals(self, obj):
        """Check if this engagement has been renewed."""
        return obj.renewals.exists()
