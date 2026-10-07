"""URL routes for the query API."""

from django.urls import path

from queries.views import (
    ConversationDetailView,
    ConversationListView,
    QueryHistoryView,
    QueryView,
)

urlpatterns = [
    path("", QueryView.as_view(), name="query"),
    path("history/", QueryHistoryView.as_view(), name="query-history"),
    path("conversations/", ConversationListView.as_view(), name="conversations"),
    path(
        "conversations/<int:pk>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
]
