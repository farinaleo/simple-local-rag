"""DRF views for the documents API: upload, list, detail, delete."""

import mimetypes
import os

from django.db import transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.token_auth import DocumentsReadPermission, DocumentsWritePermission
from documents.models import Document, DocumentVisibility
from documents.serializers import DocumentDetailSerializer, DocumentSerializer
from ingestion.tasks import ingest_document

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".png", ".jpg", ".jpeg"}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


class DocumentUploadSerializer(serializers.Serializer):
    """Multipart body of a document upload."""

    file = serializers.FileField(help_text="The document file to ingest.")


class DocumentListCreateView(APIView):
    """List documents and handle asynchronous multipart uploads."""

    def get_permissions(self):
        """Scope-aware permissions: read to list, write to upload."""
        if self.request.method == "POST":
            return [DocumentsWritePermission()]
        return [DocumentsReadPermission()]

    @extend_schema(
        operation_id="documents_list",
        responses=DocumentSerializer(many=True),
    )
    def get(self, request):
        """Return the documents the user can read, newest first."""
        queryset = _readable_documents(request.user).order_by("-created_at")
        serializer = DocumentSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=DocumentUploadSerializer,
        responses={
            202: DocumentSerializer,
            400: OpenApiResponse(description="Unsupported type, missing file or oversized upload."),
        },
    )
    def post(self, request):
        """Store an uploaded file and dispatch its ingestion (202).

        Args:
            request: The multipart request carrying the ``file`` part.

        Returns:
            202 with the document id when accepted, 400 on a rejected
            extension, missing file or oversized upload.
        """
        uploaded = request.FILES.get("file")
        if uploaded is None:
            return Response({"detail": "no file provided"}, status=status.HTTP_400_BAD_REQUEST)

        extension = os.path.splitext(uploaded.name)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            return Response(
                {"detail": f"unsupported file type: {extension or 'none'}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if uploaded.size > MAX_UPLOAD_BYTES:
            return Response(
                {"detail": "file too large (max 50 MB)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document = self._store_upload(uploaded, extension, request.user)
        ingest_document.delay(document.pk)

        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def _store_upload(self, uploaded, extension, user):
        """Persist an uploaded file and create its pending Document row.

        Args:
            uploaded: The Django uploaded file object.
            extension: The validated lowercase extension.
            user: The uploading user (None when anonymous).

        Returns:
            The created Document (status pending).
        """
        storage_dir = os.environ.get("UPLOAD_DIR", "uploads")
        os.makedirs(storage_dir, exist_ok=True)
        storage_path = os.path.join(storage_dir, f"doc_{uploaded.name}")
        with open(storage_path, "wb+") as destination:
            for chunk in uploaded.chunks():
                destination.write(chunk)

        return Document.objects.create(
            original_filename=uploaded.name,
            storage_path=storage_path,
            mime_type=uploaded.content_type
            or mimetypes.guess_type(uploaded.name)[0]
            or "application/octet-stream",
            size_bytes=uploaded.size,
            owner=user if getattr(user, "is_authenticated", False) else None,
        )


def _readable_documents(user):
    """Documents a user can read: their own plus shared ones.

    Args:
        user: The requesting user (anonymous when session auth is off).

    Returns:
        A queryset of readable documents.
    """
    if user is None or not user.is_authenticated:
        return Document.objects.all()
    from django.db.models import Q

    return Document.objects.filter(Q(owner=user) | Q(visibility=DocumentVisibility.SHARED))


class DocumentDetailView(APIView):
    """Detail and atomic deletion of a single document."""

    def get_permissions(self):
        """Scope-aware permissions: read to view, write to delete."""
        if self.request.method == "DELETE":
            return [DocumentsWritePermission()]
        return [DocumentsReadPermission()]

    @extend_schema(
        operation_id="documents_retrieve",
        responses={200: DocumentDetailSerializer, 404: OpenApiResponse()},
    )
    def get(self, request, pk):
        """Return a document including its chunks.

        Args:
            request: The GET request.
            pk: Primary key of the document.

        Returns:
            200 with the document, 404 when it does not exist.
        """
        try:
            document = Document.objects.prefetch_related("chunks").get(pk=pk)
        except Document.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not document.is_readable_by(request.user):
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = DocumentDetailSerializer(document)
        return Response(serializer.data)

    @extend_schema(
        operation_id="documents_destroy",
        responses={204: OpenApiResponse(), 404: OpenApiResponse()},
    )
    def delete(self, request, pk):
        """Delete file, row, chunks and embeddings in one transaction.

        Args:
            request: The delete request.
            pk: Primary key of the document.

        Returns:
            204 on success, 404 when the document does not exist.
        """
        with transaction.atomic():
            try:
                document = Document.objects.get(pk=pk)
            except Document.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if not (
                document.owner_id is None
                or (request.user.is_authenticated and document.owner_id == request.user.pk)
            ):
                return Response(status=status.HTTP_404_NOT_FOUND)
            try:
                os.remove(document.storage_path)
            except OSError:
                pass
            document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        operation_id="documents_visibility_update",
        request=inline_serializer(
            name="DocumentVisibilityUpdate",
            fields={"visibility": serializers.ChoiceField(choices=DocumentVisibility.values)},
        ),
        responses={200: DocumentDetailSerializer, 400: OpenApiResponse(), 404: OpenApiResponse()},
    )
    def patch(self, request, pk):
        """Toggle the visibility of a document owned by the user.

        Args:
            request: The JSON request carrying ``{"visibility": "shared"|"private"}``.
            pk: Primary key of the document.

        Returns:
            200 with the document, 404 when it does not exist or is not
            owned by the user, 400 on an invalid visibility value.
        """
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not (
            document.owner_id is None
            or (request.user.is_authenticated and document.owner_id == request.user.pk)
        ):
            return Response(status=status.HTTP_404_NOT_FOUND)
        visibility = request.data.get("visibility")
        if visibility not in DocumentVisibility.values:
            return Response(
                {"detail": "visibility must be 'private' or 'shared'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        document.visibility = visibility
        document.save(update_fields=["visibility", "updated_at"])
        serializer = DocumentSerializer(document)
        return Response(serializer.data)
