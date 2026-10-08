"""DRF views for the query API: SSE streaming and history."""

import json
import logging
import os

from django.db import transaction
from django.db.models import Prefetch
from django.http import StreamingHttpResponse
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.token_auth import QueryPermission
from documents.models import Conversation, Query, build_conversation_title
from queries.serializers import (
    ConversationDetailSerializer,
    ConversationSerializer,
    QuerySerializer,
)
from rag_core.generator import stream_answer
from rag_core.retriever import retrieve_chunks

logger = logging.getLogger(__name__)


class QueryRequestSerializer(serializers.Serializer):
    """Body of a chat query: the question to answer."""

    question = serializers.CharField(help_text="The question to answer.")
    conversation_id = serializers.IntegerField(
        required=False, help_text="Conversation to append the exchange to."
    )


class QueryView(APIView):
    """Answer a question with Server-Sent Events streaming."""

    permission_classes = [QueryPermission]

    @extend_schema(
        request=QueryRequestSerializer,
        responses={
            200: OpenApiResponse(
                description="Server-Sent Events stream: `token` events carrying "
                "answer pieces, then a final `sources` event with the chunk "
                "references.",
            ),
            400: OpenApiResponse(description="No question provided."),
        },
    )
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

        conversation = _resolve_conversation(request)
        if conversation is None:
            return Response({"detail": "conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        retrieved = retrieve_chunks(question, user=request.user)
        chunks = list(retrieved)
        chunk_texts = [chunk.content for chunk in chunks]
        history = _conversation_history(conversation)

        return StreamingHttpResponse(
            _sse_stream(
                question,
                chunks,
                chunk_texts,
                user=request.user,
                conversation=conversation,
                history=history,
            ),
            content_type="text/event-stream",
        )


def _conversation_history(conversation):
    """Return the past exchanges of a conversation for prompting.

    Args:
        conversation: The conversation the new question belongs to.

    Returns:
        The last HISTORY_TURNS exchanges, oldest first, each as a
        ``(question, answer)`` pair.
    """
    max_turns = int(os.environ.get("HISTORY_TURNS", "6"))
    messages = conversation.messages.order_by("created_at")
    if max_turns > 0:
        messages = messages[max(0, messages.count() - max_turns) :]
    return [(message.question, message.answer) for message in messages]


def _resolve_conversation(request):
    """Return the conversation the exchange belongs to.

    Args:
        request: The chat query request.

    Returns:
        The existing conversation matching conversation_id when the
        caller may use it, a fresh conversation titled from the question
        when no id is provided, or None when the id does not resolve to
        an accessible conversation.
    """
    conversation_id = request.data.get("conversation_id")
    question = (request.data.get("question") or "").strip()
    if conversation_id is None:
        owner = request.user if getattr(request.user, "is_authenticated", False) else None
        return Conversation.objects.create(owner=owner, title=build_conversation_title(question))
    try:
        conversation = Conversation.objects.get(pk=conversation_id)
    except Conversation.DoesNotExist:
        return None
    if conversation.owner_id is None:
        return conversation
    if not getattr(request.user, "is_authenticated", False):
        return None
    return conversation if conversation.owner_id == request.user.pk else None


def _sse_stream(question, chunks, chunk_texts, user=None, conversation=None, history=None):
    """Yield the SSE events of one question-answering session.

    Args:
        question: The user question.
        chunks: The retrieved source chunks.
        chunk_texts: The plain text of each source chunk.
        history: The previous exchanges of the conversation, oldest
            first, each as a ``(question, answer)`` pair.

    Yields:
        ``token`` events carrying answer pieces, then a ``sources``
        event; on generation failure an ``error`` event and a failed
        query row is recorded (no zombie rows).

    Args:
        user: The requesting user, recorded on the Query row.
        conversation: The conversation the exchange belongs to.
    """
    pieces = []
    try:
        for piece in stream_answer(question, chunk_texts, history=history):
            pieces.append(piece)
            yield _sse_event("token", {"text": piece})
    except Exception as error:  # noqa: BLE001 — surfaced to the client
        logger.exception("query generation failed")
        _record_failed_query(question, str(error), user=user, conversation=conversation)
        yield _sse_event("error", {"detail": "generation failed"})
        return

    content = "".join(pieces).strip("\n")
    query = _record_query(question, content, chunks, user=user, conversation=conversation)
    sources = QuerySerializer(query).data["sources"]
    yield _sse_event(
        "sources",
        {
            "query_id": query.pk,
            "conversation_id": conversation.pk if conversation else None,
            "sources": sources,
        },
    )


def _sse_event(event, data):
    """Format one SSE event.

    Args:
        event: The SSE event name.
        data: The JSON-serializable payload.

    Returns:
        The wire format of the event.
    """
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _record_query(question, answer, chunks, user=None, conversation=None):
    """Persist a successful exchange with its sources.

    Args:
        question: The user question.
        answer: The generated answer.
        chunks: The retrieved source chunks.
        user: The requesting user, recorded on the Query row.
        conversation: The conversation the exchange belongs to.

    Returns:
        The created Query row.
    """
    with transaction.atomic():
        query = Query.objects.create(
            question=question,
            answer=answer,
            user=user if getattr(user, "is_authenticated", False) else None,
            conversation=conversation,
        )
        query.sources.set(chunks)
        if conversation is not None:
            Conversation.objects.filter(pk=conversation.pk).update(updated_at=timezone.now())
    return query


def _record_failed_query(question, error, user=None, conversation=None):
    """Persist a failed exchange, error stored on the answer field.

    Args:
        question: The user question.
        error: The generation error message.
        user: The requesting user, recorded on the Query row.
        conversation: The conversation the exchange belongs to.
    """
    Query.objects.create(
        question=question,
        answer=f"[generation failed] {error}",
        user=user if getattr(user, "is_authenticated", False) else None,
        conversation=conversation,
    )


class QueryHistoryView(APIView):
    """Past exchanges for the frontend history panel."""

    @extend_schema(responses=QuerySerializer(many=True))
    def get(self, request):
        """Return the past queries newest-first with their sources."""
        queryset = Query.objects.prefetch_related("sources").all()
        if request.user.is_authenticated:
            queryset = queryset.filter(user=request.user)
        serializer = QuerySerializer(queryset, many=True)
        return Response(serializer.data)


class ConversationListView(APIView):
    """Conversations of the requesting user, newest activity first."""

    @extend_schema(responses=ConversationSerializer(many=True))
    def get(self, request):
        """Return the conversations owned by the requesting user."""
        queryset = Conversation.objects.all()
        if request.user.is_authenticated:
            queryset = queryset.filter(owner=request.user)
        else:
            queryset = queryset.filter(owner__isnull=True)
        serializer = ConversationSerializer(queryset, many=True)
        return Response(serializer.data)


class ConversationDetailView(APIView):
    """Detail and deletion of a single conversation."""

    def _get_conversation(self, request, pk):
        """Return the conversation when the caller may access it.

        Args:
            request: The requesting HTTP request.
            pk: Primary key of the conversation.

        Returns:
            The conversation row, or None when missing or not accessible.
        """
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return None
        if conversation.owner_id is None:
            return conversation
        if not request.user.is_authenticated:
            return None
        return conversation if conversation.owner_id == request.user.pk else None

    @extend_schema(responses={200: ConversationDetailSerializer, 404: OpenApiResponse()})
    def get(self, request, pk):
        """Return a conversation with its messages."""
        conversation = self._get_conversation(request, pk)
        if conversation is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        conversation = Conversation.objects.prefetch_related(
            Prefetch("messages", queryset=Query.objects.order_by("created_at"))
        ).get(pk=conversation.pk)
        serializer = ConversationDetailSerializer(conversation)
        return Response(serializer.data)

    def delete(self, request, pk):
        """Delete a conversation and its messages."""
        conversation = self._get_conversation(request, pk)
        if conversation is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
