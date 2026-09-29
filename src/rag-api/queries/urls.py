"""URL routes for the query API."""

from django.urls import path

from queries.views import QueryHistoryView, QueryView

urlpatterns = [
    path("", QueryView.as_view(), name="query"),
    path("history/", QueryHistoryView.as_view(), name="query-history"),
]
