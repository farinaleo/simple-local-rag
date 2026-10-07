"""Django settings module driven by environment variables.

Every deployment-specific value (debug flag, secret key, database URL)
is read from the environment, with the single root `.env` file loaded
as convenience defaults — real environment variables take precedence.
"""

import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

# Single source of configuration: the repository root .env file,
# also read by docker compose for interpolation. In containers the app
# lives at /app, so the root only exists on a local checkout: walk the
# parents and load the first .env found, if any.
_ENV_PATH = next(
    (parent / ".env" for parent in Path(__file__).resolve().parents if (parent / ".env").is_file()),
    None,
)
load_dotenv(_ENV_PATH)

BASE_DIR = Path(__file__).resolve().parent.parent

# Version of the served API, reported in the OpenAPI schema and used as a
# single source of truth for V4 releases: bump it with every release that
# changes the API surface, alongside the CHANGELOG entry.
API_VERSION = os.environ.get("API_VERSION", "4.0.0")

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-only-key")
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rag")

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

# CORS: the SPA dev server and the containerized web service.
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
).split(",")

# Parse DATABASE_URL into Django connection parameters (kept simple on
# purpose: no extra dependency, standard postgresql:// URL format).
_url = urlparse(DATABASE_URL)
_db_name = _url.path.lstrip("/")
_db_user = _url.username or ""
_db_password = _url.password or ""
_db_host = _url.hostname or "localhost"
_db_port = str(_url.port or 5432)

INSTALLED_APPS = [
    "accounts",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "health",
    "documents",
    "ingestion",
    "queries",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "config" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _db_name,
        "USER": _db_user,
        "PASSWORD": _db_password,
        "HOST": _db_host,
        "PORT": _db_port,
    }
}

# Same-origin behind the nginx reverse proxy: the SPA is served on the
# same host as the API, so cookies flow without CORS friction.
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
).split(",")

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "accounts.token_auth.BearerTokenAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Simple Local RAG API",
    "DESCRIPTION": "RAG API for documents and chat answers. External clients "
    "authenticate with a Bearer token created on the profile page.",
    "VERSION": API_VERSION,
    "SERVE_INCLUDE_SCHEMA": False,
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = os.environ.get("MEDIA_DIR", BASE_DIR / "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
