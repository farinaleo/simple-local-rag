"""Admin registration for the documents app."""

from django.contrib import admin

from documents.models import Chunk, Document, Query


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin view of documents with their ingestion status."""

    list_display = ("id", "original_filename", "status", "size_bytes", "updated_at")
    list_filter = ("status",)


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    """Admin view of chunks."""

    list_display = ("id", "document", "ordinal")
    list_filter = ("document",)


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    """Admin view of the query history."""

    list_display = ("id", "created_at", "question")
    filter_horizontal = ("sources",)
