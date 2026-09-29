"""Tests for the health endpoint."""

from rest_framework.test import APIClient


def test_health_endpoint_returns_ok():
    """The health endpoint answers 200 with {"status": "ok"}."""
    client = APIClient()
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
