"""URL configuration for the RAG API.

Routes the DRF endpoints under the /api/ prefix.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", include("health.urls")),
    path("api/documents/", include("documents.urls")),
]
