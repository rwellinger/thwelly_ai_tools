"""
Celery Konfiguration - Zentraler Import-Point für Celery
"""
import logging
from celery import Celery
from celery.signals import setup_logging, worker_process_init
from config.settings import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, LOG_LEVEL

# IMPORTANT: Import logger FIRST to initialize loguru before Celery sets up its logging
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


def _configure_loguru_for_celery():
    """Configure all Celery loggers to use loguru"""
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    # Celery Root Logger
    celery_logger = logging.getLogger('celery')
    celery_logger.handlers = [CeleryInterceptHandler()]
    celery_logger.setLevel(log_level)
    celery_logger.propagate = False

    # Celery Task Logger
    task_logger = logging.getLogger('celery.task')
    task_logger.handlers = [CeleryInterceptHandler()]
    task_logger.setLevel(log_level)
    task_logger.propagate = False

    # Root logger for all other modules
    root_logger = logging.getLogger()
    root_logger.handlers = [CeleryInterceptHandler()]
    root_logger.setLevel(log_level)

    logger.info(f"Celery logging configured to use loguru (level={LOG_LEVEL})")


# Celery Logging auf loguru umleiten (wird beim Worker-Start aufgerufen)
@setup_logging.connect
def configure_celery_logging(**kwargs):
    """Celery's logging komplett auf loguru umleiten"""
    _configure_loguru_for_celery()


# Wird bei jedem Worker-Process aufgerufen (wichtig für prefork)
@worker_process_init.connect
def configure_worker_logging(**kwargs):
    """Configure logging for each worker process"""
    _configure_loguru_for_celery()
