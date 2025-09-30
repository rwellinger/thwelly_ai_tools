"""
Celery App Package
Exportiert die wichtigsten Objekte für einfachen Import
"""
# IMPORTANT: Initialize loguru BEFORE importing celery_config
from utils.logger import logger  # noqa: F401

from .celery_config import celery_app
from .tasks import generate_song_task, generate_instrumental_task
from .slot_manager import get_slot_status

__all__ = ['celery_app', 'generate_song_task', 'generate_instrumental_task', 'get_slot_status']
