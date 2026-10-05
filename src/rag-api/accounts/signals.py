"""Signal handlers keeping a profile row in sync with each user."""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid="accounts_create_profile")
def create_profile(sender, instance, created, **kwargs):
    """Create the missing profile row whenever a user is saved.

    Args:
        sender: The user model class.
        instance: The user being saved.
        created: Whether the user was just created.
        kwargs: Additional signal arguments (unused).

    """
    from accounts.models import Profile

    Profile.objects.get_or_create(user=instance)
