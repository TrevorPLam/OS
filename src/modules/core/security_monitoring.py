"""
Security Monitoring and Alerting System (SEC-4).

Implements:
- Real-time security alerts
- SIEM integration (Splunk/Datadog export)
- PII/PHI content scanning
- Anomaly detection

SECURITY REQUIREMENTS:
- Alert on suspicious activities
- Export audit logs to SIEM
- Scan documents for sensitive data
- Track security metrics
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone

from modules.firm.audit import AuditEvent


class SecurityAlert(models.Model):
    """
    Security alert for suspicious or critical events.
    
    Tracks security incidents that require review or action.
    """
    
    # Alert Severity
    SEVERITY_LOW = 'low'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_HIGH = 'high'
    SEVERITY_CRITICAL = 'critical'
    
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High - Requires Review'),
        (SEVERITY_CRITICAL, 'Critical - Immediate Action'),
    ]
    
    # Alert Status
    STATUS_NEW = 'new'
    STATUS_INVESTIGATING = 'investigating'
    STATUS_RESOLVED = 'resolved'
    STATUS_FALSE_POSITIVE = 'false_positive'
    
    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_INVESTIGATING, 'Investigating'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_FALSE_POSITIVE, 'False Positive'),
    ]
    
    # Alert Types
    TYPE_UNAUTHORIZED_ACCESS = 'unauthorized_access'
    TYPE_EXCESSIVE_FAILURES = 'excessive_failures'
    TYPE_UNUSUAL_ACTIVITY = 'unusual_activity'
    TYPE_PII_DETECTED = 'pii_detected'
    TYPE_PHI_DETECTED = 'phi_detected'
    TYPE_BREAK_GLASS = 'break_glass'
    TYPE_BULK_DOWNLOAD = 'bulk_download'
    TYPE_OFF_HOURS_ACCESS = 'off_hours_access'
    TYPE_SUSPICIOUS_IP = 'suspicious_ip'
    
    TYPE_CHOICES = [
        (TYPE_UNAUTHORIZED_ACCESS, 'Unauthorized Access Attempt'),
        (TYPE_EXCESSIVE_FAILURES, 'Excessive Failed Attempts'),
        (TYPE_UNUSUAL_ACTIVITY, 'Unusual Activity Pattern'),
        (TYPE_PII_DETECTED, 'PII Detected in Document'),
        (TYPE_PHI_DETECTED, 'PHI Detected in Document'),
        (TYPE_BREAK_GLASS, 'Break-Glass Access Used'),
        (TYPE_BULK_DOWNLOAD, 'Bulk Download Detected'),
        (TYPE_OFF_HOURS_ACCESS, 'Off-Hours Access'),
        (TYPE_SUSPICIOUS_IP, 'Suspicious IP Address'),
    ]
    
    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='security_alerts',
        help_text='Firm this alert belongs to'
    )
    
    # Alert Details
    alert_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        db_index=True,
        help_text='Type of security alert'
    )
    
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_MEDIUM,
        db_index=True,
        help_text='Alert severity'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True,
        help_text='Alert status'
    )
    
    title = models.CharField(
        max_length=255,
        help_text='Alert title (summary)'
    )
    
    description = models.TextField(
        help_text='Detailed description of alert'
    )
    
    # Context
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_alerts',
        help_text='User involved in alert (if applicable)'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address involved'
    )
    
    resource_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='Resource type (e.g., Document, Folder)'
    )
    
    resource_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Resource ID'
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text='Additional alert context (JSON)'
    )
    
    # Timestamps
    detected_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text='When alert was detected'
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When alert was resolved'
    )
    
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_security_alerts',
        help_text='Who resolved this alert'
    )
    
    resolution_notes = models.TextField(
        blank=True,
        help_text='Notes on how alert was resolved'
    )
    
    # Notification Tracking
    notification_sent = models.BooleanField(
        default=False,
        help_text='Was notification sent for this alert?'
    )
    
    notification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When notification was sent'
    )
    
    class Meta:
        db_table = 'security_alerts'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['firm', 'severity', 'status', '-detected_at']),
            models.Index(fields=['firm', 'alert_type', '-detected_at']),
            models.Index(fields=['status', 'notification_sent']),
        ]
        permissions = [
            ('view_security_alerts', 'Can view security alerts'),
            ('manage_security_alerts', 'Can manage security alerts'),
        ]
    
    def __str__(self):
        return f"[{self.severity.upper()}] {self.title} - {self.status}"
    
    def resolve(self, resolved_by, notes=''):
        """Mark alert as resolved."""
        self.status = self.STATUS_RESOLVED
        self.resolved_at = timezone.now()
        self.resolved_by = resolved_by
        self.resolution_notes = notes
        self.save(update_fields=['status', 'resolved_at', 'resolved_by', 'resolution_notes'])
    
    def mark_false_positive(self, user, notes=''):
        """Mark alert as false positive."""
        self.status = self.STATUS_FALSE_POSITIVE
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.resolution_notes = notes
        self.save(update_fields=['status', 'resolved_at', 'resolved_by', 'resolution_notes'])


class SecurityMonitor:
    """
    Security monitoring service.
    
    Detects and alerts on suspicious activities.
    """
    
    @staticmethod
    def check_excessive_failures(firm, user, time_window_minutes=5, threshold=5):
        """
        Check for excessive failed login/access attempts.
        
        Args:
            firm: Firm instance
            user: User instance (or None for IP-based check)
            time_window_minutes: Time window to check
            threshold: Number of failures to trigger alert
        
        Returns:
            SecurityAlert instance if threshold exceeded, None otherwise
        """
        since = timezone.now() - timedelta(minutes=time_window_minutes)
        
        # Count failed auth events
        failed_attempts = AuditEvent.objects.filter(
            firm=firm,
            actor=user,
            category=AuditEvent.CATEGORY_AUTH,
            outcome='failed',
            timestamp__gte=since
        ).count()
        
        if failed_attempts >= threshold:
            return SecurityAlert.objects.create(
                firm=firm,
                alert_type=SecurityAlert.TYPE_EXCESSIVE_FAILURES,
                severity=SecurityAlert.SEVERITY_HIGH,
                title=f'Excessive failed attempts: {failed_attempts} in {time_window_minutes} minutes',
                description=f'User {user.email if user else "Unknown"} had {failed_attempts} failed attempts in the last {time_window_minutes} minutes.',
                user=user,
                metadata={
                    'failed_attempts': failed_attempts,
                    'time_window_minutes': time_window_minutes,
                    'threshold': threshold
                }
            )
        
        return None
    
    @staticmethod
    def detect_break_glass_usage(firm, user, reason, target_model, target_id):
        """
        Alert on break-glass access usage.
        
        All break-glass usage triggers a CRITICAL alert.
        """
        return SecurityAlert.objects.create(
            firm=firm,
            alert_type=SecurityAlert.TYPE_BREAK_GLASS,
            severity=SecurityAlert.SEVERITY_CRITICAL,
            title=f'Break-glass access by {user.email}',
            description=f'User {user.email} used break-glass access. Reason: {reason}',
            user=user,
            resource_type=target_model,
            resource_id=str(target_id),
            metadata={
                'reason': reason,
                'target_model': target_model,
                'target_id': str(target_id)
            }
        )
    
    @staticmethod
    def detect_bulk_download(firm, user, document_count, time_window_minutes=5, threshold=10):
        """
        Detect bulk document downloads (potential data exfiltration).
        
        Args:
            firm: Firm instance
            user: User instance
            document_count: Number of documents downloaded
            time_window_minutes: Time window
            threshold: Download count threshold
        """
        if document_count >= threshold:
            return SecurityAlert.objects.create(
                firm=firm,
                alert_type=SecurityAlert.TYPE_BULK_DOWNLOAD,
                severity=SecurityAlert.SEVERITY_HIGH,
                title=f'Bulk download detected: {document_count} documents',
                description=f'User {user.email} downloaded {document_count} documents in {time_window_minutes} minutes.',
                user=user,
                metadata={
                    'document_count': document_count,
                    'time_window_minutes': time_window_minutes,
                    'threshold': threshold
                }
            )
        
        return None
    
    @staticmethod
    def detect_off_hours_access(firm, user, timestamp, business_hours_start=9, business_hours_end=17):
        """
        Detect access outside business hours.
        
        Args:
            firm: Firm instance
            user: User instance
            timestamp: Access timestamp
            business_hours_start: Business hours start (hour, 24h format)
            business_hours_end: Business hours end (hour, 24h format)
        """
        hour = timestamp.hour
        
        # Check if outside business hours
        if hour < business_hours_start or hour >= business_hours_end:
            # Check if weekend
            is_weekend = timestamp.weekday() >= 5  # 5=Saturday, 6=Sunday
            
            severity = SecurityAlert.SEVERITY_MEDIUM
            if is_weekend:
                severity = SecurityAlert.SEVERITY_HIGH
            
            return SecurityAlert.objects.create(
                firm=firm,
                alert_type=SecurityAlert.TYPE_OFF_HOURS_ACCESS,
                severity=severity,
                title=f'Off-hours access by {user.email}',
                description=f'User {user.email} accessed the system at {timestamp.strftime("%Y-%m-%d %H:%M")} (outside business hours).',
                user=user,
                metadata={
                    'timestamp': timestamp.isoformat(),
                    'hour': hour,
                    'is_weekend': is_weekend,
                    'business_hours': f'{business_hours_start}-{business_hours_end}'
                }
            )
        
        return None


class PIIScanner:
    """
    PII/PHI content scanner for documents.
    
    Detects personally identifiable information and protected health information.
    """
    
    # Patterns for common PII/PHI
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    
    # Medical terms (PHI indicators)
    MEDICAL_TERMS = [
        'diagnosis', 'patient', 'medical record', 'prescription',
        'treatment', 'medication', 'physician', 'hospital',
        'ICD-10', 'CPT code', 'health insurance'
    ]
    
    @classmethod
    def scan_content(cls, content: str) -> Dict[str, any]:
        """
        Scan content for PII/PHI.
        
        Args:
            content: Text content to scan
        
        Returns:
            Dict with scan results:
            {
                'has_pii': bool,
                'has_phi': bool,
                'ssn_count': int,
                'credit_card_count': int,
                'email_count': int,
                'phone_count': int,
                'medical_terms': list,
                'confidence': float  # 0.0-1.0
            }
        """
        if not content:
            return {
                'has_pii': False,
                'has_phi': False,
                'ssn_count': 0,
                'credit_card_count': 0,
                'email_count': 0,
                'phone_count': 0,
                'medical_terms': [],
                'confidence': 0.0
            }
        
        # Scan for patterns
        ssn_matches = cls.SSN_PATTERN.findall(content)
        cc_matches = cls.CREDIT_CARD_PATTERN.findall(content)
        email_matches = cls.EMAIL_PATTERN.findall(content)
        phone_matches = cls.PHONE_PATTERN.findall(content)
        
        # Scan for medical terms
        content_lower = content.lower()
        found_medical_terms = [
            term for term in cls.MEDICAL_TERMS
            if term.lower() in content_lower
        ]
        
        # Determine if PII/PHI
        has_pii = len(ssn_matches) > 0 or len(cc_matches) > 0
        has_phi = len(found_medical_terms) >= 2  # At least 2 medical terms
        
        # Calculate confidence
        pii_indicators = len(ssn_matches) + len(cc_matches)
        phi_indicators = len(found_medical_terms)
        total_indicators = pii_indicators + phi_indicators
        
        confidence = min(1.0, total_indicators / 5.0)  # 5+ indicators = 100% confidence
        
        return {
            'has_pii': has_pii,
            'has_phi': has_phi,
            'ssn_count': len(ssn_matches),
            'credit_card_count': len(cc_matches),
            'email_count': len(email_matches),
            'phone_count': len(phone_matches),
            'medical_terms': found_medical_terms,
            'confidence': confidence
        }
    
    @classmethod
    def scan_document(cls, document) -> Optional[SecurityAlert]:
        """
        Scan document for PII/PHI and create alert if found.
        
        Args:
            document: Document instance
        
        Returns:
            SecurityAlert if PII/PHI detected, None otherwise
        """
        # Get document content (placeholder - would extract from actual file)
        content = getattr(document, 'content', '')
        
        # Scan content
        results = cls.scan_content(content)
        
        # Create alert if PII/PHI detected
        if results['has_pii'] or results['has_phi']:
            alert_type = SecurityAlert.TYPE_PHI_DETECTED if results['has_phi'] else SecurityAlert.TYPE_PII_DETECTED
            severity = SecurityAlert.SEVERITY_HIGH if results['confidence'] > 0.7 else SecurityAlert.SEVERITY_MEDIUM
            
            return SecurityAlert.objects.create(
                firm=document.firm,
                alert_type=alert_type,
                severity=severity,
                title=f'Sensitive data detected in document {document.id}',
                description=f'Document "{document.filename}" contains potential PII/PHI. SSNs: {results["ssn_count"]}, Credit Cards: {results["credit_card_count"]}, Medical Terms: {len(results["medical_terms"])}',
                resource_type='Document',
                resource_id=str(document.id),
                metadata={
                    'scan_results': results,
                    'document_id': document.id,
                    'filename': document.filename
                }
            )
        
        return None


class SIEMExporter:
    """
    SIEM integration for audit log export.
    
    Supports:
    - Splunk HTTP Event Collector (HEC)
    - Datadog Log API
    - Generic webhook
    """
    
    @staticmethod
    def export_to_splunk(audit_events: List[AuditEvent], splunk_hec_url: str, splunk_token: str):
        """
        Export audit events to Splunk via HTTP Event Collector.
        
        Args:
            audit_events: List of AuditEvent instances
            splunk_hec_url: Splunk HEC URL (e.g., https://splunk.company.com:8088/services/collector)
            splunk_token: Splunk HEC token
        
        Returns:
            bool: True if successful
        """
        if not audit_events:
            return True
        
        headers = {
            'Authorization': f'Splunk {splunk_token}',
            'Content-Type': 'application/json'
        }
        
        # Convert events to Splunk format
        events = []
        for event in audit_events:
            events.append({
                'time': event.timestamp.timestamp(),
                'source': 'consultantpro',
                'sourcetype': 'audit_event',
                'event': {
                    'firm_id': event.firm_id,
                    'category': event.category,
                    'action': event.action,
                    'severity': event.severity,
                    'actor_email': event.actor_email,
                    'actor_role': event.actor_role,
                    'target_model': event.target_model,
                    'target_id': event.target_id,
                    'outcome': event.outcome,
                    'ip_address': event.ip_address,
                    'metadata': event.metadata
                }
            })
        
        # Send to Splunk (batch up to 1000 events)
        batch_size = 1000
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            payload = '\n'.join(json.dumps(e) for e in batch)
            
            try:
                response = requests.post(
                    splunk_hec_url,
                    headers=headers,
                    data=payload,
                    timeout=30
                )
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Failed to export to Splunk: {e}")
                return False
        
        return True
    
    @staticmethod
    def export_to_datadog(audit_events: List[AuditEvent], datadog_api_key: str, datadog_site='datadoghq.com'):
        """
        Export audit events to Datadog Logs.
        
        Args:
            audit_events: List of AuditEvent instances
            datadog_api_key: Datadog API key
            datadog_site: Datadog site (e.g., datadoghq.com, datadoghq.eu)
        
        Returns:
            bool: True if successful
        """
        if not audit_events:
            return True
        
        url = f'https://http-intake.logs.{datadog_site}/api/v2/logs'
        headers = {
            'DD-API-KEY': datadog_api_key,
            'Content-Type': 'application/json'
        }
        
        # Convert events to Datadog format
        logs = []
        for event in audit_events:
            logs.append({
                'ddsource': 'consultantpro',
                'ddtags': f'firm:{event.firm_id},category:{event.category},severity:{event.severity}',
                'hostname': 'consultantpro-app',
                'message': f'{event.action} by {event.actor_email or "System"}',
                'timestamp': event.timestamp.isoformat(),
                'attributes': {
                    'firm_id': event.firm_id,
                    'category': event.category,
                    'action': event.action,
                    'severity': event.severity,
                    'actor_email': event.actor_email,
                    'actor_role': event.actor_role,
                    'target_model': event.target_model,
                    'target_id': event.target_id,
                    'outcome': event.outcome,
                    'ip_address': event.ip_address,
                    'metadata': event.metadata
                }
            })
        
        # Send to Datadog (batch up to 1000 logs)
        batch_size = 1000
        for i in range(0, len(logs), batch_size):
            batch = logs[i:i + batch_size]
            
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=batch,
                    timeout=30
                )
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Failed to export to Datadog: {e}")
                return False
        
        return True
    
    @staticmethod
    def export_to_webhook(audit_events: List[AuditEvent], webhook_url: str, webhook_secret: str = ''):
        """
        Export audit events to generic webhook.
        
        Args:
            audit_events: List of AuditEvent instances
            webhook_url: Webhook URL
            webhook_secret: Optional webhook secret for HMAC signature
        
        Returns:
            bool: True if successful
        """
        if not audit_events:
            return True
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'ConsultantPro-Audit-Export/1.0'
        }
        
        # Add HMAC signature if secret provided
        if webhook_secret:
            import hmac
            import hashlib
            
            payload = json.dumps([{
                'timestamp': e.timestamp.isoformat(),
                'firm_id': e.firm_id,
                'category': e.category,
                'action': e.action,
                'actor_email': e.actor_email,
                'outcome': e.outcome
            } for e in audit_events])
            
            signature = hmac.new(
                webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            headers['X-Signature-SHA256'] = signature
        
        # Send events
        try:
            response = requests.post(
                webhook_url,
                headers=headers,
                json=[{
                    'timestamp': e.timestamp.isoformat(),
                    'firm_id': e.firm_id,
                    'category': e.category,
                    'action': e.action,
                    'severity': e.severity,
                    'actor_email': e.actor_email,
                    'actor_role': e.actor_role,
                    'target_model': e.target_model,
                    'target_id': e.target_id,
                    'outcome': e.outcome,
                    'ip_address': e.ip_address,
                    'metadata': e.metadata
                } for e in audit_events],
                timeout=30
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Failed to export to webhook: {e}")
            return False


def send_security_alert_notification(alert: SecurityAlert):
    """
    Send notification for security alert.
    
    Args:
        alert: SecurityAlert instance
    
    Returns:
        bool: True if notification sent successfully
    """
    # Get firm admin emails
    from modules.firm.models import FirmMembership
    
    admins = FirmMembership.objects.filter(
        firm=alert.firm,
        role__in=['owner', 'admin', 'firm_admin'],
        is_active=True
    ).select_related('user')
    
    admin_emails = [m.user.email for m in admins if m.user.email]
    
    if not admin_emails:
        return False
    
    # Compose email
    subject = f'[{alert.severity.upper()}] Security Alert: {alert.title}'
    message = f"""
Security Alert Detected

Severity: {alert.get_severity_display()}
Type: {alert.get_alert_type_display()}
Firm: {alert.firm.name}

{alert.description}

Detected at: {alert.detected_at.strftime('%Y-%m-%d %H:%M:%S')}

Please review this alert in the security dashboard.
    """.strip()
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False
        )
        
        # Mark as notified
        alert.notification_sent = True
        alert.notification_sent_at = timezone.now()
        alert.save(update_fields=['notification_sent', 'notification_sent_at'])
        
        return True
    except Exception as e:
        print(f"Failed to send security alert notification: {e}")
        return False
