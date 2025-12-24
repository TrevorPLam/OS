"""
Signals for automatic model creation and lifecycle management.

TIER 0.5: Auto-create UserProfile for all users to track platform roles.
TIER 0.6: Auto-log break-glass events for audit trail.
"""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile, BreakGlassSession, AuditEvent


User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Auto-create UserProfile when a User is created.
    
    TIER 0.5: Every user needs a profile to track platform roles.
    Default platform_role is None (regular firm user).
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save UserProfile when User is saved.
    
    Ensures profile exists even if signal was missed.
    """
    if not hasattr(instance, 'platform_profile'):
        UserProfile.objects.get_or_create(user=instance)
    else:
        instance.platform_profile.save()


@receiver(post_save, sender=BreakGlassSession)
def log_break_glass_lifecycle(sender, instance, created, **kwargs):
    """
    Auto-log break-glass lifecycle events.
    
    TIER 0.6: All break-glass activations, revocations, and state changes
    are automatically logged to the immutable audit trail.
    """
    if created:
        # Log activation
        AuditEvent.log_break_glass_activation(instance)
    else:
        # Check for revocation
        if instance.status == BreakGlassSession.STATUS_REVOKED and instance.revoked_at:
            # Only log if this is a new revocation (not already logged)
            existing_revoke_log = AuditEvent.objects.filter(
                target_model='BreakGlassSession',
                target_id=str(instance.id),
                action=AuditEvent.ACTION_BG_REVOKED
            ).exists()
            
            if not existing_revoke_log:
                # Use the operator as the revoker if no specific user is available
                revoked_by = instance.operator
                AuditEvent.log_break_glass_revocation(instance, revoked_by)

