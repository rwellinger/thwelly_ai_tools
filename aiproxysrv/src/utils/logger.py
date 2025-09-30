"""
Centralized logging configuration using loguru.
Replaces all print() statements with structured logging.
"""
import sys
import logging
from loguru import logger

from config.settings import LOG_LEVEL

# Remove default logger
logger.remove()

# Console handler: INFO and above with colors
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)

# Flask-Logging auf loguru umleiten
class LoguruHandler(logging.Handler):
    def emit(self, record):
        # LogRecord in loguru format umwandeln
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Frame für korrekte Anzeige finden
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

# Celery-Logging auf loguru umleiten
class CeleryInterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

# Export configured logger
__all__ = ["logger"]