"""DRF serializers for the documents API."""

from rest_framework import serializers

from documents.models import Chunk, Document


class ChunkSerializer(serializers.ModelSerializer):
    """Chunk read serializer: content and ordinal."""

    class Meta:
        """Model and fields exposed by the API."""

        model = Chunk
        fields = ["id", "ordinal", "content"]


class DocumentSerializer(serializers.ModelSerializer):
    """Document read serializer: metadata and status for list and detail."""

    class Meta:
        """Model and fields exposed by the API."""

        model = Document
        fields = [
            "id",
            "original_filename",
            "mime_type",
            "size_bytes",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]


class DocumentDetailSerializer(DocumentSerializer):
    """Document detail serializer including the document chunks."""

    chunks = ChunkSerializer(many=True, read_only=True)

    class Meta(DocumentSerializer.Meta):
        """Model and fields exposed by the detail endpoint."""

        fields = DocumentSerializer.Meta.fields + ["chunks"]
