"""Celery application wired to the Django project.

Tasks live in the ``ingestion`` app; the Redis broker URL is driven by
the ``CELERY_BROKER_URL`` environment variable.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("rag_api")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
