"""Data migration: bootstrap the admin account from environment variables."""

import os

from django.db import migrations


def _bootstrap_admin(apps, schema_editor):
    """Create or promote the admin account from ADMIN_USERNAME/ADMIN_PASSWORD.

    Args:
        apps: The migration app registry.
        schema_editor: The schema editor (unused).

    """
    if apps is not None:
        user_model = apps.get_model("auth", "User")
        profile_model = apps.get_model("accounts", "Profile")
    else:
        from django.contrib.auth.models import User as user_model

        from accounts.models import Profile

        profile_model = Profile
    username = os.environ.get("ADMIN_USERNAME", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not username:
        return
    user = user_model.objects.filter(username=username).first()
    if user is None:
        user = user_model.objects.create_user(username=username, password=password)
    elif password:
        user.set_password(password)
        user.save(update_fields=["password"])
    profile_model.objects.update_or_create(user=user, defaults={"role": "admin"})


def remove_bootstrap(apps, schema_editor):
    """No-op reverse: the bootstrapped account is left in place."""
    pass


class Migration(migrations.Migration):
    """Bootstrap admin account from the compose environment."""

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(_bootstrap_admin, remove_bootstrap),
    ]
