"""Django project configuration package for the RAG API."""

from config.celery import app as celery_app

__all__ = ("celery_app",)
