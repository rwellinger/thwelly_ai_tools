"""
Celery App Package
Exportiert die wichtigsten Objekte für einfachen Import
"""
from .celery_config import celery_app
from .tasks import generate_song_task
from .slot_manager import get_slot_status

__all__ = ['celery_app', 'generate_song_task', 'get_slot_status']
