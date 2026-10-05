"""API token models: hashed bearer tokens with scopes for external clients."""

import hashlib
import secrets

from django.conf import settings
from django.db import models

TOKEN_PREFIX = "rag_"
DEFAULT_SCOPES = ["documents:read", "documents:write", "query", "ocr"]


def generate_token():
    """Generate a new plaintext token with its SHA-256 hash.

    Returns:
        The (plaintext, hash) pair; only the hash is persisted.

    """
    plaintext = TOKEN_PREFIX + secrets.token_urlsafe(32)
    return plaintext, hash_token(plaintext)


def hash_token(plaintext):
    """Return the SHA-256 hex digest of a plaintext token.

    Args:
        plaintext: The bearer token string.

    Returns:
        The hex digest stored in the database.

    """
    return hashlib.sha256(plaintext.encode()).hexdigest()


class Scope(models.TextChoices):
    """The capabilities an API token can carry; no admin scope exists."""

    DOCUMENTS_READ = "documents:read"
    DOCUMENTS_WRITE = "documents:write"
    QUERY = "query"
    OCR = "ocr"


class ApiToken(models.Model):
    """A bearer token owned by a user, stored hashed with its scopes.

    Attributes:
        user: The owning user.
        name: A human label chosen at creation.
        token_hash: The SHA-256 of the plaintext token (never stored raw).
        scopes: The granted capabilities.
        created_at: Creation timestamp.
        last_used_at: Last successful authentication, None if unused.
        is_active: Whether the token authenticates; paused tokens reject.
        expires_at: Optional expiry date.

    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_tokens"
    )
    name = models.CharField(max_length=100)
    token_hash = models.CharField(max_length=64, unique=True)
    scopes = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta options for the token model."""

        verbose_name = "api token"
        verbose_name_plural = "api tokens"
        ordering = ["-created_at"]

    def __str__(self):
        """Return a readable label for admin listings."""
        return f"{self.user.username}/{self.name}"

    @property
    def usable(self):
        """Return False when expired, paused or hard-deleted."""
        from django.utils import timezone

        if not self.is_active:
            return False
        if self.expires_at is not None and self.expires_at <= timezone.now():
            return False
        return True

    def has_scope(self, scope):
        """Return whether the token carries the given scope.

        Args:
            scope: One of the Scope values.

        Returns:
            Whether the scope is granted to this token.

        """
        return scope in self.scopes
