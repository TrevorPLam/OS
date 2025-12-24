"""
Tests for Platform Privacy Enforcement (TIER 0.5).

Verifies that:
1. UserProfile is automatically created for new users
2. Platform operators cannot access content fields
3. Break-glass operators can access content only with active session
4. Content fields are properly marked on models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from modules.firm.models import Firm, UserProfile, BreakGlassSession
from modules.firm.permissions import DenyPlatformContentAccess
from modules.firm.content_privacy import get_content_fields, is_content_field
from modules.documents.models import Document, Folder, Version
from modules.crm.models import Lead, Prospect, Campaign
from modules.finance.models import Invoice, Bill
from modules.projects.models import Project, Task, TimeEntry


User = get_user_model()


class UserProfileCreationTestCase(TestCase):
    """Test automatic UserProfile creation."""
    
    def test_user_profile_created_on_user_creation(self):
        """Test that UserProfile is automatically created when User is created."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Profile should be auto-created
        self.assertTrue(hasattr(user, 'platform_profile'))
        self.assertIsNotNone(user.platform_profile)
        self.assertEqual(user.platform_profile.user, user)
        self.assertIsNone(user.platform_profile.platform_role)
    
    def test_platform_operator_role(self):
        """Test setting platform operator role."""
        user = User.objects.create_user(
            username='operator',
            email='operator@example.com',
            password='testpass123'
        )
        
        profile = user.platform_profile
        profile.platform_role = UserProfile.PLATFORM_ROLE_OPERATOR
        profile.save()
        
        # Verify role properties
        self.assertTrue(profile.is_platform_operator)
        self.assertFalse(profile.is_break_glass_operator)
        self.assertTrue(profile.is_platform_staff)
    
    def test_break_glass_operator_role(self):
        """Test setting break-glass operator role."""
        user = User.objects.create_user(
            username='breakglass',
            email='breakglass@example.com',
            password='testpass123'
        )
        
        profile = user.platform_profile
        profile.platform_role = UserProfile.PLATFORM_ROLE_BREAK_GLASS
        profile.save()
        
        # Verify role properties
        self.assertFalse(profile.is_platform_operator)
        self.assertTrue(profile.is_break_glass_operator)
        self.assertTrue(profile.is_platform_staff)


class ContentFieldMarkingTestCase(TestCase):
    """Test that content fields are properly marked on models."""
    
    def test_document_models_have_content_fields(self):
        """Test that document models have CONTENT_FIELDS defined."""
        self.assertTrue(hasattr(Document, 'CONTENT_FIELDS'))
        self.assertTrue(hasattr(Folder, 'CONTENT_FIELDS'))
        self.assertTrue(hasattr(Version, 'CONTENT_FIELDS'))
        
        # Verify specific fields are marked
        self.assertIn('description', Document.CONTENT_FIELDS)
        self.assertIn('s3_key', Document.CONTENT_FIELDS)
        self.assertIn('description', Folder.CONTENT_FIELDS)
        self.assertIn('change_summary', Version.CONTENT_FIELDS)
    
    def test_crm_models_have_content_fields(self):
        """Test that CRM models have CONTENT_FIELDS defined."""
        self.assertTrue(hasattr(Lead, 'CONTENT_FIELDS'))
        self.assertTrue(hasattr(Prospect, 'CONTENT_FIELDS'))
        self.assertTrue(hasattr(Campaign, 'CONTENT_FIELDS'))
        
        # Verify notes/descriptions are marked
        self.assertIn('notes', Lead.CONTENT_FIELDS)
        self.assertIn('notes', Prospect.CONTENT_FIELDS)
        self.assertIn('description', Campaign.CONTENT_FIELDS)
    
    def test_finance_models_have_content_fields(self):
        """Test that finance models have CONTENT_FIELDS defined."""
        self.assertTrue(hasattr(Invoice, 'CONTENT_FIELDS'))
        self.assertTrue(hasattr(Bill, 'CONTENT_FIELDS'))
        
        # Verify line items and notes are marked
        self.assertIn('line_items', Invoice.CONTENT_FIELDS)
        self.assertIn('notes', Invoice.CONTENT_FIELDS)
        self.assertIn('line_items', Bill.CONTENT_FIELDS)
    
    def test_project_models_have_content_fields(self):
        """Test that project models have CONTENT_FIELDS defined."""
        self.assertTrue(hasattr(Project, 'CONTENT_FIELDS'))
        self.assertTrue(hasattr(Task, 'CONTENT_FIELDS'))
        self.assertTrue(hasattr(TimeEntry, 'CONTENT_FIELDS'))
        
        # Verify descriptions are marked
        self.assertIn('description', Project.CONTENT_FIELDS)
        self.assertIn('description', Task.CONTENT_FIELDS)
        self.assertIn('description', TimeEntry.CONTENT_FIELDS)


class ContentPrivacyUtilsTestCase(TestCase):
    """Test content privacy utility functions."""
    
    def test_get_content_fields(self):
        """Test get_content_fields utility."""
        fields = get_content_fields(Document)
        self.assertIsInstance(fields, list)
        self.assertGreater(len(fields), 0)
        self.assertIn('description', fields)
    
    def test_is_content_field(self):
        """Test is_content_field utility."""
        self.assertTrue(is_content_field(Document, 'description'))
        self.assertTrue(is_content_field(Document, 's3_key'))
        self.assertFalse(is_content_field(Document, 'name'))
        self.assertFalse(is_content_field(Document, 'created_at'))


class PlatformOperatorPermissionTestCase(TestCase):
    """Test platform operator permission restrictions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(
            name='Test Firm',
            slug='test-firm'
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        
        self.operator_user = User.objects.create_user(
            username='operator',
            email='operator@example.com',
            password='testpass123'
        )
        self.operator_user.platform_profile.platform_role = UserProfile.PLATFORM_ROLE_OPERATOR
        self.operator_user.platform_profile.save()
        
        self.breakglass_user = User.objects.create_user(
            username='breakglass',
            email='breakglass@example.com',
            password='testpass123'
        )
        self.breakglass_user.platform_profile.platform_role = UserProfile.PLATFORM_ROLE_BREAK_GLASS
        self.breakglass_user.platform_profile.save()
    
    def test_regular_user_can_access_content(self):
        """Test that regular users can access content."""
        permission = DenyPlatformContentAccess()
        
        # Create mock request
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.regular_user)
        self.assertTrue(permission.has_permission(request, None))
    
    def test_platform_operator_denied_content_access(self):
        """Test that platform operators are denied content access."""
        permission = DenyPlatformContentAccess()
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.operator_user)
        self.assertFalse(permission.has_permission(request, None))
    
    def test_breakglass_without_session_denied(self):
        """Test that break-glass operators need active session."""
        permission = DenyPlatformContentAccess()
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
                self.firm = None
        
        request = MockRequest(self.breakglass_user)
        # Without active break-glass session, should be denied
        self.assertFalse(permission.has_permission(request, None))
    
    def test_breakglass_with_active_session_allowed(self):
        """Test that break-glass operators with active session can access content."""
        # Create active break-glass session
        session = BreakGlassSession.objects.create(
            firm=self.firm,
            operator=self.breakglass_user,
            reason='Emergency support ticket #1234',
            expires_at=timezone.now() + timedelta(hours=4)
        )
        
        permission = DenyPlatformContentAccess()
        
        class MockRequest:
            def __init__(self, user, firm):
                self.user = user
                self.firm = firm
        
        request = MockRequest(self.breakglass_user, self.firm)
        # With active session, should be allowed
        self.assertTrue(permission.has_permission(request, None))
        
        # Clean up
        session.delete()


class BreakGlassSessionTestCase(TestCase):
    """Test break-glass session lifecycle."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.firm = Firm.objects.create(
            name='Test Firm',
            slug='test-firm'
        )
        
        self.operator = User.objects.create_user(
            username='operator',
            email='operator@example.com',
            password='testpass123'
        )
        self.operator.platform_profile.platform_role = UserProfile.PLATFORM_ROLE_BREAK_GLASS
        self.operator.platform_profile.save()
    
    def test_active_session_properties(self):
        """Test active break-glass session properties."""
        session = BreakGlassSession.objects.create(
            firm=self.firm,
            operator=self.operator,
            reason='Support ticket #1234',
            expires_at=timezone.now() + timedelta(hours=4)
        )
        
        self.assertTrue(session.is_active)
        self.assertFalse(session.is_expired)
        self.assertEqual(session.status, BreakGlassSession.STATUS_ACTIVE)
    
    def test_expired_session_properties(self):
        """Test expired break-glass session properties."""
        session = BreakGlassSession.objects.create(
            firm=self.firm,
            operator=self.operator,
            reason='Support ticket #1234',
            expires_at=timezone.now() - timedelta(hours=1)  # Already expired
        )
        
        # Mark as expired
        session.mark_expired()
        
        self.assertFalse(session.is_active)
        self.assertTrue(session.is_expired)
