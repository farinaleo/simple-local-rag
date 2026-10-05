"""URL configuration for the RAG API.

Routes the DRF endpoints under the /api/ prefix and serves the media
storage (avatars) in DEBUG mode; nginx serves it in deployments.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/health/", include("health.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/query/", include("queries.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
