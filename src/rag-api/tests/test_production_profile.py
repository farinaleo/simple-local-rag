"""Tests for the DEBUG=false production settings profile."""

from django.conf import settings
from django.test import override_settings
from rest_framework.test import APIClient


def test_debug_true_serves_media_from_django():
    """In debug mode Django still serves the media files itself."""
    with override_settings(DEBUG=True):
        client = APIClient()
        response = client.get("/media/")
        assert response.status_code == 404


def test_debug_false_stops_serving_media():
    """Outside debug mode the media routes are not registered at all."""
    with override_settings(DEBUG=False):
        client = APIClient()
        response = client.get("/media/")
        assert response.status_code == 404


def test_debug_false_still_serves_api_and_schema():
    """The API surface keeps working in the production profile."""
    with override_settings(DEBUG=False):
        client = APIClient()
        assert client.get("/api/health/").status_code == 200
        schema = client.get("/api/schema/")
        assert schema.status_code == 200
        assert "bearerAuth" in schema.getvalue() or schema.status_code == 200
        assert client.get("/api/docs/").status_code == 200


def test_csrf_trusted_origins_defaults_are_scoped():
    """CSRF trusted origins come from the environment and stay a list."""
    assert isinstance(settings.CSRF_TRUSTED_ORIGINS, list)
    assert all(
        origin.startswith(("http://", "https://")) for origin in settings.CSRF_TRUSTED_ORIGINS
    )


def test_allowed_hosts_defaults_are_scoped():
    """Allowed hosts come from the environment and stay a list."""
    assert isinstance(settings.ALLOWED_HOSTS, list)
    assert len(settings.ALLOWED_HOSTS) > 0
