"""DRF views for the query API: SSE streaming and history."""

import json
import logging

from django.db import transaction
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.token_auth import QueryPermission
from documents.models import Query
from queries.serializers import QuerySerializer
from rag_core.generator import generate_answer
from rag_core.retriever import retrieve_chunks

logger = logging.getLogger(__name__)


class QueryView(APIView):
    """Answer a question with Server-Sent Events streaming."""

    permission_classes = [QueryPermission]

    def post(self, request):
        """Stream a grounded answer, then persist it with its sources.

        Args:
            request: The JSON request carrying ``{"question": "..."}``.

        Returns:
            A StreamingHttpResponse of SSE events: one ``token`` event
            per generated piece, then a final ``sources`` event with
            the chunk references; 400 on a missing question.
        """
        question = (request.data.get("question") or "").strip()
        if not question:
            return Response({"detail": "no question provided"}, status=status.HTTP_400_BAD_REQUEST)

        retrieved = retrieve_chunks(question, user=request.user)
        chunks = list(retrieved)
        chunk_texts = [chunk.content for chunk in chunks]

        return StreamingHttpResponse(
            _sse_stream(question, chunks, chunk_texts, user=request.user),
            content_type="text/event-stream",
        )


def _sse_stream(question, chunks, chunk_texts, user=None):
    """Yield the SSE events of one question-answering session.

    Args:
        question: The user question.
        chunks: The retrieved source chunks.
        chunk_texts: The plain text of each source chunk.

    Yields:
        ``token`` events carrying answer pieces, then a ``sources``
        event; on generation failure an ``error`` event and a failed
        query row is recorded (no zombie rows).

    Args:
        user: The requesting user, recorded on the Query row.
    """
    try:
        _thinking, content = generate_answer(question, chunk_texts)
    except Exception as error:  # noqa: BLE001 — surfaced to the client
        logger.exception("query generation failed")
        _record_failed_query(question, str(error), user=user)
        yield _sse_event("error", {"detail": "generation failed"})
        return

    for piece in _split_answer_pieces(content):
        yield _sse_event("token", {"text": piece})

    query = _record_query(question, content, chunks, user=user)
    sources = QuerySerializer(query).data["sources"]
    yield _sse_event("sources", {"query_id": query.pk, "sources": sources})


def _split_answer_pieces(answer):
    """Split an answer into streamed pieces.

    Args:
        answer: The complete generated answer.

    Returns:
        The answer split into word-level pieces for progressive display.
    """
    return [f"{piece} " for piece in answer.split(" ") if piece]


def _sse_event(event, data):
    """Format one SSE event.

    Args:
        event: The SSE event name.
        data: The JSON-serializable payload.

    Returns:
        The wire format of the event.
    """
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _record_query(question, answer, chunks, user=None):
    """Persist a successful exchange with its sources.

    Args:
        question: The user question.
        answer: The generated answer.
        chunks: The retrieved source chunks.
        user: The requesting user, recorded on the Query row.

    Returns:
        The created Query row.
    """
    with transaction.atomic():
        query = Query.objects.create(
            question=question,
            answer=answer,
            user=user if getattr(user, "is_authenticated", False) else None,
        )
        query.sources.set(chunks)
    return query


def _record_failed_query(question, error, user=None):
    """Persist a failed exchange, error stored on the answer field.

    Args:
        question: The user question.
        error: The generation error message.
        user: The requesting user, recorded on the Query row.
    """
    Query.objects.create(
        question=question,
        answer=f"[generation failed] {error}",
        user=user if getattr(user, "is_authenticated", False) else None,
    )


class QueryHistoryView(APIView):
    """Past exchanges for the frontend history panel."""

    def get(self, request):
        """Return the past queries newest-first with their sources."""
        queryset = Query.objects.prefetch_related("sources").all()
        if request.user.is_authenticated:
            queryset = queryset.filter(user=request.user)
        serializer = QuerySerializer(queryset, many=True)
        return Response(serializer.data)
