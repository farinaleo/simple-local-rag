"""DRF serializers for the query history API."""

from rest_framework import serializers

from documents.models import Conversation, Document, Query
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


class ConversationSerializer(serializers.ModelSerializer):
    """Conversation list entry: title and last activity timestamp."""

    class Meta:
        """Model and fields exposed by the conversation list endpoint."""

        model = Conversation
        fields = ["id", "title", "created_at", "updated_at"]


class ConversationDetailSerializer(serializers.ModelSerializer):
    """A conversation with its full message history."""

    messages = QuerySerializer(many=True, read_only=True)

    class Meta:
        """Model and fields exposed by the conversation detail endpoint."""

        model = Conversation
        fields = ["id", "title", "messages", "created_at", "updated_at"]
