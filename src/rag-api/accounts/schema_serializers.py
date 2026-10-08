"""drf-spectacular serializers for the accounts API views.

The accounts views build their payloads by hand (profile, roles,
tokens), so the OpenAPI generator cannot guess any serializer for
them. This module provides the request and response schemas used by
the ``@extend_schema`` annotations of those views. Each serializer is
built once at import time so component names stay unique.
"""

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

TOKEN_STATUS_CHOICES = [("active", "Active"), ("paused", "Paused"), ("expired", "Expired")]

_credentials_request = inline_serializer(
    name="Credentials",
    fields={
        "username": serializers.CharField(),
        "password": serializers.CharField(write_only=True),
    },
)

_user_response = inline_serializer(
    name="UserSession",
    fields={"id": serializers.IntegerField(), "username": serializers.CharField()},
)

_me_response = inline_serializer(
    name="Me",
    fields={
        "id": serializers.IntegerField(),
        "username": serializers.CharField(),
        "role": serializers.ChoiceField(choices=["user", "admin"]),
        "must_change_password": serializers.BooleanField(),
    },
)

_profile_response = inline_serializer(
    name="Profile",
    fields={
        "id": serializers.IntegerField(),
        "username": serializers.CharField(),
        "display_name": serializers.CharField(),
        "avatar_url": serializers.CharField(allow_null=True),
        "role": serializers.ChoiceField(choices=["user", "admin"]),
    },
)

_profile_update_request = inline_serializer(
    name="ProfileUpdate",
    fields={
        "display_name": serializers.CharField(required=False),
        "avatar": serializers.ImageField(required=False),
    },
)

_password_change_request = inline_serializer(
    name="PasswordChange",
    fields={
        "old_password": serializers.CharField(required=False, write_only=True),
        "new_password": serializers.CharField(write_only=True),
    },
)

_token_fields = {
    "id": serializers.IntegerField(),
    "name": serializers.CharField(),
    "scopes": serializers.ListField(child=serializers.CharField()),
    "status": serializers.ChoiceField(choices=TOKEN_STATUS_CHOICES),
    "created_at": serializers.DateTimeField(),
}

_token_response = inline_serializer(name="Token", fields=dict(_token_fields))

_token_with_secret_response = inline_serializer(
    name="TokenWithSecret",
    fields={**_token_fields, "token": serializers.CharField(help_text="one-time plaintext")},
)

_token_create_request = inline_serializer(
    name="TokenCreate",
    fields={
        "name": serializers.CharField(),
        "scopes": serializers.ListField(child=serializers.CharField(), required=False),
    },
)

_token_update_request = inline_serializer(
    name="TokenUpdate",
    fields={"is_active": serializers.BooleanField(required=False)},
)

_admin_user_fields = {
    "id": serializers.IntegerField(),
    "username": serializers.CharField(),
    "display_name": serializers.CharField(),
    "avatar_url": serializers.CharField(allow_null=True),
    "role": serializers.ChoiceField(choices=["user", "admin"]),
    "is_active": serializers.BooleanField(),
    "must_change_password": serializers.BooleanField(),
}

_admin_user_response = inline_serializer(name="AdminUser", fields=dict(_admin_user_fields))

_admin_user_created_response = inline_serializer(
    name="AdminUserCreated",
    fields={**_admin_user_fields, "temporary_password": serializers.CharField()},
)

_admin_user_updated_response = inline_serializer(
    name="AdminUserUpdated",
    fields={
        **_admin_user_fields,
        "sessions_revoked": serializers.IntegerField(required=False),
        "temporary_password": serializers.CharField(required=False),
    },
)

_admin_user_create_request = inline_serializer(
    name="AdminUserCreate",
    fields={
        "username": serializers.CharField(),
        "role": serializers.ChoiceField(choices=["user", "admin"], required=False),
    },
)

_admin_user_update_request = inline_serializer(
    name="AdminUserUpdate",
    fields={
        "role": serializers.ChoiceField(choices=["user", "admin"], required=False),
        "is_active": serializers.BooleanField(required=False),
        "reset_password": serializers.BooleanField(required=False),
    },
)

_admin_token_response = inline_serializer(
    name="AdminToken",
    fields={
        **_token_fields,
        "user": serializers.CharField(help_text="owner username"),
    },
)

_role_update_request = inline_serializer(
    name="RoleUpdate",
    fields={"role": serializers.ChoiceField(choices=["user", "admin"])},
)


def _many(serializer):
    """Wrap an inline serializer for a list response.

    Args:
        serializer: The item serializer built at import time above.

    Returns:
        A ListSerializer child usable in ``@extend_schema`` responses.
    """
    return serializers.ListSerializer(child=type(serializer)())
