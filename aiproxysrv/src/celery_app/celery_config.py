"""
Celery Konfiguration - Zentraler Import-Point für Celery
"""
import logging
from celery import Celery
from celery.signals import setup_logging
from config.settings import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from utils.logger import CeleryInterceptHandler, logger

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
    include=['celery_app.tasks'],
    # Tasks auch explizit importieren beim App-Start
    imports=['celery_app.tasks']
)


# Celery Logging auf loguru umleiten
@setup_logging.connect
def configure_celery_logging(**kwargs):
    """Celery's logging komplett auf loguru umleiten"""

    # Celery Root Logger
    celery_logger = logging.getLogger('celery')
    celery_logger.handlers = [CeleryInterceptHandler()]
    celery_logger.setLevel(logging.DEBUG)
    celery_logger.propagate = False

    # Celery Task Logger
    task_logger = logging.getLogger('celery.task')
    task_logger.handlers = [CeleryInterceptHandler()]
    task_logger.setLevel(logging.DEBUG)
    task_logger.propagate = False

    logger.info("Celery logging configured to use loguru")
