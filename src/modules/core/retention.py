"""
Data Retention Policy Management (ASSESS-L19.4).

Implements configurable data retention schedules and auto-purge functionality
for old data per firm requirements.
"""

from datetime import timedelta
from typing import Dict, Optional
from django.conf import settings
from django.db import models
from django.utils import timezone
from modules.firm.utils import FirmScopedManager


class RetentionPolicy(models.Model):
    """
    Data retention policy configuration per firm (ASSESS-L19.4).
    
    Defines how long different types of data should be retained before
    automatic purging. Policies are configurable per firm.
    """
    
    # Data types that can have retention policies
    DATA_TYPE_CHOICES = [
        ('audit_logs', 'Audit Logs'),
        ('documents', 'Documents'),
        ('invoices', 'Invoices'),
        ('projects', 'Projects'),
        ('time_entries', 'Time Entries'),
        ('communications', 'Communications'),
        ('email_artifacts', 'Email Artifacts'),
        ('support_tickets', 'Support Tickets'),
        ('leads', 'Leads'),
        ('prospects', 'Prospects'),
    ]
    
    # Retention actions
    ACTION_ARCHIVE = 'archive'
    ACTION_ANONYMIZE = 'anonymize'
    ACTION_DELETE = 'delete'
    
    ACTION_CHOICES = [
        (ACTION_ARCHIVE, 'Archive (move to cold storage)'),
        (ACTION_ANONYMIZE, 'Anonymize (remove PII)'),
        (ACTION_DELETE, 'Delete (permanent removal)'),
    ]
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='retention_policies',
        help_text='Firm this retention policy belongs to'
    )
    
    # Policy configuration
    data_type = models.CharField(
        max_length=50,
        choices=DATA_TYPE_CHOICES,
        help_text='Type of data this policy applies to'
    )
    
    retention_days = models.IntegerField(
        help_text='Number of days to retain data before action (0 = no retention limit)'
    )
    
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        default=ACTION_ARCHIVE,
        help_text='Action to take when retention period expires'
    )
    
    # Conditions
    only_if_inactive = models.BooleanField(
        default=False,
        help_text='Only apply to inactive/closed records (e.g., closed projects, paid invoices)'
    )
    
    preserve_legal_hold = models.BooleanField(
        default=True,
        help_text='Never purge data under legal hold'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Is this retention policy active?'
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_retention_policies'
    )
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = 'core_retention_policies'
        ordering = ['firm', 'data_type']
        indexes = [
            models.Index(fields=['firm', 'data_type', 'is_active'], name='core_ret_fir_dat_act_idx'),
            models.Index(fields=['firm', 'is_active'], name='core_ret_fir_act_idx'),
        ]
        unique_together = [['firm', 'data_type']]
        verbose_name_plural = 'Retention Policies'
    
    def __str__(self):
        return f"{self.get_data_type_display()} - {self.retention_days} days - {self.get_action_display()} ({self.firm.name})"
    
    def get_cutoff_date(self) -> Optional[timezone.datetime]:
        """Calculate the cutoff date for this retention policy."""
        if self.retention_days == 0:
            return None  # No retention limit
        return timezone.now() - timedelta(days=self.retention_days)


class RetentionExecution(models.Model):
    """
    Record of retention policy execution (audit trail).
    
    Tracks when retention policies were executed and what data was affected.
    """
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='retention_executions',
        help_text='Firm this execution belongs to'
    )
    
    # Execution details
    policy = models.ForeignKey(
        RetentionPolicy,
        on_delete=models.CASCADE,
        related_name='executions',
        help_text='Retention policy that was executed'
    )
    
    executed_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the retention policy was executed'
    )
    
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='retention_executions',
        help_text='User/system that executed the policy'
    )
    
    # Results
    records_processed = models.IntegerField(
        default=0,
        help_text='Number of records processed'
    )
    
    records_archived = models.IntegerField(
        default=0,
        help_text='Number of records archived'
    )
    
    records_anonymized = models.IntegerField(
        default=0,
        help_text='Number of records anonymized'
    )
    
    records_deleted = models.IntegerField(
        default=0,
        help_text='Number of records deleted'
    )
    
    records_skipped = models.IntegerField(
        default=0,
        help_text='Number of records skipped (e.g., legal hold)'
    )
    
    execution_result = models.JSONField(
        default=dict,
        blank=True,
        help_text='Detailed execution results'
    )
    
    error_message = models.TextField(
        blank=True,
        help_text='Error message if execution failed'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = 'core_retention_executions'
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['firm', '-executed_at'], name='core_ret_exe_fir_exe_idx'),
            models.Index(fields=['policy', '-executed_at'], name='core_ret_exe_pol_exe_idx'),
        ]
    
    def __str__(self):
        return f"Retention Execution #{self.id} - {self.policy.data_type} - {self.status}"


class RetentionService:
    """
    Service for executing retention policies (ASSESS-L19.4).
    
    Handles the actual purging/anonymization/archiving of data based on
    configured retention policies.
    """
    
    @staticmethod
    def execute_policy(policy: RetentionPolicy, dry_run: bool = False) -> RetentionExecution:
        """
        Execute a retention policy.
        
        Args:
            policy: Retention policy to execute
            dry_run: If True, don't actually modify data, just report what would be done
            
        Returns:
            RetentionExecution record
        """
        from modules.core.erasure import ErasureService
        
        execution = RetentionExecution.objects.create(
            firm=policy.firm,
            policy=policy,
            executed_by=None,  # System execution
            status='running'
        )
        
        cutoff_date = policy.get_cutoff_date()
        if not cutoff_date:
            execution.status = 'completed'
            execution.error_message = 'No retention limit set (retention_days = 0)'
            execution.save()
            return execution
        
        try:
            results = {
                'processed': 0,
                'archived': 0,
                'anonymized': 0,
                'deleted': 0,
                'skipped': 0,
            }
            
            # Execute based on data type
            if policy.data_type == 'audit_logs':
                results = RetentionService._process_audit_logs(policy, cutoff_date, dry_run)
            elif policy.data_type == 'documents':
                results = RetentionService._process_documents(policy, cutoff_date, dry_run)
            elif policy.data_type == 'invoices':
                results = RetentionService._process_invoices(policy, cutoff_date, dry_run)
            elif policy.data_type == 'projects':
                results = RetentionService._process_projects(policy, cutoff_date, dry_run)
            elif policy.data_type == 'time_entries':
                results = RetentionService._process_time_entries(policy, cutoff_date, dry_run)
            elif policy.data_type == 'leads':
                results = RetentionService._process_leads(policy, cutoff_date, dry_run)
            elif policy.data_type == 'prospects':
                results = RetentionService._process_prospects(policy, cutoff_date, dry_run)
            
            execution.records_processed = results['processed']
            execution.records_archived = results['archived']
            execution.records_anonymized = results['anonymized']
            execution.records_deleted = results['deleted']
            execution.records_skipped = results['skipped']
            execution.execution_result = results
            execution.status = 'completed'
            
        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            raise
        finally:
            execution.save()
        
        return execution
    
    @staticmethod
    def _process_audit_logs(policy, cutoff_date, dry_run):
        """Process audit logs for retention."""
        from modules.firm.audit import AuditEvent
        
        queryset = AuditEvent.objects.filter(
            firm=policy.firm,
            created_at__lt=cutoff_date
        )
        
        if policy.preserve_legal_hold:
            # Skip records under legal hold (if legal_hold field exists)
            queryset = queryset.exclude(metadata__legal_hold=True)
        
        count = queryset.count()
        
        if not dry_run:
            if policy.action == RetentionPolicy.ACTION_DELETE:
                queryset.delete()
            elif policy.action == RetentionPolicy.ACTION_ARCHIVE:
                # Archive logic would go here
                pass
        
        return {'processed': count, 'archived': 0, 'anonymized': 0, 'deleted': count if policy.action == RetentionPolicy.ACTION_DELETE else 0, 'skipped': 0}
    
    @staticmethod
    def _process_documents(policy, cutoff_date, dry_run):
        """Process documents for retention."""
        from modules.documents.models import Document
        
        queryset = Document.objects.filter(
            firm=policy.firm,
            created_at__lt=cutoff_date
        )
        
        if policy.only_if_inactive:
            queryset = queryset.filter(status__in=['archived', 'deleted'])
        
        if policy.preserve_legal_hold:
            queryset = queryset.exclude(legal_hold=True)
        
        count = queryset.count()
        
        if not dry_run:
            if policy.action == RetentionPolicy.ACTION_DELETE:
                queryset.delete()
            elif policy.action == RetentionPolicy.ACTION_ARCHIVE:
                queryset.update(status='archived')
        
        return {'processed': count, 'archived': count if policy.action == RetentionPolicy.ACTION_ARCHIVE else 0, 'anonymized': 0, 'deleted': count if policy.action == RetentionPolicy.ACTION_DELETE else 0, 'skipped': 0}
    
    @staticmethod
    def _process_invoices(policy, cutoff_date, dry_run):
        """Process invoices for retention."""
        from modules.finance.models import Invoice
        
        queryset = Invoice.objects.filter(
            firm=policy.firm,
            created_at__lt=cutoff_date
        )
        
        if policy.only_if_inactive:
            queryset = queryset.filter(status__in=['paid', 'cancelled', 'refunded'])
        
        count = queryset.count()
        
        if not dry_run:
            if policy.action == RetentionPolicy.ACTION_ARCHIVE:
                # Mark as archived (would need archive field)
                pass
        
        return {'processed': count, 'archived': 0, 'anonymized': 0, 'deleted': 0, 'skipped': 0}
    
    @staticmethod
    def _process_projects(policy, cutoff_date, dry_run):
        """Process projects for retention."""
        from modules.projects.models import Project
        
        queryset = Project.objects.filter(
            firm=policy.firm,
            created_at__lt=cutoff_date
        )
        
        if policy.only_if_inactive:
            queryset = queryset.filter(status__in=['completed', 'cancelled'])
        
        count = queryset.count()
        
        if not dry_run:
            if policy.action == RetentionPolicy.ACTION_ARCHIVE:
                queryset.update(status='archived')
        
        return {'processed': count, 'archived': count if policy.action == RetentionPolicy.ACTION_ARCHIVE else 0, 'anonymized': 0, 'deleted': 0, 'skipped': 0}
    
    @staticmethod
    def _process_time_entries(policy, cutoff_date, dry_run):
        """Process time entries for retention."""
        from modules.projects.models import TimeEntry
        
        queryset = TimeEntry.objects.filter(
            firm=policy.firm,
            created_at__lt=cutoff_date
        )
        
        count = queryset.count()
        
        if not dry_run:
            if policy.action == RetentionPolicy.ACTION_DELETE:
                queryset.delete()
        
        return {'processed': count, 'archived': 0, 'anonymized': 0, 'deleted': count if policy.action == RetentionPolicy.ACTION_DELETE else 0, 'skipped': 0}
    
    @staticmethod
    def _process_leads(policy, cutoff_date, dry_run):
        """Process leads for retention."""
        from modules.crm.models import Lead
        
        queryset = Lead.objects.filter(
            firm=policy.firm,
            created_at__lt=cutoff_date
        )
        
        if policy.only_if_inactive:
            queryset = queryset.filter(status__in=['lost', 'converted'])
        
        count = queryset.count()
        
        if not dry_run:
            if policy.action == RetentionPolicy.ACTION_DELETE:
                queryset.delete()
            elif policy.action == RetentionPolicy.ACTION_ANONYMIZE:
                # Anonymize PII
                queryset.update(
                    contact_name='[Anonymized]',
                    contact_email='[anonymized]@example.com',
                    contact_phone=''
                )
        
        return {'processed': count, 'archived': 0, 'anonymized': count if policy.action == RetentionPolicy.ACTION_ANONYMIZE else 0, 'deleted': count if policy.action == RetentionPolicy.ACTION_DELETE else 0, 'skipped': 0}
    
    @staticmethod
    def _process_prospects(policy, cutoff_date, dry_run):
        """Process prospects for retention."""
        from modules.crm.models import Prospect
        
        queryset = Prospect.objects.filter(
            firm=policy.firm,
            created_at__lt=cutoff_date
        )
        
        if policy.only_if_inactive:
            queryset = queryset.filter(stage__in=['won', 'lost'])
        
        count = queryset.count()
        
        if not dry_run:
            if policy.action == RetentionPolicy.ACTION_DELETE:
                queryset.delete()
            elif policy.action == RetentionPolicy.ACTION_ANONYMIZE:
                queryset.update(
                    primary_contact_name='[Anonymized]',
                    primary_contact_email='[anonymized]@example.com',
                    primary_contact_phone=''
                )
        
        return {'processed': count, 'archived': 0, 'anonymized': count if policy.action == RetentionPolicy.ACTION_ANONYMIZE else 0, 'deleted': count if policy.action == RetentionPolicy.ACTION_DELETE else 0, 'skipped': 0}