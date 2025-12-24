"""
Signals for automatic model creation and lifecycle management.

TIER 0.5: Auto-create UserProfile for all users to track platform roles.
"""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


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
