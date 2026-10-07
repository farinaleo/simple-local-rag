"""External API surface tests: OpenAPI schema, docs, bearer flow."""

import json

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from accounts.models import Profile
from accounts.token_models import ApiToken, generate_token
from tests.fakes import FakeEmbeddingModel

pytestmark = pytest.mark.django_db

client = APIClient()


def test_schema_covers_documents_and_query_endpoints():
    """The OpenAPI schema lists the documents and query endpoints."""
    response = client.get("/api/schema/", HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    schema = response.json()
    assert "/api/documents/" in schema["paths"]
    assert "/api/documents/{id}/" in schema["paths"]
    assert "/api/query/" in schema["paths"]


def test_schema_documents_bearer_auth_and_request_bodies():
    """The schema exposes the bearer scheme and describes request bodies."""
    response = client.get("/api/schema.json/")
    assert response.status_code == 200
    schema = response.json()
    schemes = schema["components"]["securitySchemes"]
    assert schemes["bearerAuth"]["type"] == "http"
    assert schemes["bearerAuth"]["scheme"] == "bearer"
    query = schema["paths"]["/api/query/"]["post"]
    assert "application/json" in query["requestBody"]["content"]
    upload = schema["paths"]["/api/documents/"]["post"]
    assert "multipart/form-data" in upload["requestBody"]["content"]
    health = schema["paths"]["/api/health/"]["get"]["responses"]["200"]
    assert "application/json" in health["content"]


def test_schema_operation_ids_are_unique():
    """No generated operationId collides after explicit disambiguation."""
    response = client.get("/api/schema.json/")
    schema = response.json()
    operation_ids = [
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if "operationId" in operation
    ]
    assert len(operation_ids) == len(set(operation_ids))
    assert "documents_list" in operation_ids
    assert "documents_retrieve" in operation_ids


def test_docs_page_renders():
    """The browsable documentation page renders with the JSON download link."""
    response = client.get("/api/docs/")
    assert response.status_code == 200
    assert b"/api/schema.json/" in response.content


def test_schema_json_endpoint_serves_json():
    """The schema.json endpoint always serves the OpenAPI schema as JSON."""
    response = client.get("/api/schema.json/")
    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert "/api/query/" in schema["paths"]


@pytest.fixture(autouse=True)
def eager_celery(settings, monkeypatch, tmp_path):
    """Run ingestion inline and write uploads to a temporary directory."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    monkeypatch.setattr("ingestion.embedding.get_embedding_model", lambda: FakeEmbeddingModel())
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))


def test_bearer_flow_upload_then_query(monkeypatch):
    """An external client runs the full flow: token -> upload -> query."""
    user = User.objects.create_user(username="leo", password="password123")
    Profile.objects.update_or_create(user=user, defaults={"role": "user"})
    plaintext, token_hash = generate_token()
    ApiToken.objects.create(
        user=user,
        name="cli",
        token_hash=token_hash,
        scopes=["documents:read", "documents:write", "query"],
    )
    token_client = APIClient()
    headers = {"HTTP_AUTHORIZATION": f"Bearer {plaintext}"}

    listing = token_client.get("/api/documents/", **headers)
    assert listing.status_code == 200

    from django.core.files.uploadedfile import SimpleUploadedFile

    upload = token_client.post(
        "/api/documents/",
        {"file": SimpleUploadedFile("kb.txt", b"The tower is tall.", "text/plain")},
        format="multipart",
        **headers,
    )
    assert upload.status_code == 202

    monkeypatch.setattr(
        "queries.views.generate_answer",
        lambda question, texts: ("", "The tower is tall and made of iron."),
    )
    query = token_client.post(
        "/api/query/",
        {"question": "How tall?"},
        format="json",
        **headers,
    )
    assert query.status_code == 200
    assert query["Content-Type"].startswith("text/event-stream")
    tokens = []
    for part in query.streaming_content:
        for block in part.decode().split("\n\n"):
            if block.startswith("event: token"):
                tokens.append(json.loads(block.splitlines()[1].removeprefix("data: ")))
    assert "".join(entry["text"] for entry in tokens).strip() != ""
