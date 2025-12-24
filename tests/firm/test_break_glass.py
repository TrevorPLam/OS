"""
Tests for Break-Glass Access and Audit Events (TIER 0.6).

Verifies that:
1. Break-glass sessions can be activated
2. Sessions auto-expire
3. Sessions can be revoked early
4. All actions are logged immutably
5. Impersonation mode is properly indicated
6. Time limits are enforced
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from modules.firm.models import Firm, UserProfile, BreakGlassSession, AuditEvent


User = get_user_model()


class BreakGlassActivationTestCase(TestCase):
    """Test break-glass activation and lifecycle."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(
            name='Test Firm',
            slug='test-firm'
        )
        
        self.operator = User.objects.create_user(
            username='breakglass',
            email='breakglass@example.com',
            password='testpass123'
        )
        self.operator.platform_profile.platform_role = UserProfile.PLATFORM_ROLE_BREAK_GLASS
        self.operator.platform_profile.save()
    
    def test_session_creation_logs_activation(self):
        """Test that creating a session logs an activation event."""
        # Count existing events
        initial_count = AuditEvent.objects.count()
        
        # Create session
        session = BreakGlassSession.objects.create(
            firm=self.firm,
            operator=self.operator,
            reason='Emergency support ticket #1234',
            expires_at=timezone.now() + timedelta(hours=4)
        )
        
        # Verify activation event was logged
        new_count = AuditEvent.objects.count()
        self.assertEqual(new_count, initial_count + 1)
        
        # Verify event details
        event = AuditEvent.objects.latest('timestamp')
        self.assertEqual(event.category, AuditEvent.CATEGORY_BREAK_GLASS)
        self.assertEqual(event.action, AuditEvent.ACTION_BG_ACTIVATED)
        self.assertEqual(event.actor, self.operator)
        self.assertEqual(event.firm, self.firm)
        self.assertIn('Emergency support', event.reason)
    
    def test_session_revocation_logs_event(self):
        """Test that revoking a session logs a revocation event."""
        # Create session
        session = BreakGlassSession.objects.create(
            firm=self.firm,
            operator=self.operator,
            reason='Emergency support ticket #1234',
            expires_at=timezone.now() + timedelta(hours=4)
        )
        
        # Count events after creation
        count_after_create = AuditEvent.objects.count()
        
        # Revoke session
        session.revoke('Support completed')
        session.save()
        
        # Verify revocation event was logged
        new_count = AuditEvent.objects.count()
        self.assertEqual(new_count, count_after_create + 1)
        
        # Verify event details
        event = AuditEvent.objects.latest('timestamp')
        self.assertEqual(event.category, AuditEvent.CATEGORY_BREAK_GLASS)
        self.assertEqual(event.action, AuditEvent.ACTION_BG_REVOKED)
        self.assertIn('Support completed', event.reason)
    
    def test_session_expiry_detection(self):
        """Test that sessions are detected as expired after time limit."""
        # Create session that already expired
        session = BreakGlassSession.objects.create(
            firm=self.firm,
            operator=self.operator,
            reason='Emergency support ticket #1234',
            expires_at=timezone.now() - timedelta(hours=1)  # Expired 1 hour ago
        )
        
        # Check expiry
        self.assertTrue(session.is_expired)
        self.assertFalse(session.is_active)
    
    def test_active_session_properties(self):
        """Test active session properties."""
        session = BreakGlassSession.objects.create(
            firm=self.firm,
            operator=self.operator,
            reason='Emergency support ticket #1234',
            expires_at=timezone.now() + timedelta(hours=4)
        )
        
        self.assertFalse(session.is_expired)
        self.assertTrue(session.is_active)
        self.assertEqual(session.status, BreakGlassSession.STATUS_ACTIVE)
    
    def test_reason_required_for_activation(self):
        """Test that reason is required for activation."""
        with self.assertRaises(Exception):
            BreakGlassSession.objects.create(
                firm=self.firm,
                operator=self.operator,
                reason='',  # Empty reason should fail
                expires_at=timezone.now() + timedelta(hours=4)
            )


class AuditEventImmutabilityTestCase(TestCase):
    """Test audit event immutability."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(
            name='Test Firm',
            slug='test-firm'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_audit_event_cannot_be_updated(self):
        """Test that audit events cannot be modified after creation."""
        event = AuditEvent.objects.create(
            firm=self.firm,
            category=AuditEvent.CATEGORY_AUTH,
            action='test_action',
            actor=self.user,
            actor_username=self.user.username,
            reason='Test event'
        )
        
        # Try to update
        with self.assertRaises(ValueError):
            event.reason = 'Modified reason'
            event.save()
    
    def test_audit_event_cannot_be_deleted(self):
        """Test that audit events cannot be deleted."""
        event = AuditEvent.objects.create(
            firm=self.firm,
            category=AuditEvent.CATEGORY_AUTH,
            action='test_action',
            actor=self.user,
            actor_username=self.user.username,
            reason='Test event'
        )
        
        # Try to delete
        with self.assertRaises(ValueError):
            event.delete()
    
    def test_audit_event_denormalizes_actor_info(self):
        """Test that actor info is denormalized for immutability."""
        event = AuditEvent.objects.create(
            firm=self.firm,
            category=AuditEvent.CATEGORY_AUTH,
            action='test_action',
            actor=self.user,
            reason='Test event'
        )
        
        # Verify denormalized fields
        self.assertEqual(event.actor_username, self.user.username)
        self.assertEqual(event.actor_email, self.user.email)


class BreakGlassContentAccessTestCase(TestCase):
    """Test content access during break-glass sessions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(
            name='Test Firm',
            slug='test-firm'
        )
        
        self.operator = User.objects.create_user(
            username='breakglass',
            email='breakglass@example.com',
            password='testpass123'
        )
        self.operator.platform_profile.platform_role = UserProfile.PLATFORM_ROLE_BREAK_GLASS
        self.operator.platform_profile.save()
    
    def test_content_access_logged(self):
        """Test that content access during break-glass is logged."""
        # Create active session
        session = BreakGlassSession.objects.create(
            firm=self.firm,
            operator=self.operator,
            reason='Emergency support ticket #1234',
            expires_at=timezone.now() + timedelta(hours=4)
        )
        
        # Log content access
        event = AuditEvent.log_break_glass_content_access(
            session=session,
            target_model='Document',
            target_id='123',
            description='Accessed confidential document'
        )
        
        # Verify event was logged
        self.assertEqual(event.category, AuditEvent.CATEGORY_BREAK_GLASS)
        self.assertEqual(event.action, AuditEvent.ACTION_BG_CONTENT_ACCESS)
        self.assertEqual(event.actor, self.operator)
        self.assertEqual(event.firm, self.firm)
        self.assertEqual(event.target_model, 'Document')
        self.assertEqual(event.target_id, '123')
    
    def test_multiple_content_accesses_logged_separately(self):
        """Test that each content access is logged separately."""
        session = BreakGlassSession.objects.create(
            firm=self.firm,
            operator=self.operator,
            reason='Emergency support ticket #1234',
            expires_at=timezone.now() + timedelta(hours=4)
        )
        
        initial_count = AuditEvent.objects.filter(
            action=AuditEvent.ACTION_BG_CONTENT_ACCESS
        ).count()
        
        # Log multiple accesses
        AuditEvent.log_break_glass_content_access(
            session, 'Document', '1', 'Doc 1'
        )
        AuditEvent.log_break_glass_content_access(
            session, 'Document', '2', 'Doc 2'
        )
        AuditEvent.log_break_glass_content_access(
            session, 'Invoice', '3', 'Invoice 3'
        )
        
        new_count = AuditEvent.objects.filter(
            action=AuditEvent.ACTION_BG_CONTENT_ACCESS
        ).count()
        
        self.assertEqual(new_count, initial_count + 3)
