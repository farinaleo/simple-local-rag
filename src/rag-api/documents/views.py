"""DRF views for the documents API: upload, list, detail, delete."""

import mimetypes
import os

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document
from documents.serializers import DocumentDetailSerializer, DocumentSerializer
from ingestion.tasks import ingest_document

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


class DocumentListCreateView(APIView):
    """List documents and handle asynchronous multipart uploads."""

    def get(self, request):
        """Return every document with name, size, status and timestamps."""
        queryset = Document.objects.all().order_by("-created_at")
        serializer = DocumentSerializer(queryset, many=True)
        return Response(serializer.data)

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

        document = self._store_upload(uploaded, extension)
        ingest_document.delay(document.pk)

        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def _store_upload(self, uploaded, extension):
        """Persist an uploaded file and create its pending Document row.

        Args:
            uploaded: The Django uploaded file object.
            extension: The validated lowercase extension.

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
        )


class DocumentDetailView(APIView):
    """Detail and atomic deletion of a single document."""

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
        serializer = DocumentDetailSerializer(document)
        return Response(serializer.data)

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
            try:
                os.remove(document.storage_path)
            except OSError:
                pass
            document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
