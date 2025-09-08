"""
Celery Konfiguration - Zentraler Import-Point für Celery
"""
from celery import Celery
from config.settings import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

# Celery App erstellen
celery_app = Celery(
    "taskmgr",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Celery Konfiguration
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_time_limit=1800,
    task_soft_time_limit=1500,
    worker_concurrency=1,
    worker_prefetch_multiplier=1,
    task_acks_late=True,

    # Tasks automatisch entdecken
    include=['celery_app.tasks']
)
