"""DRF serializers for the query history API."""

from rest_framework import serializers

from documents.models import Document, Query
from documents.serializers import ChunkSerializer


class SourceDocumentSerializer(serializers.ModelSerializer):
    """Minimal document info carried by a query source."""

    class Meta:
        """Model and fields exposed for a source reference."""

        model = Document
        fields = ["id", "original_filename"]


class QuerySourceSerializer(ChunkSerializer):
    """A source chunk with a reference to its parent document."""

    document = SourceDocumentSerializer(read_only=True)

    class Meta(ChunkSerializer.Meta):
        """Model and fields exposed for a source."""

        fields = ChunkSerializer.Meta.fields + ["document"]


class QuerySerializer(serializers.ModelSerializer):
    """Query history entry: question, answer and sources."""

    sources = QuerySourceSerializer(many=True, read_only=True)

    class Meta:
        """Model and fields exposed by the history endpoint."""

        model = Query
        fields = ["id", "question", "answer", "sources", "created_at"]
